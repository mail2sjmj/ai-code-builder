"""
File upload and parsing service.
Handles validation, disk storage, pandas parsing, and session data extraction.
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.config.settings import Settings
from app.session.session_store import SessionData
from app.utils.file_utils import get_session_dir, safe_filename

logger = logging.getLogger(__name__)


async def parse_uploaded_file(
    file: UploadFile,
    settings: Settings,
    *,
    header_row: int | None = None,
    meta_file: UploadFile | None = None,
) -> tuple[str, SessionData]:
    """
    Validate, store, and parse an uploaded CSV/XLSX file.

    Returns:
        (session_id, SessionData) on success.
    Raises:
        HTTPException 422 on validation failure.
        HTTPException 500 on unexpected errors.
    """
    # ── 1. Validate extension ────────────────────────────────────────────────
    original_name = file.filename or "upload"
    suffix = Path(original_name).suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "INVALID_FILE_TYPE",
                "message": f"File type '{suffix}' is not allowed. "
                           f"Accepted: {settings.ALLOWED_EXTENSIONS}",
            },
        )

    # ── 2. Read content + validate size ─────────────────────────────────────
    content = await file.read()
    file_size = len(content)
    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "FILE_TOO_LARGE",
                "message": f"File size {file_size / 1_048_576:.1f} MB exceeds "
                           f"limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
            },
        )
    if file_size == 0:
        raise HTTPException(
            status_code=422,
            detail={"error_code": "EMPTY_FILE", "message": "Uploaded file is empty."},
        )

    # ── 3. Create session directory under INBOUND_DIR ────────────────────────
    # INBOUND_DIR holds uploaded files and their parquet caches for the
    # full session lifetime.  TEMP_DIR is reserved for sandbox execution
    # artifacts which are short-lived and can live on faster/ephemeral storage.
    session_id = str(uuid.uuid4())
    session_dir = get_session_dir(settings.INBOUND_DIR, session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    safe_name = safe_filename(original_name)
    file_path = session_dir / safe_name
    file_path.write_bytes(content)
    logger.info("Saved upload: %s (%d bytes) → %s", original_name, file_size, file_path)

    # ── 4. Parse with pandas ─────────────────────────────────────────────────
    try:
        if meta_file is not None:
            # Meta file supplies the column names; data file contains raw rows only.
            meta_content = await meta_file.read()
            meta_suffix = Path(meta_file.filename or "").suffix.lower()
            import io
            if meta_suffix == ".xlsx":
                meta_df = pd.read_excel(io.BytesIO(meta_content), header=0, nrows=0, engine="openpyxl")
            else:
                meta_df = pd.read_csv(io.BytesIO(meta_content), header=0, nrows=0)
            meta_columns = list(meta_df.columns)

            # Read the data file with no header — every row is a data row.
            if suffix == ".csv":
                df = pd.read_csv(file_path, header=None, on_bad_lines="skip")
            else:
                df = pd.read_excel(file_path, header=None, engine="openpyxl")

            if len(df.columns) != len(meta_columns):
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": "COLUMN_MISMATCH",
                        "message": (
                            f"Meta file has {len(meta_columns)} columns but data file has "
                            f"{len(df.columns)} columns. They must match."
                        ),
                    },
                )
            df.columns = meta_columns
            logger.info("Applied %d meta columns to data file", len(meta_columns))
        else:
            # header_row is 1-indexed from the user; pandas uses 0-indexed.
            pandas_header = (header_row - 1) if header_row is not None else 0
            if suffix == ".csv":
                df = pd.read_csv(file_path, header=pandas_header, on_bad_lines="skip")
            else:
                df = pd.read_excel(file_path, header=pandas_header, engine="openpyxl")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to parse file: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "PARSE_ERROR",
                "message": f"Could not parse file: {exc}",
            },
        ) from exc

    if df.empty:
        raise HTTPException(
            status_code=422,
            detail={"error_code": "EMPTY_DATASET", "message": "File contains no data rows."},
        )

    # ── 5. Cache as parquet for fast re-reads ────────────────────────────────
    parquet_path = session_dir / "data.parquet"
    df.to_parquet(parquet_path, index=False)

    # ── 6. Extract metadata ──────────────────────────────────────────────────
    session_data = SessionData(
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
        file_path=str(file_path),
        parquet_path=str(parquet_path),
        filename=original_name,
        row_count=len(df),
        column_count=len(df.columns),
        columns=df.columns.tolist(),
        dtypes={col: str(dtype) for col, dtype in df.dtypes.items()},
        file_size_bytes=file_size,
    )
    logger.info(
        "Parsed file: session=%s rows=%d cols=%d",
        session_id,
        session_data.row_count,
        session_data.column_count,
    )
    return session_id, session_data
