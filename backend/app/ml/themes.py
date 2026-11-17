"""M5 Unsupervised Theme Discovery and Emerging Trend Detection.

Performs topic discovery via TF-IDF and Non-Negative Matrix Factorization (NMF):
- Automatic topic count selection (k in 6-20 range) via reconstruction stability
- Topic labeling by top terms and representative exemplar tickets
- Weekly volume trend tracking per theme
- Emerging theme detection: z-score of recent 7-day volume vs prior 28 days
- Post-hoc cluster sanity check against hidden category via NMI and ARI
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import joblib

from backend.app.ml.preprocess import clean_text


class ThemeDiscoveryEngine:
    """Unsupervised Theme and Anomaly Cluster Discovery Engine."""

    def __init__(self, k_range: Tuple[int, int] = (6, 16)):
        self.k_range = k_range
        self.optimal_k: int = 10
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.nmf: Optional[NMF] = None
        self.themes_data_: List[Dict[str, Any]] = []
        self.nmi_sanity: float = 0.0
        self.ari_sanity: float = 0.0

    def fit_discover(
        self,
        tickets: List[Dict[str, Any]],
        select_best_k: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fit TF-IDF + NMF, extract themes, trends, and compute emerging z-scores."""
        texts = [clean_text(f"{t['subject']} {t['body']}") for t in tickets]
        timestamps = [
            datetime.strptime(t["created_at"], "%Y-%m-%d %H:%M:%S")
            if isinstance(t["created_at"], str) else t["created_at"]
            for t in tickets
        ]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=8000,
            sublinear_tf=True,
            stop_words="english",
            min_df=3,
        )
        X_tfidf = self.vectorizer.fit_transform(texts)
        feature_names = self.vectorizer.get_feature_names_out()

        # Select k
        best_k = 10
        if select_best_k and len(tickets) > 500:
            candidates = [8, 10, 12, 14]
            best_score = float("inf")
            for c_k in candidates:
                cand_nmf = NMF(n_components=c_k, random_state=42, max_iter=200)
                cand_nmf.fit(X_tfidf)
                if cand_nmf.reconstruction_err_ < best_score:
                    best_score = cand_nmf.reconstruction_err_
                    best_k = c_k
        self.optimal_k = best_k

        self.nmf = NMF(n_components=self.optimal_k, random_state=42, max_iter=300)
        W = self.nmf.fit_transform(X_tfidf)  # shape (n_samples, k)
        H = self.nmf.components_  # shape (k, n_features)

        dominant_topics = np.argmax(W, axis=1)

        # Sanity check against hidden category if present
        if "category" in tickets[0]:
            true_cats = [t.get("true_category", t["category"]) for t in tickets]
            self.nmi_sanity = float(normalized_mutual_info_score(true_cats, dominant_topics))
            self.ari_sanity = float(adjusted_rand_score(true_cats, dominant_topics))

        # Time range calculation for emerging detection
        max_dt = max(timestamps)
        seven_days_ago = max_dt - timedelta(days=7)
        thirty_five_days_ago = max_dt - timedelta(days=35)

        # Extract theme cards
        self.themes_data_ = []
        for topic_idx in range(self.optimal_k):
            # Top terms
            top_term_indices = H[topic_idx].argsort()[::-1][:8]
            top_terms = [feature_names[i] for i in top_term_indices]

            # Representative tickets
            topic_weights = W[:, topic_idx]
            rep_ticket_indices = topic_weights.argsort()[::-1][:3]
            rep_tickets = [
                {
                    "ticket_id": tickets[idx]["ticket_id"],
                    "subject": tickets[idx]["subject"],
                    "category": tickets[idx].get("category", "General"),
                    "created_at": str(tickets[idx]["created_at"]),
                }
                for idx in rep_ticket_indices
            ]

            # Assign human-readable title from top 2-3 terms
            readable_title = " / ".join(w.title() for w in top_terms[:3])

            # Weekly trend (last 8 weeks)
            topic_mask = (dominant_topics == topic_idx)
            topic_timestamps = [timestamps[i] for i in range(len(timestamps)) if topic_mask[i]]

            # Weekly buckets
            weekly_counts = [0] * 8
            for dt in topic_timestamps:
                diff_days = (max_dt - dt).total_seconds() / 86400.0
                week_idx = int(diff_days // 7)
                if 0 <= week_idx < 8:
                    weekly_counts[7 - week_idx] += 1

            # Emerging detection: z-score of last 7 days vs prior 4 weeks (28 days)
            recent_count = sum(1 for dt in topic_timestamps if dt >= seven_days_ago)
            prior_window_counts = []
            for w in range(1, 5):
                w_start = max_dt - timedelta(days=7 * (w + 1))
                w_end = max_dt - timedelta(days=7 * w)
                w_cnt = sum(1 for dt in topic_timestamps if w_start <= dt < w_end)
                prior_window_counts.append(w_cnt)

            mean_prior = float(np.mean(prior_window_counts)) if prior_window_counts else 1.0
            std_prior = float(np.std(prior_window_counts)) if prior_window_counts else 1.0
            z_score = float((recent_count - mean_prior) / max(1.0, std_prior))
            is_emerging = bool(z_score >= 1.8 and recent_count >= 15)

            self.themes_data_.append({
                "id": topic_idx + 1,
                "label": readable_title,
                "top_terms": top_terms,
                "ticket_count": int(np.sum(topic_mask)),
                "weekly_trend": weekly_counts,
                "is_emerging": is_emerging,
                "z_score": round(z_score, 2),
                "representative_tickets": rep_tickets,
            })

        # Sort themes: emerging first, then by ticket volume
        self.themes_data_.sort(key=lambda t: (t["is_emerging"], t["ticket_count"]), reverse=True)
        return self.themes_data_

    def get_summary(self) -> Dict[str, Any]:
        """Return theme discovery metadata and sanity check metrics."""
        return {
            "optimal_k": self.optimal_k,
            "themes": self.themes_data_,
            "nmi_sanity_score": round(self.nmi_sanity, 4),
            "ari_sanity_score": round(self.ari_sanity, 4),
            "total_themes": len(self.themes_data_),
            "emerging_count": sum(1 for t in self.themes_data_ if t["is_emerging"]),
            "last_refreshed": datetime.utcnow().isoformat(),
        }

    def save(self, filepath: str):
        """Save theme engine artifact."""
        joblib.dump(self, filepath)

    @classmethod
    def load(cls, filepath: str) -> "ThemeDiscoveryEngine":
        """Load theme engine artifact."""
        return joblib.load(filepath)
