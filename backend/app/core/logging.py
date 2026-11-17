"""Privacy-conscious structured logging with PII redaction."""

import logging
import re
import sys
from typing import Any

# Regex patterns for PII redaction
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
IPV4_REGEX = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")


def redact_pii(text: str) -> str:
    """Redact email addresses, phone numbers, and IPv4 addresses from text."""
    if not isinstance(text, str):
        return text
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    text = IPV4_REGEX.sub("[REDACTED_IP]", text)
    return text


class PIIRedactingFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive PII from all log records."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_pii(original)


def setup_logger(name: str = "supportpulse") -> logging.Logger:
    """Set up structured logger with PII redaction filter."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = PIIRedactingFormatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = setup_logger()
