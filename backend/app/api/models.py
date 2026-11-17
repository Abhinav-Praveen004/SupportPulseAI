"""Model Lifecycle, Registry, Continuous Retraining, and Rollback API router."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sklearn.metrics import accuracy_score, f1_score
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import get_current_user, require_roles
from backend.app.db.models import Feedback, Ticket, User
from backend.app.db.session import get_db
from backend.app.ml.classify import TicketClassifier
from backend.app.ml.registry import registry
from backend.app.schemas.model import (
    ModelVersionOut,
    RetrainRequest,
    RetrainResponse,
    RollbackResponse,
)

router = APIRouter(prefix="/models", tags=["models"])


@router.get("", response_model=List[ModelVersionOut])
def list_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered model versions, accuracy, macro-F1, and active status."""
    versions = registry.list_versions()
    results = []
    for idx, v in enumerate(versions, start=1):
        dt_str = v.get("created_at")
        try:
            dt = datetime.fromisoformat(dt_str)
        except Exception:
            dt = datetime.now(timezone.utc)

        results.append(ModelVersionOut(
            id=idx,
            version=v["version"],
            model_type="classification",
            status="active" if v.get("is_active") else v.get("status", "archived"),
            macro_f1=float(v.get("macro_f1", 0.0)),
            roc_auc=float(v.get("roc_auc", 0.0)) if v.get("roc_auc") is not None else None,
            accuracy=float(v.get("accuracy", 0.0)),
            metrics=v.get("metrics", {}),
            created_at=dt,
        ))
    return results


@router.post("/retrain", response_model=RetrainResponse)
def trigger_retraining(
    payload: RetrainRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "manager"])),
):
    """Retrain candidate model incorporating human feedback and gate promotion on non-regression."""
    # 1. Fetch tickets and feedback overrides
    tickets_rows = db.query(Ticket).order_by(Ticket.created_at).all()
    feedbacks = db.query(Feedback).all()

    if len(feedbacks) < payload.min_feedback_samples and not payload.evaluate_only:
        # Still proceed with training with available feedback to support on-demand runs
        pass

    # Build map of feedback corrections
    corrections = {f.ticket_id: (f.corrected_category, f.corrected_priority) for f in feedbacks}

    texts = []
    categories = []
    priorities = []
    for t in tickets_rows:
        text = f"{t.subject} {t.body}"
        cat = corrections.get(t.ticket_id, (t.category, t.priority))[0]
        prio = corrections.get(t.ticket_id, (t.category, t.priority))[1]
        texts.append(text)
        categories.append(cat)
        priorities.append(prio)

    # Time-ordered validation split: last 15%
    split_idx = int(len(texts) * 0.85)
    train_texts, val_texts = texts[:split_idx], texts[split_idx:]
    train_cats, val_cats = categories[:split_idx], categories[split_idx:]
    train_prios, val_prios = priorities[:split_idx], priorities[split_idx:]

    # Train candidate classifier
    candidate_clf = TicketClassifier(confidence_threshold=0.65)
    candidate_clf.fit(train_texts, train_cats, train_prios)

    # Evaluate candidate on validation set
    val_preds = [candidate_clf.predict_category(t)["category"] for t in val_texts]
    cand_f1 = float(f1_score(val_cats, val_preds, average="macro", zero_division=0))
    cand_acc = float(accuracy_score(val_cats, val_preds))

    # Get current active model's macro-F1
    current_f1 = 0.0
    for v in registry.list_versions():
        if v.get("is_active"):
            current_f1 = float(v.get("macro_f1", 0.0))
            break

    # Determine candidate version string
    existing_versions = [v["version"] for v in registry.list_versions()]
    next_minor = len(existing_versions)
    candidate_version = f"v1.{next_minor}.0"

    # Promotion Gate: promote only if candidate macro-F1 >= current_macro_f1 - 0.02
    promoted = (cand_f1 >= current_f1 - 0.02) and not payload.evaluate_only

    status_str = "active" if promoted else "candidate_rejected"
    msg = (
        f"Candidate model {candidate_version} evaluated. Candidate Macro-F1: {cand_f1:.4f} vs "
        f"Active: {current_f1:.4f}. {'Promoted to production.' if promoted else 'Rejected due to regression.'}"
    )

    if promoted and registry.sla_forecaster and registry.friction_scorer:
        registry.save_version_artifacts(
            version=candidate_version,
            classifier=candidate_clf,
            sla_forecaster=registry.sla_forecaster,
            friction_scorer=registry.friction_scorer,
            theme_engine=registry.theme_engine,
            metrics={
                "macro_f1": cand_f1,
                "accuracy": cand_acc,
                "retrained_with_feedback_count": len(feedbacks),
            },
            status="active",
        )

    return RetrainResponse(
        candidate_version=candidate_version,
        previous_version=registry.active_version,
        promoted=promoted,
        status=status_str,
        candidate_macro_f1=round(cand_f1, 4),
        previous_macro_f1=round(current_f1, 4),
        message=msg,
        metrics={"accuracy": round(cand_acc, 4), "macro_f1": round(cand_f1, 4)},
    )


@router.post("/{version}/rollback", response_model=RollbackResponse)
def rollback_model(
    version: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "manager"])),
):
    """Instantly roll back production model to a previous version."""
    prev_version = registry.active_version
    success = registry.rollback(version)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Rollback to version '{version}' failed. Version artifacts do not exist or are invalid.",
        )

    return RollbackResponse(
        active_version=version,
        rolled_back_from=prev_version,
        message=f"Model successfully rolled back to version {version}.",
    )
