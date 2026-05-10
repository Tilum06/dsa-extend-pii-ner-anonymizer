"""Regex-based detectors for structured PII."""

from __future__ import annotations

from typing import Any


EMAIL_PATTERN = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
PHONE_PATTERN = r"(\+?\d{1,3}[\s.-]?)?(\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4}"
URL_PATTERN = r"https?://\S+|www\.\S+"


def detect_email(text: str) -> list[dict[str, Any]]:
    """Detect email spans in text."""
    raise NotImplementedError


def detect_phone(text: str) -> list[dict[str, Any]]:
    """Detect phone spans in text."""
    raise NotImplementedError


def detect_url(text: str) -> list[dict[str, Any]]:
    """Detect URL spans in text."""
    raise NotImplementedError


def detect_by_regex(text: str) -> list[dict[str, Any]]:
    """Run all regex-based detectors and return merged spans."""
    raise NotImplementedError
