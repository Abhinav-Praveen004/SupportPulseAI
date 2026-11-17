# SupportPulse AI - Implementation Plan

## Overview
SupportPulse AI is a lightweight, locally deployable, ML-powered IT service-desk intelligence platform running entirely on CPU (<= 8 GB RAM) without external API dependencies. This plan defines the end-to-end execution across 9 distinct phases (P0 to P8), tracking deliverables, verification criteria, and risk mitigation.

---

## Phase Breakdown

### Phase 0: Repository Scaffolding & Tooling
- **Goals**: Set up repo layout, pinned dependencies, environment configuration, Docker Compose skeleton, Makefile targets, and CI-style test harnesses.
- **Tasks**:
  1. Create directory structure (`backend/app/{api,core,db,services,ml,scheduler}`, `backend/tests`, `ml`, `data`, `models`, `reports`, `frontend/src`, `docs`).
  2. Backend setup: Python virtualenv, pinned `requirements.txt` (FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, scikit-learn, pandas, numpy, joblib, vaderSentiment, APScheduler, pytest, httpx, ruff).
  3. Frontend setup: Vite + React 18 + TypeScript strict mode + Tailwind CSS + Lucide + Recharts + TanStack Query + Vitest.
  4. Docker Compose (`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`).
  5. Cross-platform Makefile / task scripts (`setup`, `seed`, `train`, `eval`, `dev`, `test`, `up`, `down`).
  6. Empty test suite running green for both backend (`pytest`) and frontend (`vitest`).
- **Exit Criteria**: `make test` (or backend pytest + frontend test) runs green on empty suites; git commit made; `PROGRESS.md` updated.

---

### Phase 1: Synthetic Data Layer & Ingestion Engine
- **Goals**: Implement realistic synthetic ticket generator (20,000 tickets across 12 months) and CSV ingestion engine.
- **Tasks**:
  1. Define database schema (Tickets, Users, Alerts, Feedback, ModelVersions, Settings) with SQLite default and PostgreSQL support.
  2. Implement seeded synthetic generator (`ml/seed_data.py`) with:
     - 10 IT categories, P1-P4 priorities, SLA targets (4h, 8h, 24h, 72h).
     - Realistic text templates, paraphrasing, synonyms, realistic typos, 1-4 sentence bodies.
     - Latent requester frustration variable driving angry cues, reopens, repeat contacts, escalation.
     - SLA breach probability driven by priority, category complexity, queue load, hour, weekend, noise.
     - VPN outage incident burst injected in final 2 weeks.
     - Time-ordered split (70% train, 15% validation, 15% test).
     - 8-10% intentionally ambiguous/mislabeled tickets for realistic noise.
  3. Write data profiling script writing dataset distributions and summary to `/reports/data_profile.json`.
  4. Implement generic CSV importer with flexible column mapping for external data loading.
  5. Unit tests for generator reproducibility, schema integrity, and CSV importer.
- **Exit Criteria**: 20k tickets seed reproducibly, `data/tickets.csv` generated, `/reports/data_profile.json` created, tests passing; git commit made; `PROGRESS.md` updated.

---

### Phase 2: ML Modules & Offline Evaluation (M1 - M6)
- **Goals**: Build, train, calibrate, evaluate, and save all ML modules with zero data leakage.
- **Tasks**:
  1. **Baseline**: Regex and keyword matching rule classifier for category and priority.
  2. **M1 Classification**: Calibrated LinearSVC/LogisticRegression on TF-IDF word (1-2) + char (3-5) n-grams for category & priority. Confidence calculation, human triage fallback below threshold, top n-gram explanations.
  3. **M2 Routing**: Team workload + predicted category recommendation engine with explainable rationale.
  4. **M3 SLA Risk Forecasting**: HistGradientBoostingClassifier trained on temporal snapshot slices (0%, 25%, 50%, 75% elapsed SLA window) without `resolved_at` leakage. Breach probability, risk bands (Low/Medium/High/Critical), minutes to breach, top risk drivers via feature ablation. Threshold tuned on validation set for target 80% recall. Lead-time analysis vs reactive baseline (0 min).
  5. **M4 Explainable Friction Score (0-100)**: VADER sentiment + IT domain lexicon + frustration text cues (ALL CAPS, punctuation repetition, urgency phrases) + behavioral signals (contacts, reopens, SLA elapsed ratio). Weights fit via Logistic Regression on synthetic escalation flag.
  6. **M5 Theme Discovery**: TF-IDF + NMF topic modeling (k=6..20 selected via silhouette/reconstruction error). Cluster labeling, top terms, representative tickets, weekly volume trends, emerging theme z-score detection (last 7d vs prior 28d), NMI/ARI cluster sanity check.
  7. **M6 Model Registry & Feedback Loop**: Versioned artifacts in `models/`, metadata tracking, candidate model retrain & evaluation, promotion gate (macro-F1 non-regression), rollback support.
  8. Write `ml/train_all.py` and `ml/evaluate_all.py` generating all metrics to `reports/*.json` (classification, baseline, SLA risk, lead time, friction, themes, latency).
  9. Unit tests for temporal leakage, calibration sanity, reproducibility, and inference speed.
