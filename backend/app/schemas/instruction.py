"""Pydantic schemas for the instruction refinement endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class RefineRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    raw_instructions: str = Field(min_length=10, max_length=5000)
