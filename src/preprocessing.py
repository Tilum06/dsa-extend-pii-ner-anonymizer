"""Preprocessing helpers for loading and preparing the dataset."""

from __future__ import annotations

import ast
import csv
import json
import re
from pathlib import Path
from typing import Any

from .config import PROCESSED_DATA_PATH, RAW_DATA_PATH


LABEL_MAPPING = {
    "NAME_STUDENT": "NAME",
    "EMAIL": "EMAIL",
    "PHONE_NUM": "PHONE",
    "STREET_ADDRESS": "ADDRESS",
    "USERNAME": "USERNAME",
    "URL_PERSONAL": "URL",
}


def load_raw_dataset(path: str | Path = RAW_DATA_PATH) -> list[dict[str, Any]]:
    """Load the raw CSV dataset into memory."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Raw dataset not found: {path}")

    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            rows.append(dict(row))

    return rows


def parse_list_cell(value: Any) -> list[str]:
    """Parse a CSV cell containing a list-like string into a Python list."""
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    value = str(value).strip()

    if value == "":
        return []

    try:
        parsed = ast.literal_eval(value)

        if isinstance(parsed, list):
            return [str(item) for item in parsed]

    except (ValueError, SyntaxError):
        pass

    # Fallback đơn giản nếu cell không đúng dạng Python list.
    return [item.strip() for item in value.split(",") if item.strip()]


def normalize_text(text: str) -> str:
    """Normalize input text before detection."""
    if text is None:
        return ""

    text = str(text)

    # Chuẩn hóa newline và tab.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")

    # Xóa khoảng trắng thừa ở cuối dòng nhưng không phá toàn bộ cấu trúc text.
    text = "\n".join(line.rstrip() for line in text.split("\n"))

    return text.strip()


def map_bio_label(label: str) -> str | None:
    """Map one BIO label from the dataset to the project entity type."""
    if not label or label == "O":
        return None

    label = str(label).strip()

    if "-" not in label:
        return None

    prefix, raw_type = label.split("-", 1)

    if prefix not in {"B", "I"}:
        return None

    return LABEL_MAPPING.get(raw_type)


def _find_token_span(text: str, token: str, search_start: int) -> tuple[int, int]:
    """Find token span in text from search_start."""
    start = text.find(token, search_start)

    if start == -1:
        # Fallback: tìm token bằng regex escaped.
        match = re.search(re.escape(token), text[search_start:])
        if match is None:
            return search_start, search_start + len(token)

        start = search_start + match.start()

    end = start + len(token)
    return start, end


def bio_labels_to_entities(
    tokens: list[str],
    labels: list[str],
    text: str | None = None,
) -> list[dict[str, Any]]:
    """Convert BIO labels into entity spans."""
    if len(tokens) != len(labels):
        raise ValueError(
            f"tokens and labels must have the same length, "
            f"got {len(tokens)} tokens and {len(labels)} labels"
        )

    if text is None:
        text = " ".join(tokens)

    entities: list[dict[str, Any]] = []

    current_type: str | None = None
    current_start: int | None = None
    current_end: int | None = None

    search_pos = 0

    for token, label in zip(tokens, labels):
        token_start, token_end = _find_token_span(text, token, search_pos)
        search_pos = token_end

        mapped_type = map_bio_label(label)

        is_begin = str(label).startswith("B-")
        is_inside = str(label).startswith("I-")

        if mapped_type is None:
            if current_type is not None:
                entities.append(
                    {
                        "type": current_type,
                        "text": text[current_start:current_end],
                        "start": current_start,
                        "end": current_end,
                    }
                )

            current_type = None
            current_start = None
            current_end = None
            continue

        if is_begin or current_type != mapped_type:
            if current_type is not None:
                entities.append(
                    {
                        "type": current_type,
                        "text": text[current_start:current_end],
                        "start": current_start,
                        "end": current_end,
                    }
                )

            current_type = mapped_type
            current_start = token_start
            current_end = token_end

        elif is_inside and current_type == mapped_type:
            current_end = token_end

    if current_type is not None:
        entities.append(
            {
                "type": current_type,
                "text": text[current_start:current_end],
                "start": current_start,
                "end": current_end,
            }
        )

    return entities


def build_processed_record(raw_row: dict[str, Any]) -> dict[str, Any]:
    """Build one processed record from one raw sample."""
    document_id = raw_row.get("document", "")

    try:
        document_id = int(document_id)
    except (TypeError, ValueError):
        pass

    text = normalize_text(raw_row.get("text", ""))
    tokens = parse_list_cell(raw_row.get("tokens", ""))
    labels = parse_list_cell(raw_row.get("labels", ""))

    ground_truth = bio_labels_to_entities(tokens=tokens, labels=labels, text=text)

    return {
        "id": document_id,
        "text": text,
        "tokens": tokens,
        "ground_truth": ground_truth,
    }


def build_processed_dataset(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build all processed records from raw samples."""
    records: list[dict[str, Any]] = []

    for raw_row in raw_rows:
        records.append(build_processed_record(raw_row))

    return records


def save_processed_dataset(
    records: list[dict[str, Any]],
    output_path: str | Path = PROCESSED_DATA_PATH,
) -> None:
    """Write processed records to disk."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)