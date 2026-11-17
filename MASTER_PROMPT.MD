# MASTER BUILD PROMPT: SupportPulse AI

## 1. ROLE AND MISSION
You are a senior full-stack and ML engineer working as an autonomous build agent. Build SupportPulse AI end to end in the current working directory: a lightweight, locally deployable, ML-powered IT service-desk intelligence platform. It must run on a single laptop (CPU only, 8 GB RAM) with one command. No data may leave the machine at runtime and no paid or external AI APIs may be used.

## 2. PROBLEM CONTEXT (what this system must visibly fix)
Traditional service desks depend on manual tier-1 triage or static keyword/regex rules. The disadvantages to address:
1. Heavy reliance on manual triage -> slow, expensive assignment.
2. Rigid, brittle keyword rules that miss synonyms and multi-sentence descriptions.
3. Subjective, inconsistent prioritization across agents.
4. Reactive SLA management: alerts fire only after the deadline is breached.
Commercial SaaS tools are also expensive per agent, opaque, and raise data-privacy concerns.
The build must produce measurable evidence (see section 12) that SupportPulse AI beats a keyword-rule baseline and gives advance warning before SLA breaches.

## 3. WORKING RULES
1. Plan first. Write PLAN.md (phases, tasks, risks), then execute phase by phase. After each phase: run tests, fix failures, make a git commit (conventional commit message), and update PROGRESS.md.
2. Do not ask me questions unless truly blocked. Make sensible decisions and record each in DECISIONS.md with a one-line rationale.
3. Never fabricate results. Every metric, chart or number in any document or UI must come from a script run in this repo. Evaluation scripts write JSON to /reports and docs read from those files.
4. The dataset is synthetic unless I supply real data. Label it as synthetic in the README, the model card, and on the Model Lab page.
5. Keep dependencies minimal and pinned. CPU only. Prefer simple, explainable models over heavy ones. Every prediction must ship with an explanation.
6. Code quality: Python type hints + docstrings + ruff/black; TypeScript strict mode + eslint + prettier.
7. FRONTEND DESIGN: before writing any UI code, locate and read the "taste" skill installed for this project (check the project/user skills directories), and follow it for all visual decisions: typography, colour, spacing, layout, motion, and empty/loading/error states. If you cannot find it, note that in PROGRESS.md, apply the fallback rules in section 9, and flag it clearly in your final report. Do not guess what the skill says.

## 4. FIXED TECH STACK
Backend: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, SQLite by default (PostgreSQL via DATABASE_URL), APScheduler, scikit-learn, pandas, numpy, joblib, vaderSentiment. No heavy deep-learning libraries.
Frontend: React 18, Vite, TypeScript (strict), Tailwind CSS, React Router, TanStack Query, Recharts, lucide-react. Live updates via Server-Sent Events.
Infra: Docker Compose (api, web), Makefile, .env.example, pytest, vitest.

## 5. REPOSITORY LAYOUT
- backend/app/ : api/, core/ (config, security, logging), db/ (models, migrations), services/, ml/ (preprocess, classify, route, sla_risk, friction, themes, registry, explain), scheduler/, main.py
- backend/tests/
- ml/ : scripts for data generation, training, evaluation (seed_data.py, train_all.py, evaluate_all.py)
- data/ (generated, gitignored), models/ (versioned artifacts, gitignored), reports/ (evaluation JSON + figures)
- frontend/ : src/ (app, pages, components, lib, styles/tokens)
- docs/ : ARCHITECTURE.md, MODEL_CARD.md, EVALUATION.md, API.md, DEMO_SCRIPT.md, REPORT_SNIPPETS.md
- Makefile targets: setup, seed, train, eval, dev, test, up, down

## 6. DATA LAYER
Write a seeded, reproducible synthetic data generator (default 20,000 tickets across 12 months).
Fields: ticket_id, created_at, subject, body, requester_id, department, channel, category, priority (P1-P4), assigned_team, agent_id, first_response_at, resolved_at, sla_hours, breached, reopen_count, contact_count, escalated, status.
- 10 categories: Password/Access, Network/VPN, Email, Hardware, Software Install, Application Error, Security Incident, Printer, Cloud/Infrastructure, Service Request.
- SLA targets: P1 4h, P2 8h, P3 24h, P4 72h (configurable in Settings).
- Text realism: template + paraphrase variation, synonyms, typos, 1-4 sentence bodies, mixed formality, about 8-10% ambiguous or mislabeled tickets so models are not trivially perfect.
- Latent frustration variable that drives angry language, repeat contacts, reopens and escalation.
- Breach probability driven by priority, category complexity, queue load, team workload, hour of day, weekend, and noise.
- Inject an "incident burst" in the final 2 weeks (e.g., a VPN outage cluster) to test theme discovery.
- Also provide a CSV importer with column mapping so real data can be loaded later.
- Use time-ordered train/validation/test splits to prevent leakage.

