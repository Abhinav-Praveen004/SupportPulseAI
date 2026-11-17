"""Theme Discovery and Emerging Cluster API router."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.security import get_current_user
from backend.app.db.models import Ticket, User
from backend.app.db.session import get_db
from backend.app.ml.registry import registry
from backend.app.ml.themes import ThemeDiscoveryEngine
from backend.app.schemas.dashboard import ThemeListResponse

router = APIRouter(prefix="/themes", tags=["themes"])


@router.get("", response_model=ThemeListResponse)
def get_discovered_themes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve unsupervised theme clusters, top terms, trends, and emerging anomalies."""
    if not registry.theme_engine:
        registry.load_active_models()

    if registry.theme_engine:
        summary = registry.theme_engine.get_summary()
        return ThemeListResponse(
            themes=summary["themes"],
            total_themes=summary["total_themes"],
            emerging_count=summary["emerging_count"],
            nmi_sanity_score=summary["nmi_sanity_score"],
            ari_sanity_score=summary["ari_sanity_score"],
            last_refreshed=summary["last_refreshed"],
        )

    # Fallback: fit on live tickets
    return refresh_themes(db=db, current_user=current_user)


@router.post("/refresh", response_model=ThemeListResponse)
def refresh_themes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Re-run unsupervised theme discovery on recent tickets and update active model."""
    tickets_rows = (
        db.query(Ticket)
        .order_by(Ticket.created_at.desc())
        .limit(5000)
        .all()
    )

    tickets_data = [
        {
            "ticket_id": t.ticket_id,
            "subject": t.subject,
            "body": t.body,
            "category": t.category,
            "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for t in reversed(tickets_rows)
    ]

    engine = ThemeDiscoveryEngine()
    engine.fit_discover(tickets_data, select_best_k=True)
    registry.theme_engine = engine

    # Save to active model directory
    v_dir = registry.get_version_dir(registry.active_version)
    if v_dir.exists():
        engine.save(str(v_dir / "themes.joblib"))

    summary = engine.get_summary()
    return ThemeListResponse(
        themes=summary["themes"],
        total_themes=summary["total_themes"],
        emerging_count=summary["emerging_count"],
        nmi_sanity_score=summary["nmi_sanity_score"],
        ari_sanity_score=summary["ari_sanity_score"],
        last_refreshed=summary["last_refreshed"],
    )
