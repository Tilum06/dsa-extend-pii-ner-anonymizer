"""Context-based detectors for NAME, ORGANIZATION, LOCATION, USERNAME, and ADDRESS."""

from __future__ import annotations

import re
from typing import Any, TypedDict


class Entity(TypedDict):
    """Public entity shape returned by context detectors."""

    type: str
    text: str
    start: int
    end: int


class Sentence(TypedDict):
    """Sentence span in the original input text."""

    sentence: str
    start: int
    end: int


class Candidate(TypedDict):
    """Internal candidate span before final resolution."""

    text: str
    start: int
    end: int


class ScoredCandidate(TypedDict):
    """Candidate plus final tag and score after multi-label scoring."""

    type: str
    text: str
    start: int
    end: int
    score: int


class DetectorContext(TypedDict):
    """Shared preprocessing context used by all context detectors."""

    text: str
    lower: str
    sentences: list[Sentence]
    email_spans: list[tuple[int, int]]


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
ORG_TRIGGERS = {
    "company",
    "organization",
    "organisation",
    "employer",
    "work at",
    "work for",
    "works at",
    "works for",
    "worked at",
    "worked for",
    "joined",
    "founded",
    "employed by",
}
LOCATION_TRIGGERS = {
    "location",
    "located at",
    "located in",
    "city",
    "district",
    "province",
    "state",
    "country",
    "from",
    "in",
    "at",
    "near",
    "visited",
    "visit",
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
        "p.m.",
        "a.m.",
        "p.s.",
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

_ORG_SUFFIXES = {
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
    "university",
    "college",
    "school",
    "academy",
    "polytechnic",
    "faculty",
    "bank",
    "exchange",
}

_LOCATION_SUFFIXES = {
    "city",
    "town",
    "village",
    "district",
    "province",
    "state",
    "county",
    "country",
    "region",
    "downtown",
    "neighborhood",
    "neighbourhood",
    "street",
    "road",
    "avenue",
    "boulevard",
    "drive",
    "lane",
    "court",
    "place",
    "terrace",
    "park",
    "garden",
    "gardens",
    "airport",
    "station",
    "terminal",
    "port",
    "harbor",
    "market",
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
    "campus",
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
    "store",
    "shop",
    "outlet",
    "warehouse",
}

_PROPER_NOUN_CONNECTORS = {"of", "the", "and", "&"}
_ENTITY_SCORE_THRESHOLDS = {"NAME": 0, "ORGANIZATION": 3, "LOCATION": 3}
_ENTITY_SCORE_TIEBREAK = {"ORGANIZATION": 0, "LOCATION": 1, "NAME": 2}

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
    "no",
    "not",
    "just",
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
    "contact",
    "email",
    "address",
    "phone",
    "number",
    "username",
    "user",
    "names",
    "name",
    "here",
    "plain",
    "text",
    "without",
    "triggers",
    "street",
    "road",
    "avenue",
    "boulevard",
    "drive",
    "lane",
    "court",
    "place",
    "terrace",
    "suite",
    "apartment",
    "apt",
    "unit",
}

