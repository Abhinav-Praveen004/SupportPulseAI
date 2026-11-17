"""Integration tests for Backend FastAPI Endpoints and Auth."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.ml.registry import registry

# Preload models for testing
registry.load_active_models()

client = TestClient(app)


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate demo admin and return bearer token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def agent_token():
    """Authenticate demo agent and return bearer token."""
    response = client.post(
        "/api/auth/login",
        data={"username": "agent", "password": "agent123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


def test_health_endpoints():
    """Verify system health probes."""
    resp1 = client.get("/health")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "ok"

    resp2 = client.get("/api/health")
    assert resp2.status_code == 200
    assert resp2.json()["database_connected"] is True
    assert resp2.json()["models_in_memory"] is True


def test_auth_me(agent_token):
    """Verify /api/auth/me returns authenticated agent profile."""
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {agent_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "agent"
    assert data["role"] == "agent"


def test_stateless_playground_analyze():
    """Verify /api/analyze runs multi-model inference on arbitrary free text."""
    payload = {
        "text": "AnyConnect VPN keeps dropping gateway connection with error 504",
        "department": "Engineering",
        "channel": "portal",
        "contact_count": 2,
    }
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "Network/VPN"
    assert data["category_confidence"] > 0.50
    assert "routing_recommendation" in data
    assert "friction_score" in data
    assert "sla_risk_band" in data
    assert len(data["top_contributing_ngrams"]) > 0


def test_tickets_crud_and_feedback(agent_token):
    """Verify ticket creation, ML analysis, retrieval, patch, and feedback loop."""
    headers = {"Authorization": f"Bearer {agent_token}"}

    # 1. Create ticket
    create_payload = {
        "subject": "Printer on 3rd floor is jamming constantly",
        "body": "Paper tray 2 is stuck and printing stops with error code 12. Multiple people waiting.",
        "department": "Marketing",
        "channel": "slack",
        "contact_count": 2,
    }
    create_resp = client.post("/api/tickets", json=create_payload, headers=headers)
    assert create_resp.status_code == 201
    ticket = create_resp.json()
    ticket_id = ticket["ticket_id"]
    assert ticket["predicted_category"] == "Printer"
    assert ticket["sla_risk_band"] in ("Low", "Medium", "High", "Critical")

    # 2. Retrieve ticket by ID
    get_resp = client.get(f"/api/tickets/{ticket_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["ticket_id"] == ticket_id

    # 3. Patch ticket status
    patch_resp = client.patch(
        f"/api/tickets/{ticket_id}",
        json={"status": "in_progress", "assigned_team": "IT Helpdesk"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "in_progress"

    # 4. Submit feedback override
    feedback_payload = {
        "corrected_category": "Hardware",
        "corrected_priority": "P2",
        "notes": "Physical tray replacement required.",
    }
    fb_resp = client.post(f"/api/tickets/{ticket_id}/feedback", json=feedback_payload, headers=headers)
    assert fb_resp.status_code == 200
    assert fb_resp.json()["status"] == "success"

    # Verify override updated the ticket
    updated_ticket = client.get(f"/api/tickets/{ticket_id}", headers=headers).json()
    assert updated_ticket["category"] == "Hardware"
    assert updated_ticket["priority"] == "P2"


def test_dashboard_summary_and_forecast(agent_token):
    """Verify dashboard KPI metrics and risk forecast endpoints."""
    headers = {"Authorization": f"Bearer {agent_token}"}

    summary_resp = client.get("/api/dashboard/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_tickets"] > 0
    assert "open_tickets" in summary
    assert "volume_by_day" in summary
    assert "category_distribution" in summary

    forecast_resp = client.get("/api/risk/forecast", headers=headers)
    assert forecast_resp.status_code == 200
    forecast = forecast_resp.json()
    assert "total_at_risk" in forecast
    assert "team_hour_heatmap" in forecast
    assert "at_risk_tickets" in forecast


def test_theme_discovery_endpoint(agent_token):
    """Verify themes endpoint returns cluster cards with top terms."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    resp = client.get("/api/themes", headers=headers)
    assert resp.status_code == 200
    themes_data = resp.json()
    assert themes_data["total_themes"] > 0
    assert len(themes_data["themes"]) > 0
    theme1 = themes_data["themes"][0]
    assert "label" in theme1
    assert len(theme1["top_terms"]) > 0
    assert "weekly_trend" in theme1


def test_models_registry_and_status(agent_token):
    """Verify model registry listing and status."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    resp = client.get("/api/models", headers=headers)
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) > 0
    active_v = next((v for v in versions if v["status"] == "active"), None)
    assert active_v is not None
    assert active_v["version"] == "v1.0.0"
