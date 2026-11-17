"""M1 Text Classification Module for Ticket Category and Priority.

Features:
- Combined Word (1-2 grams) and Character (3-5 grams) TF-IDF representations
- Calibrated probability estimates for category and priority
- Automated human triage fallback for low confidence predictions
- Top contributing n-gram explanation extraction
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC
import joblib

from backend.app.ml.preprocess import clean_text


def build_text_pipeline(max_word_features: int = 12000, max_char_features: int = 15000) -> FeatureUnion:
    """Construct multi-granular TF-IDF feature union (word + subword character n-grams)."""
    word_vec = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=max_word_features,
        sublinear_tf=True,
        stop_words="english",
        strip_accents="unicode",
    )
    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=max_char_features,
        sublinear_tf=True,
        strip_accents="unicode",
    )
    return FeatureUnion([("word", word_vec), ("char", char_vec)])


class TicketClassifier:
    """Unified Classifier for Ticket Category and Priority."""

    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self.category_pipeline: Optional[Pipeline] = None
        self.priority_pipeline: Optional[Pipeline] = None
        self.category_classes_: List[str] = []
        self.priority_classes_: List[str] = []

    def fit(self, texts: List[str], categories: List[str], priorities: List[str]):
        """Fit category and priority classification models."""
        cleaned_texts = [clean_text(t) for t in texts]

        # 1. Category Classifier (Calibrated Linear Model)
        cat_features = build_text_pipeline()
        cat_clf = CalibratedClassifierCV(
            estimator=LinearSVC(C=1.0, random_state=42, dual="auto"),
            cv=3,
            method="sigmoid",
        )
        self.category_pipeline = Pipeline([
            ("features", cat_features),
            ("clf", cat_clf),
        ])
        self.category_pipeline.fit(cleaned_texts, categories)
        self.category_classes_ = list(self.category_pipeline.classes_)

        # 2. Priority Classifier
        prio_features = build_text_pipeline(max_word_features=6000, max_char_features=8000)
        prio_clf = CalibratedClassifierCV(
            estimator=LinearSVC(C=0.8, random_state=42, dual="auto"),
            cv=3,
            method="sigmoid",
        )
        self.priority_pipeline = Pipeline([
            ("features", prio_features),
            ("clf", prio_clf),
        ])
        self.priority_pipeline.fit(cleaned_texts, priorities)
        self.priority_classes_ = list(self.priority_pipeline.classes_)

        return self

    def predict_category(self, text: str) -> Dict[str, Any]:
        """Predict category with calibrated probabilities and confidence."""
        if not self.category_pipeline:
            raise RuntimeError("Category model is not trained or loaded.")

        cleaned = clean_text(text)
        probs = self.category_pipeline.predict_proba([cleaned])[0]
        cat_probs = {cls: float(prob) for cls, prob in zip(self.category_classes_, probs)}

        best_cat = max(cat_probs.keys(), key=lambda k: cat_probs[k])
        confidence = cat_probs[best_cat]
        needs_triage = confidence < self.confidence_threshold

        top_ngrams = self.explain_category(cleaned, best_cat)

        return {
            "category": best_cat,
            "confidence": float(confidence),
            "probabilities": cat_probs,
            "needs_human_triage": bool(needs_triage),
            "top_contributing_ngrams": top_ngrams,
        }

    def predict_priority(self, text: str) -> Dict[str, Any]:
        """Predict priority with calibrated probabilities."""
        if not self.priority_pipeline:
            raise RuntimeError("Priority model is not trained or loaded.")

        cleaned = clean_text(text)
        probs = self.priority_pipeline.predict_proba([cleaned])[0]
        prio_probs = {cls: float(prob) for cls, prob in zip(self.priority_classes_, probs)}

        best_prio = max(prio_probs.keys(), key=lambda k: prio_probs[k])
        confidence = prio_probs[best_prio]

        return {
            "priority": best_prio,
            "confidence": float(confidence),
            "probabilities": prio_probs,
        }

    def explain_category(self, text: str, target_class: str, top_k: int = 6) -> List[Dict[str, Any]]:
        """Extract highest-impact n-grams for predicted class via model weights."""
        try:
            if not self.category_pipeline:
                return []
            features_transformer = self.category_pipeline.named_steps["features"]
            clf = self.category_pipeline.named_steps["clf"]

            feature_names = features_transformer.get_feature_names_out()
            x_vec = features_transformer.transform([text]).tocsr()
            non_zero_indices = x_vec.indices

            if len(non_zero_indices) == 0:
                return []

            class_idx = list(self.category_classes_).index(target_class)

            # Average linear weights across calibrated folds
            weights_sum = np.zeros(len(feature_names))
            for cal_clf in clf.calibrated_classifiers_:
                weights_sum += cal_clf.estimator.coef_[class_idx]
            avg_weights = weights_sum / len(clf.calibrated_classifiers_)

            contributions = []
            for idx in non_zero_indices:
                val = x_vec[0, idx]
                weight = avg_weights[idx]
                score = float(val * weight)
                if score > 0:
                    raw_name = feature_names[idx].replace("word__", "").replace("char__", "")
                    contributions.append({"ngram": raw_name, "score": round(score, 4)})

            contributions.sort(key=lambda item: item["score"], reverse=True)
            return contributions[:top_k]
        except Exception:
            return []

    def save(self, filepath: str):
        """Save classifier artifact."""
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "TicketClassifier":
        """Load classifier artifact."""
        return joblib.load(filepath)
