"""Developer, Seeding, Import, and Healthcheck API router."""

import io
import json
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import get_current_user, require_roles
from backend.app.db.models import Ticket, User
from backend.app.db.session import engine, get_db
from backend.app.ml.registry import registry
from backend.app.services.importer import import_tickets_from_csv
from ml.seed_data import generate_synthetic_dataset

router = APIRouter(tags=["developer"])


@router.get("/health")
def health_check():
    """System health status and operational indicators."""
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        db_ok = False

    models_loaded = (
        registry.classifier is not None
        and registry.sla_forecaster is not None
        and registry.friction_scorer is not None
    )

    return {
        "status": "healthy" if db_ok and models_loaded else "degraded",
        "app": settings.APP_NAME,
        "database_connected": db_ok,
        "active_model_version": registry.active_version,
        "models_in_memory": models_loaded,
        "privacy": "Zero external network calls; local CPU execution only",
    }


@router.get("/reports")
def get_evaluation_reports():
    """Retrieve all empirical benchmark evaluation reports."""
    reports_dir = Path("reports")

    def load_json(name: str):
        p = reports_dir / name
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading report {name}: {e}")
                return None
        return None

    return {
        "classification": load_json("classification_metrics.json"),
        "baseline": load_json("baseline_metrics.json"),
        "slaRisk": load_json("sla_risk_metrics.json"),
        "leadTime": load_json("lead_time_analysis.json"),
        "friction": load_json("friction_metrics.json"),
        "latency": load_json("latency_benchmarks.json"),
    }


@router.get("/models/status")
def model_status():
    """Detailed model runtime status and inference capabilities."""
    return {
        "active_version": registry.active_version,
        "is_ready": (
            registry.classifier is not None
            and registry.sla_forecaster is not None
            and registry.friction_scorer is not None
        ),
        "modules": {
            "M1_Classification": registry.classifier is not None,
            "M2_Routing": True,
            "M3_SLARisk": registry.sla_forecaster is not None,
            "M4_Friction": registry.friction_scorer is not None,
            "M5_Themes": registry.theme_engine is not None,
            "M6_Registry": True,
        },
        "sla_alert_threshold": (
            registry.sla_forecaster.alert_threshold if registry.sla_forecaster else 0.50
        ),
    }


@router.post("/import/csv")
async def import_csv_file(
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "manager"])),
):
    """Import external tickets from CSV file with column mapping."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    mapping_dict = None
    if column_mapping:
        try:
            mapping_dict = json.loads(column_mapping)
        except Exception:
            raise HTTPException(status_code=400, detail="column_mapping must be valid JSON.")

    content = await file.read()
    text_content = content.decode("utf-8", errors="replace")

    imported, errors, error_samples = import_tickets_from_csv(
        db=db,
        csv_file=text_content,
        custom_mapping=mapping_dict,
    )

    return {
        "filename": file.filename,
        "imported_count": imported,
        "error_count": errors,
        "error_samples": error_samples,
    }


@router.post("/dev/seed")
def seed_dev_data(
    count: int = 500,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    """Generate and inject fresh synthetic tickets for testing."""
    tickets, profile = generate_synthetic_dataset(
        count=count,
        output_path="data/dev_seed.csv",
        report_path="reports/dev_seed_profile.json",
    )
    with open("data/dev_seed.csv", "r", encoding="utf-8") as f:
        content = f.read()
        imported, errors, _ = import_tickets_from_csv(db, content)

    return {
        "status": "success",
        "generated": len(tickets),
        "imported": imported,
        "breach_rate": profile["key_metrics"]["breach_rate_pct"],
    }
