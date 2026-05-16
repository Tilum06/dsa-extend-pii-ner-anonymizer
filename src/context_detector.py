"""Context-based detectors for NAME, USERNAME, and ADDRESS."""

from __future__ import annotations

import re
from typing import Any
import src.tokenizer as tokenizer

# ---------------------------------------------------------------------------
# Constants & Triggers
# ---------------------------------------------------------------------------

NAME_TRIGGERS = {"my name is", "full name", "name:"}
USERNAME_TRIGGERS = {"username", "user name", "account", "handle"}
ADDRESS_TRIGGERS = {
    "street",
    "road",
    "avenue",
    "district",
    "city",
    "st.",
    "rd.",
    "ave.",
}

_WEAK_USERNAME_TRIGGERS = {"account", "handle"}
_USERNAME_RE = re.compile(r"@?[A-Za-z0-9_][\w.\-]*")

# Title prefixes to strip from name candidates
_TITLE_PREFIXES = {
    "dr.",
    "mr.",
    "mrs.",
    "ms.",
    "prof.",
    "dr",
    "mr",
    "mrs",
    "ms",
    "prof",
}

# Address abbreviations — dấu "." ở đây KHÔNG phải cuối câu
_ADDR_ABBREVS = {
    "st.",
    "rd.",
    "ave.",
    "apt.",
    "blvd.",
    "dr.",
    "ln.",
    "ct.",
    "pl.",
    "ter.",
}

# Tokens whose trailing "." is NOT a sentence boundary
_NO_SPLIT_ABBREVS = (
    _TITLE_PREFIXES
    | _ADDR_ABBREVS
    | {
        "jr.",
        "sr.",
        "etc.",
        "vs.",
        "fig.",
        "no.",
        "vol.",
        "inc.",
        "ltd.",
        "corp.",
        "u.s.",
        "u.k.",
        "j.k.",
        "e.g.",
        "i.e.",
        "approx.",
        "dept.",
        "est.",
    }
)

# Top-level domains — "." before them is NOT a sentence boundary
_TLDS = {
    "com",
    "net",
    "org",
    "edu",
    "gov",
    "io",
    "co",
    "info",
    "biz",
    "vn",
    "uk",
    "us",
    "au",
    "ca",
    "de",
    "fr",
    "jp",
    "cn",
    "me",
    "tv",
    "app",
    "dev",
    "ai",
}

# Label triggers — sau dấu ":" gần như chắc chắn là tên
_LABEL_TRIGGERS = {
    # Dạng đơn giản
    "contact person:",
    "submitted by:",
    "author:",
    "written by:",
    "signed by:",
    "prepared by:",
    "reported by:",
    "from:",
    "sender:",
    "recipient:",
    "applicant:",
    "client:",
    "patient:",
    # Dạng "X Information:" / "X Info:"
    "contact information:",
    "contact info:",
    "personal information:",
    "personal info:",
    "user information:",
    "profile information:",
    # Dạng "X Details:" / "X Data:"
    "contact details:",
    "personal details:",
    "user details:",
    "account details:",
    "profile details:",
    # Dạng khác hay gặp
    "full name:",
    "name:",
    "my name is",
    "regards,",
    "sincerely,",
    "best regards,",
}

# Job titles dùng để dừng thu thập candidate (tránh "Mieko Mitsubishi Account Manager")
_JOB_TITLE_STOPWORDS = {
    "account",
    "manager",
    "director",
    "officer",
    "president",
    "executive",
    "engineer",
    "developer",
    "designer",
    "analyst",
    "consultant",
    "architect",
    "coordinator",
    "administrator",
    "supervisor",
    "specialist",
    "associate",
    "representative",
    "assistant",
    "secretary",
    "treasurer",
    "chairman",
    "partner",
    "founder",
    "owner",
    "principal",
    "professor",
    "doctor",
    "attorney",
    "counsel",
    "advisor",
    "agent",
    "inspector",
    "auditor",
}

