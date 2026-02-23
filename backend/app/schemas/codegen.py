"""Pydantic schemas for the code generation endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class CodeGenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    refined_prompt: str = Field(min_length=50, max_length=20_000)


class CodeFixRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    broken_code: str = Field(min_length=10, max_length=100_000)
    error_message: str = Field(min_length=1, max_length=5_000)
