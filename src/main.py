"""Entry point for the rule-based PII detection pipeline."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .anonymizer import anonymize_text
from .config import PROCESSED_DATA_PATH
from .context_detector import detect_by_context
from .evaluator import compute_precision_recall_f1
from .merger import merge_entities
from .regex_detector import detect_regex_entities

RESULTS_DIR = Path("results")
PREDICTIONS_PATH = RESULTS_DIR / "predictions.json"
ANONYMIZED_PATH = RESULTS_DIR / "anonymized_output.json"
EVALUATION_PATH = RESULTS_DIR / "evaluation_result.csv"


def load_json(path: str | Path) -> list[dict[str, Any]]:
    """Load a JSON array from disk."""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(records: list[dict[str, Any]], path: str | Path) -> None:
    """Write JSON records to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)


def save_evaluation_csv(metrics: dict[str, int | float], path: str | Path) -> None:
    """Write aggregate metrics to CSV."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Metric", "Value"])
        for key, value in metrics.items():
            writer.writerow([key, value])


def run_pipeline(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Run detection, merging, anonymization, and aggregate evaluation."""
    predictions: list[dict[str, Any]] = []
    anonymized_outputs: list[dict[str, Any]] = []

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for index, sample in enumerate(samples, start=1):
        sample_id = sample.get("id", index)
        text = sample.get("text", "")

        regex_entities = detect_regex_entities(text)
        context_entities = detect_by_context(text, excluded_entities=regex_entities)
        final_entities = merge_entities(regex_entities, context_entities)

        predictions.append(
            {
                "id": sample_id,
                "predicted_entities": final_entities,
            }
        )
        anonymized_outputs.append(
            {
                "id": sample_id,
                "original_text": text,
                "anonymized_text": anonymize_text(text, final_entities),
            }
        )

        metrics = compute_precision_recall_f1(
            final_entities,
            sample.get("ground_truth", []),
        )
        total_tp += int(metrics["tp"])
        total_fp += int(metrics["fp"])
        total_fn += int(metrics["fn"])

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "predictions": predictions,
        "anonymized_outputs": anonymized_outputs,
        "metrics": {
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
    }


def main() -> None:
    """Run the full project pipeline using the processed dataset."""
    samples = load_json(PROCESSED_DATA_PATH)
    result = run_pipeline(samples)

    save_json(result["predictions"], PREDICTIONS_PATH)
    save_json(result["anonymized_outputs"], ANONYMIZED_PATH)
    save_evaluation_csv(result["metrics"], EVALUATION_PATH)

    print(f"Processed {len(samples)} samples")
    print(f"Saved predictions to {PREDICTIONS_PATH}")
    print(f"Saved anonymized output to {ANONYMIZED_PATH}")
    print(f"Saved evaluation metrics to {EVALUATION_PATH}")


if __name__ == "__main__":
    main()
