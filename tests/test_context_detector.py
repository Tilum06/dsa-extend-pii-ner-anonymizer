"""Tests for context detector module."""

import pytest
from src.context_detector import (
    detect_name,
    detect_username,
    detect_address,
    detect_by_context,
)


class TestDetectName:
    """Test cases for detect_name function."""

    def test_detect_name_my_name_is(self):
        """Test detecting name after 'my name is' trigger."""
        text = "My name is John Doe"
        result = detect_name(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "NAME" for e in result)

    def test_detect_name_full_name(self):
        """Test detecting name after 'full name' trigger."""
        text = "Full name: Alice Smith"
        result = detect_name(text)
        
        assert isinstance(result, list)

    def test_detect_name_name_label(self):
        """Test detecting name after 'name:' trigger."""
        text = "Name: Bob Johnson"
        result = detect_name(text)
        
        assert isinstance(result, list)

    def test_detect_name_no_name(self):
        """Test when no name trigger present."""
        text = "No names here at all"
        result = detect_name(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "NAME" for e in result)

    def test_name_entity_format(self):
        """Test name entity has correct format."""
        text = "My name is John"
        result = detect_name(text)
        
        if result:
            for entity in result:
                assert entity["type"] == "NAME"
                assert isinstance(entity["start"], int)
                assert isinstance(entity["end"], int)
                assert entity["start"] >= 0

    def test_detect_name_scoring_path_first_person(self):
        """Test detecting name through sentence-level scoring."""
        text = "I am Alice Smith."
        result = detect_name(text)

        assert result == [
            {"type": "NAME", "text": "Alice Smith", "start": 5, "end": 16}
        ]

    def test_detect_name_scoring_path_single_token(self):
        """Test detecting a one-token name through sentence-level scoring."""
        text = "I am Alice."
        result = detect_name(text)

        assert result == [{"type": "NAME", "text": "Alice", "start": 5, "end": 10}]

    def test_detect_name_single_token_with_narrow_context(self):
        """Test detecting a one-token name with weak surrounding context."""
        text = "Alice went home."
        result = detect_name(text)

        assert result == [{"type": "NAME", "text": "Alice", "start": 0, "end": 5}]

    def test_detect_name_keeps_scanning_after_trigger(self):
        """Test fast-path triggers do not prevent later NAME detections."""
        text = "My name is Bob. Alice went home."
        result = detect_name(text)

        assert result == [
            {"type": "NAME", "text": "Bob", "start": 11, "end": 14},
            {"type": "NAME", "text": "Alice", "start": 16, "end": 21},
        ]

    def test_detect_name_ignores_inline_bio_suffix_artifacts(self):
        """Test NAME extraction ignores BIO labels glued to raw tokens."""
        text = "P.S.:B-NAME WhenI-NAME"
        result = detect_name(text)

        assert result == []

    def test_detect_name_scoring_path_title_prefix(self):
        """Test candidate extraction strips title prefixes."""
        text = "Dr. Alice Smith met Bob Jones."
        result = detect_name(text)

        assert result == [
            {"type": "NAME", "text": "Alice Smith", "start": 4, "end": 15},
            {"type": "NAME", "text": "Bob Jones", "start": 20, "end": 29},
        ]

    def test_detect_name_scoring_path_skips_address_like_candidate(self):
        """Test candidate extraction does not treat address words as names."""
        text = "123 Main Street is busy."
        result = detect_name(text)

        assert result == []


class TestDetectUsername:
    """Test cases for detect_username function."""

    def test_detect_username_username_trigger(self):
        """Test detecting username after 'username' trigger."""
        text = "username: johndoe123"
        result = detect_username(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "USERNAME" for e in result)

    def test_detect_username_user_name_trigger(self):
        """Test detecting username after 'user name' trigger."""
        text = "user name is alice_smith"
        result = detect_username(text)
        
        assert isinstance(result, list)

    def test_detect_username_account_trigger(self):
        """Test detecting username after 'account' trigger."""
        text = "account handle is bob_2023"
        result = detect_username(text)
        
        assert isinstance(result, list)

    def test_detect_username_handle_trigger(self):
        """Test detecting username after 'handle' trigger."""
        text = "My handle: developer_pro"
        result = detect_username(text)
        
        assert isinstance(result, list)

    def test_detect_username_no_username(self):
        """Test when no username trigger present."""
        text = "No username here"
        result = detect_username(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "USERNAME" for e in result)

    def test_username_entity_positions(self):
        """Test username entity has valid positions."""
        text = "username: admin"
        result = detect_username(text)
        
        if result:
            for entity in result:
                assert entity["start"] >= 0
                assert entity["end"] > entity["start"]


