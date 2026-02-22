"""Instruction refinement endpoint — SSE streaming."""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.api.dependencies import deps_session_store, deps_settings
from app.config.settings import Settings
from app.schemas.instruction import RefineRequest
from app.services.instruction_service import stream_instruction_refinement
from app.session.session_store import SessionStore
from app.utils.streaming import sse_event_generator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Instructions"])


@router.post(
    "/instructions/refine",
    summary="Refine raw instructions into a structured AI prompt",
    description="Streams a refined, structured prompt via Server-Sent Events.",
)
async def refine_instructions(
    body: RefineRequest,
    settings: Settings = Depends(deps_settings),
    session_store: SessionStore = Depends(deps_session_store),
) -> StreamingResponse:
    stream = stream_instruction_refinement(
        session_id=body.session_id,
        raw_instructions=body.raw_instructions,
        session_store=session_store,
        settings=settings,
    )
    return StreamingResponse(
        sse_event_generator(stream),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
