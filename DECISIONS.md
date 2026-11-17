# SupportPulse AI - Architectural & Technical Decisions

| ID | Date | Decision | Rationale |
|---|---|---|---|
| DEC-001 | 2026-11-17 | Use `.venv` in repo root for backend Python environment | Isolates dependencies without polluting global Python while keeping execution portable. |
| DEC-002 | 2026-11-17 | Activate Section 9 UI design fallback rules | The "taste" skill was searched for in builtin, user, and marketplace catalog and is not installed. |
| DEC-003 | 2026-11-17 | Default database to SQLite with PostgreSQL via `DATABASE_URL` | Zero-friction local single-command deployment with zero external service requirements. |
| DEC-004 | 2026-11-17 | Strict chronological data splitting (70% train, 15% val, 15% test) | Eliminates future-to-past temporal leakage across all supervised models (M1, M3, M4). |
| DEC-005 | 2026-11-17 | Calibrated Linear Models (CalibratedClassifierCV + LinearSVC / LogisticRegression) for M1 | Extremely fast (< 10ms CPU inference), highly interpretable n-gram coefficients, well-calibrated probabilities. |
| DEC-006 | 2026-11-17 | HistGradientBoostingClassifier for SLA risk forecasting (M3) | Native support for missing values, handles mixed numeric/categorical features rapidly on CPU without deep learning bloat. |
| DEC-007 | 2026-11-17 | Counterfactual ablation for M3 feature attribution | CPU-friendly, fast explainability for tree models without heavyweight SHAP dependency overhead. |