# Suffixes chỉ tổ chức/địa điểm — candidate kết thúc bằng các từ này
# thì là tên công ty/trường/địa điểm, KHÔNG phải tên người
_ORG_PLACE_SUFFIXES = {
    # Loại hình công ty / doanh nghiệp
    "company",
    "corporation",
    "corp",
    "incorporated",
    "inc",
    "limited",
    "ltd",
    "llc",
    "plc",
    "group",
    "holdings",
    "ventures",
    "enterprise",
    "enterprises",
    "associates",
    "partners",
    "partnership",
    "agency",
    "bureau",
    "firm",
    "studio",
    "studios",
    "lab",
    "labs",
    "solutions",
    "services",
    "systems",
    "technologies",
    "tech",
    "international",
    "global",
    "national",
    # Loại hình tổ chức / cơ quan
    "organization",
    "organisation",
    "foundation",
    "institute",
    "institution",
    "association",
    "society",
    "committee",
    "commission",
    "council",
    "department",
    "division",
    "branch",
    "office",
    "ministry",
    "authority",
    "board",
    "federation",
    "union",
    "network",
    "alliance",
    "center",
    "centre",
    "clinic",
    "hospital",
    # Trường học
    "university",
    "college",
    "school",
    "academy",
    "institute",
    "polytechnic",
    "faculty",
    "campus",
    # Địa điểm / cơ sở vật chất
    "hotel",
    "motel",
    "resort",
    "hostel",
    "inn",
    "restaurant",
    "cafe",
    "bar",
    "pub",
    "club",
    "lounge",
    "mall",
    "plaza",
    "tower",
    "towers",
    "building",
    "complex",
    "stadium",
    "arena",
    "theater",
    "theatre",
    "cinema",
    "gallery",
    "museum",
    "library",
    "park",
    "garden",
    "gardens",
    "airport",
    "station",
    "terminal",
    "port",
    "harbor",
    "market",
    "store",
    "shop",
    "outlet",
    "warehouse",
    "bank",
    "exchange",
}

# Từ thường đứng cuối label header (e.g. "Contact Information:", "Personal Details:")
# Token này viết hoa nhưng KHÔNG phải tên người — loại khỏi candidate group
_LABEL_HEADER_WORDS = {
    # Từ chỉ loại thông tin
    "information",
    "info",
    "details",
    "data",
    "summary",
    "overview",
    "profile",
    "record",
    "records",
    "section",
    "form",
    "sheet",
    "report",
    "note",
    "notes",
    "description",
    "statement",
    # Từ label hay đứng trước ":" chỉ vai trò / quan hệ
    "witness",
    "nominee",
    "supervisor",
    "referee",
    "guarantor",
    "beneficiary",
    "trustee",
    "guardian",
    "executor",
    "delegate",
    "representative",
    "spokesperson",
    "liaison",
    "contact",
    "emergency",
    "primary",
    "secondary",
    "alternate",
    "backup",
}

# Stopwords for name token collection
_NAME_STOPWORDS = {
    "and",
    "or",
    "but",
    "the",
    "a",
    "an",
    "in",
    "at",
    "on",
    "of",
    "to",
    "with",
    "for",
    "from",
    "by",
    "as",
    "into",
    "via",
    "about",
    "i",
    "you",
    "he",
    "she",
    "they",
    "we",
    "it",
    "my",
    "your",
    "his",
    "her",
    "their",
    "our",
    "its",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "has",
    "have",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "shall",
    "works",
    "worked",
    "work",
    "lives",
    "lived",
    "live",
    "graduated",
    "graduate",
    "studied",
    "studies",
    "study",
    "joined",
    "joins",
    "join",
    "founded",
    "founds",
    "found",
    "manages",
    "managed",
    "manage",
    "went",
    "goes",
    "go",
    "said",
    "says",
    "say",
    "made",
    "makes",
    "make",
    "took",
    "takes",
    "take",
    "came",
    "comes",
    "come",
    "got",
    "gets",
    "get",
    "knew",
    "knows",
    "know",
    "called",
    "calls",
    "call",
}

# Verb suffix — only triggered after >= 1 name token already collected
_VERB_SUFFIX_RE = re.compile(r".{3,}(ing|tion|sion|ment|ed|ness)$", re.IGNORECASE)

