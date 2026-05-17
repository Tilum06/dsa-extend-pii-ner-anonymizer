"""Text anonymization helpers."""

from __future__ import annotations

import re
from typing import Any


def build_token_entity_dict(
    text: str, entities: list[dict[str, Any]]
) -> dict[str, str]:
    """Build a dictionary mapping each token in *text* to its BIO label.

    Uses BIO tagging: ``B-TYPE`` for the first token of an entity,
    ``I-TYPE`` for continuation tokens, and ``"O"`` for non-entity tokens.

    Parameters
    ----------
    text:
        The original input text.
    entities:
        A list of entity dicts, each with keys ``type``, ``start``, ``end``
        (character offsets) and optionally ``text``.

    Returns
    -------
    dict[str, str]
        ``{token: bio_label}`` for every whitespace-delimited token in
        *text*.  If duplicate tokens exist, the **last** assignment wins.

    Notes
    -----
    Because a plain ``dict`` loses positional information for duplicate
    tokens, the companion helper :func:`build_token_entity_list` returns a
    list of ``(token, bio_label)`` tuples preserving order.
    """
    token_entity_list = build_token_entity_list(text, entities)
    return {token: entity_type for token, entity_type in token_entity_list}


def build_token_entity_list(
    text: str, entities: list[dict[str, Any]]
) -> list[tuple[str, str]]:
    """Return an **ordered** list of ``(token, bio_label)`` tuples.

    Uses BIO (Begin–Inside–Outside) tagging:

    * ``B-TYPE`` – first token of an entity span
    * ``I-TYPE`` – continuation token of the same entity span
    * ``O``      – token not covered by any entity

    Unlike :func:`build_token_entity_dict`, this preserves positional
    information even when the same token string appears more than once.
    """
    # Find each token's character span via regex so we get accurate offsets
    token_spans: list[tuple[str, int, int]] = [
        (m.group(), m.start(), m.end())
        for m in re.finditer(r"\S+", text)
    ]

    # Sort entities by start for efficient lookup
    sorted_entities = sorted(entities, key=lambda e: e["start"])

    # Track which entity (by index) was assigned to the previous token
    # so we can distinguish B- vs I- tags.
    prev_ent_idx: int | None = None

    result: list[tuple[str, str]] = []

    for token_text, tok_start, tok_end in token_spans:
        label = "O"
        matched_ent_idx: int | None = None

        for ent_idx, ent in enumerate(sorted_entities):
            ent_start = ent["start"]
            ent_end = ent["end"]

            # Entity ends before this token — skip
            if ent_end <= tok_start:
                continue
            # Entity starts after this token — no further entities can match
            if ent_start >= tok_end:
                break

            # Overlap detected: determine B- or I- prefix
            matched_ent_idx = ent_idx
            if prev_ent_idx == ent_idx:
                # Same entity as previous token → continuation
                label = f"I-{ent['type']}"
            else:
                # First token of this entity
                label = f"B-{ent['type']}"
            break

        prev_ent_idx = matched_ent_idx
        result.append((token_text, label))

    return result


def anonymize_text(text: str, entities: list[dict[str, Any]]) -> str:
    """Replace entity spans with ``[ENTITY_TYPE]`` placeholders.

    Parameters
    ----------
    text:
        The original input text.
    entities:
        A list of entity dicts with ``type``, ``start``, and ``end``.

    Returns
    -------
    str
        Text with detected PII spans replaced by labels such as ``[EMAIL]``.
    """
    anonymized = text
    for entity in sorted(entities, key=lambda e: e["start"], reverse=True):
        label = f"[{entity['type']}]"
        anonymized = anonymized[: entity["start"]] + label + anonymized[entity["end"] :]
    return anonymized
