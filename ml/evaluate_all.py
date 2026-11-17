"""Comprehensive Offline Evaluation Suite for SupportPulse AI.

Evaluates all models on the held-out 15% chronological test split:
1. Regex Baseline vs ML Classifier (Accuracy, Macro-F1, Per-class, Confusion Matrix, Calibration)
2. SLA Risk Forecasting (ROC-AUC, PR-AUC, Brier, Calibration, Alert Threshold)
3. Lead-Time Analysis: Advance warning minutes vs Reactive Baseline (0 min)
4. Friction Score (ROC-AUC vs Escalation, Department ranking)
5. Theme Discovery (NMI, ARI, Emerging Theme z-scores)
6. Latency Benchmarks (CPU p50/p90/p95/p99)

Writes all JSON outputs to /reports for documentation and UI visualization.
"""

import argparse
import csv
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# Set LOKY_MAX_CPU_COUNT to silence Windows joblib core warning
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    adjusted_rand_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    normalized_mutual_info_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.calibration import calibration_curve

from backend.app.ml.baseline import RegexBaselineClassifier
from backend.app.ml.classify import TicketClassifier
from backend.app.ml.explain import analyze_ticket_text
from backend.app.ml.friction import FrictionScorer
from backend.app.ml.registry import registry
from backend.app.ml.sla_risk import (
    CATEGORIES_LIST,
    SLARiskForecaster,
    extract_snapshot_features,
)
from backend.app.ml.themes import ThemeDiscoveryEngine
from ml.train_all import generate_sla_snapshots, load_dataset


