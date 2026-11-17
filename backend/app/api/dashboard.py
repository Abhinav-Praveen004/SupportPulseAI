"""Dashboard and SLA Risk Analytics API router."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_current_user
from backend.app.db.models import Alert, Ticket, User
from backend.app.db.session import get_db
from backend.app.ml.registry import registry
from backend.app.schemas.dashboard import DashboardSummary, RiskForecastResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve top-level KPI metrics, live risk counts, and volume trends."""
    total_tickets = db.query(Ticket).count()

    open_statuses = ["open", "in_progress", "waiting_on_customer"]
    open_query = db.query(Ticket).filter(Ticket.status.in_(open_statuses))
    open_count = open_query.count()

    # High / Critical risk count
    high_critical_count = open_query.filter(
        Ticket.sla_risk_band.in_(["High", "Critical"])
    ).count()

    # Predicted breaches in next 4 hours
    predicted_next_4h = open_query.filter(
        Ticket.sla_risk_band.in_(["High", "Critical"]),
        Ticket.estimated_minutes_to_breach <= 240.0,
    ).count()

    # Average friction score
    avg_friction = (
        db.query(func.avg(Ticket.friction_score))
        .filter(Ticket.status.in_(open_statuses))
        .scalar()
        or 0.0
    )

    # Auto-triaged share (confidence >= threshold)
    auto_triaged = (
        db.query(Ticket)
        .filter(Ticket.needs_human_triage.is_(False))
        .count()
    )
    auto_share = (auto_triaged / max(1, total_tickets)) * 100.0

    # Volume by day (last 14 days)
    volume_by_day: List[Dict[str, Any]] = []
    # Query ticket counts grouped by date
    daily_rows = (
        db.query(
            func.date(Ticket.created_at).label("day"),
            func.count(Ticket.id).label("count"),
            func.sum(func.case((Ticket.breached.is_(True), 1), else_=0)).label("breached"),
        )
        .group_by(func.date(Ticket.created_at))
        .order_by(desc("day"))
        .limit(14)
        .all()
    )
    for row in reversed(daily_rows):
        volume_by_day.append({
            "date": str(row.day),
            "tickets": int(row.count),
            "breached": int(row.breached or 0),
        })

    # Category distribution for open tickets
    cat_rows = (
        db.query(Ticket.category, func.count(Ticket.id))
        .filter(Ticket.status.in_(open_statuses))
        .group_by(Ticket.category)
        .order_by(desc(func.count(Ticket.id)))
        .all()
    )
    category_dist = [{"category": c, "count": count} for c, count in cat_rows]

    # Recent alerts
    recent_alerts_rows = (
        db.query(Alert)
        .order_by(desc(Alert.created_at))
        .limit(6)
        .all()
    )
    recent_alerts = [
        {
            "id": a.id,
            "ticket_id": a.ticket_id,
            "message": a.message,
            "current_band": a.current_band,
            "previous_band": a.previous_band,
            "acknowledged": a.acknowledged,
            "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for a in recent_alerts_rows
    ]

    # Top at-risk tickets
    top_risk_rows = (
        open_query.order_by(desc(Ticket.sla_breach_probability))
        .limit(5)
        .all()
    )
    top_at_risk = [
        {
            "ticket_id": t.ticket_id,
            "subject": t.subject,
            "category": t.category,
            "priority": t.priority,
            "assigned_team": t.assigned_team,
            "risk_band": t.sla_risk_band,
            "probability": t.sla_breach_probability or 0.0,
            "friction_score": t.friction_score,
            "estimated_minutes": t.estimated_minutes_to_breach or 0.0,
        }
        for t in top_risk_rows
    ]

    return DashboardSummary(
        total_tickets=total_tickets,
        open_tickets=open_count,
        high_critical_risk_count=high_critical_count,
        predicted_breaches_next_4h=predicted_next_4h,
        avg_friction_score=round(float(avg_friction), 1),
        auto_triaged_share_pct=round(auto_share, 1),
        volume_by_day=volume_by_day,
        category_distribution=category_dist,
        recent_alerts=recent_alerts,
        top_at_risk_tickets=top_at_risk,
    )


@router.get("/risk/forecast", response_model=RiskForecastResponse)
def get_risk_forecast(
    threshold: Optional[float] = Query(None, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve ranked at-risk queue, team x hour heat matrix, and precision/recall curve."""
    active_thresh = threshold if threshold is not None else (
        registry.sla_forecaster.alert_threshold if registry.sla_forecaster else 0.50
    )

    open_statuses = ["open", "in_progress", "waiting_on_customer"]
    open_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_(open_statuses))
        .order_by(desc(Ticket.sla_breach_probability))
        .all()
    )

    now = datetime.now(timezone.utc)
    at_risk_items = []
    team_hour_matrix: Dict[str, Dict[int, int]] = {}

    for t in open_tickets:
        prob = t.sla_breach_probability or 0.0
        if prob >= active_thresh:
            c_dt = t.created_at
            if c_dt.tzinfo is None:
                c_dt = c_dt.replace(tzinfo=timezone.utc)
            elapsed_min = max(0.0, (now - c_dt).total_seconds() / 60.0)
            target_min = t.sla_hours * 60.0

            at_risk_items.append({
                "ticket_id": t.ticket_id,
                "subject": t.subject,
                "category": t.category,
                "priority": t.priority,
                "assigned_team": t.assigned_team,
                "sla_risk_band": t.sla_risk_band,
                "sla_breach_probability": round(prob, 4),
                "estimated_minutes_to_breach": round(t.estimated_minutes_to_breach or 0.0, 1),
                "elapsed_minutes": round(elapsed_min, 1),
                "target_minutes": round(target_min, 1),
            })

            # Heatmap bucket
            team_dict = team_hour_matrix.setdefault(t.assigned_team, {h: 0 for h in range(24)})
            team_dict[t.created_at.hour] = team_dict.get(t.created_at.hour, 0) + 1

    # Format heatmap
    heatmap_list = [
        {"team": team, "hours": hours}
        for team, hours in team_hour_matrix.items()
    ]

    # Load precision-recall curve from reports if available
    pr_curve = []
    sla_rep_path = settings.REPORTS_DIR / "sla_risk_metrics.json"
    if sla_rep_path.exists():
        try:
            with open(sla_rep_path, "r", encoding="utf-8") as f:
                sla_rep = json.load(f)
                pr_curve = sla_rep.get("calibration_curve", [])
        except Exception:
            pass

    return RiskForecastResponse(
        total_at_risk=len(at_risk_items),
        high_critical_count=sum(1 for i in at_risk_items if i["sla_risk_band"] in ("High", "Critical")),
        team_hour_heatmap=heatmap_list,
        at_risk_tickets=at_risk_items[:50],  # Return top 50
        precision_recall_curve=pr_curve,
        active_threshold=round(active_thresh, 4),
    )
