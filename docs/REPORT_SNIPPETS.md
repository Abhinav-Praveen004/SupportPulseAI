# SupportPulse AI: Project Report Snippets

*Ready-to-paste sections for technical, academic, or executive project reports.*
*All metrics and tables presented below are extracted directly from empirical benchmark logs in `/reports`.*

---

## 1. Executive Summary

SupportPulse AI is an air-gapped, lightweight IT service-desk intelligence platform designed to eliminate reactive operational failures without relying on external, paid Large Language Model (LLM) APIs or cloud dependencies. Deployed as an edge-native system requiring under 8 GB of host RAM, SupportPulse AI couples calibrated linear models and gradient-boosted decision trees with unsupervised matrix factorization to provide automated triage, dynamic team dispatch, advance SLA breach forecasting, real-time friction scoring, and emerging problem cluster detection. Evaluated across a synthetic benchmark corpus of 20,000 enterprise IT tickets spanning 12 months, SupportPulse AI achieves a **100.00% category classification accuracy** (+12.33% over a keyword/regex baseline), forecasts SLA breaches with a **median lead time of 480.0 minutes (8.0 hours)** at an **ROC-AUC of 0.8734**, detects customer escalation risk with an **ROC-AUC of 0.9257**, and flags emerging operational crises with high statistical confidence (**z-score of +5.49σ**) — all while maintaining a median single-ticket CPU inference latency of **17.2 milliseconds** (p95: **20.4 milliseconds**; throughput: **57.9 tickets/second**).

---

## 2. System Architecture

SupportPulse AI adopts a decoupled, local-first micro-architecture consisting of three primary layers:

1. **Analytical Data & Feature Store**: Built upon SQLite (with an optional PostgreSQL transition path via SQLAlchemy ORM), managing ticket lifecycles, full-text descriptions, audit histories, resolution events, and operator feedback loops.
2. **Machine Learning Inference Suite (M1–M6)**: Composed of six specialized CPU-optimized sub-models:
   - **M1 (Category Classifier)**: Word and character n-gram TF-IDF vectorizer coupled with a Calibrated Linear Support Vector Classifier (`CalibratedClassifierCV(LinearSVC)`), emitting calibrated probability distributions and top indicative feature terms.
   - **M2 (Team Routing Engine)**: Deterministic, skill-mapped routing matrix overlaying category predictions with real-time team queue load balancing and fallback overflow logic.
   - **M3 (SLA Risk Forecaster)**: Multi-snapshot HistGradientBoostingClassifier operating on dynamic ticket velocity features (elapsed minutes, SLA ratio, contact count, reopen count, updates) to compute breach probability before milestone violations occur.
   - **M4 (User Friction Scorer)**: Hybrid composite model synthesizing rule-based sentiment polarities (VADER lexicon adapted with IT support terminology), uppercase/exclamation urgency signals, and non-linear behavioral friction indicators (reopens, repeat contacts, stalled status transitions).
   - **M5 (Topic & Emerging Theme Miner)**: Unsupervised Non-Negative Matrix Factorization (NMF) discovering latent problem clusters, evaluated via reconstruction error and automatic k-selection ($k=14$), with temporal rolling-window z-score anomaly detection for zero-day incident surges.
   - **M6 (Unified Explanation Generator)**: Counterfactual feature attribution engine isolating the exact delta in risk caused by operator actions, ticket age, and customer sentiment.
3. **Reactive Presentation & Event Layer**: A FastAPI asynchronous backend server providing RESTful endpoints, Server-Sent Events (SSE) for live triage broadcasting, APScheduler background job workers for automated rescoring, and a React 18 / TypeScript / Tailwind CSS dashboard designed in strict accordance with restrained human-computer interaction principles (WCAG AA accessibility, multi-modal badge indicators, and zero external asset CDNs).

---

## 3. Machine Learning Methodology

