"""Text preprocessing and feature normalization utilities."""

import re
from typing import List

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PUNCT_REPEATS = re.compile(r"([!?.]){2,}")
MULTIPLE_SPACES = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalize whitespace and strip URLs/email patterns for robust n-gram extraction."""
    if not text or not isinstance(text, str):
        return ""
    text = URL_PATTERN.sub(" [URL] ", text)
    text = EMAIL_PATTERN.sub(" [EMAIL] ", text)
    text = MULTIPLE_SPACES.sub(" ", text)
    return text.strip()


def extract_text_cues(text: str) -> dict:
    """Extract linguistic frustration cues from raw ticket text."""
    if not text:
        return {
            "all_caps_ratio": 0.0,
            "exclamation_count": 0,
            "question_count": 0,
            "urgency_phrase_count": 0,
            "char_length": 0,
        }

    letters = [c for c in text if c.isalpha()]
    all_caps_ratio = sum(1 for c in letters if c.isupper()) / max(1, len(letters))
    exclamation_count = text.count("!")
    question_count = text.count("?")

    lower_text = text.lower()
    urgency_phrases = [
        "again",
        "still not working",
        "third time",
        "unacceptable",
        "escalate",
        "asap",
        "urgent",
        "immediately",
        "blocking",
        "broken",
        "down",
        "losing revenue",
    ]
    urgency_phrase_count = sum(lower_text.count(phrase) for phrase in urgency_phrases)

    return {
        "all_caps_ratio": min(1.0, float(all_caps_ratio)),
        "exclamation_count": int(exclamation_count),
        "question_count": int(question_count),
        "urgency_phrase_count": int(urgency_phrase_count),
        "char_length": len(text),
    }
