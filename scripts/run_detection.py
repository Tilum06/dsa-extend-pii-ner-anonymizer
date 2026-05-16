"""Run the detection pipeline on processed data.

Usage:
    python scripts/run_detection.py --input data/processed/processed_data.json --output results/predictions.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path so `src` package can be imported.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.regex_detector import detect_regex_entities
from src.context_detector import detect_by_context
from src.merger import merge_entities


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Detect PII entities in processed data and save predictions.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/processed_data.json",
        help="Path to the processed JSON dataset (default: data/processed/processed_data.json)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/predictions.json",
        help="Path for the predictions JSON output (default: results/predictions.json)",
    )
    return parser.parse_args()


def load_processed_data(path: Path) -> list[dict[str, Any]]:
    """Load the processed dataset from a JSON file."""
    with path.open("r", encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)
    return data


def run_detection(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run regex + context detectors on every sample and merge the results.

    Returns a list of prediction records, each containing:
        - id: the sample id
        - predicted_entities: merged entity list
    """
    predictions: list[dict[str, Any]] = []
    total = len(samples)

    for idx, sample in enumerate(samples, start=1):
        sample_id = sample.get("id", idx)
        text: str = sample.get("text", "")

        # --- Regex-based detection ---
        regex_entities = detect_regex_entities(text)

        # --- Context-based detection ---
        context_entities = detect_by_context(text)

        # --- Merge ---
        try:
            merged = merge_entities(regex_entities, context_entities)
        except NotImplementedError:
            # If merger is not yet implemented, just concatenate and sort.
            merged = sorted(
                regex_entities + context_entities,
                key=lambda e: e["start"],
            )

        predictions.append({
            "id": sample_id,
            "predicted_entities": merged,
        })

        if idx % 200 == 0 or idx == total:
            print(f"      Processed {idx}/{total} samples ...")

    return predictions


def save_predictions(predictions: list[dict[str, Any]], path: Path) -> None:
    """Write predictions to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)


def main() -> None:
    """Run the full detection pipeline."""
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # --- Step 1: Load processed data ---
    print(f"[1/3] Loading processed data from: {input_path}")
    samples = load_processed_data(input_path)
    print(f"      Loaded {len(samples)} samples.")

    # --- Step 2: Run detection ---
    print("[2/3] Running detection pipeline ...")
    predictions = run_detection(samples)
    entity_count = sum(len(p["predicted_entities"]) for p in predictions)
    print(f"      Detected {entity_count} total entities across {len(predictions)} samples.")

    # --- Step 3: Save predictions ---
    print(f"[3/3] Saving predictions to: {output_path}")
    save_predictions(predictions, output_path)
    print("      Done.")


if __name__ == "__main__":
    main()
