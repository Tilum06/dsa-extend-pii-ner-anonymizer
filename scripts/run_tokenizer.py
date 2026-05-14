"""Run tokenizer from command line.

Example:
    python scripts/run_tokenizer.py --input data/raw/pii_text.csv --output data/processed/tokenized.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from src.tokenizer import tokenize_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tokenize PII text CSV.")
    parser.add_argument("--input", required=True, help="Path to CSV with document,text columns")
    parser.add_argument("--output", required=True, help="Path to output tokenized CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tokenize_csv(args.input, args.output)
    print(f"Saved tokenized CSV to {args.output}")


if __name__ == "__main__":
    main()
