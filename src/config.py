"""Project-wide configuration and constants."""

from pathlib import Path

RAW_DATA_PATH = Path("data/raw/pii_dataset.csv")
PROCESSED_DATA_PATH = Path("data/processed/processed_data.json")

ENTITY_PRIORITY = [
    "EMAIL",
    "URL",
    "PHONE",
    "ADDRESS",
    "NAME",
    "USERNAME",
]

LABEL_MAPPING = {
    "NAME_STUDENT": "NAME",
    "EMAIL": "EMAIL",
    "PHONE_NUM": "PHONE",
    "STREET_ADDRESS": "ADDRESS",
    "USERNAME": "USERNAME",
    "URL_PERSONAL": "URL",
}
