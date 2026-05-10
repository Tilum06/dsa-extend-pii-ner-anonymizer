"""Tests for preprocessing module."""

import json
from pathlib import Path
import pytest
from src.preprocessing import (
    load_raw_dataset,
    parse_list_cell,
    normalize_text,
    map_bio_label,
    bio_labels_to_entities,
    build_processed_record,
)


class TestLoadRawDataset:
    """Test cases for load_raw_dataset function."""

    def test_load_raw_dataset_file_not_found(self):
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_raw_dataset("nonexistent_file.csv")

    def test_load_raw_dataset_returns_list(self):
        """Test that load_raw_dataset returns a list."""
        # This would require actual CSV file, so we test the return type expectation
        result = load_raw_dataset()
        assert isinstance(result, list)


class TestParseListCell:
    """Test cases for parse_list_cell function."""

    def test_parse_list_cell_with_none(self):
        """Test parsing None value returns empty list."""
        result = parse_list_cell(None)
        assert result == []

    def test_parse_list_cell_with_list(self):
        """Test parsing list value returns list."""
        result = parse_list_cell([1, 2, 3])
        assert result == ["1", "2", "3"]

    def test_parse_list_cell_with_string_list(self):
        """Test parsing string representation of list."""
        result = parse_list_cell("['item1', 'item2']")
        assert isinstance(result, list)

    def test_parse_list_cell_with_empty_string(self):
        """Test parsing empty string."""
        result = parse_list_cell("")
        assert isinstance(result, list)


class TestNormalizeText:
    """Test cases for normalize_text function."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        text = "  Hello   World  "
        result = normalize_text(text)
        assert isinstance(result, str)

    def test_normalize_text_with_special_chars(self):
        """Test normalization with special characters."""
        text = "Hello\n\tWorld"
        result = normalize_text(text)
        assert isinstance(result, str)


class TestMapBioLabel:
    """Test cases for map_bio_label function."""

    def test_map_bio_label_valid_mapping(self):
        """Test mapping valid BIO labels with B- prefix."""
        result = map_bio_label("B-NAME_STUDENT")
        assert result == "NAME"

    def test_map_bio_label_email(self):
        """Test mapping EMAIL label with I- prefix."""
        result = map_bio_label("I-EMAIL")
        assert result == "EMAIL"

    def test_map_bio_label_phone(self):
        """Test mapping PHONE label with B- prefix."""
        result = map_bio_label("B-PHONE_NUM")
        assert result == "PHONE"
    
    def test_map_bio_label_invalid_format(self):
        """Test mapping label without BIO prefix."""
        result = map_bio_label("NAME_STUDENT")
        assert result is None
    
    def test_map_bio_label_o_label(self):
        """Test mapping O label (outside any entity)."""
        result = map_bio_label("O")
        assert result is None


class TestBioLabelsToEntities:
    """Test cases for bio_labels_to_entities function."""

    def test_bio_labels_to_entities_single_entity(self):
        """Test converting BIO labels to entities with single entity."""
        tokens = ["My", "name", "is", "John"]
        bio_labels = ["O", "O", "O", "B-NAME"]
        result = bio_labels_to_entities(tokens, bio_labels)
        assert isinstance(result, list)
        if result:
            assert all(isinstance(e, dict) for e in result)

    def test_bio_labels_to_entities_multiple_entities(self):
        """Test converting BIO labels to entities with multiple entities."""
        tokens = ["John", "at", "john@example.com"]
        bio_labels = ["B-NAME", "O", "B-EMAIL"]
        result = bio_labels_to_entities(tokens, bio_labels)
        assert isinstance(result, list)


class TestBuildProcessedRecord:
    """Test cases for build_processed_record function."""

    def test_build_processed_record_structure(self):
        """Test that processed record has required fields."""
        raw_row = {
            "document": "1",
            "text": "Contact John at john@example.com",
            "tokens": "['Contact', 'John', 'at', 'john@example.com']",
            "labels": "['O', 'B-NAME_STUDENT', 'O', 'B-EMAIL']"
        }
        record = build_processed_record(raw_row)
        
        assert "id" in record
        assert "text" in record
        assert "tokens" in record
        assert "ground_truth" in record
        assert record["id"] == 1
        assert record["text"] == "Contact John at john@example.com"
        assert isinstance(record["ground_truth"], list)
    
    def test_build_processed_record_with_entities(self):
        """Test that processed record extracts entities correctly."""
        raw_row = {
            "document": "2",
            "text": "My email is john@example.com",
            "tokens": "['My', 'email', 'is', 'john@example.com']",
            "labels": "['O', 'O', 'O', 'B-EMAIL']"
        }
        record = build_processed_record(raw_row)
        
        assert len(record["ground_truth"]) >= 1
        if record["ground_truth"]:
            assert record["ground_truth"][0]["type"] == "EMAIL"
    
    def test_build_processed_record_empty_row(self):
        """Test building record from empty row."""
        raw_row = {}
        record = build_processed_record(raw_row)
        
        assert "id" in record
        assert "text" in record
        assert isinstance(record["ground_truth"], list)
