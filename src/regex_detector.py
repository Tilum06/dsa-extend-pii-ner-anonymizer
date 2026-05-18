"""Regex-based detectors for structured PII (EMAIL, PHONE, URL, DATE)."""

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
URL_PATTERN = re.compile(
    r"(?:https?://|www\.)[^\s]+"
)

# Broad phone pattern – we post-validate with digit count.
# Covers:
#   +84 912 345 678  |  0912345678  |  0912 345 678  |  0912-345-678
#   (091) 234 5678   |  +1 (415) 555-2671  |  415.555.2671
PHONE_PATTERN = re.compile(
    r"(?<![a-zA-Z0-9@/])"
    r"(?:"
        r"\d{8,15}"                                  # continuous digits
        r"|"
        r"(?:\+\d{1,3}[\s.\-]?)?"
        r"(?:\(?\d{2,5}\)?[\s.\-])?"
        r"\d{2,5}"
        r"(?:[\s.\-]\d{2,5}){0,4}"
    r")"
    r"(?![a-zA-Z0-9@])"
)

# ---------------------------------------------------------------------------
# DATE patterns
# ---------------------------------------------------------------------------
# Full and abbreviated English month names for reuse in patterns.
_MONTHS_FULL = (
    r"January|February|March|April|May|June"
    r"|July|August|September|October|November|December"
)
_MONTHS_ABBR = (
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
)
_MONTHS_ALL = rf"(?:{_MONTHS_FULL}|{_MONTHS_ABBR})"

DATE_PATTERNS: list[re.Pattern[str]] = [
    # --- Vietnamese formats ---
    # ngày DD tháng MM năm YYYY  /  DD tháng MM năm YYYY
    re.compile(
        r"(?:ngày\s+)?\d{1,2}\s+tháng\s+\d{1,2}\s+năm\s+\d{4}",
        re.IGNORECASE,
    ),
    # ngày D/M/YYYY  (Vietnamese prefix)
    re.compile(
        r"ngày\s+\d{1,2}/\d{1,2}/\d{2,4}",
        re.IGNORECASE,
    ),
    # tháng MM năm YYYY  (Vietnamese month/year)
    re.compile(
        r"tháng\s+\d{1,2}\s+năm\s+\d{4}",
        re.IGNORECASE,
    ),
    # năm YYYY  (Vietnamese contextual year)
    re.compile(
        r"năm\s+\d{4}",
        re.IGNORECASE,
    ),

    # --- English month-name formats ---
    # January 2, 2024  /  Jan 2, 2024
    re.compile(
        rf"{_MONTHS_ALL}\.?\s+\d{{1,2}},?\s+\d{{4}}"
    ),
    # 2 January 2024  /  2 Jan 2024
    re.compile(
        rf"\d{{1,2}}\s+{_MONTHS_ALL}\.?\s+\d{{4}}"
    ),
    # January 2024  /  Jan 2024  (month-year only)
    re.compile(
        rf"{_MONTHS_ALL}\.?\s+\d{{4}}"
    ),
    # year YYYY  (English contextual year)
    re.compile(
        r"year\s+\d{4}",
        re.IGNORECASE,
    ),

    # --- ISO / numeric formats ---
    # YYYY-MM-DD  /  YYYY/MM/DD
    re.compile(
        r"(?<!\d)\d{4}[/\-]\d{1,2}[/\-]\d{1,2}(?!\d)"
    ),
    # DD/MM/YYYY  DD-MM-YYYY  DD.MM.YYYY  (also 2-digit year)
    re.compile(
        r"(?<!\d)\d{1,2}[/\-.]"
        r"\d{1,2}[/\-.]"
        r"\d{2,4}(?!\d)"
    ),
    # MM/YYYY  (month/year numeric)
    re.compile(
        r"(?<!\d)\d{1,2}/\d{4}(?!\d)"
    ),
]

# Characters considered trailing punctuation that should be stripped from
# the end (and sometimes the start) of detected matches.
_TRAILING_PUNCT = set(".,;:!?)]}\"'")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _strip_trailing_punctuation(text: str, start: int, end: int) -> tuple[str, int, int]:
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


