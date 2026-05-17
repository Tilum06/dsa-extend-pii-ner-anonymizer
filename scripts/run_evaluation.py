"""Run the evaluation pipeline and produce metrics.

Usage:
    python scripts/run_evaluation.py \
        --input data/processed/processed_data.json \
        --predictions results/predictions.json \
        --output results/evaluation_result.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path so `src` package can be imported.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.evaluator import compute_precision_recall_f1


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate PII detection predictions against ground truth.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/processed_data.json",
        help="Path to the processed JSON dataset with ground truth (default: data/processed/processed_data.json)",
    )
    parser.add_argument(
        "--predictions",
        type=str,
        default="results/predictions.json",
        help="Path to the predictions JSON file (default: results/predictions.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/evaluation_result.csv",
        help="Path for the evaluation result CSV (default: results/evaluation_result.csv)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array from *path*."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_single_sample(
    predicted: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate one sample with the project evaluator."""
    return compute_precision_recall_f1(predicted, ground_truth)


# ---------------------------------------------------------------------------
# Core evaluation logic
# ---------------------------------------------------------------------------

def run_evaluation(
    samples: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Match samples by id and aggregate metrics.

    Returns a dict with total_tp, total_fp, total_fn, precision, recall, f1.
    """
    # Build lookup: id -> predicted_entities
    pred_map: dict[Any, list[dict[str, Any]]] = {}
    for pred in predictions:
        pred_map[pred["id"]] = pred.get("predicted_entities", [])

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for sample in samples:
        sample_id = sample.get("id")
        ground_truth = sample.get("ground_truth", [])
        predicted = pred_map.get(sample_id, [])

        metrics = evaluate_single_sample(predicted, ground_truth)

        total_tp += metrics.get("tp", 0)
        total_fp += metrics.get("fp", 0)
        total_fn += metrics.get("fn", 0)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "TP": total_tp,
        "FP": total_fp,
        "FN": total_fn,
        "Precision": round(precision, 4),
        "Recall": round(recall, 4),
        "F1": round(f1, 4),
    }


def save_evaluation_csv(metrics: dict[str, Any], path: Path) -> None:
    """Write evaluation metrics to a CSV file with Metric,Value columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Value"])
        for metric, value in metrics.items():
            writer.writerow([metric, value])


def main() -> None:
    """Run the full evaluation pipeline."""
    args = parse_args()

    input_path = Path(args.input)
    predictions_path = Path(args.predictions)
    output_path = Path(args.output)

    # --- Step 1: Load data ---
    print(f"[1/3] Loading processed data from: {input_path}")
    samples = load_json(input_path)
    print(f"      Loaded {len(samples)} samples with ground truth.")

    print(f"      Loading predictions from: {predictions_path}")
    predictions = load_json(predictions_path)
    print(f"      Loaded {len(predictions)} prediction records.")

    # --- Step 2: Evaluate ---
    print("[2/3] Evaluating predictions ...")
    metrics = run_evaluation(samples, predictions)

    print()
    print("      +------------------------------+")
    print("      |    Evaluation Results         |")
    print("      +--------------+---------------+")
    print("      | Metric       | Value         |")
    print("      +--------------+---------------+")
    for key, val in metrics.items():
        print(f"      | {key:<12s} | {str(val):>13s} |")
    print("      +--------------+---------------+")
    print()

    # --- Step 3: Save CSV ---
    print(f"[3/3] Saving evaluation results to: {output_path}")
    save_evaluation_csv(metrics, output_path)
    print("      Done.")


if __name__ == "__main__":
    main()