# Special characters that disqualify a token from being part of a name
# Lưu ý: dấu "-" KHÔNG nằm trong list này vì tên có thể có dạng "Mary-Jane"
_SPECIAL_CHARS_RE = re.compile(r"[~!@#$%^&*()\[\]{};=+?\"']")

# Pronouns
_FIRST_PERSON = {"i", "i'm", "i am", "me", "my"}
_THIRD_PERSON = {"he", "his", "him", "she", "her"}

# Job detection
_ROLE_MARKERS_RE = re.compile(
    r"\b(?:a|an|the|as\s+a|as\s+an|is\s+a|is\s+an|am\s+a|am\s+an|"
    r"was\s+a|was\s+an|work(?:s|ed)?\s+as(?:\s+a(?:n)?)?|"
    r"working\s+as(?:\s+a(?:n)?)?)\s+(\w+)",
    re.IGNORECASE,
)
_JOB_SUFFIX_RE = re.compile(
    r"\b\w*(man|men|woman|women|er|ist|ant|ent|or|eur|eer|ician|ian)\b",
    re.IGNORECASE,
)
_JOB_HARDLIST = {
    "coach",
    "surgeon",
    "nurse",
    "pilot",
    "chef",
    "judge",
    "professional",
    "attorney",
    "actress",
    "waitress",
    "mechanic",
    "ceo",
    "cto",
    "cfo",
    "doctor",
    "lawyer",
    "teacher",
    "professor",
    "officer",
    "director",
    "manager",
    "analyst",
    "consultant",
    "architect",
    "developer",
    "designer",
    "scientist",
    "researcher",
    "writer",
    "editor",
    "journalist",
    "photographer",
    "artist",
    "musician",
    "dancer",
    "actor",
    "model",
    "athlete",
    "trainer",
    "therapist",
    "counselor",
    "advisor",
    "assistant",
    "coordinator",
    "administrator",
    "supervisor",
    "inspector",
    "detective",
    "agent",
}

# Address regex — street types sorted longest first to avoid early match
_STREET_TYPES = (
    r"Boulevard|Terrace|Avenue|Street|Circle|Drive|Court|Place|Lane|"
    r"Trail|Road|Walk|Park|Loop|Pass|Point|Run|Path|Bend|Ridge|Hill|"
    r"Square|Pines|Baron|Via|"
    r"Blvd\.|Ave\.|Ter\.|Rd\.|St\.|Dr\.|Ln\.|Ct\.|Pl\."
)
_DIRECTIONS = (
    r"(?:\s+(?:North|South|East|West|Northeast|Northwest|Southeast|Southwest))?"
)
_UNIT = r"(?:\s+(?:Suite|Apt\.?|Apartment|Unit)\s+\d+)?"

_ADDRESS_RE = re.compile(
    r"\b(\d{1,5})(?!\d)\s+"  # house number: 1–5 digits (no longer number)
    r"((?:[A-Z0-9][A-Za-z0-9]*\s+)+?)"  # street name words (non-greedy)
    r"("
    + _STREET_TYPES
    + r")"  # street type (longest-first)
    + _DIRECTIONS
    + _UNIT
    + r"\b",
    re.IGNORECASE,
)

_EMAIL_RE = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+")


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------


