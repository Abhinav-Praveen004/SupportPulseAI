"""End-to-end Integration Smoke Test: Ingest -> Analyse -> Alert -> Feedback -> Retrain -> Rollback."""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.app.db.models import Alert, Feedback, Ticket, User
from backend.app.db.session import SessionLocal
from backend.app.main import app
from backend.app.ml.registry import registry
from backend.app.scheduler.tasks import rescore_open_tickets

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_models():
    """Ensure models are loaded before e2e run."""
    registry.load_active_models()


def test_e2e_ingest_analyse_alert_flow():
    """Verify complete end-to-end cycle: Ingest ticket -> ML analysis -> Rescore -> Alert raised -> Ack."""
    # 1. Login as admin
    login_resp = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Ingest urgent ticket with high follow-up contacts
    create_payload = {
        "subject": "CRITICAL: US-East gateway timeout on VPN",
        "body": "GlobalProtect VPN server unreachable across engineering! UNACCEPTABLE! Third time reporting!",
        "department": "Engineering",
        "channel": "slack",
        "priority": "P1",
        "contact_count": 4,
        "reopen_count": 2,
    }
    t_resp = client.post("/api/tickets", json=create_payload, headers=headers)
    assert t_resp.status_code == 201
    ticket_data = t_resp.json()
    ticket_id = ticket_data["ticket_id"]

    assert ticket_data["predicted_category"] == "Network/VPN"
    assert ticket_data["routing_recommendation"] == "Network Ops"
    assert ticket_data["friction_band"] in ("Uneasy", "Frustrated", "Critical")

    # 3. Simulate elapsed time and risk escalation: set ticket created_at to 6 hours ago
    db = SessionLocal()
    try:
        t_obj = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        t_obj.sla_risk_band = "Low"  # Simulate initial low band
        from datetime import timedelta
        t_obj.created_at = datetime.utcnow() - timedelta(hours=6)
        db.commit()
    finally:
        db.close()

    # Run rescoring task to trigger proactive escalation alert
    rescored = rescore_open_tickets()
    assert rescored >= 1

    # 4. Check for alerts raised
    alerts_resp = client.get("/api/alerts", headers=headers)
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) > 0

    # 5. Acknowledge the alert
    unack_alert = next((a for a in alerts if not a["acknowledged"]), alerts[0])
    ack_resp = client.post(f"/api/alerts/{unack_alert['id']}/ack", headers=headers)
    assert ack_resp.status_code == 200
    assert ack_resp.json()["acknowledged"] is True
    assert ack_resp.json()["acknowledged_by"] == "admin"


def test_e2e_feedback_retrain_rollback_loop():
    """Verify complete continuous learning loop: Agent feedback -> Retrain candidate -> Rollback."""
    login_resp = client.post("/api/auth/login", data={"username": "agent", "password": "agent123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Agent submits override feedback on a ticket
    ticket = client.get("/api/tickets?pageSize=1", headers=headers).json()["items"][0]
    fb_resp = client.post(
        f"/api/tickets/{ticket['ticket_id']}/feedback",
        json={
            "corrected_category": "Cloud/Infrastructure",
            "corrected_priority": "P1",
            "notes": "E2E automated test override",
        },
        headers=headers,
    )
    assert fb_resp.status_code == 200

    # 2. Admin logs in to trigger retrain
    admin_login = client.post("/api/auth/login", data={"username": "admin", "password": "admin123"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}

    retrain_resp = client.post(
        "/api/models/retrain",
        json={"min_feedback_samples": 0, "evaluate_only": False},
        headers=admin_headers,
    )
    assert retrain_resp.status_code == 200
    retrain_data = retrain_resp.json()
    assert "candidate_version" in retrain_data
    assert "promoted" in retrain_data

    # 3. Rollback back to v1.0.0
    rb_resp = client.post("/api/models/v1.0.0/rollback", headers=admin_headers)
    assert rb_resp.status_code == 200
    assert rb_resp.json()["active_version"] == "v1.0.0"
