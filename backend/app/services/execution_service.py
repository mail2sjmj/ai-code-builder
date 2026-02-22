"""
Execution orchestration service.
Submits code to the sandbox asynchronously and manages job state.
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import pandas as pd
from fastapi import HTTPException

from app.config.settings import Settings
from app.sandbox.runner import execute_code_in_sandbox
from app.sandbox.validator import validate_code
from app.session.session_store import ExecutionJob, SessionStore

logger = logging.getLogger(__name__)


async def submit_execution_job(
    session_id: str,
    code: str,
    session_store: SessionStore,
    settings: Settings,
) -> str:
    """
    Validate code, enqueue execution, return job_id immediately.

    Raises:
        HTTPException 404 if session not found.
        HTTPException 422 if code fails validation.
    """
    session = await session_store.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )

    # AST validation before any execution
    validation = validate_code(code)
    if not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "CODE_VALIDATION_FAILED",
                "message": "Code failed security validation.",
                "errors": validation.errors,
            },
        )

    job_id = str(uuid.uuid4())
    job = ExecutionJob(job_id=job_id, status="queued")
    await session_store.add_execution_job(session_id, job)

    # Fire-and-forget background task
    asyncio.create_task(
        _run_job(job_id, session_id, code, session_store, settings)
    )
    logger.info("Queued execution job: %s for session: %s", job_id, session_id)
    return job_id


async def _run_job(
    job_id: str,
    session_id: str,
    code: str,
    session_store: SessionStore,
    settings: Settings,
) -> None:
    """Background task: run sandbox, update job status."""
    session = await session_store.get_session(session_id)
    if session is None:
        return

    job = ExecutionJob(
        job_id=job_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    await session_store.update_execution_job(session_id, job)

    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None,
            execute_code_in_sandbox,
            code,
            str(session.parquet_path).replace("data.parquet", ""),  # session_dir
            session.parquet_path,
            settings.SANDBOX_TIMEOUT_SECONDS,
            settings.SANDBOX_MAX_OUTPUT_ROWS,
        )
    except Exception as exc:
        logger.exception("Unexpected error in sandbox: %s", exc)
        job.status = "error"
        job.error_message = f"Internal error: {exc}"
        job.finished_at = datetime.now(timezone.utc)
        await session_store.update_execution_job(session_id, job)
        return

    job.finished_at = datetime.now(timezone.utc)
    job.execution_time_ms = result.execution_time_ms

    if result.success and result.output_csv_path:
        job.status = "success"
        job.output_csv_path = result.output_csv_path
        try:
            df_out = pd.read_csv(result.output_csv_path, nrows=settings.PREVIEW_ROW_COUNT)
            job.preview_columns = df_out.columns.tolist()
            job.preview_rows = df_out.to_dict(orient="records")
        except Exception as exc:
            logger.warning("Could not read output CSV for preview: %s", exc)
            job.preview_rows = []
            job.preview_columns = []
    else:
        job.status = "error"
        error_detail = result.stderr or "Execution failed with no error output."
        if result.timed_out:
            error_detail = f"Timeout: execution exceeded {settings.SANDBOX_TIMEOUT_SECONDS}s limit."
        job.error_message = error_detail

    await session_store.update_execution_job(session_id, job)
    logger.info("Job %s finished with status=%s in %dms", job_id, job.status, result.execution_time_ms)


async def get_execution_result(
    job_id: str,
    session_id: str,
    session_store: SessionStore,
) -> ExecutionJob:
    """Fetch the current state of an execution job."""
    job = await session_store.get_execution_job(session_id, job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "JOB_NOT_FOUND", "message": f"Job '{job_id}' not found."},
        )
    return job


async def stream_output_csv(
    job_id: str,
    session_id: str,
    session_store: SessionStore,
    chunk_size: int = 65536,
) -> AsyncIterator[bytes]:
    """Stream the output CSV file as bytes chunks."""
    job = await get_execution_result(job_id, session_id, session_store)
    if job.status != "success" or not job.output_csv_path:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "OUTPUT_NOT_READY", "message": "Output CSV is not available yet."},
        )
    import aiofiles
    async with aiofiles.open(job.output_csv_path, mode="rb") as f:
        while chunk := await f.read(chunk_size):
            yield chunk
