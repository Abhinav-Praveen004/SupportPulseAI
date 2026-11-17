"""Stateless Text Analysis router for the interactive Playground."""

from fastapi import APIRouter
from backend.app.ml.explain import analyze_ticket_text
from backend.app.schemas.ticket import TextAnalysisRequest, TextAnalysisResponse

router = APIRouter(tags=["playground"])


@router.post("/analyze", response_model=TextAnalysisResponse)
def analyze_free_text(payload: TextAnalysisRequest):
    """Stateless inference endpoint for ad-hoc text analysis in the Playground."""
    result = analyze_ticket_text(
        subject=payload.text,
        body="",
        department=payload.department or "Engineering",
        channel=payload.channel or "portal",
        contact_count=payload.contact_count or 1,
        reopen_count=payload.reopen_count or 0,
        elapsed_minutes=payload.elapsed_minutes or 0.0,
    )
    return result