### 3.1 Feature Engineering & Text Representation
To ensure execution within CPU environments without GPU acceleration, text representations utilize a hybrid dual-vectorizer scheme:
$$\mathbf{x}_{\text{text}} = \left[ \text{TF-IDF}_{\text{word}(1,2)}(\text{text}) \;\|\; \text{TF-IDF}_{\text{char}(3,5)}(\text{text}) \right]$$
The word n-gram pipeline (1–2 grams, capped at 5,000 features) captures domain nomenclature (e.g., *"Docker Desktop"*, *"CRM Gateway"*), while the sub-word character n-gram pipeline (3–5 grams, capped at 5,000 features) grants robustness against user typos, truncated error logs, and colloquial abbreviations.

### 3.2 Dynamic Snapshot Modeling for SLA Breach
Unlike static time-of-creation classifiers that fail to capture ticket evolution, the SLA Risk Forecaster (M3) constructs longitudinal snapshot records for every ticket across discrete time intervals ($t \in \{0.0, 0.25, 0.5, 0.75, 1.0\} \times \text{SLA target}$). Each snapshot encodes temporal features:
$$\mathbf{x}_{\text{SLA}}(t) = \left[ \Delta t_{\text{elapsed}}, \frac{\Delta t_{\text{elapsed}}}{\text{SLA}_{\text{target}}}, N_{\text{contacts}}, N_{\text{reopens}}, \text{Priority}, \text{Category} \right]$$
A histogram-based gradient-boosted tree (`HistGradientBoostingClassifier`) optimizes binary log-loss over 10,465 evaluation snapshots, providing early risk escalation hours before SLA exhaustion.

### 3.3 Composite Customer Friction Formulation
Customer friction $F \in [0, 100]$ is computed as a weighted combination of linguistic sentiment $S$, linguistic urgency cues $U$, and operational customer behavior $B$:
$$F = \min\left(100, \; w_S \cdot S + w_U \cdot U + w_B \cdot B\right)$$
Empirically calibrated logistic regression weights against historical supervisor escalations yielded:
- Behavioral Weight ($w_B$): **0.789** (78.9% contribution: reopens, contact loops, idle duration)
- Linguistic Text Urgency ($w_U$): **0.123** (12.3% contribution: CAPS, repeated punctuation, urgency keywords)
- Sentiment Polarity ($w_S$): **0.088** (8.8% contribution: negative valence from VADER + IT lexicon)

---

## 4. Empirical Evaluation & Key Results

### 4.1 Ticket Classification: M1 vs. Keyword Baseline
Evaluated on a strictly held-out test split of 3,000 tickets across 10 service-desk categories:

| Metric | Keyword / Regex Baseline | SupportPulse AI (Calibrated LinearSVC) | Delta / Absolute Gain |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | 87.67% | **100.00%** | **+12.33%** |
| **Macro Average F1** | 0.8258 | **1.0000** | **+0.1742** |
| **Weighted Average F1** | 0.8687 | **1.0000** | **+0.1313** |
| **Hardware / Security Incidents F1** | 0.5693 | **1.0000** | **+0.4307** |
| **Service Request F1** | 0.4917 | **1.0000** | **+0.5083** |
| **Human Triage Fallback Rate** | 12.33% (unmatched) | **0.00%** (conf $\ge$ 0.70) | **-12.33%** |
| **Mean Prediction Confidence** | N/A (binary rules) | **0.9936** | High Calibration |

*Source: `reports/classification_metrics.json` and `reports/baseline_metrics.json`.*

### 4.2 Proactive SLA Risk Forecasting & Advance Warning Lead Time
Evaluated over 10,465 longitudinal ticket snapshots and 1,590 historical breach occurrences:

| Evaluation Dimension | Traditional Reactive Alerting | SupportPulse AI Proactive Forecaster |
| :--- | :---: | :---: |
| **Detection Mechanism** | Threshold trigger upon breach | Dynamic gradient boosted hazard model |
| **Median Advance Warning** | **0.0 minutes** | **480.0 minutes (8.00 hours)** |
| **Mean Advance Warning** | 0.0 minutes | **970.3 minutes (16.17 hours)** |
| **Interquartile Range (p25–p75)**| [0.0, 0.0] min | **[480.0, 1440.0] min (8h to 24h)** |
| **Breaches Caught in Advance** | 0.0% | **93.52%** |
| **Area Under ROC (ROC-AUC)** | N/A | **0.8734** |
| **Precision at Alert Threshold** | N/A | **91.25%** ($\tau = 0.3055$) |
| **Recall at Alert Threshold** | N/A | **75.07%** |
| **Brier Calibration Score** | N/A | **0.2126** |

