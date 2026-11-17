"""Pydantic schemas for Model Management and Registry."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ModelVersionOut(BaseModel):
    id: int
    version: str
    model_type: str
    status: str
    macro_f1: float
    roc_auc: Optional[float] = None
    accuracy: float
    metrics: Dict[str, Any]
    created_at: datetime


class RetrainRequest(BaseModel):
    min_feedback_samples: Optional[int] = 10
    evaluate_only: Optional[bool] = False


class RetrainResponse(BaseModel):
    candidate_version: str
    previous_version: str
    promoted: bool
    status: str
    candidate_macro_f1: float
    previous_macro_f1: float
    message: str
    metrics: Dict[str, Any]


class RollbackResponse(BaseModel):
    active_version: str
    rolled_back_from: str
    message: str
