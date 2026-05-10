"""Context-based detectors for NAME, USERNAME, and ADDRESS."""

from __future__ import annotations

from typing import Any


NAME_TRIGGERS = ["my name is", "full name", "name:"]
USERNAME_TRIGGERS = ["username", "user name", "account", "handle"]
ADDRESS_TRIGGERS = ["street", "road", "avenue", "district", "city", "st.", "rd.", "ave."]


def detect_name(text: str) -> list[dict[str, Any]]:
    """Detect NAME spans using context rules."""
    raise NotImplementedError


def detect_username(text: str) -> list[dict[str, Any]]:
    """Detect USERNAME spans using context rules."""
    raise NotImplementedError


def detect_address(text: str) -> list[dict[str, Any]]:
    """Detect ADDRESS spans using context rules."""
    raise NotImplementedError


def detect_by_context(text: str) -> list[dict[str, Any]]:
    """Run all context-based detectors and return merged spans."""
    raise NotImplementedError