## 7. ML MODULES
Each module needs: training script, saved versioned artifact, evaluation JSON, and an explanation function.

M1 Classification (category and priority): TF-IDF word (1-2 grams) + character (3-5 grams) features, calibrated LinearSVC or LogisticRegression. Return a probability per class. Below a configurable confidence threshold, flag "needs human triage". Explanation: top contributing n-grams. REQUIRED BASELINE: implement the old-system regex/keyword classifier and evaluate it on the same test set. Report accuracy, macro-F1, per-class precision/recall, confusion matrix, and calibration.

M2 Routing: recommend a team from predicted category plus current team workload; expose the reasoning.

M3 SLA risk forecasting: HistGradientBoostingClassifier. Build training snapshots per ticket at several elapsed points (creation, 25%, 50%, 75% of SLA window) using only features known at that moment (no leakage of resolved_at). Features: category, priority, text-model outputs, queue length, team open load, hour/weekday, fraction of SLA elapsed, contact_count, reopen_count. Output: breach probability, risk band (Low/Medium/High/Critical), estimated minutes to breach, and top risk drivers via counterfactual feature ablation. Evaluate ROC-AUC, PR-AUC, Brier score and calibration on a time-based test split. Pick the alert threshold on validation data for a target recall (default 80%) and report the resulting precision. Report LEAD-TIME ANALYSIS: median minutes between first alert and actual breach, versus 0 for the reactive baseline.

M4 Friction score (0-100), explainable: weighted components for (a) sentiment (VADER plus a small IT-support lexicon), (b) frustration cues (ALL CAPS ratio, repeated "!", phrases like "again", "still not working", "third time", "unacceptable", "escalate"), (c) behaviour (contact_count, reopen_count, elapsed/SLA ratio). Fit the component weights with logistic regression against the synthetic escalated flag, keep configurable defaults, and report AUC. Return the component breakdown and a band (Calm/Uneasy/Frustrated/Critical).

M5 Theme discovery (unsupervised): TF-IDF + NMF or TruncatedSVD+KMeans, with k chosen from a range (6-20) by a coherence or silhouette criterion. Label each theme by its top terms and representative tickets. Compute weekly volume trends. Emerging-theme detection: z-score of the last 7 days against the prior 28. Sanity-check clusters against the hidden category with NMI/ARI, and state clearly that this is a sanity check, not supervision. Re-run on demand and on a schedule.

M6 Feedback loop and registry: agents accept or override category/priority; store the feedback. A retrain job builds a candidate model, evaluates it on a held-out set, and promotes it only if macro-F1 is not worse than the current model. Keep versions with metrics, and support one-click rollback.

## 8. BACKEND API (JSON, documented via OpenAPI)
- POST /api/tickets (create + run full analysis, return enriched ticket); GET /api/tickets (filters, pagination, sort by risk or friction); GET/PATCH /api/tickets/{id}; POST /api/tickets/{id}/feedback
- POST /api/analyze (stateless analysis of free text for the Playground)
- GET /api/dashboard/summary; GET /api/risk/forecast
- GET /api/alerts; POST /api/alerts/{id}/ack
- GET /api/themes; POST /api/themes/refresh
- GET /api/models; POST /api/models/retrain; POST /api/models/{version}/rollback
- GET /api/stream (SSE for new tickets, risk changes, alerts)
- POST /api/import/csv; POST /api/dev/seed; GET /health
- Auth: JWT with roles (admin, manager, agent), hashed passwords, seeded demo users documented in README.
Scheduler: every N minutes (configurable) re-score open tickets; create deduplicated alerts when a ticket's risk band escalates. Delivery: in-app by default, optional generic webhook and SMTP email, both off unless configured.

