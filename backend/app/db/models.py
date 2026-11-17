"""SQLAlchemy database models for SupportPulse AI."""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from backend.app.db.session import Base


class User(Base):
    """User account with role-based access control."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="agent", nullable=False)  # admin, manager, agent
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Ticket(Base):
    """IT Support ticket with full lifecycle and ML enrichment fields."""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(30), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    requester_id = Column(String(50), nullable=False, index=True)
    department = Column(String(50), nullable=False, index=True)
    channel = Column(String(30), default="portal")  # portal, email, slack, phone
    category = Column(String(50), nullable=False, index=True)
    priority = Column(String(10), nullable=False, index=True)  # P1, P2, P3, P4
    assigned_team = Column(String(50), nullable=False, index=True)
    agent_id = Column(String(50), nullable=True, index=True)
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True, index=True)
    sla_hours = Column(Float, nullable=False)
    breached = Column(Boolean, default=False, index=True)
    reopen_count = Column(Integer, default=0)
    contact_count = Column(Integer, default=1)
    escalated = Column(Boolean, default=False, index=True)
    status = Column(String(30), default="open", index=True)  # open, in_progress, waiting_on_customer, resolved, closed

    # ML Enrichment Fields
    predicted_category = Column(String(50), nullable=True)
    category_confidence = Column(Float, nullable=True)
    predicted_priority = Column(String(10), nullable=True)
    priority_confidence = Column(Float, nullable=True)
    needs_human_triage = Column(Boolean, default=False, index=True)
    sla_breach_probability = Column(Float, nullable=True, index=True)
    sla_risk_band = Column(String(20), default="Low", index=True)  # Low, Medium, High, Critical
    estimated_minutes_to_breach = Column(Float, nullable=True)
    friction_score = Column(Float, default=0.0, index=True)  # 0 to 100
    friction_band = Column(String(20), default="Calm", index=True)  # Calm, Uneasy, Frustrated, Critical
    routing_recommendation = Column(String(100), nullable=True)
    explanation_data = Column(Text, nullable=True)  # JSON serialized explanations

    __table_args__ = (
        Index("idx_ticket_status_risk", "status", "sla_risk_band"),
        Index("idx_ticket_created_at_desc", created_at.desc()),
    )


class Alert(Base):
    """Proactive system alerts generated on risk band escalation."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(30), ForeignKey("tickets.ticket_id"), index=True, nullable=False)
    alert_type = Column(String(50), default="risk_escalation", nullable=False)
    previous_band = Column(String(20), nullable=False)
    current_band = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by = Column(String(50), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Feedback(Base):
    """Agent override and feedback logging for continuous retraining."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(30), ForeignKey("tickets.ticket_id"), index=True, nullable=False)
    original_category = Column(String(50), nullable=False)
    corrected_category = Column(String(50), nullable=False)
    original_priority = Column(String(10), nullable=False)
    corrected_priority = Column(String(10), nullable=False)
    agent_id = Column(String(50), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ModelVersion(Base):
    """Model registry version tracking, metrics, and deployment state."""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(30), unique=True, index=True, nullable=False)
    model_type = Column(String(50), default="all", nullable=False)
    status = Column(String(20), default="candidate", index=True)  # active, candidate, archived
    macro_f1 = Column(Float, nullable=False)
    roc_auc = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=False)
    metrics_json = Column(Text, nullable=False)
    artifact_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    """Dynamic system configuration and threshold overrides."""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)  # JSON-encoded value
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
