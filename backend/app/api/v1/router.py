"""Aggregated v1 API router."""

from fastapi import APIRouter

from app.api.v1 import codegen, execution, instructions, upload

router = APIRouter()
router.include_router(upload.router)
router.include_router(instructions.router)
router.include_router(codegen.router)
router.include_router(execution.router)
