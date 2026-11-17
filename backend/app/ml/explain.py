"""Unified Explainability and Inference Engine.

Orchestrates multi-model inference (M1 classification, M2 routing, M3 SLA risk, M4 friction)
and aggregates explainability payloads.
"""

from typing import Any, Dict, Optional
from datetime import datetime
from backend.app.ml.registry import registry


def analyze_ticket_text(
    subject: str,
    body: str,
    department: str = "Engineering",
    channel: str = "portal",
    sla_hours: Optional[float] = None,
    contact_count: int = 1,
    reopen_count: int = 0,
    elapsed_minutes: float = 0.0,
    team_open_load: int = 15,
) -> Dict[str, Any]:
    """Run full ML analysis pipeline for a ticket or draft text."""
    combined_text = f"{subject}. {body}"

    # Ensure models are loaded
    if not registry.classifier:
        registry.load_active_models()

    if not registry.classifier or not registry.sla_forecaster or not registry.friction_scorer:
        raise RuntimeError("ML models are not available. Run 'python -m ml.train_all' first.")

    # 1. M1 Classification
    cat_res = registry.classifier.predict_category(combined_text)
    prio_res = registry.classifier.predict_priority(combined_text)

    predicted_cat = cat_res["category"]
    predicted_prio = prio_res["priority"]

    # Effective SLA target hours
    target_sla_hours = sla_hours or (
        4.0 if predicted_prio == "P1" else
        8.0 if predicted_prio == "P2" else
        24.0 if predicted_prio == "P3" else 72.0
    )

    # 2. M2 Routing
    rec_team, route_reason = registry.routing_engine.recommend_team(
        predicted_category=predicted_cat,
        category_confidence=cat_res["confidence"],
        team_workload={rec_team: team_open_load} if "rec_team" in locals() else None,
    )

    # 3. M3 SLA Risk
    total_minutes = target_sla_hours * 60.0
    fraction_elapsed = min(1.0, elapsed_minutes / max(1.0, total_minutes))
    now = datetime.now()

    sla_res = registry.sla_forecaster.predict_risk(
        category=predicted_cat,
        priority=predicted_prio,
        sla_hours=target_sla_hours,
        category_confidence=cat_res["confidence"],
        hour=now.hour,
        weekday=now.weekday(),
        team_open_load=team_open_load,
        fraction_sla_elapsed=fraction_elapsed,
        contact_count=contact_count,
        reopen_count=reopen_count,
    )

    # 4. M4 Friction Score
    fric_res = registry.friction_scorer.calculate(
        text=combined_text,
        contact_count=contact_count,
        reopen_count=reopen_count,
        elapsed_ratio=fraction_elapsed,
    )

    return {
        "category": predicted_cat,
        "category_confidence": round(cat_res["confidence"], 4),
        "category_probabilities": {k: round(v, 4) for k, v in cat_res["probabilities"].items()},
        "priority": predicted_prio,
        "priority_confidence": round(prio_res["confidence"], 4),
        "priority_probabilities": {k: round(v, 4) for k, v in prio_res["probabilities"].items()},
        "needs_human_triage": cat_res["needs_human_triage"],
        "sla_breach_probability": sla_res["breach_probability"],
        "sla_risk_band": sla_res["risk_band"],
        "estimated_minutes_to_breach": sla_res["estimated_minutes_to_breach"],
        "friction_score": fric_res["score"],
        "friction_band": fric_res["band"],
        "friction_breakdown": fric_res["breakdown"],
        "routing_recommendation": rec_team,
        "routing_reasoning": route_reason,
        "top_contributing_ngrams": cat_res["top_contributing_ngrams"],
        "sla_top_drivers": sla_res["top_drivers"],
    }
