"""Pydantic schemas for the code generation endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class CodeGenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    refined_prompt: str = Field(min_length=50, max_length=20_000)
