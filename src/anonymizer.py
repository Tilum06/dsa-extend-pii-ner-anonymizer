"""Text anonymization helpers."""

from __future__ import annotations

from typing import Any


def anonymize_text(text: str, entities: list[dict[str, Any]]) -> str:
    """Replace entity spans with label placeholders."""
    raise NotImplementedError
