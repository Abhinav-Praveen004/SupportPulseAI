"""Legacy Rule-Based Baseline Classifier (Regex and Keyword matching).

Emulates the legacy tier-1 keyword/regex routing system commonly used in IT desks.
Provides the reference baseline that SupportPulse AI is evaluated against.
"""

import re
from typing import Dict, List, Tuple
import numpy as np

# Keyword rules for categories
CATEGORY_KEYWORDS = {
    "Password/Access": [
        r"\bpassword\b", r"\breset\b", r"\bunlock\b", r"\bmfa\b", r"\bokta\b",
        r"\bcredentials\b", r"\bsso\b", r"\blockout\b", r"\btoken\b", r"\blogin\b"
    ],
    "Network/VPN": [
        r"\bvpn\b", r"\bwi-?fi\b", r"\btunnel\b", r"\bglobalprotect\b", r"\banyconnect\b",
        r"\bnetwork\b", r"\bgateway\b", r"\bsubnet\b", r"\bdisconnect\b", r"\brouter\b"
    ],
    "Email": [
        r"\boutlook\b", r"\bmailbox\b", r"\bemail\b", r"\bexchange\b", r"\bcalendar\b",
        r"\binvite\b", r"\bquota\b", r"\bspam\b", r"\battachments?\b"
    ],
    "Hardware": [
        r"\blaptop\b", r"\bscreen\b", r"\bkeyboard\b", r"\bbattery\b", r"\bdock\b",
        r"\bmonitor\b", r"\bmouse\b", r"\bcharger\b", r"\bheadset\b", r"\bmacbook\b",
        r"\btrackpad\b", r"\bflicker\b"
    ],
    "Software Install": [
        r"\binstall\b", r"\blicense\b", r"\bsoftware\b", r"\bfigma\b", r"\bdocker\b",
        r"\bintellij\b", r"\bupgrade\b", r"\bactivation\b", r"\bprovision\b"
    ],
    "Application Error": [
        r"\b500\b", r"\b502\b", r"\b504\b", r"\berror\b", r"\bexception\b", r"\bcrash\b",
        r"\bfreeze\b", r"\btimeout\b", r"\bbatch\b", r"\bnullpointer\b"
    ],
    "Security Incident": [
        r"\bphishing\b", r"\bmalware\b", r"\bstolen\b", r"\bunauthorized\b",
        r"\bransomware\b", r"\bcompromise\b", r"\bhack\b", r"\bvirus\b", r"\bduo\b"
    ],
    "Printer": [
        r"\bprinter\b", r"\bpaper\b", r"\btoner\b", r"\bjam\b", r"\bprint\b",
        r"\bspooler\b", r"\bcartridge\b", r"\bphotocopy\b"
    ],
    "Cloud/Infrastructure": [
        r"\baws\b", r"\bkubernetes\b", r"\bk8s\b", r"\bec2\b", r"\bs3\b",
        r"\bterraform\b", r"\bcluster\b", r"\bpod\b", r"\bcloud\b", r"\bcertificate\b"
    ],
    "Service Request": [
        r"\brequest\b", r"\brequisition\b", r"\bchair\b", r"\bguest\b", r"\bmonitor\b",
        r"\baccessories\b", r"\bstanding desk\b", r"\bvisitor\b", r"\border\b"
    ],
}

PRIORITY_KEYWORDS = {
    "P1": [r"\bcritical\b", r"\burgent\b", r"\bp1\b", r"\bemergency\b", r"\bproduction down\b", r"\boutage\b", r"\blosing revenue\b"],
    "P2": [r"\bhigh\b", r"\basap\b", r"\bblocking\b", r"\bp2\b", r"\bsevere\b", r"\bimportant\b"],
    "P4": [r"\blow\b", r"\bminor\b", r"\bp4\b", r"\bwhen possible\b", r"\bno rush\b", r"\bnice to have\b"],
}


class RegexBaselineClassifier:
    """Keyword and Regex baseline classifier."""

    def __init__(self):
        self.category_patterns = {
            cat: [re.compile(p, re.IGNORECASE) for p in patterns]
            for cat, patterns in CATEGORY_KEYWORDS.items()
        }
        self.priority_patterns = {
            prio: [re.compile(p, re.IGNORECASE) for p in patterns]
            for prio, patterns in PRIORITY_KEYWORDS.items()
        }
        self.categories = list(CATEGORY_KEYWORDS.keys())
        self.priorities = ["P1", "P2", "P3", "P4"]

    def predict_category(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """Classify category using keyword hit counts."""
        scores = {cat: 0 for cat in self.categories}
        for cat, patterns in self.category_patterns.items():
            for pat in patterns:
                matches = len(pat.findall(text))
                scores[cat] += matches

        total_hits = sum(scores.values())
        if total_hits == 0:
            # Fallback to Service Request with uniform low probabilities
            probs = {cat: 1.0 / len(self.categories) for cat in self.categories}
            return "Service Request", 0.10, probs

        # Normalized smoothed probabilities
        probs = {cat: (scores[cat] + 0.1) / (total_hits + 0.1 * len(self.categories)) for cat in self.categories}
        best_cat = max(scores.keys(), key=lambda c: scores[c])
        confidence = probs[best_cat]
        return best_cat, confidence, probs

    def predict_priority(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """Classify priority using keyword match hierarchy."""
        for prio in ["P1", "P2", "P4"]:
            for pat in self.priority_patterns[prio]:
                if pat.search(text):
                    probs = {p: 0.1 for p in self.priorities}
                    probs[prio] = 0.70
                    return prio, 0.70, probs

        # Default is P3 (Medium)
        probs = {"P1": 0.05, "P2": 0.15, "P3": 0.65, "P4": 0.15}
        return "P3", 0.65, probs

    def predict(self, texts: List[str]) -> Tuple[List[str], List[str]]:
        """Batch prediction returning (categories, priorities)."""
        cat_preds = []
        prio_preds = []
        for text in texts:
            cat, _, _ = self.predict_category(text)
            prio, _, _ = self.predict_priority(text)
            cat_preds.append(cat)
            prio_preds.append(prio)
        return cat_preds, prio_preds
