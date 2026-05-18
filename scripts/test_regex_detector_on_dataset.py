"""Evaluate the regex detector (EMAIL, PHONE, URL) against ground truth.

Usage:
    python scripts/test_regex_detector_on_dataset.py \
        --input data/processed/processed_data.json \
        --output results/regex_detector_evaluation.csv \
        --errors results/regex_detector_errors.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure project root is importable
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.regex_detector import detect_regex_entities

# Only these entity types belong to Person 2 (regex detector).
_TARGET_TYPES = {"EMAIL", "PHONE", "URL"}

# Cap on error examples saved to JSON (to keep the file manageable).
_MAX_ERROR_EXAMPLES = 50


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate regex detector on processed dataset.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/processed_data.json",
        help="Path to processed dataset JSON (default: data/processed/processed_data.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/regex_detector_evaluation.csv",
        help="Path for evaluation CSV (default: results/regex_detector_evaluation.csv)",
    )
    parser.add_argument(
        "--errors",
        type=str,
        default="results/regex_detector_errors.json",
        help="Path for error examples JSON (default: results/regex_detector_errors.json)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entity_key(entity: dict[str, Any]) -> tuple[str, int, int]:
    """Hashable key for exact-span matching: (type, start, end)."""
    return (entity["type"], entity["start"], entity["end"])


def _filter_types(
    entities: list[dict[str, Any]],
    allowed: set[str],
) -> list[dict[str, Any]]:
    """Keep only entities whose type is in *allowed*."""
    return [e for e in entities if e.get("type") in allowed]


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def compute_metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    """Return precision, recall, F1 from raw counts."""
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


# ---------------------------------------------------------------------------
# Core evaluation
# ---------------------------------------------------------------------------

def evaluate_on_dataset(
    samples: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],      # per-type metrics
    dict[str, Any],                  # overall metrics
    list[dict[str, Any]],            # error examples
]:
    """Run detect_regex_entities on every sample, compare to ground truth.

    Returns
    -------
    per_type : dict mapping entity type -> {tp, fp, fn, precision, recall, f1}
    overall  : dict with aggregated {tp, fp, fn, precision, recall, f1}
    errors   : list of error example dicts (capped at _MAX_ERROR_EXAMPLES)
    """
    # Counters per entity type
    counts: dict[str, dict[str, int]] = {
        t: {"tp": 0, "fp": 0, "fn": 0} for t in _TARGET_TYPES
    }
    errors: list[dict[str, Any]] = []

    total = len(samples)

    for idx, sample in enumerate(samples, start=1):
        sample_id = sample.get("id", idx)
        text: str = sample.get("text", "")

        # --- Predict ---
        predicted_all = detect_regex_entities(text)
        predicted = _filter_types(predicted_all, _TARGET_TYPES)

        # --- Ground truth (only our types) ---
        gt_all = sample.get("ground_truth", [])
        ground_truth = _filter_types(gt_all, _TARGET_TYPES)

        # --- Exact-span matching ---
        pred_keys = {_entity_key(e) for e in predicted}
        gt_keys = {_entity_key(e) for e in ground_truth}

        tp_keys = pred_keys & gt_keys
        fp_keys = pred_keys - gt_keys
        fn_keys = gt_keys - pred_keys

        # Accumulate per-type
        for key in tp_keys:
            etype = key[0]
            counts[etype]["tp"] += 1
        for key in fp_keys:
            etype = key[0]
            counts[etype]["fp"] += 1
        for key in fn_keys:
            etype = key[0]
            counts[etype]["fn"] += 1

        # --- Collect error examples ---
        if (fp_keys or fn_keys) and len(errors) < _MAX_ERROR_EXAMPLES:
            fp_entities = [e for e in predicted if _entity_key(e) in fp_keys]
            fn_entities = [e for e in ground_truth if _entity_key(e) in fn_keys]
            errors.append({
                "sample_id": sample_id,
                "text": text[:500],  # truncate very long texts
                "false_positives": fp_entities,
                "false_negatives": fn_entities,
                "predicted_entities": predicted,
                "ground_truth_entities": ground_truth,
            })

        if idx % 500 == 0 or idx == total:
            print(f"  Processed {idx}/{total} samples ...")

    # --- Compute per-type metrics ---
    per_type: dict[str, dict[str, Any]] = {}
    for etype in sorted(_TARGET_TYPES):
        c = counts[etype]
        m = compute_metrics(c["tp"], c["fp"], c["fn"])
        per_type[etype] = {"tp": c["tp"], "fp": c["fp"], "fn": c["fn"], **m}

    # --- Compute overall metrics ---
    total_tp = sum(c["tp"] for c in counts.values())
    total_fp = sum(c["fp"] for c in counts.values())
    total_fn = sum(c["fn"] for c in counts.values())
    overall_m = compute_metrics(total_tp, total_fp, total_fn)
    overall = {"tp": total_tp, "fp": total_fp, "fn": total_fn, **overall_m}

    return per_type, overall, errors


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_metrics(
    per_type: dict[str, dict[str, Any]],
    overall: dict[str, Any],
) -> None:
    header = f"  {'Entity':<10s} {'TP':>6s} {'FP':>6s} {'FN':>6s} {'Prec':>8s} {'Recall':>8s} {'F1':>8s}"
    sep = "  " + "-" * 56
    print()
    print(header)
    print(sep)
    for etype in sorted(per_type):
        m = per_type[etype]
        print(
            f"  {etype:<10s} {m['tp']:>6d} {m['fp']:>6d} {m['fn']:>6d}"
            f" {m['precision']:>8.4f} {m['recall']:>8.4f} {m['f1']:>8.4f}"
        )
    print(sep)
    print(
        f"  {'Overall':<10s} {overall['tp']:>6d} {overall['fp']:>6d} {overall['fn']:>6d}"
        f" {overall['precision']:>8.4f} {overall['recall']:>8.4f} {overall['f1']:>8.4f}"
    )
    print()


def save_csv(
    per_type: dict[str, dict[str, Any]],
    overall: dict[str, Any],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Entity", "TP", "FP", "FN", "Precision", "Recall", "F1"])
        for etype in sorted(per_type):
            m = per_type[etype]
            writer.writerow([
                etype, m["tp"], m["fp"], m["fn"],
                m["precision"], m["recall"], m["f1"],
            ])
        writer.writerow([
            "Overall", overall["tp"], overall["fp"], overall["fn"],
            overall["precision"], overall["recall"], overall["f1"],
        ])


def save_errors(errors: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(errors, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    errors_path = Path(args.errors)

    # --- Load ---
    print(f"[1/4] Loading processed data from: {input_path}")
    with input_path.open("r", encoding="utf-8") as f:
        samples: list[dict[str, Any]] = json.load(f)
    print(f"      Loaded {len(samples)} samples.")

    # --- Evaluate ---
    print("[2/4] Running regex detector and evaluating ...")
    per_type, overall, errors = evaluate_on_dataset(samples)

    # --- Print ---
    print("[3/4] Results:")
    print_metrics(per_type, overall)

    # --- Save ---
    print(f"[4/4] Saving evaluation CSV to: {output_path}")
    save_csv(per_type, overall, output_path)

    print(f"      Saving error examples ({len(errors)} samples) to: {errors_path}")
    save_errors(errors, errors_path)

    print("      Done.")


if __name__ == "__main__":
    main()
