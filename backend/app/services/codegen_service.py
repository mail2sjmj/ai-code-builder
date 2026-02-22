"""
Python code generation service — calls Anthropic Claude with SSE streaming.
Strips markdown code fences from streamed output.
"""

import json
import logging
from collections.abc import AsyncIterator

import anthropic
import pandas as pd
from fastapi import HTTPException

from app.config.settings import Settings
from app.prompts.codegen_prompt import (
    CODEGEN_SYSTEM_PROMPT,
    CODEGEN_USER_PROMPT_TEMPLATE,
)
from app.session.session_store import SessionStore

logger = logging.getLogger(__name__)

# Fence patterns to strip from streaming output
_OPENING_FENCES = ("```python", "```py", "```")
_CLOSING_FENCE = "```"


def _strip_fences(text: str) -> str:
    """Remove markdown code fences from a complete code string."""
    lines = text.splitlines()
    if lines and lines[0].strip() in _OPENING_FENCES:
        lines = lines[1:]
    if lines and lines[-1].strip() == _CLOSING_FENCE:
        lines = lines[:-1]
    return "\n".join(lines)


async def stream_code_generation(
    session_id: str,
    refined_prompt: str,
    session_store: SessionStore,
    settings: Settings,
) -> AsyncIterator[str]:
    """
    Stream generated Python code from Anthropic Claude.

    Yields:
        Code text deltas as they arrive.
    Raises:
        HTTPException 404 if session not found.
        HTTPException 502 on Anthropic API errors.
    """
    session = await session_store.get_session(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )

    # Load sample data for context
    try:
        df_sample = pd.read_parquet(session.parquet_path).head(3)
        sample_data_json = json.dumps(df_sample.to_dict(orient="records"), default=str, indent=2)
    except Exception as exc:
        logger.warning("Could not load sample data: %s", exc)
        sample_data_json = "[]"

    column_schema_detailed = "\n".join(
        f"  - {col}: {dtype}" for col, dtype in session.dtypes.items()
    )
    user_prompt = CODEGEN_USER_PROMPT_TEMPLATE.format(
        refined_prompt=refined_prompt,
        filename=session.filename,
        row_count=session.row_count,
        column_schema_detailed=column_schema_detailed,
        sample_data_json=sample_data_json,
    )

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    accumulated: list[str] = []
    fence_stripped = False

    try:
        async with client.messages.stream(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=settings.CODEGEN_MAX_TOKENS,
            system=CODEGEN_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            async for text_delta in stream.text_stream:
                accumulated.append(text_delta)

                # Strip leading fence on first meaningful chunk
                if not fence_stripped:
                    joined = "".join(accumulated)
                    # Wait until we have enough content to detect a fence
                    if len(joined) >= 12 or "\n" in joined:
                        fence_stripped = True
                        first_line_end = joined.find("\n")
                        if first_line_end != -1:
                            first_line = joined[:first_line_end].strip()
                            if first_line in _OPENING_FENCES:
                                # Emit everything after the fence line
                                yield joined[first_line_end + 1:]
                                accumulated.clear()
                                continue
                        # No fence detected — emit accumulated as-is
                        yield joined
                        accumulated.clear()
                else:
                    yield text_delta

            # Flush anything remaining
            if accumulated:
                yield "".join(accumulated)

    except anthropic.RateLimitError as exc:
        logger.warning("Anthropic rate limit: %s", exc)
        raise HTTPException(
            status_code=429,
            detail={"error_code": "RATE_LIMITED", "message": "AI service rate limit reached."},
        ) from exc
    except anthropic.APIError as exc:
        logger.exception("Anthropic API error during code gen: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={"error_code": "AI_API_ERROR", "message": f"AI service error: {exc}"},
        ) from exc
