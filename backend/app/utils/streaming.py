"""
Server-Sent Events (SSE) streaming utilities.
"""

import json
import logging
from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)


async def sse_event_generator(
    async_iter: AsyncIterator[str],
) -> AsyncIterator[str]:
    """
    Wrap an async string iterator as an SSE event stream.

    Each chunk is emitted as:  data: {"chunk": "<text>"}\n\n
    A final sentinel:          data: {"done": true}\n\n
    """
    try:
        async for text in async_iter:
            payload = json.dumps({"chunk": text})
            yield f"data: {payload}\n\n"
    except Exception as exc:
        logger.exception("Error during SSE streaming: %s", exc)
        error_payload = json.dumps({"error": str(exc)})
        yield f"data: {error_payload}\n\n"
    finally:
        yield f"data: {json.dumps({'done': True})}\n\n"
