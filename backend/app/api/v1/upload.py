"""File upload endpoint."""

import logging

from fastapi import APIRouter, Depends, UploadFile

from app.api.dependencies import deps_session_store, deps_settings
from app.config.settings import Settings
from app.schemas.upload import UploadResponse
from app.services.file_service import parse_uploaded_file
from app.session.session_store import SessionStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Upload"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a CSV or XLSX file",
    description="Upload a data file to start a new session. Returns session metadata.",
)
async def upload_file(
    file: UploadFile,
    settings: Settings = Depends(deps_settings),
    session_store: SessionStore = Depends(deps_session_store),
) -> UploadResponse:
    session_id, session_data = await parse_uploaded_file(file, settings)
    await session_store.create_session(session_data)
    logger.info("Upload endpoint: new session %s", session_id)
    return UploadResponse(
        session_id=session_id,
        filename=session_data.filename,
        row_count=session_data.row_count,
        column_count=session_data.column_count,
        columns=session_data.columns,
        dtypes=session_data.dtypes,
        file_size_bytes=session_data.file_size_bytes,
    )