def _split_sentences(text: str) -> list[tuple[str, int]]:
    """Split text into (sentence, start_offset) pairs.

    A '.' ends a sentence only when:
      - Followed by whitespace (or end of string)
      - The token ending with '.' is NOT a known abbreviation
      - The text after '.' is NOT a TLD (to avoid splitting emails/URLs)
    """
    sentences: list[tuple[str, int]] = []
    current_start = 0
    i = 0

    while i < len(text):
        ch = text[i]

        if ch in ".!?":
            if ch == ".":
                # Find the token that ends with this dot
                tok_start = i - 1
                while tok_start >= current_start and not text[tok_start].isspace():
                    tok_start -= 1
                tok_start += 1
                token_lower = text[tok_start : i + 1].lower()

                # Known abbreviation → not a sentence boundary
                if token_lower in _NO_SPLIT_ABBREVS:
                    i += 1
                    continue

                # Looks like a TLD (email / URL) → not a sentence boundary
                after_dot = i + 1
                tld_m = re.match(
                    r"([a-z]{2,6})", text[after_dot : after_dot + 7].lower()
                )
                if tld_m and tld_m.group(1) in _TLDS:
                    i += 1
                    continue

                # Must be followed by whitespace to count as sentence end
                if after_dot < len(text) and not text[after_dot].isspace():
                    i += 1
                    continue

            # Sentence boundary confirmed
            sentence = text[current_start : i + 1].strip()
            if sentence:
                sentences.append((sentence, current_start))
            current_start = i + 1
            while current_start < len(text) and text[current_start].isspace():
                current_start += 1
            i = current_start
        else:
            i += 1

    remainder = text[current_start:].strip()
    if remainder:
        sentences.append((remainder, current_start))

    return sentences


# ---------------------------------------------------------------------------
# NAME helpers
# ---------------------------------------------------------------------------


def _extract_name_candidates(
    sentence: tuple[str, int],
) -> list[tuple[str, int, int]]:
    """Scan sentences for consecutive title-cased token groups (2–4 tokens).

    Rules:
    - Strip leading title prefixes (Dr., Mr., etc.) and "As"
    - Discard tokens with special characters
    - Discard groups where previous token was a pure number (→ likely address)
    - Discard groups starting with a digit
    - Minimum 2 tokens to be a valid candidate
    """
    candidates: list[tuple[str, int, int]] = []

    sentence_text, sent_offset = sentence[0], sentence[1]
    tokens = re.findall(r"\S+", sentence_text)
    i = 0
    while i < len(tokens):
        token = tokens[i]
        clean_token = token.strip(",;:!?\"'")

        # Check for title prefix
        if clean_token.lower() in _TITLE_PREFIXES or (
            clean_token.lower() == "as" and i + 1 < len(tokens)
        ):
            i += 1
            continue

        # Check if token is a valid name token
        if (
            clean_token
            and clean_token[0].isupper()
            and not any(c.isdigit() for c in clean_token)
            and not _SPECIAL_CHARS_RE.search(clean_token)
        ):
            start_idx = sentence_text.find(token, sent_offset)
            end_idx = start_idx + len(token)

            # Collect consecutive title-cased tokens (up to 4)
            name_tokens = [clean_token]
            j = i + 1
            while j < len(tokens) and len(name_tokens) < 4:
                next_token = tokens[j]
                clean_next = next_token.strip(",;:!?\"'")
                if (
                    clean_next
                    and clean_next[0].isupper()
                    and not any(c.isdigit() for c in clean_next)
                    and not _SPECIAL_CHARS_RE.search(clean_next)
                ):
                    name_tokens.append(clean_next)
                    end_idx = sentence_text.find(next_token, sent_offset) + len(
                        next_token
                    )
                    j += 1
                else:
                    break

            if len(name_tokens) >= 2:
                candidates.append((" ".join(name_tokens), start_idx, end_idx))
                i = j
            else:
                i += 1
        else:
            i += 1

    return candidates


def _has_job_in_sentence(sentence: str) -> bool:
    """Return True if the sentence contains a job/occupation signal."""
    words = re.findall(r"\b\w+\b", sentence.lower())
    for w in words:
        if w in _JOB_HARDLIST:
            return True
    for m in _ROLE_MARKERS_RE.finditer(sentence):
        word = m.group(1).lower()
        if _JOB_SUFFIX_RE.fullmatch(word):
            return True
    return False


