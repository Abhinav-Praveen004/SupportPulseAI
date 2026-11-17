"""M4 Explainable Friction Score (0-100) Engine.

Components:
1. Domain-adapted VADER sentiment with IT support lexicon
2. Linguistic frustration cues (caps ratio, punctuation repeats, urgency phrases)
3. Operational behavioral signals (contact count, reopens, SLA elapsed ratio)
4. Fit weights via Logistic Regression against synthetic escalation flag
"""

from typing import Any, Dict, Optional, Tuple
import numpy as np
from sklearn.linear_model import LogisticRegression
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import joblib

from backend.app.ml.preprocess import extract_text_cues

IT_SUPPORT_LEXICON = {
    "unacceptable": -3.5,
    "blocking": -3.2,
    "broken": -2.8,
    "down": -2.5,
    "escalate": -3.0,
    "disaster": -3.8,
    "ridiculous": -3.2,
    "ignored": -2.8,
    "terrible": -3.4,
    "useless": -3.0,
    "fixed": 2.5,
    "resolved": 2.5,
    "thank": 2.0,
    "thanks": 2.0,
    "great": 2.2,
    "excellent": 2.8,
}


class FrictionScorer:
    """Multi-component explainable friction score model."""

    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.vader.lexicon.update(IT_SUPPORT_LEXICON)
        # Default component weights (sum to 1.0)
        self.weights = np.array([0.25, 0.40, 0.35], dtype=np.float32)
        self.fitted_logistic: Optional[LogisticRegression] = None

    def compute_subscores(
        self,
        text: str,
        contact_count: int = 1,
        reopen_count: int = 0,
        elapsed_ratio: float = 0.0,
    ) -> Tuple[float, float, float]:
        """Compute the 3 normalized subscores (0-100 each)."""
        # 1. Sentiment Subscore (0 = positive, 100 = very negative)
        scores = self.vader.polarity_scores(text)
        compound = scores["compound"]  # -1.0 to +1.0
        sentiment_score = max(0.0, min(100.0, (1.0 - compound) * 50.0))

        # 2. Text Cues Subscore (0 to 100)
        cues = extract_text_cues(text)
        caps_part = min(40.0, cues["all_caps_ratio"] * 100.0)
        excl_part = min(30.0, cues["exclamation_count"] * 10.0)
        urgency_part = min(30.0, cues["urgency_phrase_count"] * 15.0)
        cues_score = min(100.0, caps_part + excl_part + urgency_part)

        # 3. Behavioral Subscore (0 to 100)
        contacts_part = min(40.0, max(0, contact_count - 1) * 12.0)
        reopens_part = min(35.0, reopen_count * 20.0)
        elapsed_part = min(25.0, elapsed_ratio * 25.0)
        behavior_score = min(100.0, contacts_part + reopens_part + elapsed_part)

        return float(sentiment_score), float(cues_score), float(behavior_score)

    def fit_weights(self, X_components: np.ndarray, y_escalated: np.ndarray):
        """Fit component weights with Logistic Regression on synthetic escalation labels."""
        self.fitted_logistic = LogisticRegression(C=1.0, max_iter=500, random_state=42)
        self.fitted_logistic.fit(X_components, y_escalated)
        raw_coefs = np.maximum(0.01, self.fitted_logistic.coef_[0])
        self.weights = raw_coefs / np.sum(raw_coefs)
        return self

    def calculate(
        self,
        text: str,
        contact_count: int = 1,
        reopen_count: int = 0,
        elapsed_ratio: float = 0.0,
    ) -> Dict[str, Any]:
        """Compute full friction score (0-100), band, and component breakdown."""
        s_sent, s_cues, s_behav = self.compute_subscores(text, contact_count, reopen_count, elapsed_ratio)

        final_score = (
            self.weights[0] * s_sent
            + self.weights[1] * s_cues
            + self.weights[2] * s_behav
        )
        final_score = round(max(0.0, min(100.0, float(final_score))), 1)

        # Determine band
        if final_score >= 76.0:
            band = "Critical"
        elif final_score >= 51.0:
            band = "Frustrated"
        elif final_score >= 26.0:
            band = "Uneasy"
        else:
            band = "Calm"

        return {
            "score": final_score,
            "band": band,
            "breakdown": {
                "sentiment_subscore": round(s_sent, 1),
                "text_cues_subscore": round(s_cues, 1),
                "behavioral_subscore": round(s_behav, 1),
                "weights": {
                    "sentiment": round(float(self.weights[0]), 3),
                    "text_cues": round(float(self.weights[1]), 3),
                    "behavioral": round(float(self.weights[2]), 3),
                },
            },
        }

    def save(self, filepath: str):
        """Save friction model artifact."""
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "FrictionScorer":
        """Load friction model artifact."""
        return joblib.load(filepath)
