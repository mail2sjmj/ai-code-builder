"""Pydantic schemas for the code execution endpoints."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExecuteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    code: str = Field(min_length=10, max_length=50_000)


class ExecutionJobResponse(BaseModel):
    job_id: str
    status: str


class ExecutionResult(BaseModel):
    job_id: str
    status: str  # queued | running | success | error
    preview_rows: list[dict] = []
    preview_columns: list[str] = []
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