- **Exit Criteria**: All 6 models trained and serialized; baseline and ML evaluation reports generated in `/reports`; lead-time analysis documented; tests pass; git commit made; `PROGRESS.md` updated.

---

### Phase 3: Backend API, Scheduler & Streaming
- **Goals**: Build production-ready FastAPI backend with OpenAPI documentation, authentication, scheduler, and SSE.
- **Tasks**:
  1. Core security: JWT auth (access tokens), bcrypt password hashing, roles (admin, manager, agent), PII-redacting structured logger.
  2. Seed default users (admin, manager, agent) documented in README.
  3. REST Endpoints:
     - `POST /api/tickets`, `GET /api/tickets` (filters, sort, pagination), `GET /api/tickets/{id}`, `PATCH /api/tickets/{id}`, `POST /api/tickets/{id}/feedback`.
     - `POST /api/analyze` (stateless Playground endpoint).
     - `GET /api/dashboard/summary`, `GET /api/risk/forecast`.
     - `GET /api/alerts`, `POST /api/alerts/{id}/ack`.
     - `GET /api/themes`, `POST /api/themes/refresh`.
     - `GET /api/models`, `POST /api/models/retrain`, `POST /api/models/{version}/rollback`.
     - `GET /api/stream` (Server-Sent Events for real-time ticket creation, risk shifts, alerts).
     - `POST /api/import/csv`, `POST /api/dev/seed`, `GET /health`.
  4. Scheduler: APScheduler periodic task rescoring open tickets every N minutes, triggering deduplicated alerts when risk band escalates.
  5. Backend integration tests (FastAPI TestClient) for all routes, permissions, and streaming.
- **Exit Criteria**: All endpoints functioning, OpenAPI spec generated, tests green; git commit made; `PROGRESS.md` updated.

---

### Phase 4: Frontend Foundation & Design System
- **Goals**: Build design system following taste skill / fallback rules, app shell, navigation, and reusable UI components.
- **Tasks**:
  1. Confirm taste skill status (fallback rules applied: restrained palette with one accent, clear type scale with two font families, 4/8px spacing grid, generous whitespace, subtle motion).
  2. Implement design tokens (`tokens.ts`, `tailwind.config.js`). Light and dark themes with WCAG AA compliance.
  3. App shell: Top navigation / sidebar, active route indicators, theme toggle, connection status (SSE indicator), user badge.
  4. Reusable UI components: Card, Button, Input, Select, Badge, Table, Modal, Drawer, Tabs, SkeletonLoader, EmptyState, ErrorBoundary, RiskMeter, FrictionGauge, TermHighlighter, Tooltip.
  5. Component tests with Vitest.
- **Exit Criteria**: App shell renders cleanly in light and dark modes; responsive layout; vitest suite green; git commit made; `PROGRESS.md` updated.

---