## 9. FRONTEND
Pages:
1. Command Center: KPI strip (open tickets, high-risk count, predicted breaches in next 4h, average friction, auto-triaged share), live risk queue, volume chart, category mix, alerts feed.
2. Triage Queue: dense table with auto category, priority, confidence, risk meter, friction badge, SLA countdown, filters, and a detail drawer.
3. Ticket Detail: text with influential terms highlighted, predictions with confidence and explanations, risk-over-time chart, friction breakdown, routing recommendation, agent override and feedback controls.
4. SLA Risk Forecast: ranked at-risk list, team x hour heatmap, threshold slider showing the live precision/recall trade-off.
5. Friction Monitor: distribution, most frustrated departments, trend.
6. Theme Explorer: theme cards with top terms, trend sparklines, "emerging" badge, representative tickets.
7. Playground: paste a ticket, see all predictions instantly.
8. Model Lab: versions, metrics, baseline-vs-ML comparison, confusion matrix, calibration, retrain/rollback, and a visible "synthetic data" notice.
9. Settings: SLA policy, risk thresholds, friction weights, alert channels.
Design requirements (apply the taste skill; these apply on top of it):
- One central design-token file; light and dark themes; responsive down to tablet.
- Distinctive, intentional look: no generic template or default-library appearance, no lorem ipsum.
- Skeleton loaders, meaningful empty states, and error states for every data view.
- Keyboard-accessible, WCAG AA contrast, tabular numerals for figures, and risk/friction semantics never conveyed by colour alone.
- Purposeful motion that respects prefers-reduced-motion.
Fallback if the taste skill is missing: restrained palette with one accent, a clear type scale with two font families at most, a consistent 4/8px spacing grid, generous whitespace, and subtle motion only.

## 10. NON-FUNCTIONAL REQUIREMENTS
- Privacy: zero outbound network calls at runtime; redact emails/phone numbers/IPs from logs.
- Security: password hashing, short-lived JWTs, input validation, rate limiting, configurable CORS, no secrets in the repo.
- Performance: single-ticket analysis under 300 ms p95 on CPU; models loaded at startup; indexed queries so dashboard endpoints respond under 500 ms on 20k tickets.
- Reproducibility: fixed seeds and pinned deps; `make setup seed train eval up` must work from a clean clone.
- Observability: structured logs, /health, and a model-status endpoint.

## 11. PHASES AND ACCEPTANCE CRITERIA
P0 Scaffold: repo, tooling, CI-style Makefile, docker-compose skeleton. Done when `make test` runs green on an empty suite.
P1 Data: generator, schema, importer. Done when 20k tickets seed reproducibly and the data profile report is written to /reports.
P2 ML: M1-M6 trained and evaluated. Done when all metric JSONs exist, the baseline comparison runs, and lead-time analysis is produced.
P3 Backend: all endpoints, auth, scheduler, SSE. Done when API tests pass and OpenAPI is complete.
P4 Frontend foundation: read the taste skill, build the tokens, layout shell, shared components. Done when the shell renders in both themes.
P5 Frontend pages: all nine pages wired to the real API. Done when no page uses mock data.
P6 Integration: live SSE updates, alert flow, feedback -> retrain -> promote/rollback loop working end to end.
P7 Hardening and docs: tests, accessibility pass, performance check, all docs generated from real reports.
P8 Final verification: fresh-clone run of the full pipeline, then the final report.

## 12. TESTING AND EVIDENCE
- Backend unit and API tests (pytest); ML tests for no-leakage, reproducibility, and probability calibration sanity; frontend component tests (vitest); one end-to-end smoke test of ingest -> analyse -> alert.
- EVALUATION.md must include: (1) regex baseline vs ML classifier on identical data; (2) SLA lead-time results vs the reactive approach; (3) friction score AUC; (4) theme NMI/ARI; (5) latency numbers. All numbers come from /reports.

## 13. DOCUMENTATION DELIVERABLES
README (quickstart, architecture overview, demo logins, screenshots), ARCHITECTURE.md (Mermaid diagram of the data flow), MODEL_CARD.md (data, intended use, limitations, bias, synthetic-data disclosure), EVALUATION.md, API.md, DEMO_SCRIPT.md (a 5-minute walkthrough), and REPORT_SNIPPETS.md with ready-to-paste paragraphs for an academic project report (implementation and results), using real measured numbers.

## 14. DEFINITION OF DONE
- Fresh clone -> one command sequence -> a working app with seeded data.
- All tests green; no TODO placeholders; no mock data in the UI.
- Every claim in the docs traceable to a file in /reports.
- UI follows the taste skill (or the fallback rules, flagged).

## 15. FINAL OUTPUT
When finished, reply with: what was built, how to run it, the real headline metrics, deviations from this prompt and why (from DECISIONS.md), known limitations, and suggested next steps.