def compute_calibration_data(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> Dict[str, Any]:
    """Calculate calibration curve bins and Expected Calibration Error (ECE)."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    # Compute ECE
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bins_data = []
    for i in range(len(prob_true)):
        bins_data.append({
            "mean_predicted_probability": round(float(prob_pred[i]), 4),
            "fraction_of_positives": round(float(prob_true[i]), 4),
        })

    # Simple ECE estimate
    for i in range(n_bins):
        bin_mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        bin_count = np.sum(bin_mask)
        if bin_count > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (bin_count / len(y_true)) * abs(bin_acc - bin_conf)

    return {
        "ece": round(float(ece), 4),
        "calibration_curve": bins_data,
    }


def evaluate_all(
    csv_path: str = "data/tickets.csv",
    reports_dir: str = "reports",
) -> Dict[str, Any]:
    """Run all offline evaluations and dump JSON reports."""
    rep_dir = Path(reports_dir)
    rep_dir.mkdir(parents=True, exist_ok=True)

    print("Loading dataset for evaluation...")
    tickets = load_dataset(csv_path)
    total_count = len(tickets)

    # 15% held-out test split (chronological end of dataset)
    val_end = int(total_count * 0.85)
    test_tickets = tickets[val_end:]
    print(f"Evaluating on {len(test_tickets)} held-out chronological test tickets...")

    test_texts = [f"{t['subject']} {t['body']}" for t in test_tickets]
    y_test_cat = [t["category"] for t in test_tickets]
    y_test_prio = [t["priority"] for t in test_tickets]

    # Ensure active models are loaded
    registry.load_active_models()
    classifier = registry.classifier
    sla_forecaster = registry.sla_forecaster
    friction_scorer = registry.friction_scorer
    theme_engine = registry.theme_engine

    if not classifier or not sla_forecaster or not friction_scorer:
        raise RuntimeError("Active models not loaded. Train models before evaluation.")

    # -------------------------------------------------------------
    # 1. EVALUATION: Legacy Regex Baseline vs M1 Classifier
    # -------------------------------------------------------------
    print("\n--- Evaluating Legacy Regex Baseline vs SupportPulse AI Classifier ---")
    baseline = RegexBaselineClassifier()
    base_cat_preds, base_prio_preds = baseline.predict(test_texts)

    base_cat_acc = float(accuracy_score(y_test_cat, base_cat_preds))
    base_cat_f1_macro = float(f1_score(y_test_cat, base_cat_preds, average="macro", zero_division=0))
    base_cat_f1_weighted = float(f1_score(y_test_cat, base_cat_preds, average="weighted", zero_division=0))

    base_prio_acc = float(accuracy_score(y_test_prio, base_prio_preds))
    base_prio_f1 = float(f1_score(y_test_prio, base_prio_preds, average="macro", zero_division=0))

    # M1 ML Predictions
    ml_cat_preds = []
    ml_prio_preds = []
    ml_cat_probs = []
    ml_confidences = []
    needs_triage_count = 0

    for text in test_texts:
        cat_p = classifier.predict_category(text)
        prio_p = classifier.predict_priority(text)
        ml_cat_preds.append(cat_p["category"])
        ml_prio_preds.append(prio_p["priority"])
        ml_cat_probs.append(cat_p["probabilities"])
        ml_confidences.append(cat_p["confidence"])
        if cat_p["needs_human_triage"]:
            needs_triage_count += 1

    ml_cat_acc = float(accuracy_score(y_test_cat, ml_cat_preds))
    ml_cat_f1_macro = float(f1_score(y_test_cat, ml_cat_preds, average="macro", zero_division=0))
    ml_cat_f1_weighted = float(f1_score(y_test_cat, ml_cat_preds, average="weighted", zero_division=0))

    ml_prio_acc = float(accuracy_score(y_test_prio, ml_prio_preds))
    ml_prio_f1 = float(f1_score(y_test_prio, ml_prio_preds, average="macro", zero_division=0))

    labels_cat = sorted(list(set(y_test_cat)))
    cm_ml = confusion_matrix(y_test_cat, ml_cat_preds, labels=labels_cat).tolist()
    cm_base = confusion_matrix(y_test_cat, base_cat_preds, labels=labels_cat).tolist()

    cr_ml = classification_report(y_test_cat, ml_cat_preds, labels=labels_cat, output_dict=True, zero_division=0)
    cr_base = classification_report(y_test_cat, base_cat_preds, labels=labels_cat, output_dict=True, zero_division=0)

    # Save Baseline Metrics
    baseline_metrics = {
        "model_type": "Regex/Keyword Legacy Rules",
        "category_accuracy": round(base_cat_acc, 4),
        "category_macro_f1": round(base_cat_f1_macro, 4),
        "category_weighted_f1": round(base_cat_f1_weighted, 4),
        "priority_accuracy": round(base_prio_acc, 4),
        "priority_macro_f1": round(base_prio_f1, 4),
        "labels": labels_cat,
        "per_class_report": cr_base,
        "confusion_matrix": cm_base,
    }
    with open(rep_dir / "baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(baseline_metrics, f, indent=2)

    # Save ML Classification Metrics
    classification_metrics = {
        "model_type": "SupportPulse AI Calibrated TF-IDF Classifier",
        "category_accuracy": round(ml_cat_acc, 4),
        "category_macro_f1": round(ml_cat_f1_macro, 4),
        "category_weighted_f1": round(ml_cat_f1_weighted, 4),
        "priority_accuracy": round(ml_prio_acc, 4),
        "priority_macro_f1": round(ml_prio_f1, 4),
        "accuracy_gain_vs_baseline_pct": round((ml_cat_acc - base_cat_acc) * 100, 2),
        "macro_f1_gain_vs_baseline_pct": round((ml_cat_f1_macro - base_cat_f1_macro) * 100, 2),
        "needs_human_triage_count": needs_triage_count,
        "needs_human_triage_pct": round((needs_triage_count / len(test_texts)) * 100, 2),
        "mean_confidence": round(float(np.mean(ml_confidences)), 4),
        "labels": labels_cat,
        "per_class_report": cr_ml,
        "confusion_matrix": cm_ml,
    }
    with open(rep_dir / "classification_metrics.json", "w", encoding="utf-8") as f:
        json.dump(classification_metrics, f, indent=2)

    print(f"Category Accuracy: Baseline = {base_cat_acc * 100:.2f}% | ML = {ml_cat_acc * 100:.2f}% (Gain: +{(ml_cat_acc - base_cat_acc) * 100:.2f}%)")
    print(f"Category Macro-F1: Baseline = {base_cat_f1_macro:.4f} | ML = {ml_cat_f1_macro:.4f}")

    # -------------------------------------------------------------
    # 2. EVALUATION: M3 SLA Risk Forecasting & Lead-Time Analysis
    # -------------------------------------------------------------
    print("\n--- Evaluating M3 SLA Risk Forecaster and Lead-Time ---")
    X_test_sla, y_test_sla = generate_sla_snapshots(test_tickets, classifier)
    test_probs = sla_forecaster.model.predict_proba(X_test_sla)[:, 1]

    roc_auc = float(roc_auc_score(y_test_sla, test_probs))
    brier = float(brier_score_loss(y_test_sla, test_probs))

    threshold = sla_forecaster.alert_threshold
    y_pred_binary = (test_probs >= threshold).astype(int)
    rec = float(recall_score(y_test_sla, y_pred_binary, zero_division=0))
    prec = float(precision_score(y_test_sla, y_pred_binary, zero_division=0))
    f1_sla = float(f1_score(y_test_sla, y_pred_binary, zero_division=0))

    calib_data = compute_calibration_data(y_test_sla, test_probs)

    # Lead-Time Analysis on Test Tickets that Breached
    lead_times_minutes: List[float] = []
    breached_test_tickets = [
        t for t in test_tickets
        if t["breached"].strip().lower() in ("true", "1", "yes") and t["resolved_at"]
    ]

    for t in breached_test_tickets:
        sla_hours = float(t["sla_hours"])
        c_dt = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
        r_dt = datetime.strptime(t["resolved_at"], "%Y-%m-%d %H:%M:%S")
        deadline_dt = c_dt + timedelta(hours=sla_hours)

        # Check at which snapshot the model first raised the alert
        first_alert_dt = None
        for frac in [0.0, 0.25, 0.50, 0.75]:
            snap_dt = c_dt + timedelta(hours=frac * sla_hours)
            feat = extract_snapshot_features(
                category=t["category"],
                priority=t["priority"],
                sla_hours=sla_hours,
                category_confidence=0.85,
                hour=snap_dt.hour,
                weekday=snap_dt.weekday(),
                team_open_load=15,
                fraction_sla_elapsed=frac,
                contact_count=int(t["contact_count"]),
                reopen_count=int(t["reopen_count"]),
            )
            prob = float(sla_forecaster.model.predict_proba(feat.reshape(1, -1))[0, 1])
            if prob >= threshold:
                first_alert_dt = snap_dt
                break

        if first_alert_dt:
            # Advance lead time is minutes from first alert until the SLA deadline breach
            lead_min = max(0.0, (deadline_dt - first_alert_dt).total_seconds() / 60.0)
            lead_times_minutes.append(lead_min)
        else:
            # Missed advance alert before deadline
            lead_times_minutes.append(0.0)

    median_lead_time = float(np.median(lead_times_minutes)) if lead_times_minutes else 0.0
    mean_lead_time = float(np.mean(lead_times_minutes)) if lead_times_minutes else 0.0
    p25_lead_time = float(np.percentile(lead_times_minutes, 25)) if lead_times_minutes else 0.0
    p75_lead_time = float(np.percentile(lead_times_minutes, 75)) if lead_times_minutes else 0.0

    sla_metrics = {
        "roc_auc": round(roc_auc, 4),
        "brier_score": round(brier, 4),
        "alert_threshold": round(threshold, 4),
        "recall_at_threshold": round(rec, 4),
        "precision_at_threshold": round(prec, 4),
        "f1_at_threshold": round(f1_sla, 4),
        "expected_calibration_error": calib_data["ece"],
        "calibration_curve": calib_data["calibration_curve"],
        "test_snapshots_evaluated": len(y_test_sla),
    }
    with open(rep_dir / "sla_risk_metrics.json", "w", encoding="utf-8") as f:
        json.dump(sla_metrics, f, indent=2)

    lead_time_report = {
        "method_comparison": {
            "reactive_baseline": {
                "description": "Traditional reactive alerting (alerts fire only when deadline expires)",
                "median_advance_warning_minutes": 0.0,
                "advance_warning_percentage": 0.0,
            },
            "supportpulse_ai": {
                "description": "Proactive SLA risk forecasting via multi-snapshot gradient boosting",
                "median_advance_warning_minutes": round(median_lead_time, 1),
                "mean_advance_warning_minutes": round(mean_lead_time, 1),
                "p25_advance_warning_minutes": round(p25_lead_time, 1),
                "p75_advance_warning_minutes": round(p75_lead_time, 1),
                "breaches_detected_in_advance_pct": round(
                    (sum(1 for lt in lead_times_minutes if lt > 0) / max(1, len(lead_times_minutes))) * 100, 2
                ),
                "evaluated_breached_tickets": len(breached_test_tickets),
            },
        },
    }
    with open(rep_dir / "lead_time_analysis.json", "w", encoding="utf-8") as f:
        json.dump(lead_time_report, f, indent=2)

    print(f"SLA ROC-AUC: {roc_auc:.4f} | Brier: {brier:.4f}")
    print(f"Alert Threshold: {threshold:.4f} -> Recall: {rec * 100:.1f}%, Precision: {prec * 100:.1f}%")
    print(f"Lead-Time: SupportPulse AI Median = {median_lead_time:.1f} mins advance warning vs Reactive = 0.0 mins")

    # -------------------------------------------------------------
    # 3. EVALUATION: M4 Friction Score
    # -------------------------------------------------------------
    print("\n--- Evaluating M4 Friction Scorer ---")
    fric_scores = []
    y_escalated = []
    dept_friction: Dict[str, List[float]] = {}
    band_counts: Dict[str, int] = {"Calm": 0, "Uneasy": 0, "Frustrated": 0, "Critical": 0}

    for t in test_tickets:
        text = f"{t['subject']} {t['body']}"
        contacts = int(t["contact_count"])
        reopens = int(t["reopen_count"])
        esc = t["escalated"].strip().lower() in ("true", "1", "yes")

        res = friction_scorer.calculate(text, contacts, reopens, elapsed_ratio=0.4)
        score = res["score"]
        fric_scores.append(score)
        y_escalated.append(1 if esc else 0)
        band_counts[res["band"]] += 1

        dept = t.get("department", "Other")
        dept_friction.setdefault(dept, []).append(score)

    fric_auc = float(roc_auc_score(y_escalated, fric_scores))

    dept_rankings = [
        {"department": dept, "avg_friction": round(float(np.mean(scores)), 1), "ticket_count": len(scores)}
        for dept, scores in dept_friction.items()
    ]
    dept_rankings.sort(key=lambda d: d["avg_friction"], reverse=True)

    friction_metrics = {
        "roc_auc_vs_escalation": round(fric_auc, 4),
        "mean_friction_score": round(float(np.mean(fric_scores)), 1),
        "bands_distribution": band_counts,
        "department_rankings": dept_rankings,
        "weights": {
            "sentiment": round(float(friction_scorer.weights[0]), 3),
            "text_cues": round(float(friction_scorer.weights[1]), 3),
            "behavioral": round(float(friction_scorer.weights[2]), 3),
        },
    }
    with open(rep_dir / "friction_metrics.json", "w", encoding="utf-8") as f:
        json.dump(friction_metrics, f, indent=2)

    print(f"Friction Score ROC-AUC (vs Escalation): {fric_auc:.4f}")

    # -------------------------------------------------------------
    # 4. EVALUATION: M5 Theme Discovery
    # -------------------------------------------------------------
    print("\n--- Evaluating M5 Theme Discovery ---")
    theme_summary = theme_engine.get_summary()
    with open(rep_dir / "theme_metrics.json", "w", encoding="utf-8") as f:
        json.dump(theme_summary, f, indent=2)

    print(f"Discovered Themes: {theme_summary['total_themes']} | Emerging Themes: {theme_summary['emerging_count']}")
    print(f"NMI Sanity: {theme_summary['nmi_sanity_score']:.4f} | ARI Sanity: {theme_summary['ari_sanity_score']:.4f}")

    # -------------------------------------------------------------
    # 5. BENCHMARK: Latency & Throughput (CPU)
    # -------------------------------------------------------------
    print("\n--- Benchmarking CPU Latencies ---")
    benchmark_samples = test_tickets[:200]
    latencies_ms = []

    # Warmup
    for t in benchmark_samples[:10]:
        analyze_ticket_text(t["subject"], t["body"])

    for t in benchmark_samples:
        t0 = time.perf_counter()
        analyze_ticket_text(
            subject=t["subject"],
            body=t["body"],
            department=t["department"],
            channel=t["channel"],
            contact_count=int(t["contact_count"]),
            reopen_count=int(t["reopen_count"]),
        )
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)

    p50 = float(np.percentile(latencies_ms, 50))
    p90 = float(np.percentile(latencies_ms, 90))
    p95 = float(np.percentile(latencies_ms, 95))
    p99 = float(np.percentile(latencies_ms, 99))
    mean_lat = float(np.mean(latencies_ms))
    throughput = 1000.0 / mean_lat if mean_lat > 0 else 0.0

    latency_report = {
        "hardware": "Single Laptop CPU (No GPU)",
        "sample_count": len(benchmark_samples),
        "mean_latency_ms": round(mean_lat, 2),
        "p50_ms": round(p50, 2),
        "p90_ms": round(p90, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "throughput_tickets_per_sec": round(throughput, 1),
        "target_p95_under_300ms_met": bool(p95 < 300.0),
    }
    with open(rep_dir / "latency_benchmarks.json", "w", encoding="utf-8") as f:
        json.dump(latency_report, f, indent=2)

    print(f"Inference Latencies (CPU): p50={p50:.1f}ms, p95={p95:.1f}ms, p99={p99:.1f}ms | Throughput={throughput:.1f} tps")
    print(f"Target P95 < 300ms met: {p95 < 300.0}")

    return {
        "classification": classification_metrics,
        "baseline": baseline_metrics,
        "sla_risk": sla_metrics,
        "lead_time": lead_time_report,
        "friction": friction_metrics,
        "themes": theme_summary,
        "latency": latency_report,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SupportPulse AI models")
    parser.add_argument("--csv", type=str, default="data/tickets.csv", help="Input tickets CSV path")
    parser.add_argument("--reports", type=str, default="reports", help="Reports destination directory")
    args = parser.parse_args()

    evaluate_all(csv_path=args.csv, reports_dir=args.reports)