def _resolve_regex_overlaps(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove overlapping entities using priority EMAIL > URL > PHONE > DATE.

    When two entities overlap, the one with higher priority (lower index in
    the priority list) is kept.  Among equal priority, the earlier start wins;
    among equal start, the longer span wins.
    """
    priority = {"EMAIL": 0, "URL": 1, "PHONE": 2, "DATE": 3}

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

        results.append({
            "type": "EMAIL",
            "text": entity_text,
            "start": start,
            "end": end,
        })
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

        results.append({
            "type": "URL",
            "text": entity_text,
            "start": start,
            "end": end,
        })
    return results


def detect_phone(text: str) -> list[dict[str, Any]]:
    """Detect phone number spans in *text*.

    Validation rules applied after regex matching:
    - Total digit count must be between 9 and 15 (inclusive).
    - The candidate must not be inside an EMAIL or URL span.
    - Leading/trailing whitespace and punctuation are trimmed while
      preserving correct character indexes.

    Returns a list of entity dicts with keys: type, text, start, end.
    """
    # First, find all EMAIL and URL spans so we can exclude phone candidates
    # that fall inside them.
    email_spans = [(m.start(), m.end()) for m in EMAIL_PATTERN.finditer(text)]
    url_spans = [(m.start(), m.end()) for m in URL_PATTERN.finditer(text)]
    excluded_spans = email_spans + url_spans

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
        if start > 0 and (text[start - 1].isalnum() or text[start - 1] == '@'):
            continue    
        if end < len(text) and (text[end].isalnum() or text[end] == '@'):
            continue

        results.append({
            "type": "PHONE",
            "text": entity_text,
            "start": start,
            "end": end,
        })
    return results


def detect_date(text: str) -> list[dict[str, Any]]:
    """Detect date/time spans in *text*.

    Covers numeric dates, English month-name dates, Vietnamese date formats,
    month/year, and contextual year-only ("năm 2024", "year 2024").

    Candidates that overlap with an EMAIL, URL, or PHONE span are discarded
    to avoid false positives.

    Returns a list of entity dicts with keys: type, text, start, end.
    """
    # Build exclusion spans from higher-priority entity types.
    # Use raw regex for EMAIL/URL, but validated results for PHONE so that
    # short false-positive phone candidates (e.g. "01") don't block dates.
    email_spans = [(m.start(), m.end()) for m in EMAIL_PATTERN.finditer(text)]
    url_spans = [(m.start(), m.end()) for m in URL_PATTERN.finditer(text)]
    phone_results = detect_phone(text)
    phone_spans = [(p["start"], p["end"]) for p in phone_results]
    excluded_spans = email_spans + url_spans + phone_spans

    raw_matches: list[tuple[int, int, str]] = []  # (start, end, text)

    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            start = match.start()
            end = match.end()

            # Strip trailing punctuation.
            entity_text, start, end = _strip_trailing_punctuation(text, start, end)

            if not entity_text:
                continue

            # Skip if overlapping with a higher-priority entity.
            if _overlaps_any_span(start, end, excluded_spans):
                continue

            raw_matches.append((start, end, entity_text))

    # De-duplicate: when multiple patterns match the same or overlapping span,
    # keep the longest match.  Sort by start then longest span.
    raw_matches.sort(key=lambda m: (m[0], -(m[1] - m[0])))
    results: list[dict[str, Any]] = []
    occupied: list[tuple[int, int]] = []

    for start, end, entity_text in raw_matches:
        if _overlaps_any_span(start, end, occupied):
            continue
        results.append({
            "type": "DATE",
            "text": entity_text,
            "start": start,
            "end": end,
        })
        occupied.append((start, end))

    return results


# ---------------------------------------------------------------------------
# Public aggregated detector
# ---------------------------------------------------------------------------

def detect_regex_entities(text: str) -> list[dict[str, Any]]:
    """Run all regex-based detectors and return a clean, non-overlapping,
    sorted list of entity dicts.

    Priority for overlap resolution: EMAIL > URL > PHONE > DATE.
    Output is sorted by ``start`` index ascending.
    """
    all_entities: list[dict[str, Any]] = []
    all_entities.extend(detect_email(text))
    all_entities.extend(detect_url(text))
    all_entities.extend(detect_phone(text))
    all_entities.extend(detect_date(text))

    # Resolve any remaining overlaps.
    clean = _resolve_regex_overlaps(all_entities)
    return clean


# Alias so the rest of the project (web/app.py, tests, merger) can import
# the original name used in the skeleton.
detect_by_regex = detect_regex_entities


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        # Case A
        (
            "Contact: john@gmail.com, phone: +84 912 345 678.",
            "Case A: email + phone",
        ),
        # Case B
        (
            "Visit https://example.com/profile/0912345678 now.",
            "Case B: URL containing phone-like digits",
        ),
        # Case C
        (
            "My email is john123@gmail.com",
            "Case C: email with digits (no false phone)",
        ),
        # Case D
        (
            "Call me at 0912-345-678 or 0912 345 678.",
            "Case D: two phone numbers",
        ),
        # Case E
        (
            "Website: www.example.com.",
            "Case E: www URL with trailing period",
        ),
        # Case F
        (
            "The year is 2024 and the code is 12345.",
            "Case F: no entities (short numbers)",
        ),
        # Case G
        (
            "Emergency number: (091) 234 5678.",
            "Case G: phone with parentheses",
        ),
        # Case H
        (
            "Send to jane.doe+test@example.co.uk!",
            "Case H: email with plus and exclamation",
        ),
        # Mixed
        (
            "Email me at john@gmail.com, visit http://example.com/path?q=1 "
            "or www.example.com, call +1 (415) 555-2671 or 415.555.2671.",
            "Mixed: all entity types",
        ),
        # Edge: empty
        (
            "",
            "Edge: empty string",
        ),
        # --- DATE test cases ---
        # Case I: numeric dates
        (
            "The deadline is 01/02/2024 or 2024-02-01.",
            "Case I: numeric dates (DD/MM/YYYY and YYYY-MM-DD)",
        ),
        # Case J: English month-name dates
        (
            "Born on January 2, 2024 and graduated 2 Jan 2024.",
            "Case J: English month-name dates",
        ),
        # Case K: Vietnamese dates
        (
            "Ngày sinh: ngày 02 tháng 01 năm 2024.",
            "Case K: Vietnamese date",
        ),
        # Case L: month/year only
        (
            "Published in January 2024 and 01/2024.",
            "Case L: month/year formats",
        ),
        # Case M: contextual year only
        (
            "Established in năm 2024 and year 2024.",
            "Case M: contextual year-only",
        ),
        # Case N: bare 4-digit number should NOT be detected as DATE
        (
            "The code is 2024 and ID is 1999.",
            "Case N: bare numbers (no false DATE)",
        ),
        # Case O: date inside URL should NOT be detected
        (
            "See https://example.com/2024/01/02 for details.",
            "Case O: date-like segment inside URL",
        ),
    ]

    for text, label in test_cases:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"  Input: {text!r}")
        print(f"{'='*60}")
        entities = detect_regex_entities(text)
        if not entities:
            print("  (no entities detected)")
        for ent in entities:
            print(
                f"  {ent['type']:6s}  "
                f"[{ent['start']:3d}:{ent['end']:3d}]  "
                f"{ent['text']!r}"
            )
