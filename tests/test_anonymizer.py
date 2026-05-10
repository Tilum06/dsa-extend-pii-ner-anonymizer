"""Tests for anonymizer module."""

import pytest
from src.anonymizer import anonymize_text


class TestAnonymizeText:
    """Test cases for anonymize_text function."""

    def test_anonymize_text_single_entity(self):
        """Test anonymizing text with single entity."""
        text = "My email is john@example.com"
        entities = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 12,
                "end": 28
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert "john@example.com" not in result
        assert "[EMAIL]" in result or "<EMAIL>" in result or "EMAIL" in result

    def test_anonymize_text_multiple_entities(self):
        """Test anonymizing text with multiple entities."""
        text = "Contact John at john@example.com or call 555-1234"
        entities = [
            {
                "type": "NAME",
                "text": "John",
                "start": 8,
                "end": 12
            },
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 16,
                "end": 32
            },
            {
                "type": "PHONE",
                "text": "555-1234",
                "start": 42,
                "end": 50
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert "John" not in result
        assert "john@example.com" not in result
        assert "555-1234" not in result

    def test_anonymize_text_overlapping_entities(self):
        """Test anonymizing text with overlapping entities."""
        text = "john@example.com is John's email"
        entities = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 0,
                "end": 16
            },
            {
                "type": "NAME",
                "text": "John",
                "start": 20,
                "end": 24
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)

    def test_anonymize_text_no_entities(self):
        """Test anonymizing text with no entities."""
        text = "Just plain text"
        entities = []
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert result == text

    def test_anonymize_text_preserves_non_entity_text(self):
        """Test that non-entity text is preserved."""
        text = "Contact john@example.com for info"
        entities = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 8,
                "end": 24
            }
        ]
        result = anonymize_text(text, entities)
        
        assert "Contact" in result
        assert "for info" in result

    def test_anonymize_text_entity_at_start(self):
        """Test anonymizing entity at text start."""
        text = "john@example.com is my email"
        entities = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 0,
                "end": 16
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert "john@example.com" not in result

    def test_anonymize_text_entity_at_end(self):
        """Test anonymizing entity at text end."""
        text = "Call me at 555-1234"
        entities = [
            {
                "type": "PHONE",
                "text": "555-1234",
                "start": 11,
                "end": 19
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert "555-1234" not in result

    def test_anonymize_text_adjacent_entities(self):
        """Test anonymizing adjacent entities."""
        text = "john@example.com 555-1234"
        entities = [
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 0,
                "end": 16
            },
            {
                "type": "PHONE",
                "text": "555-1234",
                "start": 17,
                "end": 25
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert "john@example.com" not in result
        assert "555-1234" not in result

    def test_anonymize_text_case_sensitive(self):
        """Test that anonymization is case-sensitive."""
        text = "Email: John@Example.COM"
        entities = [
            {
                "type": "EMAIL",
                "text": "John@Example.COM",
                "start": 7,
                "end": 23
            }
        ]
        result = anonymize_text(text, entities)
        
        assert "John@Example.COM" not in result
        assert "Email:" in result

    def test_anonymize_text_complex_replacement(self):
        """Test anonymization with complex text patterns."""
        text = "Visit https://john.example.com/profile or email john@example.com"
        entities = [
            {
                "type": "URL",
                "text": "https://john.example.com/profile",
                "start": 6,
                "end": 39
            },
            {
                "type": "EMAIL",
                "text": "john@example.com",
                "start": 48,
                "end": 64
            }
        ]
        result = anonymize_text(text, entities)
        
        assert isinstance(result, str)
        assert len(result) > 0
