"""Background Scheduler for Automated Ticket Rescoring and Alert Escalation."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List
import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.db.models import Alert, Ticket
from backend.app.db.session import SessionLocal
from backend.app.ml.explain import analyze_ticket_text

RISK_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def send_webhook_notification(alert_payload: Dict[str, Any]):
    """Send optional webhook notification if URL configured."""
    if not settings.WEBHOOK_URL:
        return
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post(settings.WEBHOOK_URL, json=alert_payload)
    except Exception as e:
        logger.error(f"Failed to deliver webhook alert: {e}")


def rescore_open_tickets() -> int:
    """Periodic job: rescores open tickets, updates SLA risk, and fires deduplicated alerts."""
    db: Session = SessionLocal()
    rescored_count = 0
    new_alerts_count = 0

    try:
        open_tickets = (
            db.query(Ticket)
            .filter(Ticket.status.in_(["open", "in_progress", "waiting_on_customer"]))
            .all()
        )

        now = datetime.now(timezone.utc)

        for ticket in open_tickets:
            try:
                # Calculate elapsed minutes
                c_dt = ticket.created_at
                if c_dt.tzinfo is None:
                    c_dt = c_dt.replace(tzinfo=timezone.utc)
                elapsed_min = max(0.0, (now - c_dt).total_seconds() / 60.0)

                # Run multi-model analysis
                analysis = analyze_ticket_text(
                    subject=ticket.subject,
                    body=ticket.body,
                    department=ticket.department,
                    channel=ticket.channel,
                    sla_hours=ticket.sla_hours,
                    contact_count=ticket.contact_count,
                    reopen_count=ticket.reopen_count,
                    elapsed_minutes=elapsed_min,
                )

                old_band = ticket.sla_risk_band or "Low"
                new_band = analysis["sla_risk_band"]
                new_prob = analysis["sla_breach_probability"]

                # Check if risk band escalated
                if RISK_ORDER.get(new_band, 1) > RISK_ORDER.get(old_band, 1):
                    # Check for duplicate unacknowledged alert for same band
                    existing = (
                        db.query(Alert)
                        .filter(
                            Alert.ticket_id == ticket.ticket_id,
                            Alert.current_band == new_band,
                            Alert.acknowledged.is_(False),
                        )
                        .first()
                    )

                    if not existing:
                        alert_msg = (
                            f"Proactive SLA Escalation: Ticket {ticket.ticket_id} shifted from "
                            f"{old_band} to {new_band} (breach probability: {new_prob * 100:.1f}%). "
                            f"Est. {analysis['estimated_minutes_to_breach']:.0f} mins remaining."
                        )
                        new_alert = Alert(
                            ticket_id=ticket.ticket_id,
                            alert_type="risk_escalation",
                            previous_band=old_band,
                            current_band=new_band,
                            message=alert_msg,
                            acknowledged=False,
                            created_at=datetime.utcnow(),
                        )
                        db.add(new_alert)
                        new_alerts_count += 1

                        send_webhook_notification({
                            "event": "alert_created",
                            "ticket_id": ticket.ticket_id,
                            "previous_band": old_band,
                            "current_band": new_band,
                            "breach_probability": new_prob,
                            "message": alert_msg,
                        })

                # Update ticket's ML fields
                ticket.predicted_category = analysis["category"]
                ticket.category_confidence = analysis["category_confidence"]
                ticket.predicted_priority = analysis["priority"]
                ticket.priority_confidence = analysis["priority_confidence"]
                ticket.needs_human_triage = analysis["needs_human_triage"]
                ticket.sla_breach_probability = new_prob
                ticket.sla_risk_band = new_band
                ticket.estimated_minutes_to_breach = analysis["estimated_minutes_to_breach"]
                ticket.friction_score = analysis["friction_score"]
                ticket.friction_band = analysis["friction_band"]
                ticket.routing_recommendation = analysis["routing_recommendation"]
                ticket.explanation_data = json.dumps({
                    "top_contributing_ngrams": analysis["top_contributing_ngrams"],
                    "sla_top_drivers": analysis["sla_top_drivers"],
                    "friction_breakdown": analysis["friction_breakdown"],
                    "routing_reasoning": analysis["routing_reasoning"],
                })

                rescored_count += 1
            except Exception as e:
                logger.error(f"Error rescoring ticket {ticket.ticket_id}: {e}")

        db.commit()
        if rescored_count > 0:
            logger.info(f"Scheduler: rescored {rescored_count} open tickets ({new_alerts_count} new alerts raised).")
    finally:
        db.close()

    return rescored_count