### Phase 5: Frontend Pages (Real API Integration)
- **Goals**: Implement all 9 pages fully integrated with the backend API (zero mock data).
- **Tasks**:
  1. **Command Center**: KPI cards, real-time risk queue, volume chart, category distribution, live alert feed.
  2. **Triage Queue**: High-density table, live countdown, confidence badge, risk meter, friction badge, column filters, quick triage actions, drawer view.
  3. **Ticket Detail**: Highlighted influential n-grams, model predictions with explanations, risk-over-time trend, friction breakdown, routing recommendation, feedback & override controls.
  4. **SLA Risk Forecast**: Ranked high-risk tickets, team x hour heat matrix, precision-recall trade-off threshold slider.
  5. **Friction Monitor**: Distribution histogram, department frustration rankings, time trend.
  6. **Theme Explorer**: Topic cards, top n-grams, sparkline volume trends, emerging theme alerts, representative ticket samples.
  7. **Playground**: Free-text input area, instant multi-model inference breakdown with explanation visualization.
  8. **Model Lab**: Version history, ML vs regex baseline comparison table, confusion matrix heatmap, calibration plot, retrain trigger, one-click rollback, prominent synthetic data banner.
  9. **Settings**: SLA target configuration, risk threshold adjustments, friction weight sliders, alert notification channels.
- **Exit Criteria**: All 9 pages operational against live API; zero mock data; UI tests passing; git commit made; `PROGRESS.md` updated.

---

### Phase 6: Integration, Streaming & End-to-End Workflows
- **Goals**: Connect live SSE streams, verify real-time alert escalation, and complete the feedback-retrain-promote loop.
- **Tasks**:
  1. Wire SSE stream to frontend React state (live ticket ingest, live risk updates, live alerts notification).
  2. End-to-end alert workflow: ticket creation -> background rescore -> risk escalation -> alert raised -> agent acknowledgment.
  3. End-to-end feedback loop: agent overrides category/priority -> feedback saved -> retrain triggered -> candidate evaluated -> promoted/rolled back.
  4. Automated integration test running end-to-end pipeline.
- **Exit Criteria**: Real-time reactivity verified; end-to-end workflow automated; git commit made; `PROGRESS.md` updated.

---

### Phase 7: Hardening, Performance & Documentation
- **Goals**: Audit performance, verify accessibility, and generate all final documentation from real reports.
- **Tasks**:
  1. Performance benchmark: verify p95 single-ticket analysis < 300 ms on CPU, dashboard response < 500 ms on 20k rows. Write results to `reports/latency_benchmarks.json`.
  2. Security & privacy check: zero outbound network calls, PII redaction verified, password hashing verified.
  3. Accessibility review: WCAG AA contrast, keyboard accessibility, semantic HTML, tabular figures.
  4. Generate documentation:
     - `ARCHITECTURE.md`: Architecture diagrams and data flow.
     - `MODEL_CARD.md`: Specifications, data disclosure, ethical considerations.
     - `EVALUATION.md`: Empirical results (ML vs baseline, lead time, AUCs, NMI/ARI, latencies).
     - `API.md`: API reference.
     - `DEMO_SCRIPT.md`: 5-minute step-by-step walkthrough.
     - `REPORT_SNIPPETS.md`: Ready-to-use report snippets with real measured numbers.
     - `README.md`: Quickstart, demo accounts, feature overview, screenshots/walkthrough.
- **Exit Criteria**: All docs generated with traceable numbers from `/reports`; benchmarks confirmed; git commit made; `PROGRESS.md` updated.

---

### Phase 8: Final Verification & Delivery
- **Goals**: Test clean one-command startup, clean-clone verification, and formulate final response.
- **Tasks**:
  1. Execute verification sequence (`make setup seed train eval test up`).
  2. Ensure all tests green (backend and frontend).
  3. Verify Definition of Done checklist.
  4. Deliver final executive summary.
- **Exit Criteria**: Everything operational, fully documented, clean repository state.

---

## Risk Analysis & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| In-memory model latency exceeding 300 ms on CPU | High | Pre-load models at startup into memory singleton; use fast TF-IDF + linear models and compact HistGradientBoosting trees. |
| Temporal data leakage in SLA prediction | Critical | Strict time-based snapshots (0%, 25%, 50%, 75% elapsed SLA) excluding future fields (`resolved_at`, final breach flag at intermediate points). |
| High RAM consumption during training on 20k tickets | Medium | Sparse matrices for TF-IDF, chunked processing, compact feature representations; peak RAM < 1.5 GB. |
| Frontend design inconsistency without external UI kits | Medium | Centralized `tokens.ts` design system enforcing 4/8px grid, restrained color palette, and accessible components. |
| Non-deterministic evaluation metrics | Medium | Fixed global random seeds (`seed=42`) across NumPy, scikit-learn, and synthetic data generators. |