def _score_candidate(candidate: str, sentence: str, full_text: str) -> tuple[int, bool]:
    """Score a name candidate in its sentence context.

    Returns (score, is_definitive).
    is_definitive=True → caller should break and return this candidate immediately.
    """
    score = 0
    sent_lower = sentence.lower()
    cand_lower = candidate.lower()
    cand_parts = cand_lower.split()

    # --- Definitive patterns (break immediately) ---

    # Strong triggers: "my name is X", "full name: X", "name: X"
    for trigger in NAME_TRIGGERS or _LABEL_TRIGGERS:
        if trigger in sent_lower:
            idx = sent_lower.find(trigger)
            after = sentence[idx + len(trigger) :].strip().lstrip(":").strip()
            if after.lower().startswith(cand_lower):
                return 100, True

    # "I, [name]" or "[name], I"
    if re.search(r"\bI\s*,\s*" + re.escape(candidate), sentence, re.IGNORECASE):
        return 100, True
    if re.search(re.escape(candidate) + r"\s*,\s*I\b", sentence, re.IGNORECASE):
        return 100, True

    # "I'm [name]" / "I am [name]"
    if re.search(r"\bI'?m\s+" + re.escape(candidate), sentence, re.IGNORECASE):
        return 100, True
    if re.search(r"\bI\s+am\s+" + re.escape(candidate), sentence, re.IGNORECASE):
        return 100, True

    # "I was named [name]"
    if re.search(
        r"\bI\s+was\s+named\s+" + re.escape(candidate), sentence, re.IGNORECASE
    ):
        return 100, True

    # --- Non-definitive scoring ---

    # "my name" in sentence
    if "my name" in sent_lower:
        score += 10

    # "As [name]," at start of sentence
    if re.match(r"^\s*As\s+" + re.escape(candidate) + r"\s*,", sentence, re.IGNORECASE):
        score += 5

    # Pattern "label: [name]" — candidate xuất hiện ngay sau dấu ":"
    # Không cần biết label là gì, chỉ cần có dấu ":" trước candidate
    colon_before = re.search(
        r":\s*\n?\s*" + re.escape(candidate),
        sentence,
        re.IGNORECASE,
    )
    if colon_before:
        score += 5

    # Appositive pattern: "[name], <job title/role>," — tên đứng trước chức danh trong dấu phẩy
    # e.g. "Kazuo Sun, air traffic controller, ..."
    if re.search(re.escape(candidate) + r"\s*,\s*\w+", sentence, re.IGNORECASE):
        # Kiểm tra từ sau dấu phẩy có phải job title không
        appos_m = re.search(
            re.escape(candidate) + r"\s*,\s*(\w+(?:\s+\w+)?)",
            sentence,
            re.IGNORECASE,
        )
        if appos_m:
            appos_words = appos_m.group(1).lower().split()
            if any(
                w in _JOB_HARDLIST or w in _JOB_TITLE_STOPWORDS for w in appos_words
            ):
                score += 3

    # Signature pattern: candidate đứng trên dòng riêng, dòng tiếp theo là job title
    # e.g. "Mieko Mitsubishi\nAccount Manager\n1309..."
    sig_m = re.search(
        re.escape(candidate) + r"\s*\n\s*(\w+(?:\s+\w+)?)",
        full_text,
        re.IGNORECASE,
    )
    if sig_m:
        next_line_words = sig_m.group(1).lower().split()
        if any(
            w in _JOB_HARDLIST or w in _JOB_TITLE_STOPWORDS for w in next_line_words
        ):
            score += 4

    # Pronoun scoring — first-person beats third-person (no stacking)
    has_first = any(
        re.search(r"\b" + re.escape(p) + r"\b", sent_lower) for p in _FIRST_PERSON
    )
    has_third = any(
        re.search(r"\b" + re.escape(p) + r"\b", sent_lower) for p in _THIRD_PERSON
    )

    if has_first:
        score += 2
    elif has_third:
        score += 1

    # Job/occupation in the same sentence
    if _has_job_in_sentence(sentence):
        score += 2

    # Repetition in full text (partial match: each part of name counted)
    repeat_count = 0
    for part in cand_parts:
        repeat_count += len(
            re.findall(r"\b" + re.escape(part) + r"\b", full_text, re.IGNORECASE)
        )
    repeat_count -= len(cand_parts)  # subtract the candidate itself
    if repeat_count > 0:
        score += min(repeat_count, 5)  # cap at +5

    # Title prefix present before candidate anywhere in full text
    if re.search(
        r"\b(?:Dr|Mr|Mrs|Ms|Prof)\.?\s+" + re.escape(candidate),
        full_text,
        re.IGNORECASE,
    ):
        score += 1

    return score, False