*Source: `reports/sla_risk_metrics.json` and `reports/lead_time_analysis.json`.*

### 4.3 Customer Friction & Escalation Modeling
Evaluated against supervisor escalation ground truth across 3,000 test cases:

- **Escalation ROC-AUC**: **0.9257**
- **Mean Dataset Friction**: **26.6 / 100**
- **Population Distribution**:
  - *Calm* ($0 \le F < 25$): 2,076 tickets (69.2%)
  - *Uneasy* ($25 \le F < 50$): 598 tickets (19.9%)
  - *Frustrated* ($50 \le F < 75$): 258 tickets (8.6%)
  - *Critical* ($75 \le F \le 100$): 68 tickets (2.3%)
- **Top Frictional Departments**: Legal (28.6 avg), Marketing (27.2 avg), Operations (26.9 avg), Sales (26.8 avg).

*Source: `reports/friction_metrics.json`.*

### 4.4 Unsupervised Incident Theme Discovery
Non-Negative Matrix Factorization across 20,000 tickets identified $k=14$ coherent operational themes, verified against ground-truth service taxonomies:
- **Normalized Mutual Information (NMI)**: **0.6052**
- **Adjusted Rand Index (ARI)**: **0.5382**
- **Zero-Day Incident Anomaly Surge**: A simulated infrastructure disruption (550 burst tickets in the final 14 days representing corporate VPN gateway authentication failures) was isolated as an emerging theme with a **z-score of +5.49σ** above rolling 28-day baseline ticket arrival rates.

*Source: `reports/theme_metrics.json`.*

### 4.5 Latency, Throughput & Hardware Benchmarks
Benchmarked on commodity single-laptop CPU hardware without GPU acceleration ($N=200$ consecutive inference calls):

| Metric | Measured Value | Operational Target | Status |
| :--- | :---: | :---: | :---: |
| **Mean Latency** | **17.28 ms** | < 200 ms | PASS |
| **Median (p50)** | **17.15 ms** | < 150 ms | PASS |
| **90th Percentile (p90)** | **19.60 ms** | < 250 ms | PASS |
| **95th Percentile (p95)** | **20.42 ms** | < 300 ms | **PASS (14.7x faster than SLA)** |
| **99th Percentile (p99)** | **23.11 ms** | < 500 ms | PASS |
| **Throughput** | **57.9 tickets/sec** | > 20 tickets/sec | **PASS (2.9x capacity)** |
| **Resident Memory (RSS)** | **< 350 MB** | < 8,000 MB | PASS |

*Source: `reports/latency_benchmarks.json`.*

---

## 5. Engineering Decisions & Architecture Tradeoffs

1. **Calibrated Linear Support Vector Machines over Large Language Models**:
   - *Rationale*: Eliminates cold-start latency, token billing, rate limiting, and private credential leakage. A calibrated LinearSVC using word and character n-grams runs in ~17 ms on CPU while reaching 100.0% categorization accuracy on standard domain nomenclature.
2. **HistGradientBoosting over Deep Neural Networks for SLA Hazard Prediction**:
   - *Rationale*: Tabular and velocity features exhibit structured interactions well-suited for tree-based partitioning. Histogram gradient boosting natively handles missing values, scales logarithmically with depth, and trains in under 15 seconds without GPU acceleration.
3. **Decoupled Asynchronous Rescoring Architecture**:
   - *Rationale*: Tickets dynamically age even when inactive. Decoupling inference via APScheduler background tasks ensures that SLA risk and friction scores update continuously, broadcasting status transitions over Server-Sent Events (SSE) to connected browser clients without polling.

---

## 6. Synthetic Data & Ethical Disclosure

All evaluations and demonstrations in SupportPulse AI are conducted on a procedurally generated, synthetic enterprise service-desk dataset (`data/tickets.csv`, $N=20,000$) parameterized using fixed pseudorandom seeds (`seed=42`). No real employee records, proprietary intellectual property, or confidential communications were ingested or retained. In production environments, retraining should be monitored against demographic and department bias metrics to ensure equitable resolution SLAs across non-technical and executive business units.
