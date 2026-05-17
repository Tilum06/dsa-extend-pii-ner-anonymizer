# Project Summary

This project is a rule-based PII detection and anonymization pipeline. It focuses
on deterministic text processing rather than machine learning. The main goal is
to identify sensitive entities in raw text, merge overlapping detections, and
replace them with anonymized placeholders.

## Core Flow

1. Raw text is passed into detector modules.
2. Regex detectors find structured PII such as email, phone number, and URL.
3. Context detectors find entities that need surrounding text, such as name,
   username, and address.
4. The merger resolves overlaps and combines detector outputs.
5. The anonymizer replaces detected spans in the original text.

## Main Modules

- `src/tokenizer.py`: tokenizes text with whitespace splitting for dataset compatibility.
- `src/regex_detector.py`: detects structured PII with regular expressions.
- `src/context_detector.py`: detects NAME, USERNAME, and ADDRESS from raw text.
- `src/merger.py`: merges entity lists and resolves conflicts.
- `src/anonymizer.py`: replaces detected entities with anonymized labels.
- `scripts/run_detection.py`: runs the detection pipeline over input data.
- `web/app.py`: provides a simple web demo.

## Context Detector API

The public context detector API accepts raw text directly:

```python
from src.context_detector import detect_by_context

entities = detect_by_context(raw_text)
```

Callers do not need to split sentences, lowercase text, tokenize text, or
pre-filter email spans. `detect_by_context()` builds a shared preprocessing
context internally and passes it to the individual detectors.

Available public functions:

- `detect_name(text)`
- `detect_username(text)`
- `detect_address(text)`
- `detect_by_context(text, excluded_entities=None)`

`excluded_entities` can be used to prevent context detections from overlapping
entities already found by another detector, such as EMAIL or URL.

## Design Direction

The detector layer should keep this boundary:

- Public functions accept raw input.
- Internal helpers operate on structured context objects.
- Entity outputs use a consistent shape: `type`, `text`, `start`, `end`.
- Overlap handling belongs in resolver/merger logic, not in callers.

This keeps the project easy to moduleize later. The current
`context_detector.py` already has a shared `DetectorContext` internally; the next
clean split would be moving name, username, address, shared types, and resolver
logic into separate files under a `context_detector/` package.