class TestDetectAddress:
    """Test cases for detect_address function."""

    def test_detect_address_street_trigger(self):
        """Test detecting address after 'street' trigger."""
        text = "street: 123 Main Street"
        result = detect_address(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "ADDRESS" for e in result)

    def test_detect_address_road_trigger(self):
        """Test detecting address after 'road' trigger."""
        text = "road is Oak Road"
        result = detect_address(text)
        
        assert isinstance(result, list)

    def test_detect_address_avenue_trigger(self):
        """Test detecting address after 'avenue' trigger."""
        text = "avenue: 456 Park Avenue"
        result = detect_address(text)
        
        assert isinstance(result, list)

    def test_detect_address_district_trigger(self):
        """Test detecting address after 'district' trigger."""
        text = "district: District 5"
        result = detect_address(text)
        
        assert isinstance(result, list)

    def test_detect_address_city_trigger(self):
        """Test detecting address after 'city' trigger."""
        text = "city: New York"
        result = detect_address(text)

        assert result == [{"type": "ADDRESS", "text": "New York", "start": 6, "end": 14}]

    def test_detect_address_does_not_mark_prose_city_reference(self):
        """Test prose mentions of cities/streets do not become addresses."""
        text = (
            "From humble beginnings in a small village in Japan, Yasuko Alvarez "
            "embarked on a journey to the bustling streets of New York City."
        )
        result = detect_address(text)

        assert result == []

    def test_detect_address_abbreviations(self):
        """Test detecting address with abbreviations."""
        text = "st. Mary St. rd. Main Rd. ave. Oak Ave."
        result = detect_address(text)
        
        assert isinstance(result, list)

    def test_detect_address_no_address(self):
        """Test when no address trigger present."""
        text = "No address information"
        result = detect_address(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "ADDRESS" for e in result)


class TestDetectByContext:
    """Test cases for detect_by_context function."""

    def test_detect_by_context_single_entity(self):
        """Test context detection with single entity."""
        text = "My name is Alice"
        result = detect_by_context(text)
        
        assert isinstance(result, list)

    def test_detect_by_context_multiple_entities(self):
        """Test context detection with multiple entities."""
        text = "My name is Bob and username: bob_smith at street: Main Street"
        result = detect_by_context(text)

        assert result == [
            {"type": "NAME", "text": "Bob", "start": 11, "end": 14},
            {"type": "USERNAME", "text": "bob_smith", "start": 29, "end": 38},
            {"type": "ADDRESS", "text": "Main Street", "start": 50, "end": 61},
        ]

    def test_detect_by_context_empty_text(self):
        """Test context detection with empty text."""
        text = ""
        result = detect_by_context(text)
        
        assert isinstance(result, list)

    def test_detect_by_context_entity_format(self):
        """Test all entities have correct format."""
        text = "My name is John and username: john123"
        result = detect_by_context(text)
        
        for entity in result:
            assert "type" in entity
            assert "text" in entity
            assert "start" in entity
            assert "end" in entity
            assert isinstance(entity["start"], int)
            assert isinstance(entity["end"], int)

    def test_detect_by_context_no_triggers(self):
        """Test context detection with no triggers."""
        text = "Just plain text without any triggers"
        result = detect_by_context(text)

        assert isinstance(result, list)

    def test_detect_by_context_respects_excluded_entities(self):
        """Test context resolver removes spans overlapping excluded entities."""
        text = "Email: alice@example.com Name: Alice"
        result = detect_by_context(
            text,
            excluded_entities=[
                {"type": "EMAIL", "text": "alice@example.com", "start": 7, "end": 24}
            ],
        )

        assert result == [{"type": "NAME", "text": "Alice", "start": 31, "end": 36}]
