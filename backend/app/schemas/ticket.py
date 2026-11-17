"""Pydantic schemas for Tickets and ML Analysis."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TicketBase(BaseModel):
    subject: str = Field(..., min_length=3, max_length=255)
    body: str = Field(..., min_length=5)
    requester_id: Optional[str] = "USR-EMPLOYEE"
    department: Optional[str] = "Engineering"
    channel: Optional[str] = "portal"
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_team: Optional[str] = None
    agent_id: Optional[str] = None
    sla_hours: Optional[float] = None
    contact_count: Optional[int] = 1
    reopen_count: Optional[int] = 0
    escalated: Optional[bool] = False
    status: Optional[str] = "open"


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None
    assigned_team: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[str] = None
    contact_count: Optional[int] = None
    reopen_count: Optional[int] = None
    escalated: Optional[bool] = None


class TicketFeedbackCreate(BaseModel):
    corrected_category: str
    corrected_priority: str
    notes: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    ticket_id: str
    created_at: datetime
    subject: str
    body: str
    requester_id: str
    department: str
    channel: str
    category: str
    priority: str
    assigned_team: str
    agent_id: Optional[str] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    sla_hours: float
    breached: bool
    reopen_count: int
    contact_count: int
    escalated: bool
    status: str

    # ML Fields
    predicted_category: Optional[str] = None
    category_confidence: Optional[float] = None
    predicted_priority: Optional[str] = None
    priority_confidence: Optional[float] = None
    needs_human_triage: bool = False
    sla_breach_probability: Optional[float] = None
    sla_risk_band: str = "Low"
    estimated_minutes_to_breach: Optional[float] = None
    friction_score: float = 0.0
    friction_band: str = "Calm"
    routing_recommendation: Optional[str] = None
    explanation_data: Optional[str] = None

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[TicketOut]


class TextAnalysisRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Ticket subject or combined subject and body")
    department: Optional[str] = "Engineering"
    channel: Optional[str] = "portal"
    contact_count: Optional[int] = 1
    reopen_count: Optional[int] = 0
    elapsed_minutes: Optional[float] = 0.0


class TextAnalysisResponse(BaseModel):
    category: str
    category_confidence: float
    category_probabilities: Dict[str, float]
    priority: str
    priority_confidence: float
    priority_probabilities: Dict[str, float]
    needs_human_triage: bool
    sla_breach_probability: float
    sla_risk_band: str
    estimated_minutes_to_breach: float
    friction_score: float
    friction_band: str
    friction_breakdown: Dict[str, Any]
    routing_recommendation: str
    routing_reasoning: str
    top_contributing_ngrams: List[Dict[str, Any]]
    sla_top_drivers: List[Dict[str, Any]]
