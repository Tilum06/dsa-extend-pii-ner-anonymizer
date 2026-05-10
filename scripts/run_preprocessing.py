"""Run the preprocessing pipeline."""

from src.preprocessing import (
    build_processed_dataset,
    load_raw_dataset,
    save_processed_dataset,
)


def main():
    raw_rows = load_raw_dataset()
    records = build_processed_dataset(raw_rows)
    save_processed_dataset(records)


if __name__ == "__main__":
    main()