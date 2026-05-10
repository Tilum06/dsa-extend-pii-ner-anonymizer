"""Tests for evaluator module."""

import pytest
from src.evaluator import (
    compute_precision_recall_f1,
    evaluate_predictions,
)


class TestComputePrecisionRecallF1:
    """Test cases for compute_precision_recall_f1 function."""

    def test_compute_metrics_perfect_match(self):
        """Test metrics with perfect prediction."""
        predicted = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 10,
                "end": 26
            }
        ]
        ground_truth = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 10,
                "end": 26
            }
        ]
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_compute_metrics_partial_match(self):
        """Test metrics with partial matches."""
        predicted = [
            {"type": "EMAIL", "start": 10, "end": 26},
            {"type": "PHONE", "start": 30, "end": 40},
        ]
        ground_truth = [
            {"type": "EMAIL", "start": 10, "end": 26},
        ]
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)
        assert 0 <= result["precision"] <= 1
        assert 0 <= result["recall"] <= 1
        assert 0 <= result["f1"] <= 1

    def test_compute_metrics_no_predictions(self):
        """Test metrics when no predictions."""
        predicted = []
        ground_truth = [
            {"type": "EMAIL", "start": 10, "end": 26},
        ]
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0

    def test_compute_metrics_no_ground_truth(self):
        """Test metrics when no ground truth."""
        predicted = [
            {"type": "EMAIL", "start": 10, "end": 26},
        ]
        ground_truth = []
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)

    def test_compute_metrics_empty_predictions(self):
        """Test metrics with empty lists."""
        result = compute_precision_recall_f1([], [])
        
        assert isinstance(result, dict)
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result

    def test_compute_metrics_wrong_type_match(self):
        """Test metrics when entity type doesn't match."""
        predicted = [
            {"type": "NAME", "start": 10, "end": 26},
        ]
        ground_truth = [
            {"type": "EMAIL", "start": 10, "end": 26},
        ]
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)
        # Should not match due to type mismatch
        assert result["precision"] == 0.0 or result["recall"] == 0.0

    def test_compute_metrics_position_mismatch(self):
        """Test metrics when positions don't match exactly."""
        predicted = [
            {"type": "EMAIL", "start": 10, "end": 25},
        ]
        ground_truth = [
            {"type": "EMAIL", "start": 10, "end": 26},
        ]
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)

    def test_compute_metrics_multiple_entities(self):
        """Test metrics with multiple entities."""
        predicted = [
            {"type": "EMAIL", "start": 10, "end": 26},
            {"type": "PHONE", "start": 30, "end": 40},
            {"type": "NAME", "start": 0, "end": 8},
        ]
        ground_truth = [
            {"type": "EMAIL", "start": 10, "end": 26},
            {"type": "PHONE", "start": 30, "end": 40},
        ]
        result = compute_precision_recall_f1(predicted, ground_truth)
        
        assert isinstance(result, dict)
        assert 0 <= result["precision"] <= 1
        assert 0 <= result["recall"] <= 1


class TestEvaluatePredictions:
    """Test cases for evaluate_predictions function."""

    def test_evaluate_predictions_single_sample(self):
        """Test evaluating single sample."""
        samples = [
            {
                "text": "john@example.com",
                "predicted": [
                    {"type": "EMAIL", "start": 0, "end": 16}
                ],
                "ground_truth": [
                    {"type": "EMAIL", "start": 0, "end": 16}
                ]
            }
        ]
        result = evaluate_predictions(samples)
        
        assert isinstance(result, dict)
        assert "precision" in result
        assert "recall" in result
        assert "f1" in result

    def test_evaluate_predictions_multiple_samples(self):
        """Test evaluating multiple samples."""
        samples = [
            {
                "text": "Email: john@example.com",
                "predicted": [
                    {"type": "EMAIL", "start": 7, "end": 23}
                ],
                "ground_truth": [
                    {"type": "EMAIL", "start": 7, "end": 23}
                ]
            },
            {
                "text": "Phone: 555-1234",
                "predicted": [
                    {"type": "PHONE", "start": 7, "end": 15}
                ],
                "ground_truth": [
                    {"type": "PHONE", "start": 7, "end": 15}
                ]
            }
        ]
        result = evaluate_predictions(samples)
        
        assert isinstance(result, dict)
        assert isinstance(result.get("precision"), (int, float))
        assert isinstance(result.get("recall"), (int, float))
        assert isinstance(result.get("f1"), (int, float))

    def test_evaluate_predictions_empty_samples(self):
        """Test evaluating empty sample list."""
        result = evaluate_predictions([])
        
        assert isinstance(result, dict)

    def test_evaluate_predictions_no_matches(self):
        """Test evaluating samples with no correct predictions."""
        samples = [
            {
                "text": "john@example.com",
                "predicted": [
                    {"type": "NAME", "start": 0, "end": 16}
                ],
                "ground_truth": [
                    {"type": "EMAIL", "start": 0, "end": 16}
                ]
            }
        ]
        result = evaluate_predictions(samples)
        
        assert isinstance(result, dict)

    def test_evaluate_predictions_all_correct(self):
        """Test evaluating samples with all correct predictions."""
        samples = [
            {
                "text": "john@example.com and 555-1234",
                "predicted": [
                    {"type": "EMAIL", "start": 0, "end": 16},
                    {"type": "PHONE", "start": 21, "end": 29}
                ],
                "ground_truth": [
                    {"type": "EMAIL", "start": 0, "end": 16},
                    {"type": "PHONE", "start": 21, "end": 29}
                ]
            }
        ]
        result = evaluate_predictions(samples)
        
        assert isinstance(result, dict)
        if result.get("precision") is not None:
            assert 0 <= result["precision"] <= 1

    def test_evaluate_predictions_partial_matches(self):
        """Test evaluating samples with partial matches."""
        samples = [
            {
                "text": "john@example.com",
                "predicted": [
                    {"type": "EMAIL", "start": 0, "end": 16},
                    {"type": "NAME", "start": 0, "end": 4}
                ],
                "ground_truth": [
                    {"type": "EMAIL", "start": 0, "end": 16}
                ]
            }
        ]
        result = evaluate_predictions(samples)
        
        assert isinstance(result, dict)

    def test_evaluate_predictions_returns_dict(self):
        """Test that evaluate_predictions always returns dict."""
        samples = [{"predicted": [], "ground_truth": []}]
        result = evaluate_predictions(samples)
        
        assert isinstance(result, dict)
