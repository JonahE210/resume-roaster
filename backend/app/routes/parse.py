"""POST /parse — PDF upload -> structured resume JSON + layout boxes."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.parser.assemble import parse_resume
from app.schemas.resume import ParseResult

router = APIRouter(tags=["parse"])


@router.post("/parse", response_model=ParseResult)
async def parse_endpoint(file: UploadFile = File(...)) -> ParseResult:
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(400, "Upload a PDF file.")
    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(400, "Empty file.")
    try:
        return parse_resume(pdf_bytes)
    except Exception as exc:  # noqa: BLE001 - surface parse failures cleanly
        raise HTTPException(422, f"Failed to parse PDF: {exc}") from exc
