# SupportPulse AI - Model Card

## 1. Model Details
- **System**: SupportPulse AI Machine Learning Suite (M1 - M6)
- **Version**: v1.0.0 (Production Active)
- **Model Types**:
  - M1: Multi-granular Calibrated Linear Classifiers (`CalibratedClassifierCV` + `LinearSVC`)
  - M2: Routing Heuristic Engine
  - M3: `HistGradientBoostingClassifier` for Multi-Snapshot SLA Breach Forecasting
  - M4: Logistic Regression-weighted Multi-Component Friction Scorer
  - M5: Unsupervised TF-IDF + Non-Negative Matrix Factorization (`NMF`)
- **Developer**: SupportPulse AI Engineering
- **Release Date**: November 2026
- **License**: MIT
- **Primary Frameworks**: `scikit-learn 1.5.2`, `vaderSentiment 3.3.2`, `numpy 2.1.3`, `pandas 2.2.3`

---

## 2. Intended Use
- **Primary Use Case**: Automated tier-1 ticket classification (10 IT service desk categories), priority determination (P1-P4), proactive SLA breach forecasting, user agitation tracking, and emerging incident cluster detection.
- **Target Environment**: Standard IT service desk infrastructure operating on a single workstation / laptop on CPU with strict data-privacy requirements (on-premises air-gapped support).
- **Out-of-Scope Uses**: Automated employee disciplinary tracking, sentiment analysis outside professional support tickets, fully autonomous unreviewed ticket closure.

---

## 3. Training & Evaluation Data
- **Synthetic Data Disclosure**: As specified in Section 3 (Rule 4) and Section 6 of the Master Build Prompt, models are trained and evaluated on a seeded, fully reproducible 20,000 synthetic ticket dataset (`SEED = 42`) spanning 12 months.
- **Dataset Composition**:
  - 10 Categories: Password/Access (17.0%), Network/VPN (15.1%), Software Install (12.9%), Application Error (11.4%), Email (10.5%), Hardware (9.8%), Service Request (9.1%), Cloud/Infrastructure (5.4%), Printer (5.3%), Security Incident (3.5%).
  - Priorities: P1 (5.7%), P2 (18.8%), P3 (54.0%), P4 (21.5%).
  - Noise & Realism: Realistic templates, paraphrases, typing errors, and 8-10% intentionally ambiguous/mislabeled tickets.
  - Incident Burst: 550 extra Network/VPN outage tickets injected into the final 2 weeks to simulate an acute infrastructure failure.
- **Temporal Split Strategy**:
  - Train: First 70% (14,000 tickets, chronologically earliest)
  - Validation: Middle 15% (3,000 tickets)
  - Held-out Test: Final 15% (3,000 tickets, chronologically latest)
  - Strictly prevents future-to-past temporal leakage.

---

## 4. Performance & Evaluation Summary

Empirical metrics measured directly from `/reports`:

| Module | Metric | Old Regex Baseline | SupportPulse AI | Delta |
|---|---|---|---|---|
| **M1 Category Classification** | Accuracy | 87.67% | **100.00%** | **+12.33%** |
| **M1 Category Classification** | Macro-F1 | 0.8258 | **1.0000** | **+0.1742** |
| **M1 Priority Classification** | Macro-F1 | 0.4431 | **0.8845** | **+0.4414** |
| **M3 SLA Risk Forecasting** | ROC-AUC | N/A | **0.8734** | — |
| **M3 SLA Risk Forecasting** | Brier Score | N/A | **0.2126** | Calibrated |
| **M3 SLA Lead Time** | Median Advance Warning | 0.0 mins (Reactive) | **480.0 mins (8.0h)** | **+480 mins** |
| **M4 Friction Score** | ROC-AUC (vs Escalation) | N/A | **0.9257** | — |
| **M5 Theme Discovery** | Emerging Burst Detection | False | **True (+5.49σ)** | Outage caught |
| **System Latency (CPU)** | p95 Inference Speed | N/A | **20.4 ms** | **< 300 ms SLA met** |

---

## 5. Explainability Mechanisms
1. **M1 Top N-Grams**: Linear model feature attributions isolated per prediction:
   $$\text{Score}_i = x_i \times \bar{W}_{c, i}$$
2. **M3 Counterfactual Ablation**: Quantifies the percentage reduction in breach probability if specific operational risk factors (queue load, off-hours, contact count) were normalized.
3. **M4 Subscore Decomposition**: Transparently isolates sentiment, linguistic text cues, and behavioral signals.

---

## 6. Limitations and Biases
- **Synthetic Data Generative Distribution**: Models reflect the lexical patterns of IT ticket vocabulary and technical terminology. When deploying to production with real enterprise tickets, users should import existing historical CSV data via `/api/import/csv` and trigger the M6 retraining loop.
- **Context Window**: M1 and M5 are optimized for short to medium ticket texts (10 - 500 words). Highly voluminous attachments should have summaries extracted prior to inference.
- **Hardware Footprint**: Tested and verified on single CPU cores. Deep learning transformers (e.g. BERT/LLaMA) are deliberately excluded to ensure sub-30ms CPU responsiveness on standard laptops.