# ---------------------------------------------------------------------------
# Public detectors
# ---------------------------------------------------------------------------


def detect_name(text: str) -> list[dict[str, Any]]:
    """Detect NAME spans using trigger rules + scoring algorithm."""
    entities: list[dict[str, Any]] = []
    lower = text.lower()
    seen_spans: set[tuple[int, int]] = set()

    # --- Fast path: strong triggers ---
    for trigger in NAME_TRIGGERS or _LABEL_TRIGGERS:
        search_start = 0
        while True:
            trigger_pos = lower.find(trigger, search_start)
            if trigger_pos == -1:
                break

            after = trigger_pos + len(trigger)
            while after < len(text) and text[after] in " \t:":
                after += 1

            name_tokens: list[str] = []
            name_start: int | None = None

            for m in re.finditer(r"\S+", text[after:]):
                token = m.group()
                clean = token.rstrip(".,;:!?\"'")
                if not (
                    clean and clean[0].isupper() and not any(c.isdigit() for c in clean)
                ):
                    break
                if clean.lower() in _NAME_STOPWORDS:
                    break
                if _SPECIAL_CHARS_RE.search(clean):
                    break
                if name_tokens and _VERB_SUFFIX_RE.fullmatch(clean):
                    break
                if name_start is None:
                    name_start = after + m.start()
                name_tokens.append(clean)
                if len(name_tokens) == 4:
                    break

            if name_tokens and name_start is not None:
                name_text = " ".join(name_tokens)
                span = (name_start, name_start + len(name_text))
                if span not in seen_spans:
                    seen_spans.add(span)
                    entities.append(
                        {
                            "type": "NAME",
                            "text": name_text,
                            "start": span[0],
                            "end": span[1],
                        }
                    )
            search_start = trigger_pos + len(trigger)

    if entities:
        return entities

    # --- Scoring path ---
    sentences = _split_sentences(text)
    candidates = _extract_name_candidates(text)

    if not candidates:
        return []

    # best_scores: candidate_text -> (score, start, end)
    best_scores: dict[str, tuple[int, int, int]] = {}

    for cand_text, cand_start, cand_end in candidates:
        best_score = 0

        for sent, _ in sentences:
            # Check if any part of the candidate appears in the sentence
            parts = cand_text.lower().split()
            if not any(p in sent.lower() for p in parts):
                continue

            s, definitive = _score_candidate(cand_text, sent, text)

            if definitive:
                entities.append(
                    {
                        "type": "NAME",
                        "text": cand_text,
                        "start": cand_start,
                        "end": cand_end,
                    }
                )
                return entities

            best_score = max(best_score, s)

        existing = best_scores.get(cand_text)
        if existing is None or best_score > existing[0]:
            best_scores[cand_text] = (best_score, cand_start, cand_end)

    if not best_scores:
        return []

    # Pick winner: highest score; tie → earliest position
    winner_text = max(
        best_scores,
        key=lambda t: (best_scores[t][0], -best_scores[t][1]),
    )
    _, winner_start, winner_end = best_scores[winner_text]

    entities.append(
        {
            "type": "NAME",
            "text": winner_text,
            "start": winner_start,
            "end": winner_end,
        }
    )
    return entities


def detect_username(text: str) -> list[dict[str, Any]]:
    """Detect USERNAME spans using context rules."""
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
                peek = after
                while peek < len(text) and text[peek] == " ":
                    peek += 1
                if peek >= len(text):
                    search_start = trigger_pos + 1
                    continue
                if text[peek] == ":":
                    after = peek + 1
                elif lower[peek : peek + 3] == "is ":
                    after = peek + 3
                else:
                    search_start = trigger_pos + 1
                    continue
            else:
                while after < len(text) and text[after] in " \t:":
                    after += 1
                if lower[after : after + 3] == "is ":
                    after += 3

            while after < len(text) and text[after] == " ":
                after += 1

            m = re.match(r"\S+", text[after:])
            if m:
                token = m.group().rstrip(".,;:!?")
                if _USERNAME_RE.fullmatch(token):
                    entities.append(
                        {
                            "type": "USERNAME",
                            "text": token,
                            "start": after,
                            "end": after + len(token),
                        }
                    )

            search_start = trigger_pos + len(trigger)

    return entities


