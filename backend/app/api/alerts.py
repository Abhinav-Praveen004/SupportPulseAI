"""Alerts API router for proactive SLA breach notifications and acknowledgments."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.db.models import Alert, User
from backend.app.db.session import get_db
from backend.app.schemas.alert import AlertAckResponse, AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(
    acknowledged: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve system alerts with optional acknowledgment filter."""
    query = db.query(Alert)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    alerts = query.order_by(desc(Alert.created_at)).offset(offset).limit(limit).all()
    return alerts


@router.post("/{alert_id}/ack", response_model=AlertAckResponse)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Acknowledge proactive SLA alert by human agent."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    now = datetime.now(timezone.utc)
    alert.acknowledged = True
    alert.acknowledged_by = current_user.username
    alert.acknowledged_at = now
    db.commit()

    return AlertAckResponse(
        id=alert.id,
        acknowledged=True,
        acknowledged_by=current_user.username,
        acknowledged_at=now,
        message=f"Alert {alert_id} acknowledged by {current_user.username}",
    )
