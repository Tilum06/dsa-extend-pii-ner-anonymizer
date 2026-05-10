"""Utilities for combining and de-duplicating detected entities."""

from __future__ import annotations

from typing import Any

from .config import ENTITY_PRIORITY


def sort_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort entities by position and project priority."""
    raise NotImplementedError


def resolve_overlaps(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove overlapping entities according to project priority."""
    raise NotImplementedError


def merge_entities(*entity_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge multiple detector outputs into one entity list."""
    raise NotImplementedError
