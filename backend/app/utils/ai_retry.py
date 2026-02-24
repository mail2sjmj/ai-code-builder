"""
Retry helpers for Anthropic API calls.

Anthropic can return HTTP 429 (rate-limit) or HTTP 529 (overloaded) transiently.
Both are safe to retry with exponential back-off because no partial work has been
committed on the server side.
"""

import asyncio
import logging
import random
from collections.abc import AsyncIterator, Callable
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

# Status codes that warrant automatic retries
_RETRYABLE_STATUS: frozenset[int] = frozenset({429, 529})

DEFAULT_MAX_RETRIES: int = 5   # mirrors Settings.AI_MAX_RETRIES default
BASE_DELAY_SECS: float = 1.5


def _should_retry(exc: anthropic.APIStatusError, attempt: int, max_retries: int) -> bool:
    return exc.status_code in _RETRYABLE_STATUS and attempt < max_retries


def _delay(attempt: int) -> float:
    """Exponential back-off with ±0.5 s jitter."""
    return BASE_DELAY_SECS * (2 ** attempt) + random.uniform(0.0, 0.5)


async def anthropic_stream_with_retry(
    make_stream: Callable[[], Any],
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> AsyncIterator[str]:
    """
    Yield text chunks from an Anthropic streaming call, retrying on 429/529.

    Retries only when no chunks have been yielded yet — restarting mid-stream
    would produce duplicate output on the SSE channel.

    Args:
        make_stream: Zero-arg callable returning ``client.messages.stream(...)``.
        max_retries: Maximum number of additional attempts after the first failure.
    """
    for attempt in range(max_retries + 1):
        chunks_yielded = False
        try:
            async with make_stream() as stream:
                async for text_delta in stream.text_stream:
                    chunks_yielded = True
                    yield text_delta
            return  # clean completion — exit retry loop
        except anthropic.APIStatusError as exc:
            if _should_retry(exc, attempt, max_retries) and not chunks_yielded:
                wait = _delay(attempt)
                logger.warning(
                    "Anthropic HTTP %d (attempt %d/%d) — retrying in %.1fs",
                    exc.status_code, attempt + 1, max_retries, wait,
                )
                await asyncio.sleep(wait)
            else:
                raise


async def anthropic_accumulate_with_retry(
    make_stream: Callable[[], Any],
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> str:
    """
    Accumulate the full text response from an Anthropic call, retrying on 429/529.

    Used by codegen/autofix services that buffer the entire response before
    post-processing (e.g. stripping markdown fences) and then yield it once.

    Args:
        make_stream: Zero-arg callable returning ``client.messages.stream(...)``.
        max_retries: Maximum number of additional attempts after the first failure.

    Returns:
        Concatenated text string from all stream deltas.
    """
    for attempt in range(max_retries + 1):
        accumulated: list[str] = []
        try:
            async with make_stream() as stream:
                async for text_delta in stream.text_stream:
                    accumulated.append(text_delta)
            return "".join(accumulated)
        except anthropic.APIStatusError as exc:
            if _should_retry(exc, attempt, max_retries):
                wait = _delay(attempt)
                logger.warning(
                    "Anthropic HTTP %d (attempt %d/%d) — retrying in %.1fs",
                    exc.status_code, attempt + 1, max_retries, wait,
                )
                await asyncio.sleep(wait)
            else:
                raise
    return ""  # unreachable — satisfies type-checker
