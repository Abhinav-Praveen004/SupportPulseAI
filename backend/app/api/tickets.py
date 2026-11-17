"""Ticket Management and Real-Time ML Analysis API router."""

import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from backend.app.api.stream import stream_manager
from backend.app.core.security import get_current_user
from backend.app.db.models import Feedback, Ticket, User
from backend.app.db.session import get_db
from backend.app.ml.explain import analyze_ticket_text
from backend.app.schemas.ticket import (
    TextAnalysisRequest,
    TextAnalysisResponse,
    TicketCreate,
    TicketFeedbackCreate,
    TicketListResponse,
    TicketOut,
    TicketUpdate,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new ticket, trigger real-time ML enrichment, and broadcast via SSE."""
    # Generate unique ticket ID
    last_id = db.query(func.max(Ticket.id)).scalar() or 0
    ticket_id = f"TCK-{(last_id + 1):05d}"

    # Target SLA hours
    prio = payload.priority or "P3"
    sla_hours = payload.sla_hours or (
        4.0 if prio == "P1" else 8.0 if prio == "P2" else 24.0 if prio == "P3" else 72.0
    )

    # Run ML analysis
    analysis = analyze_ticket_text(
        subject=payload.subject,
        body=payload.body,
        department=payload.department or "Engineering",
        channel=payload.channel or "portal",
        sla_hours=sla_hours,
        contact_count=payload.contact_count or 1,
        reopen_count=payload.reopen_count or 0,
        elapsed_minutes=0.0,
    )

    cat = payload.category or analysis["category"]
    prio = payload.priority or analysis["priority"]
    team = payload.assigned_team or analysis["routing_recommendation"]

    ticket = Ticket(
        ticket_id=ticket_id,
        created_at=datetime.now(timezone.utc),
        subject=payload.subject,
        body=payload.body,
        requester_id=payload.requester_id or current_user.username,
        department=payload.department or "Engineering",
        channel=payload.channel or "portal",
        category=cat,
        priority=prio,
        assigned_team=team,
        agent_id=payload.agent_id,
        sla_hours=sla_hours,
        breached=False,
        reopen_count=payload.reopen_count or 0,
        contact_count=payload.contact_count or 1,
        escalated=payload.escalated or False,
        status=payload.status or "open",
        # ML Enrichment
        predicted_category=analysis["category"],
        category_confidence=analysis["category_confidence"],
        predicted_priority=analysis["priority"],
        priority_confidence=analysis["priority_confidence"],
        needs_human_triage=analysis["needs_human_triage"],
        sla_breach_probability=analysis["sla_breach_probability"],
        sla_risk_band=analysis["sla_risk_band"],
        estimated_minutes_to_breach=analysis["estimated_minutes_to_breach"],
        friction_score=analysis["friction_score"],
        friction_band=analysis["friction_band"],
        routing_recommendation=analysis["routing_recommendation"],
        explanation_data=json.dumps({
            "top_contributing_ngrams": analysis["top_contributing_ngrams"],
            "sla_top_drivers": analysis["sla_top_drivers"],
            "friction_breakdown": analysis["friction_breakdown"],
            "routing_reasoning": analysis["routing_reasoning"],
        }),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Broadcast event via SSE
    await stream_manager.broadcast("ticket_created", {
        "ticket_id": ticket.ticket_id,
        "subject": ticket.subject,
        "category": ticket.category,
        "priority": ticket.priority,
        "sla_risk_band": ticket.sla_risk_band,
        "friction_score": ticket.friction_score,
        "status": ticket.status,
    })

    return ticket


@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    risk_band: Optional[str] = None,
    friction_band: Optional[str] = None,
    assigned_team: Optional[str] = None,
    needs_triage: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", pattern="^(created_at|risk|friction|priority|sla_hours)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tickets with filtering, pagination, and sorting."""
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)
    if category:
        query = query.filter(Ticket.category == category)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if risk_band:
        query = query.filter(Ticket.sla_risk_band == risk_band)
    if friction_band:
        query = query.filter(Ticket.friction_band == friction_band)
    if assigned_team:
        query = query.filter(Ticket.assigned_team == assigned_team)
    if needs_triage is not None:
        query = query.filter(Ticket.needs_human_triage == needs_triage)
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.ticket_id.ilike(search_fmt),
                Ticket.subject.ilike(search_fmt),
                Ticket.body.ilike(search_fmt),
                Ticket.requester_id.ilike(search_fmt),
            )
        )

    # Sorting
    sort_col = Ticket.created_at
    if sort_by == "risk":
        sort_col = Ticket.sla_breach_probability
    elif sort_by == "friction":
        sort_col = Ticket.friction_score
    elif sort_by == "priority":
        sort_col = Ticket.priority
    elif sort_by == "sla_hours":
        sort_col = Ticket.sla_hours

    if sort_order == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(sort_col)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    return TicketListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed ticket record and associated ML explanations."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update ticket properties and broadcast update via SSE."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    if "status" in update_data and update_data["status"] in ("resolved", "closed") and not ticket.resolved_at:
        ticket.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(ticket)

    await stream_manager.broadcast("ticket_updated", {
        "ticket_id": ticket.ticket_id,
        "status": ticket.status,
        "category": ticket.category,
        "priority": ticket.priority,
        "assigned_team": ticket.assigned_team,
    })

    return ticket


@router.post("/{ticket_id}/feedback")
async def submit_feedback(
    ticket_id: str,
    payload: TicketFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record human agent override for model retraining feedback loop."""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

    feedback = Feedback(
        ticket_id=ticket.ticket_id,
        original_category=ticket.predicted_category or ticket.category,
        corrected_category=payload.corrected_category,
        original_priority=ticket.predicted_priority or ticket.priority,
        corrected_priority=payload.corrected_priority,
        agent_id=current_user.username,
        notes=payload.notes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(feedback)

    # Apply override to ticket
    ticket.category = payload.corrected_category
    ticket.priority = payload.corrected_priority
    ticket.needs_human_triage = False

    db.commit()

    await stream_manager.broadcast("feedback_submitted", {
        "ticket_id": ticket_id,
        "agent": current_user.username,
        "corrected_category": payload.corrected_category,
        "corrected_priority": payload.corrected_priority,
    })

    return {"status": "success", "message": "Feedback recorded for model retraining."}
