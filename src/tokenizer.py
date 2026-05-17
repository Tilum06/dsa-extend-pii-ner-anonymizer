"""Tokenizer module for PII text dataset.

Input file format:
    document,text

Output file format:
    document,text,tokens

The Kaggle PII dataset's original `tokens` column is equivalent to
whitespace tokenization with `text.split()`, so this module uses the same
rule to reproduce that format.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def tokenize_text(text: str) -> list[str]:
    """Tokenize raw text into the same style as the original dataset tokens.

    The original PII dataset keeps punctuation attached to words when there is
    no whitespace separator. For example:
        "Popova," -> "Popova,"
        "experience." -> "experience."

    Therefore, whitespace splitting is the correct tokenizer for matching the
    dataset token format.
    """
    if text is None:
        return []
    return str(text).split()


def tokenize_records(records: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Tokenize the text field of each record."""
    output: list[dict[str, str]] = []

    for row in records:
        document = row.get("document", "")
        text = row.get("text", "")
        tokens = tokenize_text(text)

        output.append(
            {
                "document": document,
                "text": text,
                "tokens": repr(tokens),
            }
        )

    return output


def tokenize_csv(input_path: str | Path, output_path: str | Path) -> None:
    """Read a CSV with document/text columns and save document/text/tokens."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("Input CSV has no header.")

        required_columns = {"document", "text"}
        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        tokenized_rows = tokenize_records(reader)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["document", "text", "tokens"])
        writer.writeheader()
        writer.writerows(tokenized_rows)


def main() -> None:
    tokenize_csv("data/raw/pii_text.csv", "data/processed/tokenized.csv")


if __name__ == "__main__":
    main()
