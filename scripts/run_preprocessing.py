"""Run the preprocessing pipeline.

Usage:
    python scripts/run_preprocessing.py --input data/raw/pii_dataset.csv --output data/processed/processed_data.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src` package can be imported
# regardless of the directory the script is invoked from.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.preprocessing import (
    build_processed_dataset,
    load_raw_dataset,
    save_processed_dataset,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Preprocess the raw PII dataset into a structured JSON file.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/pii_dataset.csv",
        help="Path to the raw CSV dataset (default: data/raw/pii_dataset.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/processed_data.json",
        help="Path for the processed JSON output (default: data/processed/processed_data.json)",
    )
    return parser.parse_args()


def main() -> None:
    """Run the full preprocessing pipeline."""
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # --- Step 1: Load raw dataset ---
    print(f"[1/3] Loading raw dataset from: {input_path}")
    raw_rows = load_raw_dataset(input_path)
    print(f"      Loaded {len(raw_rows)} raw rows.")

    # --- Step 2: Build processed dataset ---
    print("[2/3] Building processed dataset ...")
    records = build_processed_dataset(raw_rows)
    print(f"      Built {len(records)} processed records.")

    # --- Step 3: Save to disk ---
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[3/3] Saving processed data to: {output_path}")
    save_processed_dataset(records, output_path)
    print("      Done.")


if __name__ == "__main__":
    main()