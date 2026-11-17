# SupportPulse AI - Empirical Evaluation Report

This document reports empirical performance benchmarks measured directly on the held-out 15% chronological test set (3,000 tickets) and written to `/reports/*.json`.

---

## 1. Classification: Old Regex Baseline vs SupportPulse AI (M1)

Source: `reports/classification_metrics.json` and `reports/baseline_metrics.json`

### 1.1 Headline Comparison

| Evaluation Metric | Legacy Regex Baseline | SupportPulse AI (ML) | Absolute Delta | Relative Gain |
|---|---|---|---|---|
| **Category Overall Accuracy** | 87.67% | **100.00%** | **+12.33%** | +14.06% |
| **Category Macro-F1** | 0.8258 | **1.0000** | **+0.1742** | +21.09% |
| **Category Weighted-F1** | 0.8654 | **1.0000** | **+0.1346** | +15.55% |
| **Priority Overall Accuracy** | 56.40% | **89.20%** | **+32.80%** | +58.15% |
| **Priority Macro-F1** | 0.4431 | **0.8845** | **+0.4414** | +99.62% |
| **Human Triage Fallback Rate** | 0.00% (Silent error) | **0.00%** (Conf >= 0.65) | — | Safety gate |
| **Average Prediction Confidence**| N/A | **96.84%** | — | Calibrated |

### 1.2 Per-Class Category Precision & Recall Breakdown

| Category | Regex Precision | Regex Recall | Regex F1 | ML Precision | ML Recall | ML F1 |
|---|---|---|---|---|---|---|
| **Application Error** | 0.892 | 0.841 | 0.866 | **1.000** | **1.000** | **1.000** |
| **Cloud/Infrastructure** | 0.941 | 0.724 | 0.818 | **1.000** | **1.000** | **1.000** |
| **Email** | 0.912 | 0.890 | 0.901 | **1.000** | **1.000** | **1.000** |
| **Hardware** | 0.864 | 0.882 | 0.873 | **1.000** | **1.000** | **1.000** |
| **Network/VPN** | 0.982 | 0.954 | 0.968 | **1.000** | **1.000** | **1.000** |
| **Password/Access** | 0.925 | 0.961 | 0.943 | **1.000** | **1.000** | **1.000** |
| **Printer** | 0.954 | 0.912 | 0.932 | **1.000** | **1.000** | **1.000** |
| **Security Incident** | 0.880 | 0.625 | 0.731 | **1.000** | **1.000** | **1.000** |
| **Service Request** | 0.542 | 0.710 | 0.615 | **1.000** | **1.000** | **1.000** |
| **Software Install** | 0.854 | 0.760 | 0.804 | **1.000** | **1.000** | **1.000** |

---

## 2. SLA Risk Forecasting & Lead-Time Analysis (M3)

Source: `reports/sla_risk_metrics.json` and `reports/lead_time_analysis.json`

### 2.1 Model Discrimination and Calibration
- **ROC-AUC**: `0.8734`
- **Brier Score Loss**: `0.2126`
- **Optimal Alert Decision Threshold**: `0.3055` (calibrated on validation split targeting $\ge 80\%$ recall)
- **Recall at Alert Threshold**: `75.1%`
- **Precision at Alert Threshold**: `91.2%`
- **F1 Score at Alert Threshold**: `0.8239`
- **Expected Calibration Error (ECE)**: `0.0452`

### 2.2 Lead-Time Analysis (Proactive vs Reactive Alerting)

Traditional service-desk systems operate **reactively**: an SLA alert is only raised when the contractual deadline has already expired ($0.0\text{ minutes}$ advance warning). SupportPulse AI forecasts risk across multi-snapshot temporal slices ($0\%, 25\%, 50\%, 75\%$ elapsed):

| Alerting Paradigm | Advance Warning (Median) | Advance Warning (Mean) | 25th - 75th Percentile | Breaches Detected Ahead of Time |
|---|---|---|---|---|
| **Reactive Baseline** | **0.0 minutes** | 0.0 minutes | [0.0, 0.0] | 0.0% |
| **SupportPulse AI (M3)** | **480.0 minutes (8.0h)** | **512.4 minutes** | **[180.0, 720.0]** | **88.4%** |

**Business Implication**: IT operations teams receive an average of **8 hours of advance notice** before a ticket violates its SLA, providing ample window for manager queue rebalancing and escalation mitigation.

---

## 3. Friction Score & User Agitation Analysis (M4)

Source: `reports/friction_metrics.json`

- **ROC-AUC vs Supervisor Escalation**: `0.9257`
- **Mean Dataset Friction**: `34.2 / 100`
- **Fitted Component Weights**:
  - Behavioral Signals (contacts, reopens, elapsed SLA ratio): `78.9%`
  - Text Frustration Cues (ALL CAPS, punctuation repeats, urgency words): `12.3%`
  - Sentiment Polarity (VADER + IT Domain Lexicon): `8.8%`

### Department Friction Leaderboard

| Rank | Department | Mean Friction Index | Elevated Friction Tickets |
|---|---|---|---|
| 1 | **Engineering** | **42.1 / 100** | 184 |
| 2 | **Sales** | **39.8 / 100** | 152 |
| 3 | **Customer Support** | **38.5 / 100** | 48 |
| 4 | **Finance** | **33.2 / 100** | 98 |
| 5 | **Operations** | **31.0 / 100** | 64 |
| 6 | **Human Resources** | **28.4 / 100** | 52 |
| 7 | **Marketing** | **27.5 / 100** | 46 |
| 8 | **Legal** | **24.0 / 100** | 12 |

---

## 4. Unsupervised Theme Discovery & Outage Detection (M5)

Source: `reports/theme_metrics.json`

- **Optimal Topic Count ($k$)**: `14` (selected via NMF reconstruction stability)
- **Cluster Sanity Checks** (Post-hoc comparison vs hidden true category labels):
  - **Normalized Mutual Information (NMI)**: `0.6052`
  - **Adjusted Rand Index (ARI)**: `0.5382`
- **Emerging Anomaly Detection**:
  - Injected VPN gateway outage burst in the final 14 days was successfully detected with an anomaly **z-score of +5.49σ** against the 28-day baseline, automatically tripping the `EMERGING` badge in the UI.

---

## 5. Latency & Resource Utilization Benchmarks

Source: `reports/latency_benchmarks.json`

Measured on standard CPU workstation (Python 3.13, single laptop execution):

| Metric | Measured Value | Spec Target (Section 10) | Compliance |
|---|---|---|---|
| **Median Latency (p50)** | **17.2 ms** | < 100 ms | Passed |
| **90th Percentile (p90)** | **19.8 ms** | < 200 ms | Passed |
| **95th Percentile (p95)** | **20.4 ms** | **< 300 ms** | **Passed** |
| **99th Percentile (p99)** | **23.1 ms** | < 500 ms | Passed |
| **Single-Core Throughput** | **57.9 tickets/sec** | > 10 tps | Passed |
| **Peak Memory Consumption** | **~850 MB** | < 8,000 MB (8 GB) | Passed |
| **External Network Calls** | **0 calls** | 0 calls | 100% Air-Gapped |
