"""Regex-based detectors for structured PII (EMAIL, PHONE, URL)."""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches common email addresses.
# Local part: word chars, dots, plus, hyphens.
# Domain: labels separated by dots, TLD at least 2 chars.
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,}"
)

# Matches URLs starting with http://, https://, or www.
# Captures the rest until whitespace, then trailing punctuation is stripped.
URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s]+")

# Broad phone pattern – we post-validate with digit count.
# Covers:
#   +84 912 345 678  |  0912345678  |  0912 345 678  |  0912-345-678
#   (091) 234 5678   |  +1 (415) 555-2671  |  415.555.2671
PHONE_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9@/])"
    r"(?:"
    r"\d{8,15}"  # continuous digits
    r"|"
    r"(?:\+\d{1,3}[\s.\-]?)?"
    r"(?:\(?\d{2,5}\)?[\s.\-])?"
    r"\d{2,5}"
    r"(?:[\s.\-]\d{2,5}){0,4}"
    r")"
    r"(?![a-zA-Z0-9@])"
)

# Characters considered trailing punctuation that should be stripped from
# the end (and sometimes the start) of detected matches.
_TRAILING_PUNCT = set(".,;:!?)]}\"'")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _strip_trailing_punctuation(
    text: str, start: int, end: int
) -> tuple[str, int, int]:
    """Strip common trailing punctuation from a matched span.

    Returns (cleaned_text, new_start, new_end).
    """
    while end > start and text[end - 1] in _TRAILING_PUNCT:
        end -= 1
    entity_text = text[start:end]
    return entity_text, start, end


def _count_digits(s: str) -> int:
    """Count the number of digit characters in a string."""
    return sum(1 for ch in s if ch.isdigit())


def _is_inside_any_span(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    """Return True if [start, end) is fully contained inside any span."""
    for sp_start, sp_end in spans:
        if start >= sp_start and end <= sp_end:
            return True
    return False


def _overlaps_any_span(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    """Return True if [start, end) overlaps with any span."""
    for sp_start, sp_end in spans:
        if start < sp_end and end > sp_start:
            return True
    return False


def _entity_spans(entities: list[dict[str, Any]]) -> list[tuple[int, int]]:
    """Extract (start, end) spans from already-detected entities."""
    return [(entity["start"], entity["end"]) for entity in entities]


def _resolve_regex_overlaps(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove overlapping entities using priority EMAIL > URL > PHONE.

    When two entities overlap, the one with higher priority (lower index in
    the priority list) is kept.  Among equal priority, the earlier start wins;
    among equal start, the longer span wins.
    """
    priority = {"EMAIL": 0, "URL": 1, "PHONE": 2}

    # Sort by priority (higher priority first), then by start, then by
    # longest span first.
    sorted_entities = sorted(
        entities,
        key=lambda e: (priority.get(e["type"], 99), e["start"], -e["end"]),
    )

    kept: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []

    for entity in sorted_entities:
        s, e = entity["start"], entity["end"]
        if not _overlaps_any_span(s, e, occupied):
            kept.append(entity)
            occupied.append((s, e))

    # Return sorted by start index.
    kept.sort(key=lambda ent: ent["start"])
    return kept


# ---------------------------------------------------------------------------
# Individual detectors
# ---------------------------------------------------------------------------


def detect_email(text: str) -> list[dict[str, Any]]:
    """Detect email address spans in *text*.

    Returns a list of entity dicts with keys: type, text, start, end.
    """
    results: list[dict[str, Any]] = []
    for match in EMAIL_PATTERN.finditer(text):
        raw = match.group()
        start = match.start()
        end = match.end()

        # Strip trailing punctuation that is not part of the email.
        entity_text, start, end = _strip_trailing_punctuation(text, start, end)

        if not entity_text:
            continue

        results.append(
            {
                "type": "EMAIL",
                "text": entity_text,
                "start": start,
                "end": end,
            }
        )
    return results


def detect_url(text: str) -> list[dict[str, Any]]:
    """Detect URL spans in *text*.

    Returns a list of entity dicts with keys: type, text, start, end.
    """
    results: list[dict[str, Any]] = []
    for match in URL_PATTERN.finditer(text):
        start = match.start()
        end = match.end()

        # Strip trailing punctuation.
        entity_text, start, end = _strip_trailing_punctuation(text, start, end)

        # Also balance parentheses: if URL doesn't contain '(' but ends with ')',
        # strip the trailing ')'.
        while entity_text.endswith(")") and "(" not in entity_text:
            end -= 1
            entity_text = text[start:end]

        if not entity_text:
            continue

        results.append(
            {
                "type": "URL",
                "text": entity_text,
                "start": start,
                "end": end,
            }
        )
    return results


def detect_phone(
    text: str,
    excluded_entities: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Detect phone number spans in *text*.

    Validation rules applied after regex matching:
    - Total digit count must be between 9 and 15 (inclusive).
    - The candidate must not overlap with known EMAIL or URL entities.
    - Leading/trailing whitespace and punctuation are trimmed while
      preserving correct character indexes.

    Returns a list of entity dicts with keys: type, text, start, end.
    """
    excluded_spans = _entity_spans(excluded_entities or [])

    results: list[dict[str, Any]] = []
    for match in PHONE_PATTERN.finditer(text):
        start = match.start()
        end = match.end()

        # Skip if the candidate overlaps with an EMAIL or URL.
        if _overlaps_any_span(start, end, excluded_spans):
            continue

        # Trim leading/trailing whitespace.
        while start < end and text[start] in " \t":
            start += 1
        while end > start and text[end - 1] in " \t":
            end -= 1

        # Strip trailing punctuation.
        entity_text, start, end = _strip_trailing_punctuation(text, start, end)

        if not entity_text:
            continue

        # Validate digit count.
        digit_count = _count_digits(entity_text)
        if digit_count < 9 or digit_count > 15:
            continue

        # Guard against matching part of a larger alphanumeric token.
        # Check character immediately before start and after end.
        if start > 0 and (text[start - 1].isalnum() or text[start - 1] == "@"):
            continue
        if end < len(text) and (text[end].isalnum() or text[end] == "@"):
            continue

        results.append(
            {
                "type": "PHONE",
                "text": entity_text,
                "start": start,
                "end": end,
            }
        )
    return results


# ---------------------------------------------------------------------------
# Public aggregated detector
# ---------------------------------------------------------------------------


def detect_regex_entities(text: str) -> list[dict[str, Any]]:
    """Run all regex-based detectors and return a clean, non-overlapping,
    sorted list of entity dicts.

    Priority for overlap resolution: EMAIL > URL > PHONE.
    Output is sorted by ``start`` index ascending.
    """
    email_entities = detect_email(text)
    url_entities = detect_url(text)
    phone_entities = detect_phone(text, email_entities + url_entities)

    all_entities: list[dict[str, Any]] = []
    all_entities.extend(email_entities)
    all_entities.extend(url_entities)
    all_entities.extend(phone_entities)

    # Resolve any remaining overlaps.
    clean = _resolve_regex_overlaps(all_entities)
    return clean
