"""Evaluation helpers for exact-span entity metrics."""

from __future__ import annotations

from typing import Any


def compute_precision_recall_f1(
    predicted: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> dict[str, int | float]:
    """Compute entity-level precision, recall, and F1 for one sample."""
    pred_keys = {(e["type"], e["start"], e["end"]) for e in predicted}
    gold_keys = {(e["type"], e["start"], e["end"]) for e in ground_truth}

    tp = len(pred_keys & gold_keys)
    fp = len(pred_keys - gold_keys)
    fn = len(gold_keys - pred_keys)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_predictions(samples: list[dict[str, Any]]) -> dict[str, int | float]:
    """Aggregate metrics for records with predicted_entities and ground_truth."""
    total_tp = 0
    total_fp = 0
    total_fn = 0

    for sample in samples:
        metrics = compute_precision_recall_f1(
            sample.get("predicted_entities", []),
            sample.get("ground_truth", []),
        )
        total_tp += int(metrics["tp"])
        total_fp += int(metrics["fp"])
        total_fn += int(metrics["fn"])

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }
