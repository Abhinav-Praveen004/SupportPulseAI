"""Pydantic schemas for Dashboard, Themes, and Analytics."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    high_critical_risk_count: int
    predicted_breaches_next_4h: int
    avg_friction_score: float
    auto_triaged_share_pct: float
    volume_by_day: List[Dict[str, Any]]
    category_distribution: List[Dict[str, Any]]
    recent_alerts: List[Dict[str, Any]]
    top_at_risk_tickets: List[Dict[str, Any]]


class RiskForecastItem(BaseModel):
    ticket_id: str
    subject: str
    category: str
    priority: str
    assigned_team: str
    sla_risk_band: str
    sla_breach_probability: float
    estimated_minutes_to_breach: float
    elapsed_minutes: float
    target_minutes: float


class RiskForecastResponse(BaseModel):
    total_at_risk: int
    high_critical_count: int
    team_hour_heatmap: List[Dict[str, Any]]
    at_risk_tickets: List[RiskForecastItem]
    precision_recall_curve: List[Dict[str, Any]]
    active_threshold: float


class ThemeItem(BaseModel):
    id: int
    label: str
    top_terms: List[str]
    ticket_count: int
    weekly_trend: List[int]
    is_emerging: bool
    z_score: float
    representative_tickets: List[Dict[str, Any]]


class ThemeListResponse(BaseModel):
    themes: List[ThemeItem]
    total_themes: int
    emerging_count: int
    nmi_sanity_score: float
    ari_sanity_score: float
    last_refreshed: str
