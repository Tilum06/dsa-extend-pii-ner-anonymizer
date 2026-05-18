"""Focused tests for scored context detectors."""

from __future__ import annotations

from src.context_detector import (
    detect_by_context,
    detect_location,
    detect_name,
    detect_organization,
)


def test_detect_by_context_scores_organization_and_location_candidates():
    text = "I work at OpenAI Inc in San Francisco."

    result = detect_by_context(text)

    assert {
        "type": "ORGANIZATION",
        "text": "OpenAI Inc",
        "start": text.index("OpenAI Inc"),
        "end": text.index("OpenAI Inc") + len("OpenAI Inc"),
    } in result
    assert {
        "type": "LOCATION",
        "text": "San Francisco",
        "start": text.index("San Francisco"),
        "end": text.index("San Francisco") + len("San Francisco"),
    } in result


def test_detect_by_context_prefers_address_over_overlapping_location():
    text = "I live at 123 Main Street."

    result = detect_by_context(text)

    assert result == [
        {
            "type": "ADDRESS",
            "text": "123 Main Street",
            "start": text.index("123 Main Street"),
            "end": text.index("123 Main Street") + len("123 Main Street"),
        }
    ]


def test_detect_by_context_prefers_organization_over_same_span_location():
    text = "I work at OpenAI."

    result = detect_by_context(text)

    assert result == [
        {
            "type": "ORGANIZATION",
            "text": "OpenAI",
            "start": text.index("OpenAI"),
            "end": text.index("OpenAI") + len("OpenAI"),
        }
    ]


def test_scored_entity_pipeline_assigns_one_final_tag_per_candidate():
    text = "I work at OpenAI."

    assert detect_name(text) == []
    assert detect_location(text) == []
    assert detect_organization(text) == [
        {
            "type": "ORGANIZATION",
            "text": "OpenAI",
            "start": text.index("OpenAI"),
            "end": text.index("OpenAI") + len("OpenAI"),
        }
    ]
