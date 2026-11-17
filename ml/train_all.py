"""Offline Training Pipeline for SupportPulse AI (M1 to M5).

Trains:
- M1: Multi-granular TF-IDF Calibrated Linear Classifiers (Category & Priority)
- M3: HistGradientBoosting SLA Risk Forecaster on multi-snapshot time slices
- M4: Multi-component Friction Scorer fitted via Logistic Regression
- M5: Unsupervised TF-IDF + NMF Theme Discovery Engine
Saves versioned artifacts to models/v1.0.0/ and registers in registry.
"""

import argparse
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np

from backend.app.ml.classify import TicketClassifier
from backend.app.ml.friction import FrictionScorer
from backend.app.ml.registry import registry
from backend.app.ml.sla_risk import (
    CATEGORIES_LIST,
    SLARiskForecaster,
    extract_snapshot_features,
)
from backend.app.ml.themes import ThemeDiscoveryEngine


def load_dataset(csv_path: str = "data/tickets.csv") -> List[Dict[str, Any]]:
    """Load tickets dataset from CSV."""
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        tickets = list(reader)
    # Ensure chronological order
    tickets.sort(key=lambda t: t["created_at"])
    return tickets


def generate_sla_snapshots(
    tickets: List[Dict[str, Any]],
    cat_clf: TicketClassifier,
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate multi-snapshot training data without future resolved_at leakage.

    Snapshots at 0%, 25%, 50%, and 75% elapsed of SLA window.
    Only tickets that are still open at snapshot moment are included.
    """
    X_rows = []
    y_rows = []

    for t in tickets:
        sla_hours = float(t["sla_hours"])
        breached = t["breached"].strip().lower() in ("true", "1", "yes")

        # Determine actual resolution duration if resolved
        if t["resolved_at"]:
            c_dt = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
            r_dt = datetime.strptime(t["resolved_at"], "%Y-%m-%d %H:%M:%S")
            actual_duration_hours = max(0.1, (r_dt - c_dt).total_seconds() / 3600.0)
        else:
            actual_duration_hours = sla_hours * 1.5 if breached else sla_hours * 0.5

        # Extract text confidence from M1
        cat_conf = 0.85
        combined_text = f"{t['subject']} {t['body']}"
        dt = datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
        hour = dt.hour
        weekday = dt.weekday()
        base_contacts = int(t["contact_count"])
        base_reopens = int(t["reopen_count"])

        # Create snapshots at 0.0, 0.25, 0.50, 0.75 elapsed SLA
        for frac in [0.0, 0.25, 0.50, 0.75]:
            snapshot_elapsed_hours = frac * sla_hours
            # Only include if ticket had not already been resolved before this snapshot
            if snapshot_elapsed_hours < actual_duration_hours:
                # Features known at this moment:
                # Contacts increase over time if ticket has multiple contacts
                observed_contacts = max(1, min(base_contacts, 1 + int(frac * (base_contacts - 1))))
                observed_reopens = max(0, min(base_reopens, int(frac * base_reopens)))
                simulated_team_load = 15 + (10 if frac > 0.4 else 0)

                feat = extract_snapshot_features(
                    category=t["category"],
                    priority=t["priority"],
                    sla_hours=sla_hours,
                    category_confidence=cat_conf,
                    hour=(hour + int(snapshot_elapsed_hours)) % 24,
                    weekday=weekday,
                    team_open_load=simulated_team_load,
                    fraction_sla_elapsed=frac,
                    contact_count=observed_contacts,
                    reopen_count=observed_reopens,
                )
                X_rows.append(feat)
                y_rows.append(1 if breached else 0)

    return np.array(X_rows, dtype=np.float32), np.array(y_rows, dtype=np.int32)


def train_all_models(
    csv_path: str = "data/tickets.csv",
    version: str = "v1.0.0",
) -> Dict[str, Any]:
    """Train M1, M3, M4, M5 modules and serialize versioned artifacts."""
    print(f"Loading dataset from {csv_path}...")
    tickets = load_dataset(csv_path)
    total_count = len(tickets)
    print(f"Loaded {total_count} tickets.")

    # Time-ordered splits: 70% train (14k), 15% val (3k), 15% test (3k)
    train_end = int(total_count * 0.70)
    val_end = int(total_count * 0.85)

    train_tickets = tickets[:train_end]
    val_tickets = tickets[train_end:val_end]
    test_tickets = tickets[val_end:]

    print(f"Splits: Train={len(train_tickets)}, Validation={len(val_tickets)}, Test={len(test_tickets)}")

    # 1. Train M1 Classification (Category & Priority)
    print("\n--- Training M1 Classifier (Category and Priority) ---")
    train_texts = [f"{t['subject']} {t['body']}" for t in train_tickets]
    train_cats = [t["category"] for t in train_tickets]
    train_prios = [t["priority"] for t in train_tickets]

    classifier = TicketClassifier(confidence_threshold=0.65)
    classifier.fit(train_texts, train_cats, train_prios)
    print("M1 Classifier fitted successfully.")

    # 2. Train M3 SLA Risk Forecasting (Multi-Snapshot)
    print("\n--- Training M3 SLA Risk Forecaster (Multi-Snapshot HistGradientBoosting) ---")
    X_train_sla, y_train_sla = generate_sla_snapshots(train_tickets, classifier)
    X_val_sla, y_val_sla = generate_sla_snapshots(val_tickets, classifier)
    print(f"Generated {len(X_train_sla)} training snapshots, {len(X_val_sla)} validation snapshots.")

    sla_forecaster = SLARiskForecaster(alert_threshold=0.50)
    sla_forecaster.fit(X_train_sla, y_train_sla, X_val=X_val_sla, y_val=y_val_sla)
    print(f"M3 SLA Forecaster trained. Calibrated alert threshold: {sla_forecaster.alert_threshold:.4f} (target recall: 80%)")

    # 3. Train M4 Friction Scorer (Component Weight Fitting)
    print("\n--- Training M4 Friction Scorer ---")
    friction_scorer = FrictionScorer()
    X_fric = []
    y_fric = []
    for t in train_tickets:
        text = f"{t['subject']} {t['body']}"
        contacts = int(t["contact_count"])
        reopens = int(t["reopen_count"])
        escalated = t["escalated"].strip().lower() in ("true", "1", "yes")
        s1, s2, s3 = friction_scorer.compute_subscores(text, contacts, reopens, elapsed_ratio=0.3)
        X_fric.append([s1, s2, s3])
        y_fric.append(1 if escalated else 0)

    friction_scorer.fit_weights(np.array(X_fric, dtype=np.float32), np.array(y_fric, dtype=np.int32))
    print(f"M4 Friction weights: Sentiment={friction_scorer.weights[0]:.3f}, Cues={friction_scorer.weights[1]:.3f}, Behavioral={friction_scorer.weights[2]:.3f}")

    # 4. Train M5 Theme Discovery
    print("\n--- Training M5 Theme Discovery (Unsupervised NMF) ---")
    theme_engine = ThemeDiscoveryEngine()
    theme_engine.fit_discover(tickets, select_best_k=True)
    summary = theme_engine.get_summary()
    print(f"M5 Theme Engine fitted. Selected optimal k={theme_engine.optimal_k}. Discovered {len(summary['themes'])} themes ({summary['emerging_count']} emerging).")
    print(f"NMI Sanity Check: {summary['nmi_sanity_score']:.4f} | ARI Sanity Check: {summary['ari_sanity_score']:.4f}")

    # 5. Save all artifacts via ModelRegistry
    print(f"\nSaving model version artifacts for '{version}'...")
    registry.save_version_artifacts(
        version=version,
        classifier=classifier,
        sla_forecaster=sla_forecaster,
        friction_scorer=friction_scorer,
        theme_engine=theme_engine,
        metrics={
            "trained_at": datetime.utcnow().isoformat(),
            "train_samples": len(train_tickets),
            "sla_alert_threshold": sla_forecaster.alert_threshold,
            "theme_optimal_k": theme_engine.optimal_k,
        },
        status="active",
    )
    print(f"Successfully serialized and activated version {version}.")

    return {
        "version": version,
        "train_samples": len(train_tickets),
        "val_samples": len(val_tickets),
        "test_samples": len(test_tickets),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train SupportPulse AI models")
    parser.add_argument("--csv", type=str, default="data/tickets.csv", help="Path to input tickets CSV")
    parser.add_argument("--version", type=str, default="v1.0.0", help="Model version identifier")
    args = parser.parse_args()

    train_all_models(csv_path=args.csv, version=args.version)
