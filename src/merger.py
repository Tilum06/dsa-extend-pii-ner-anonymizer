"""Utilities for combining and de-duplicating detected entities."""

from __future__ import annotations

from typing import Any

from .config import ENTITY_PRIORITY


def _priority_rank(entity_type: str) -> int:
    """Return the priority rank for an entity type (lower = higher priority).

    Types not in ENTITY_PRIORITY get the lowest priority (len of list).
    """
    try:
        return ENTITY_PRIORITY.index(entity_type)
    except ValueError:
        return len(ENTITY_PRIORITY)


def sort_entities(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort entities by position and project priority.

    Primary sort: start index ascending.
    Secondary sort: longer span first (end descending).
    Tertiary sort: higher priority first (lower rank value).
    """
    return sorted(
        entities,
        key=lambda e: (e["start"], -e["end"], _priority_rank(e["type"])),
    )


def resolve_overlaps(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove overlapping entities according to project priority.

    Strategy (greedy, priority-first):
    1. Sort all entities by priority rank (highest priority first),
       then by start index, then by longest span.
    2. Walk through the sorted list; keep an entity only if its span
       does not overlap with any already-kept entity.
    3. Return the kept entities sorted by start index.
    """
    # Sort by priority (higher = lower rank), then start, then longest span
    priority_sorted = sorted(
        entities,
        key=lambda e: (_priority_rank(e["type"]), e["start"], -e["end"]),
    )

    kept: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []  # (start, end) of kept entities

    for entity in priority_sorted:
        s, e = entity["start"], entity["end"]
        # Check overlap with any occupied span
        overlaps = any(s < oe and e > os for os, oe in occupied)
        if not overlaps:
            kept.append(entity)
            occupied.append((s, e))

    # Return sorted by start index
    kept.sort(key=lambda ent: ent["start"])
    return kept


def merge_entities(*entity_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge multiple detector outputs into one entity list.

    1. Flatten all entity groups into a single list.
    2. Resolve overlaps using project priority.
    3. Return a clean, non-overlapping, position-sorted list.
    """
    all_entities: list[dict[str, Any]] = []
    for group in entity_groups:
        all_entities.extend(group)

    if not all_entities:
        return []

    return resolve_overlaps(all_entities)
