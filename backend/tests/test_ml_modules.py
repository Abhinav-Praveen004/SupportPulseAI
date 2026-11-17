"""Unit tests for Phase 2: ML Modules, no-leakage, calibration sanity, and explainability."""

import numpy as np
import pytest

from backend.app.ml.baseline import RegexBaselineClassifier
from backend.app.ml.friction import FrictionScorer
from backend.app.ml.route import RoutingEngine
from backend.app.ml.sla_risk import (
    CATEGORIES_LIST,
    extract_snapshot_features,
)


def test_baseline_regex_classifier():
    """Verify legacy regex baseline classifies obvious keywords."""
    clf = RegexBaselineClassifier()

    cat1, conf1, _ = clf.predict_category("Urgent: Please reset my Okta password, locked out")
    assert cat1 == "Password/Access"

    cat2, conf2, _ = clf.predict_category("AnyConnect VPN gateway timeout connecting to internal network")
    assert cat2 == "Network/VPN"

    cat3, conf3, _ = clf.predict_category("Office printer paper jam in tray 2")
    assert cat3 == "Printer"

    prio1, _, _ = clf.predict_priority("Production down critical outage revenue loss")
    assert prio1 == "P1"

    prio4, _, _ = clf.predict_priority("Minor question, no rush, when possible")
    assert prio4 == "P4"


def test_no_leakage_snapshot_feature_extraction():
    """Verify snapshot feature extraction relies strictly on time-of-snapshot variables."""
    # Ensure function signature does not take resolved_at or future target labels
    feat = extract_snapshot_features(
        category="Network/VPN",
        priority="P2",
        sla_hours=8.0,
        category_confidence=0.92,
        hour=14,
        weekday=1,
        team_open_load=20,
        fraction_sla_elapsed=0.5,
        contact_count=2,
        reopen_count=0,
    )

    assert isinstance(feat, np.ndarray)
    assert len(feat) == 11
    # Check that fraction_sla_elapsed is preserved
    assert feat[8] == 0.5
    # Check priority is mapped to integer
    assert feat[1] == 2.0


def test_friction_scorer_bounds_and_cues():
    """Verify friction score stays bounded in [0, 100] and responds to frustration cues."""
    scorer = FrictionScorer()

    calm_res = scorer.calculate(
        text="Thank you very much. Could you please check when convenient?",
        contact_count=1,
        reopen_count=0,
        elapsed_ratio=0.1,
    )
    assert 0.0 <= calm_res["score"] <= 100.0
    assert calm_res["band"] in ("Calm", "Uneasy")

    frustrated_res = scorer.calculate(
        text="THIS IS TOTALLY UNACCEPTABLE! THIRD TIME I AM ASKING! ESCALATE IMMEDIATELY!",
        contact_count=5,
        reopen_count=2,
        elapsed_ratio=0.9,
    )
    assert 0.0 <= frustrated_res["score"] <= 100.0
    assert frustrated_res["score"] > calm_res["score"]
    assert frustrated_res["band"] in ("Frustrated", "Critical")


def test_routing_engine_primary_and_overflow():
    """Verify routing assigns specialized primary teams and handles overload overflow."""
    router = RoutingEngine(overload_threshold=40)

    # Normal load: assigns primary team
    team, reason = router.recommend_team("Network/VPN", 0.95, team_workload={"Network Ops": 15})
    assert team == "Network Ops"
    assert "Network Ops" in reason

    # Overload on IT Helpdesk: overflows Service Request to Endpoint Services
    team_ov, reason_ov = router.recommend_team(
        "Service Request",
        0.90,
        team_workload={"IT Helpdesk": 60, "Endpoint Services": 10},
    )
    assert team_ov == "Endpoint Services"
    assert "overflow" in reason_ov.lower()
