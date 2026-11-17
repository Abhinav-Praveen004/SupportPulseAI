# SupportPulse AI - REST API Reference

All endpoints return JSON responses and are prefixed with `/api`. Interactive Swagger documentation is available at `http://localhost:8000/api/docs`.

---

## 1. Authentication (`/api/auth`)

### `POST /api/auth/login`
Authenticate user credentials and receive a signed JWT bearer token.
- **Content-Type**: `application/x-www-form-urlencoded`
- **Request Body**: `username={username}&password={password}`
- **Response** (HTTP 200):
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "role": "agent",
  "username": "agent",
  "full_name": "Sarah Jenkins"
}
```

### `GET /api/auth/me`
Retrieve the authenticated user's profile and active role.
- **Headers**: `Authorization: Bearer <token>`
- **Response** (HTTP 200):
```json
{
  "id": 3,
  "username": "agent",
  "email": "agent@supportpulse.local",
  "full_name": "Sarah Jenkins",
  "role": "agent",
  "is_active": true,
  "created_at": "2026-11-17T12:00:00"
}
```

---

## 2. Tickets Management (`/api/tickets`)

### `POST /api/tickets`
Create a new ticket and immediately execute the synchronous multi-model inference pipeline (M1, M2, M3, M4).
- **Request Body**:
```json
{
  "subject": "VPN gateway timeout error GW-504",
  "body": "GlobalProtect client fails to connect to corporate concentrator.",
  "department": "Engineering",
  "channel": "slack",
  "priority": "P1"
}
```
- **Response** (HTTP 201):
```json
{
  "ticket_id": "TCK-20001",
  "subject": "VPN gateway timeout error GW-504",
  "body": "GlobalProtect client fails to connect to corporate concentrator.",
  "category": "Network/VPN",
  "priority": "P1",
  "assigned_team": "Network Ops",
  "predicted_category": "Network/VPN",
  "category_confidence": 0.968,
  "predicted_priority": "P1",
  "priority_confidence": 0.892,
  "needs_human_triage": false,
  "sla_breach_probability": 0.724,
  "sla_risk_band": "High",
  "estimated_minutes_to_breach": 240.0,
  "friction_score": 45.2,
  "friction_band": "Uneasy",
  "routing_recommendation": "Network Ops",
  "explanation_data": "{\"top_contributing_ngrams\": [{\"ngram\": \"vpn gateway\", \"score\": 0.82}]}"
}
```

### `GET /api/tickets`
List tickets with filtering, full-text search, pagination, and sorting.
- **Query Parameters**:
  - `page`: int (default: 1)
  - `page_size`: int (default: 25, max: 100)
  - `status`: string (`open`, `in_progress`, `waiting_on_customer`, `resolved`, `closed`)
  - `category`: string (one of 10 IT categories)
  - `priority`: string (`P1`, `P2`, `P3`, `P4`)
  - `risk_band`: string (`Low`, `Medium`, `High`, `Critical`)
  - `friction_band`: string (`Calm`, `Uneasy`, `Frustrated`, `Critical`)
  - `needs_triage`: bool (`true`, `false`)
  - `search`: string
  - `sort_by`: string (`created_at`, `risk`, `friction`, `priority`, `sla_hours`)
  - `sort_order`: string (`asc`, `desc`)

### `GET /api/tickets/{ticket_id}`
Retrieve full details and ML explanations for a specific ticket.

### `PATCH /api/tickets/{ticket_id}`
Update ticket fields (status, priority, category, assigned team, assignee).

### `POST /api/tickets/{ticket_id}/feedback`
Log an agent override and correction to feed the continuous retraining pipeline.
- **Request Body**:
```json
{
  "corrected_category": "Cloud/Infrastructure",
  "corrected_priority": "P2",
  "notes": "EC2 instance networking issue rather than local VPN client."
}
```

---

## 3. Playground & Ad-Hoc Inference (`/api/analyze`)

### `POST /api/analyze`
Stateless multi-model evaluation on arbitrary raw text.
- **Request Body**:
```json
{
  "text": "Cannot access HR shared drive after password expiration.",
  "department": "Human Resources",
  "contact_count": 2,
  "reopen_count": 0
}
```
- **Response** (HTTP 200):
```json
{
  "category": "Password/Access",
  "category_confidence": 0.954,
  "priority": "P3",
  "priority_confidence": 0.821,
  "needs_human_triage": false,
  "sla_breach_probability": 0.182,
  "sla_risk_band": "Low",
  "estimated_minutes_to_breach": 1440.0,
  "friction_score": 28.5,
  "friction_band": "Uneasy",
  "routing_recommendation": "IT Helpdesk",
  "top_contributing_ngrams": [
    {"ngram": "password", "score": 0.742},
    {"ngram": "shared drive", "score": 0.418}
  ]
}
```

---

## 4. Dashboard & Risk Analytics (`/api/dashboard`, `/api/risk`)

### `GET /api/dashboard/summary`
Returns high-level KPI telemetry, 14-day volume trajectories, category distributions, and recent alerts.

### `GET /api/risk/forecast`
Returns ranked at-risk tickets, team x hour congestion heatmap matrix, and precision/recall trade-off curve.
- **Query Parameters**:
  - `threshold`: float (optional threshold override, e.g. `0.35`)

---

## 5. Proactive Alerts (`/api/alerts`)

### `GET /api/alerts`
List proactive SLA escalation alerts.
- **Query Parameters**: `acknowledged` (bool, optional)

### `POST /api/alerts/{id}/ack`
Acknowledge an alert by the authenticated agent.

---

## 6. Theme Discovery (`/api/themes`)

### `GET /api/themes`
Retrieve unsupervised topic clusters, top n-grams, weekly volume sparklines, and emerging outage burst flags.

### `POST /api/themes/refresh`
Trigger unsupervised re-clustering over recent tickets and update active artifact.

---

## 7. Model Registry & Governance (`/api/models`)

### `GET /api/models`
List registered model versions with accuracy, macro-F1, ROC-AUC, and active production status.

### `POST /api/models/retrain`
Trigger candidate model retraining incorporating feedback overrides. Enforces macro-F1 promotion gate.

### `POST /api/models/{version}/rollback`
Instantly rollback active production model to a target version.

---

## 8. Real-Time Streaming (`/api/stream`)

### `GET /api/stream`
Server-Sent Events (SSE) live connection emitting real-time event updates:
- `ticket_created`
- `ticket_updated`
- `alert_created`
- `risk_escalated`
- `feedback_submitted`
- `ping` (every 15s keepalive)
