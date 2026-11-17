# SupportPulse AI - 5-Minute Product Walkthrough Script

This script guides an evaluator, engineer, or executive through a 5-minute live demonstration of SupportPulse AI.

---

## Preparation (30 seconds)
1. Start the system:
   ```bash
   make dev
   # Or via PowerShell: .\tasks.ps1 dev
   ```
2. Open your browser at `http://localhost:5173`.
3. Note that the application runs **100% locally on CPU** with **zero external API calls**.

---

## Minute 1: Command Center & Real-Time Telemetry
1. **Login**: Click sign-in or use pre-authenticated demo mode (Default credentials: `agent` / `agent123`).
2. **Examine the Top Navigation**:
   - Point out the **green pulsing SSE indicator** labeled `Connected` (Server-Sent Events active).
   - Toggle between **Dark Mode** and **Light Mode** using the sun/moon icon.
3. **KPI Strip Overview**:
   - Point to **High & Critical Risk**: shows tickets forecasted to breach their SLA before deadlines expire.
   - Point to **Breaches in Next 4h**: acute warning horizon.
   - Point to **Average Friction Index**: real-time user agitation tracking.
   - Point to **Auto-Triaged Share**: share of tickets meeting confidence safety criteria.
4. **Live At-Risk Queue**:
   - Click on any top at-risk ticket to preview the **Instant Detail Drawer**.

---

## Minute 2: Triage Queue & Explainable AI
1. Navigate to **Triage Queue** in the left sidebar.
2. **Dense Multi-Modal Table**:
   - Note that risk and friction are never conveyed by color alone: each badge uses distinct iconography, shapes, and text labels (WCAG AA accessible).
   - Point to the **Confidence Bar** and note the **Triage Tag** on tickets requiring human review.
3. **Filter and Search**:
   - Toggle the checkbox: *"Only Show Low-Confidence Tickets Needing Human Triage"*.
   - Filter by Category (e.g. *Network/VPN*) or Priority (*P1*).
4. **Inspect Ticket Detail**:
   - Click any ticket row to slide open the detail drawer.
   - Notice the **Influential N-Grams Highlighted** directly in the ticket description.
   - Review **M3 Counterfactual Risk Drivers**: *"High queue volume in assigned team (+18% risk)"*.
   - Review **M4 Friction Breakdown**: sentiment, text cues (ALL CAPS, punctuation), and behavioral signals (reopens, contacts).

---

## Minute 3: SLA Risk Forecast & Precision/Recall Slider
1. Navigate to **SLA Risk Forecast** in the sidebar.
2. **Interactive Threshold Slider**:
   - Drag the slider between `0.15` and `0.75`.
   - Observe how **Estimated Recall**, **Estimated Precision**, and **Flagged Tickets** update in real time.
   - Explain how managers can dynamically tune operational alert sensitivity without retraining models.
3. **Team x Hour Heatmap**:
   - Show the 24-hour congestion matrix across IT teams.
   - Identify off-hours bottlenecks where tickets experience higher breach hazards.

---

## Minute 4: Theme Explorer & Emerging Outage Detection
1. Navigate to **Theme Explorer** in the sidebar.
2. **Unsupervised Discovery**:
   - Point out that themes were discovered completely unsupervised using TF-IDF + NMF without human supervision.
   - Point to the banner displaying the cluster sanity check: $\text{NMI} = 0.6052, \text{ARI} = 0.5382$.
3. **Emerging Anomaly Alert**:
   - Point to Theme #1 with the glowing **EMERGING (+5.49σ)** badge.
   - Show how SupportPulse AI automatically caught the simulated VPN gateway outage burst in the final 2 weeks based on volume deviation from the 28-day baseline.
   - Inspect the representative ticket samples listed on the card.

---

## Minute 5: Model Lab & Feedback Retraining Loop
1. Navigate to **Model Lab** in the sidebar.
2. **Synthetic Data Disclosure**:
   - Note the prominent amber disclosure banner declaring reproducible synthetic training data (`SEED = 42`).
3. **Old Regex Baseline vs SupportPulse AI**:
   - Review the empirical comparison table:
     - Category Accuracy: **87.67% (Regex) vs 100.00% (ML)** (+12.33% gain).
     - SLA Advance Warning: **0.0 minutes (Reactive) vs 480.0 minutes / 8.0 hours (SupportPulse AI)**.
4. **Confusion Matrix & Calibration Plot**:
   - Show the 10x10 confusion matrix and the near-diagonal probabilistic calibration curve ($\text{ECE} = 0.045$).
5. **Continuous Learning Loop**:
   - Click **Trigger Retrain & Evaluate Gate**.
   - Show how the candidate model is trained, evaluated on held-out validation data, and gated against regression before promotion.
   - Point out the **1-Click Rollback** button which instantly restores previous model artifacts.
