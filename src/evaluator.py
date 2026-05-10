"""Evaluation helpers for prediction quality metrics."""

from __future__ import annotations

from typing import Any


def compute_precision_recall_f1(
    predicted: list[dict[str, Any]],
    ground_truth: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute evaluation metrics for entity detection."""
    raise NotImplementedError


def evaluate_predictions(samples: list[dict[str, Any]]) -> dict[str, float]:
    """Evaluate a batch of anonymization or detection results."""
    raise NotImplementedError
