"""Measure rule-based detector accuracy on the raw PII CSV dataset.

Run from the repository root:

    python tests/test_rule_based_accuracy.py

The script compares detected NAME, EMAIL, PHONE, and URL values against the
corresponding columns in data/raw/pii_dataset.csv.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.context_detector import detect_by_context
from src.merger import merge_entities
from src.regex_detector import detect_regex_entities


ENTITY_COLUMNS = {
    "NAME": "name",
    "EMAIL": "email",
    "PHONE": "phone",
    "URL": "url",
}

TRAILING_PUNCT = ".,;:!?)]}\"'"


def normalize_value(entity_type: str, value: str) -> str:
    """Normalize values before comparing CSV ground truth and predictions."""
    value = str(value or "").strip().strip(TRAILING_PUNCT)
    value = re.sub(r"\s+", " ", value)

    if entity_type == "PHONE":
        return re.sub(r"\D+", "", value)

    if entity_type in {"EMAIL", "URL"}:
        return value.lower()

    return value.lower()


def load_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    if limit is not None:
        return rows[:limit]

    return rows


def detect_target_entities(text: str) -> list[dict[str, Any]]:
    """Run the project detector pipeline and keep target entity types only."""
    regex_entities = detect_regex_entities(text)
    context_entities = detect_by_context(text, excluded_entities=regex_entities)
    entities = merge_entities(regex_entities, context_entities)
    return [entity for entity in entities if entity["type"] in ENTITY_COLUMNS]


def evaluate(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, int]], list[str]]:
    stats: dict[str, dict[str, int]] = {
        entity_type: defaultdict(int) for entity_type in ENTITY_COLUMNS
    }
    misses: list[str] = []

    for row_index, row in enumerate(rows, start=1):
        text = row.get("text", "")
        document_id = row.get("document", str(row_index))
        detected = detect_target_entities(text)

        predicted_by_type: dict[str, set[str]] = {
            entity_type: set() for entity_type in ENTITY_COLUMNS
        }
        for entity in detected:
            entity_type = entity["type"]
            normalized = normalize_value(entity_type, entity["text"])
            if normalized:
                predicted_by_type[entity_type].add(normalized)

        for entity_type, column in ENTITY_COLUMNS.items():
            expected = normalize_value(entity_type, row.get(column, ""))
            predicted = predicted_by_type[entity_type]

            if expected:
                stats[entity_type]["support"] += 1
                if expected in predicted:
                    stats[entity_type]["correct"] += 1
                    stats[entity_type]["tp"] += 1
                else:
                    stats[entity_type]["fn"] += 1
                    expected_raw = row.get(column, "")
                    predicted_raw = [
                        entity["text"]
                        for entity in detected
                        if entity["type"] == entity_type
                    ]
                    misses.append(
                        f"{document_id} {entity_type}: expected={expected_raw!r}, "
                        f"predicted={predicted_raw!r}"
                    )

                false_positive_count = len(predicted - {expected})
            else:
                false_positive_count = len(predicted)

            stats[entity_type]["fp"] += false_positive_count

    return stats, misses


def safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def print_report(stats: dict[str, dict[str, int]], total_rows: int) -> None:
    print(f"Evaluated rows: {total_rows}")
    print()
    print(
        f"{'Entity':<8} {'Support':>8} {'Correct':>8} {'Accuracy':>10} "
        f"{'Precision':>10} {'Recall':>10} {'F1':>10} {'FP':>6} {'FN':>6}"
    )
    print("-" * 86)

    total_support = 0
    total_correct = 0
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for entity_type in ENTITY_COLUMNS:
        item = stats[entity_type]
        support = int(item["support"])
        correct = int(item["correct"])
        tp = int(item["tp"])
        fp = int(item["fp"])
        fn = int(item["fn"])

        accuracy = safe_ratio(correct, support)
        precision = safe_ratio(tp, tp + fp)
        recall = safe_ratio(tp, tp + fn)
        f1 = safe_ratio(2 * tp, 2 * tp + fp + fn)

        total_support += support
        total_correct += correct
        total_tp += tp
        total_fp += fp
        total_fn += fn

        print(
            f"{entity_type:<8} {support:>8} {correct:>8} {accuracy:>9.2%} "
            f"{precision:>9.2%} {recall:>9.2%} {f1:>9.2%} {fp:>6} {fn:>6}"
        )

    print("-" * 86)
    overall_accuracy = safe_ratio(total_correct, total_support)
    overall_precision = safe_ratio(total_tp, total_tp + total_fp)
    overall_recall = safe_ratio(total_tp, total_tp + total_fn)
    overall_f1 = safe_ratio(2 * total_tp, 2 * total_tp + total_fp + total_fn)
    print(
        f"{'OVERALL':<8} {total_support:>8} {total_correct:>8} "
        f"{overall_accuracy:>9.2%} {overall_precision:>9.2%} "
        f"{overall_recall:>9.2%} {overall_f1:>9.2%} "
        f"{total_fp:>6} {total_fn:>6}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate rule-based NAME/EMAIL/PHONE/URL detection accuracy."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=ROOT_DIR / "data" / "raw" / "pii_dataset.csv",
        help="Path to pii_dataset.csv.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Evaluate only the first N rows.",
    )
    parser.add_argument(
        "--show-misses",
        type=int,
        default=0,
        help="Print up to N missed expected values.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.csv, args.limit)
    stats, misses = evaluate(rows)
    print_report(stats, len(rows))

    if args.show_misses:
        print()
        print(f"First {min(args.show_misses, len(misses))} misses:")
        for miss in misses[: args.show_misses]:
            print(f"- {miss}")


if __name__ == "__main__":
    main()
