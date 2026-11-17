"""Pydantic schemas for Alerts."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    ticket_id: str
    alert_type: str
    previous_band: str
    current_band: str
    message: str
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertAckResponse(BaseModel):
    id: int
    acknowledged: bool
    acknowledged_by: str
    acknowledged_at: datetime
    message: str