def detect_address(text: str) -> list[dict[str, Any]]:
    """Detect ADDRESS spans using regex pattern + trigger-keyword fallback."""
    entities: list[dict[str, Any]] = []

    # Pre-compute email spans to exclude
    email_spans = [(m.start(), m.end()) for m in _EMAIL_RE.finditer(text)]

    def _in_email(start: int, end: int) -> bool:
        return any(es <= start and end <= ee for es, ee in email_spans)

    # --- Primary: regex pattern (house number + street type) ---
    for m in _ADDRESS_RE.finditer(text):
        if _in_email(m.start(), m.end()):
            continue
        addr_text = m.group().strip()
        entities.append(
            {
                "type": "ADDRESS",
                "text": addr_text,
                "start": m.start(),
                "end": m.start() + len(addr_text),
            }
        )

    # --- Fallback: trigger keywords for addresses without street type ---
    lower = text.lower()
    for trigger in ADDRESS_TRIGGERS:
        search_start = 0
        while True:
            trigger_pos = lower.find(trigger, search_start)
            if trigger_pos == -1:
                break

            end_of_trigger = trigger_pos + len(trigger)
            if end_of_trigger < len(lower) and lower[end_of_trigger].isalpha():
                search_start = trigger_pos + 1
                continue

            clause_start = _find_clause_start(text, trigger_pos)
            clause_end = _find_clause_end(text, end_of_trigger)
            addr_text, actual_start = _strip_leading_noise(
                text, clause_start, clause_end
            )

            # Skip if leading house number has more than 5 digits
            leading_num = re.match(r"^(\d+)", addr_text)
            if leading_num and len(leading_num.group(1)) > 5:
                search_start = trigger_pos + len(trigger)
                continue

            if addr_text and not _in_email(actual_start, actual_start + len(addr_text)):
                overlap = any(
                    e["start"] <= actual_start < e["end"]
                    or actual_start <= e["start"] < actual_start + len(addr_text)
                    for e in entities
                )
                if not overlap:
                    entities.append(
                        {
                            "type": "ADDRESS",
                            "text": addr_text,
                            "start": actual_start,
                            "end": actual_start + len(addr_text),
                        }
                    )

            search_start = trigger_pos + len(trigger)

    return _deduplicate(entities)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _find_clause_start(text: str, pos: int) -> int:
    for i in range(pos - 1, -1, -1):
        if text[i] in ".\n":
            return i + 1
    return 0


def _find_clause_end(text: str, pos: int) -> int:
    for i in range(pos, len(text)):
        if text[i] in ".,\n;":
            return i
    return len(text)


_NOISE_RE = re.compile(
    r"^[\s:]*(?:(?:is|at|the|located|in|my|our|a|an|which|where|"
    r"live(?:s)?|reside(?:s)?|visit|find|me)\s+)*",
    re.IGNORECASE,
)


def _strip_leading_noise(text: str, start: int, end: int) -> tuple[str, int]:
    raw = text[start:end]
    m = _NOISE_RE.match(raw)
    offset = m.end() if m else 0
    stripped = raw[offset:].strip()
    return stripped, start + offset


def _deduplicate(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for e in entities:
        key = (e["start"], e["end"])
        if key not in seen:
            seen.add(key)
            result.append(e)
    return result


def detect_by_context(
    text: str, excluded_entities: list[dict[str, Any]] = []
) -> list[dict[str, Any]]:
    """Run all context-based detectors and return merged spans sorted by position."""
    if excluded_entities is None:
        excluded_entities = []

    entities: list[dict[str, Any]] = []
    entities.extend(detect_name(text))
    entities.extend(detect_username(text))
    entities.extend(detect_address(text))
    entities.sort(key=lambda e: e["start"])
    return entities
