"""Focused tests for merger correctness and overall merge performance."""

from __future__ import annotations

import time

from src.merger import merge_entities, resolve_overlaps


def test_merge_entities_combines_non_overlapping_groups_in_position_order():
    regex_entities = [
        {"type": "EMAIL", "text": "a@example.com", "start": 20, "end": 33},
        {"type": "PHONE", "text": "+84912345678", "start": 50, "end": 62},
    ]
    context_entities = [
        {"type": "NAME", "text": "John Smith", "start": 0, "end": 10},
    ]

    result = merge_entities(regex_entities, context_entities)

    assert result == [
        {"type": "NAME", "text": "John Smith", "start": 0, "end": 10},
        {"type": "EMAIL", "text": "a@example.com", "start": 20, "end": 33},
        {"type": "PHONE", "text": "+84912345678", "start": 50, "end": 62},
    ]


def test_resolve_overlaps_prefers_higher_priority_entity():
    entities = [
        {"type": "USERNAME", "text": "john", "start": 12, "end": 16},
        {"type": "EMAIL", "text": "john@example.com", "start": 12, "end": 28},
    ]

    assert resolve_overlaps(entities) == [
        {"type": "EMAIL", "text": "john@example.com", "start": 12, "end": 28},
    ]


def test_resolve_overlaps_prefers_longer_equal_priority_span():
    entities = [
        {"type": "NAME", "text": "John", "start": 0, "end": 4},
        {"type": "NAME", "text": "John Smith", "start": 0, "end": 10},
    ]

    assert resolve_overlaps(entities) == [
        {"type": "NAME", "text": "John Smith", "start": 0, "end": 10},
    ]


def test_merge_entities_removes_duplicate_entities():
    entity = {"type": "URL", "text": "https://example.com", "start": 5, "end": 24}

    assert merge_entities([entity], [entity]) == [entity]


def test_merge_entities_overall_performance_under_large_input():
    groups = []
    for group_index in range(4):
        group = []
        for i in range(500):
            start = i * 20 + group_index
            group.append(
                {
                    "type": "EMAIL" if group_index == 0 else "USERNAME",
                    "text": f"value-{group_index}-{i}",
                    "start": start,
                    "end": start + 10,
                }
            )
        groups.append(group)

    started_at = time.perf_counter()
    result = merge_entities(*groups)
    elapsed = time.perf_counter() - started_at

    assert result
    assert elapsed < 1.0
    assert all(result[i]["end"] <= result[i + 1]["start"] for i in range(len(result) - 1))