_POSSIBLE_SENTENCE_STARTERS = {
    "this",
    "then",
    "using",
    "each",
    "once",
    "given",
    "considering",
    "after",
    "before",
    "when",
    "while",
    "although",
    "though",
    "if",
    "unless",
    "since",
    "because",
    "as",
    "even though",
    "in case",
    "provided that",
    "fortunately",
    "if",
    "whenever",
    "whereas",
    "despite",
    "in spite of",
    "regardless of",
    "assuming that",
    "suppose",
    "supposing that",
    "let's say",
    "say that",
    "imagine that",
    "what if",
    "hypothetically",
    "for example",
    "for instance",
    "e.g.",
    "i.e.",
    "to illustrate",
    "in other words",
    "that is",
    "namely",
    "specifically",
    "such as",
    "like",
    "including",
    "particularly",
    "notably",
    "especially",
    "as an example",
    "as a case in point",
    "to put it another way",
    "in particular",
    "on the other hand",
    "alternatively",
    "in contrast",
    "conversely",
    "similarly",
    "likewise",
    "correspondingly",
    "comparatively",
    "by comparison",
    "in comparison",
    "at the same time",
    "meanwhile",
    "subsequently",
    "afterward",
    "thereafter",
    "eventually",
    "ultimately",
    "finally",
    "in conclusion",
    "to sum up",
    "in summary",
    "overall",
    "all in all",
    "in brief",
    "in short",
    "to summarize",
    "to conclude",
    "in essence",
    "in a nutshell",
    "in a word",
    "to put it simply",
    "simply put",
    "put simply",
    "frankly",
    "honestly",
    "truthfully",
    "candidly",
    "to be honest",
    "to be frank",
    "to tell the truth",
    "in my opinion",
    "personally",
    "from my perspective",
    "as far as I'm concerned",
    "if you ask me",
    "my take is",
    "the way I see it",
    "what I think is",
    "the point is",
    "the fact is",
    "the reality is",
    "the bottom line is",
    "unfortunately",
    "throughout",
    "quilting",
    "additionally",
    "one",
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
_INLINE_NAME_BIO_SUFFIX_RE = re.compile(r":?[BI]-(?:NAME|NAME_STUDENT)$")


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------


def _split_sentences(text: str) -> list[Sentence]:
    """Split text into (sentence, start_offset) pairs.

    A '.' ends a sentence only when:
      - Followed by whitespace (or end of string)
      - The token ending with '.' is NOT a known abbreviation
      - The text after '.' is NOT a TLD (to avoid splitting emails/URLs)
    """
    sentences: list[Sentence] = []
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
            raw_sentence = text[current_start : i + 1]
            leading = len(raw_sentence) - len(raw_sentence.lstrip())
            sentence_start = current_start + leading
            sentence = raw_sentence.strip()
            if sentence:
                sentences.append(
                    {
                        "sentence": sentence,
                        "start": sentence_start,
                        "end": sentence_start + len(sentence),
                    }
                )
            current_start = i + 1
            while current_start < len(text) and text[current_start].isspace():
                current_start += 1
            i = current_start
        else:
            i += 1

    raw_remainder = text[current_start:]
    leading = len(raw_remainder) - len(raw_remainder.lstrip())
    remainder_start = current_start + leading
    remainder = raw_remainder.strip()
    if remainder:
        sentences.append(
            {
                "sentence": remainder,
                "start": remainder_start,
                "end": remainder_start + len(remainder),
            }
        )

    return sentences


def _build_context(text: str) -> DetectorContext:
    """Preprocess raw text once for all context detectors."""
    if text is None:
        text = ""
    text = str(text)
    return {
        "text": text,
        "lower": text.lower(),
        "sentences": _split_sentences(text),
        "email_spans": [(m.start(), m.end()) for m in _EMAIL_RE.finditer(text)],
    }


# ---------------------------------------------------------------------------
# NAME helpers
# ---------------------------------------------------------------------------


def _clean_name_token(raw: str) -> tuple[str, int, int]:
    """Return cleaned token text and raw-relative span for NAME extraction."""
    leading = len(raw) - len(raw.lstrip(".,;:!?\"'"))
    body = raw[leading:].rstrip(".,;:!?\"'")
    match = _INLINE_NAME_BIO_SUFFIX_RE.search(body)
    if match:
        return "", leading, leading + len(body)
    return body, leading, leading + len(body)


def _has_inline_name_bio_suffix(raw: str) -> bool:
    """Return True when a token contains an inline BIO NAME label artifact."""
    body = raw.lstrip(".,;:!?\"'").rstrip(".,;:!?\"'")
    return _INLINE_NAME_BIO_SUFFIX_RE.search(body) is not None


def _is_proper_noun_token(clean: str) -> bool:
    """Return True for title-cased tokens that can belong to a proper noun."""
    return (
        bool(clean)
        and clean[0].isupper()
        and not any(c.isdigit() for c in clean)
        and not _SPECIAL_CHARS_RE.search(clean)
        and clean.lower()
        not in (
            _NAME_STOPWORDS
            | _FIRST_PERSON
            | _THIRD_PERSON
            | _POSSIBLE_SENTENCE_STARTERS
            | _LABEL_HEADER_WORDS
            | _TITLE_PREFIXES
            | _JOB_TITLE_STOPWORDS
        )
    )


def _extract_entity_candidates(
    sentence: Sentence,
    max_tokens: int = 6,
    allow_connectors: bool = True,
) -> list[Candidate]:
    """Scan a sentence for proper-noun spans used by entity scoring.

    This shared candidate extractor keeps suffixes such as "Corporation",
    "City", or "Street" so the final scoring step can decide whether the span
    is a NAME, ORGANIZATION, or LOCATION.
    """
    candidates: list[Candidate] = []
    sentence_text, sent_offset = sentence["sentence"], sentence["start"]
    token_matches = list(re.finditer(r"\S+", sentence_text))
    i = 0

    while i < len(token_matches):
        token_match = token_matches[i]
        raw = token_match.group()
        if _has_inline_name_bio_suffix(raw):
            i += 1
            continue
        clean, clean_start, clean_end = _clean_name_token(raw)
        if not _is_proper_noun_token(clean):
            i += 1
            continue

        start_idx = i
        candidate_tokens = [clean]
        candidate_start = sent_offset + token_match.start() + clean_start
        candidate_end = sent_offset + token_match.start() + clean_end
        i += 1

        while i < len(token_matches) and len(candidate_tokens) < max_tokens:
            current_match = token_matches[i]
            current_raw = current_match.group()
            if _has_inline_name_bio_suffix(current_raw):
                break
            current_clean, current_start, current_end = _clean_name_token(current_raw)
            current_lower = current_clean.lower()

            if _is_proper_noun_token(current_clean):
                candidate_tokens.append(current_clean)
                candidate_end = sent_offset + current_match.start() + current_end
                i += 1
                continue

            if (
                allow_connectors
                and current_lower in _PROPER_NOUN_CONNECTORS
                and i + 1 < len(token_matches)
            ):
                next_raw = token_matches[i + 1].group()
                next_clean, _, _ = _clean_name_token(next_raw)
                if _is_proper_noun_token(next_clean):
                    candidate_tokens.append(current_clean)
                    candidate_end = sent_offset + current_match.start() + current_end
                    i += 1
                    continue

            break

        if candidate_tokens:
            candidates.append(
                {
                    "text": " ".join(candidate_tokens),
                    "start": candidate_start,
                    "end": candidate_end,
                }
            )

        if i == start_idx:
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


def _score_candidate(name: str, sentence: Sentence) -> tuple[int, bool]:
    """Score a PERSON NAME candidate in its sentence context.

    Returns (score, is_definitive).
    is_definitive=True means the NAME score should dominate the final
    NAME/ORGANIZATION/LOCATION decision for the same span.
    """
    score = 0
    sentence_text = sentence["sentence"]
    sent_lower = sentence_text.lower()
    name_lower = name.lower()

    for trigger in NAME_TRIGGERS | _LABEL_TRIGGERS:
        if trigger in sent_lower:
            idx = sent_lower.find(trigger)
            after = sentence_text[idx + len(trigger) :].strip().lstrip(":").strip()
            if after.lower().startswith(name_lower):
                return 100, True

    if re.search(r"\bI\s*,\s*" + re.escape(name), sentence_text, re.IGNORECASE):
        return 100, True
    if re.search(re.escape(name) + r"\s*,\s*I\b", sentence_text, re.IGNORECASE):
        return 100, True
    if re.search(r"\bI'?m\s+" + re.escape(name), sentence_text, re.IGNORECASE):
        return 100, True
    if re.search(r"\bI\s+am\s+" + re.escape(name), sentence_text, re.IGNORECASE):
        return 100, True
    if re.search(
        r"\bI\s+was\s+named\s+" + re.escape(name), sentence_text, re.IGNORECASE
    ):
        return 100, True

    if "my name" in sent_lower:
        score += 10

    if re.match(r"^\s*As\s+" + re.escape(name) + r"\s*,", sentence_text, re.IGNORECASE):
        score += 5

    if re.search(r":\s*\n?\s*" + re.escape(name), sentence_text, re.IGNORECASE):
        score += 5

    appos_m = re.search(
        re.escape(name) + r"\s*,\s*(\w+(?:\s+\w+)?)",
        sentence_text,
        re.IGNORECASE,
    )
    if appos_m:
        appos_words = appos_m.group(1).lower().split()
        if any(w in _JOB_HARDLIST or w in _JOB_TITLE_STOPWORDS for w in appos_words):
            score += 3

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

    if _has_job_in_sentence(sentence_text):
        score += 2

    if re.search(
        r"\b(?:Dr|Mr|Mrs|Ms|Prof)\.?\s+" + re.escape(name),
        sentence_text,
        re.IGNORECASE,
    ):
        score += 1

    return score, False


def _candidate_window(sentence_text: str, candidate: Candidate, sent_start: int) -> str:
    """Return nearby context around a sentence-relative candidate span."""
    rel_start = max(0, candidate["start"] - sent_start)
    rel_end = max(rel_start, candidate["end"] - sent_start)
    return sentence_text[max(0, rel_start - 40) : min(len(sentence_text), rel_end + 40)]


def _score_organization_candidate(candidate: Candidate, sentence: Sentence) -> int:
    """Score a proper-noun candidate as ORGANIZATION."""
    score = 0
    text = candidate["text"]
    words = [w.lower().rstrip(".") for w in text.split()]
    sentence_text = sentence["sentence"]
    sent_lower = sentence_text.lower()
    window = _candidate_window(sentence_text, candidate, sentence["start"]).lower()

    if words and words[-1] in _ORG_SUFFIXES:
        score += 8
    if any(w in _ORG_SUFFIXES for w in words):
        score += 3
    if any(trigger in sent_lower for trigger in ORG_TRIGGERS):
        score += 2
    if re.search(
        r"\b(?:at|for|by|from|joined|founded)\s+" + re.escape(text) + r"\b",
        sentence_text,
        re.IGNORECASE,
    ):
        score += 4
    if re.search(
        re.escape(text)
        + r"\s+(?:hired|employed|announced|released|opened|launched|acquired)\b",
        sentence_text,
        re.IGNORECASE,
    ):
        score += 4
    if any(trigger in window for trigger in {"company", "employer", "organization"}):
        score += 2
    if words and words[-1] in _LOCATION_SUFFIXES:
        score -= 4

    return score


def _score_location_candidate(candidate: Candidate, sentence: Sentence) -> int:
    """Score a proper-noun candidate as LOCATION.

    LOCATION is intentionally weaker than ADDRESS in overlap resolution. It
    catches place-like spans such as cities, districts, and named facilities
    when a full street address is not available.
    """
    score = 0
    text = candidate["text"]
    words = [w.lower().rstrip(".") for w in text.split()]
    sentence_text = sentence["sentence"]
    sent_lower = sentence_text.lower()
    window = _candidate_window(sentence_text, candidate, sentence["start"]).lower()

    if words and words[-1] in _LOCATION_SUFFIXES:
        score += 8
    if any(w in _LOCATION_SUFFIXES for w in words):
        score += 3
    if any(trigger in sent_lower for trigger in LOCATION_TRIGGERS):
        score += 1
    if re.search(
        r"\b(?:in|at|from|near|to|around|inside|outside)\s+" + re.escape(text) + r"\b",
        sentence_text,
        re.IGNORECASE,
    ):
        score += 4
    if re.search(
        r"\b(?:located|lives?|resides?|visited|visit)\s+(?:in|at|near|from)?\s*"
        + re.escape(text)
        + r"\b",
        sentence_text,
        re.IGNORECASE,
    ):
        score += 4
    if any(trigger in window for trigger in {"city", "district", "province", "state"}):
        score += 2
    if words and words[-1] in _ORG_SUFFIXES:
        score -= 4

    return score


def _extract_strong_name_candidates(ctx: DetectorContext) -> dict[tuple[int, int], int]:
    """Return NAME candidate spans from strong labels/triggers with fixed score."""
    text = ctx["text"]
    lower = ctx["lower"]
    strong_spans: dict[tuple[int, int], int] = {}

    for trigger in NAME_TRIGGERS | _LABEL_TRIGGERS:
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
                if token.endswith((".", "!", "?")):
                    break
                if len(name_tokens) == 4:
                    break

            if name_tokens and name_start is not None:
                name_text = " ".join(name_tokens)
                strong_spans[(name_start, name_start + len(name_text))] = 100

            search_start = trigger_pos + len(trigger)

    return strong_spans


def _score_entity_candidate(
    candidate: Candidate,
    sentence: Sentence,
    strong_name_scores: dict[tuple[int, int], int],
) -> ScoredCandidate | None:
    """Score NAME/ORGANIZATION/LOCATION and choose the final tag for a span."""
    span = (candidate["start"], candidate["end"])
    name_score, definitive_name = _score_candidate(candidate["text"], sentence)
    if span in strong_name_scores:
        name_score = max(name_score, strong_name_scores[span])
        definitive_name = True
    if definitive_name:
        name_score = max(name_score, 100)

    scores = {
        "NAME": name_score,
        "ORGANIZATION": _score_organization_candidate(candidate, sentence),
        "LOCATION": _score_location_candidate(candidate, sentence),
    }
    eligible = [
        (entity_type, score)
        for entity_type, score in scores.items()
        if score >= _ENTITY_SCORE_THRESHOLDS[entity_type]
    ]
    if not eligible:
        return None

    entity_type, score = min(
        eligible,
        key=lambda item: (-item[1], _ENTITY_SCORE_TIEBREAK[item[0]]),
    )
    return {
        "type": entity_type,
        "text": candidate["text"],
        "start": candidate["start"],
        "end": candidate["end"],
        "score": score,
    }


def _detect_scored_entity_context(
    ctx: DetectorContext,
    entity_types: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Detect NAME/ORGANIZATION/LOCATION using one shared scoring pipeline."""
    allowed_types = entity_types or {"NAME", "ORGANIZATION", "LOCATION"}
    strong_name_scores = _extract_strong_name_candidates(ctx)
    best_by_span: dict[tuple[int, int], ScoredCandidate] = {}

    for sent in ctx["sentences"]:
        for cand in _extract_entity_candidates(sent):
            scored = _score_entity_candidate(cand, sent, strong_name_scores)
            if scored is None or scored["type"] not in allowed_types:
                continue
            span = (scored["start"], scored["end"])
            existing = best_by_span.get(span)
            if existing is None or (
                scored["score"],
                -_ENTITY_SCORE_TIEBREAK[scored["type"]],
            ) > (
                existing["score"],
                -_ENTITY_SCORE_TIEBREAK[existing["type"]],
            ):
                best_by_span[span] = scored

    entities: list[dict[str, Any]] = []
    for scored in best_by_span.values():
        entity = _make_entity(
            scored["type"],
            scored["text"],
            scored["start"],
            scored["end"],
        )
        entity["_score"] = scored["score"]  # type: ignore[index]
        entities.append(entity)

    return entities


# ---------------------------------------------------------------------------
# Public detectors
# ---------------------------------------------------------------------------


def _make_entity(entity_type: str, text: str, start: int, end: int) -> dict[str, Any]:
    return {"type": entity_type, "text": text, "start": start, "end": end}


def _entity_span(entity: dict[str, Any]) -> tuple[int, int]:
    return entity["start"], entity["end"]


def _overlaps(start: int, end: int, other_start: int, other_end: int) -> bool:
    return start < other_end and end > other_start


def _overlaps_any_entity(entity: dict[str, Any], others: list[dict[str, Any]]) -> bool:
    start, end = _entity_span(entity)
    return any(_overlaps(start, end, other["start"], other["end"]) for other in others)


def _public_entity(entity: dict[str, Any]) -> Entity:
    return {
        "type": entity["type"],
        "text": entity["text"],
        "start": entity["start"],
        "end": entity["end"],
    }


def _resolve_entities(
    entities: list[dict[str, Any]],
    excluded_entities: list[dict[str, Any]] | None = None,
) -> list[Entity]:
    """Resolve duplicates and overlaps across detector outputs."""
    excluded = excluded_entities or []
    priority = {
        "ADDRESS": 0,
        "ORGANIZATION": 1,
        "LOCATION": 2,
        "USERNAME": 3,
        "NAME": 4,
    }
    sorted_entities = sorted(
        entities,
        key=lambda e: (
            priority.get(e["type"], 99),
            -int(e.get("_score", 0)),
            e["start"],
            -(e["end"] - e["start"]),
        ),
    )

    kept: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for entity in sorted_entities:
        key = (entity["type"], entity["start"], entity["end"])
        if key in seen:
            continue
        if _overlaps_any_entity(entity, excluded):
            continue
        if _overlaps_any_entity(entity, kept):
            continue
        seen.add(key)
        kept.append(entity)

    kept.sort(key=lambda e: (e["start"], e["end"]))
    return [_public_entity(entity) for entity in kept]


def _detect_name_context(ctx: DetectorContext) -> list[dict[str, Any]]:
    """Detect NAME spans using the shared scored-entity pipeline."""
    return _detect_scored_entity_context(ctx, {"NAME"})


def detect_name(text: str) -> list[Entity]:
    """Detect NAME spans from raw text."""
    return _resolve_entities(_detect_name_context(_build_context(text)))


def _detect_organization_context(ctx: DetectorContext) -> list[dict[str, Any]]:
    """Detect ORGANIZATION spans using the shared scored-entity pipeline."""
    return _detect_scored_entity_context(ctx, {"ORGANIZATION"})


def detect_organization(text: str) -> list[Entity]:
    """Detect ORGANIZATION spans from raw text."""
    return _resolve_entities(_detect_organization_context(_build_context(text)))


def _detect_location_context(ctx: DetectorContext) -> list[dict[str, Any]]:
    """Detect LOCATION spans using the shared scored-entity pipeline."""
    return _detect_scored_entity_context(ctx, {"LOCATION"})


def detect_location(text: str) -> list[Entity]:
    """Detect LOCATION spans from raw text."""
    return _resolve_entities(_detect_location_context(_build_context(text)))


def _detect_username_context(ctx: DetectorContext) -> list[dict[str, Any]]:
    """Detect USERNAME spans using shared detector context."""
    text = ctx["text"]
    lower = ctx["lower"]
    entities: list[dict[str, Any]] = []

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
                    entity = _make_entity("USERNAME", token, after, after + len(token))
                    entity["_score"] = 10  # type: ignore[index]
                    entities.append(entity)

            search_start = trigger_pos + len(trigger)

    return entities


def detect_username(text: str) -> list[Entity]:
    """Detect USERNAME spans from raw text."""
    return _resolve_entities(_detect_username_context(_build_context(text)))


def _detect_address_context(ctx: DetectorContext) -> list[dict[str, Any]]:
    """Detect ADDRESS spans using shared detector context."""
    text = ctx["text"]
    lower = ctx["lower"]
    entities: list[dict[str, Any]] = []
    email_spans = ctx["email_spans"]

    def _in_email(start: int, end: int) -> bool:
        return any(es <= start and end <= ee for es, ee in email_spans)

    # --- Primary: regex pattern (house number + street type) ---
    for m in _ADDRESS_RE.finditer(text):
        if _in_email(m.start(), m.end()):
            continue
        addr_text = m.group().strip()
        entity = _make_entity(
            "ADDRESS", addr_text, m.start(), m.start() + len(addr_text)
        )
        entity["_score"] = 20  # type: ignore[index]
        entities.append(entity)

    # --- Fallback: trigger keywords for addresses without street type ---
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

            value_start = end_of_trigger
            while value_start < len(text) and text[value_start] in " \t":
                value_start += 1
            if value_start < len(text) and text[value_start] == ":":
                value_start += 1
                clause_start = value_start
            elif lower[value_start : value_start + 3] == "is ":
                clause_start = value_start + 3
            else:
                search_start = trigger_pos + len(trigger)
                continue
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
                    entity = _make_entity(
                        "ADDRESS",
                        addr_text,
                        actual_start,
                        actual_start + len(addr_text),
                    )
                    entity["_score"] = 5  # type: ignore[index]
                    entities.append(entity)

            search_start = trigger_pos + len(trigger)

    return entities


def detect_address(text: str) -> list[Entity]:
    """Detect ADDRESS spans from raw text."""
    return _resolve_entities(_detect_address_context(_build_context(text)))


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


def detect_by_context(
    text: str, excluded_entities: list[dict[str, Any]] | None = None
) -> list[Entity]:
    """Run all context detectors from raw text and return resolved spans."""
    ctx = _build_context(text)
    entities: list[dict[str, Any]] = []
    entities.extend(_detect_scored_entity_context(ctx))
    entities.extend(_detect_username_context(ctx))
    entities.extend(_detect_address_context(ctx))
    return _resolve_entities(entities, excluded_entities)
