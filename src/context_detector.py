"""Context-based detectors for NAME, USERNAME, and ADDRESS."""

from __future__ import annotations

from typing import Any

import re
NAME_TRIGGERS = ["my name is", "full name", "name:"]
USERNAME_TRIGGERS = ["username", "user name", "account", "handle"]
ADDRESS_TRIGGERS = ["street", "road", "avenue", "district", "city", "st.", "rd.", "ave."]

# Triggers that need an explicit separator to avoid false positives
_WEAK_USERNAME_TRIGGERS = {"account", "handle"}

# Valid username pattern: starts with alphanumeric/underscore, may contain dots/hyphens
_USERNAME_RE = re.compile(r"@?[A-Za-z0-9_][\w.\-]*")

# Words that stop name collection (common English words that aren't names)
_NAME_STOPWORDS = {
    "and", "or", "but", "the", "a", "an", "in", "at", "on", "of", "to",
    "with", "for", "from", "by", "is", "was", "are", "were", "i", "you",
    "he", "she", "they", "we", "my", "your", "his", "her", "their", "our",
}

def detect_name(text: str) -> list[dict[str, Any]]:
    """
    Detect NAME spans using context rules.
    Looks for strong trigger phrases then collects 1-4 consecutive
    title-cased tokens (no digits, not stop-words) as the name.
    """
    entities: list[dict[str, Any]] = []
    lower = text.lower()
    seen_spans: set[tuple[int, int]] = set()
 
    for trigger in NAME_TRIGGERS:
        search_start = 0
        while True:
            trigger_pos = lower.find(trigger, search_start)
            if trigger_pos == -1:
                break
 
            after = trigger_pos + len(trigger)
            # Skip whitespace and optional colon/dash separators
            while after < len(text) and text[after] in " \t:":
                after += 1
 
            name_tokens: list[str] = []
            name_start: int | None = None
 
            for m in re.finditer(r"\S+", text[after:]):
                token = m.group()
                # Strip trailing punctuation for analysis
                clean = token.rstrip(".,;:!?\"'")
                # Must start with uppercase, contain no digits, not be a stopword
                if (clean
                        and clean[0].isupper()
                        and not any(c.isdigit() for c in clean)
                        and clean.lower() not in _NAME_STOPWORDS):
                    if name_start is None:
                        name_start = after + m.start()
                    name_tokens.append(clean)
                    if len(name_tokens) == 4:
                        break
                else:
                    break
 
            if name_tokens and name_start is not None:
                name_text = " ".join(name_tokens)
                span = (name_start, name_start + len(name_text))
                if span not in seen_spans:
                    seen_spans.add(span)
                    entities.append({
                        "type": "NAME",
                        "text": name_text,
                        "start": span[0],
                        "end": span[1],
                    })
 
            search_start = trigger_pos + len(trigger)
 
    return entities
 
 
def detect_username(text: str) -> list[dict[str, Any]]:
    """
    Detect USERNAME spans using context rules.
    Looks for trigger keywords followed by a separator and a username-shaped token.
    Weak triggers (account, handle) require an explicit separator to avoid false positives like "account manager".
    """
    entities: list[dict[str, Any]] = []
    lower = text.lower()
 
    for trigger in USERNAME_TRIGGERS:
        search_start = 0
        while True:
            trigger_pos = lower.find(trigger, search_start)
            if trigger_pos == -1:
                break
 
            end_of_trigger = trigger_pos + len(trigger)
 
            # Whole-word boundary check
            if end_of_trigger < len(lower) and lower[end_of_trigger].isalpha():
                search_start = trigger_pos + 1
                continue
            if trigger_pos > 0 and lower[trigger_pos - 1].isalpha():
                search_start = trigger_pos + 1
                continue
 
            after = end_of_trigger
 
            if trigger in _WEAK_USERNAME_TRIGGERS:
                # Require explicit separator (: or " is ")
                peek = after
                while peek < len(text) and text[peek] == " ":
                    peek += 1
                if peek >= len(text):
                    search_start = trigger_pos + 1
                    continue
                if text[peek] == ":":
                    after = peek + 1
                elif lower[peek:peek + 3] == "is ":
                    after = peek + 3
                else:
                    search_start = trigger_pos + 1
                    continue
            else:
                while after < len(text) and text[after] in " \t:":
                    after += 1
                if lower[after:after + 3] == "is ":
                    after += 3
 
            while after < len(text) and text[after] == " ":
                after += 1
 
            m = re.match(r"\S+", text[after:])
            if m:
                token = m.group().rstrip(".,;:!?")
                if _USERNAME_RE.fullmatch(token):
                    entities.append({
                        "type": "USERNAME",
                        "text": token,
                        "start": after,
                        "end": after + len(token),
                    })
 
            search_start = trigger_pos + len(trigger)
 
    return entities
 
 
def detect_address(text: str) -> list[dict[str, Any]]:
    """
    Detect ADDRESS spans using context rules.
    Scans for address trigger keywords then extracts the surrounding clause
    as the address value, stripping leading filler words.
    """
    entities: list[dict[str, Any]] = []
    lower = text.lower()
 
    for trigger in ADDRESS_TRIGGERS:
        search_start = 0
        while True:
            trigger_pos = lower.find(trigger, search_start)
            if trigger_pos == -1:
                break
 
            end_of_trigger = trigger_pos + len(trigger)
 
            # Whole-word check (skip if letters follow, e.g. "streets")
            if end_of_trigger < len(lower) and lower[end_of_trigger].isalpha():
                search_start = trigger_pos + 1
                continue
 
            clause_start = _find_clause_start(text, trigger_pos)
            clause_end = _find_clause_end(text, end_of_trigger)
            addr_text, actual_start = _strip_leading_noise(text, clause_start, clause_end)
 
            if addr_text:
                entities.append({
                    "type": "ADDRESS",
                    "text": addr_text,
                    "start": actual_start,
                    "end": actual_start + len(addr_text),
                })
 
            search_start = trigger_pos + len(trigger)
 
    return _deduplicate(entities)
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def _find_clause_start(text: str, pos: int) -> int:
    """Walk backwards to the nearest sentence boundary."""
    for i in range(pos - 1, -1, -1):
        if text[i] in ".\n":
            return i + 1
    return 0
 
 
def _find_clause_end(text: str, pos: int) -> int:
    """Walk forwards to the nearest sentence-ending punctuation."""
    for i in range(pos, len(text)):
        if text[i] in ".,\n;":
            return i
    return len(text)
 
 
_NOISE_RE = re.compile(
    r"^[\s:]*(?:(?:is|at|the|located|in|my|our|a|an|which|where|live(?:s)?|reside(?:s)?|visit|find|me)\s+)*",
    re.IGNORECASE,
)
 
 
def _strip_leading_noise(text: str, start: int, end: int) -> tuple[str, int]:
    """Strip leading filler words from the address clause."""
    raw = text[start:end]
    m = _NOISE_RE.match(raw)
    offset = m.end() if m else 0
    stripped = raw[offset:].strip()
    return stripped, start + offset
 
 
def _deduplicate(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove exact duplicate spans (same start & end)."""
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for e in entities:
        key = (e["start"], e["end"])
        if key not in seen:
            seen.add(key)
            result.append(e)
    return result
 
 
def detect_by_context(text: str) -> list[dict[str, Any]]:
    """Run all context-based detectors and return merged spans sorted by position."""
    entities: list[dict[str, Any]] = []
    entities.extend(detect_name(text))
    entities.extend(detect_username(text))
    entities.extend(detect_address(text))
    entities.sort(key=lambda e: e["start"])
    return entities
