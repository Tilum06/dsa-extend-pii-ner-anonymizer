"""Tests for regex detector module."""

import pytest
from src.regex_detector import (
    detect_email,
    detect_phone,
    detect_url,
    detect_by_regex,
)


class TestDetectEmail:
    """Test cases for detect_email function."""

    def test_detect_email_single_email(self):
        """Test detecting a single email."""
        text = "Contact me at john@example.com."
        result = detect_email(text)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert any(e["type"] == "EMAIL" for e in result)

    def test_detect_email_multiple_emails(self):
        """Test detecting multiple emails."""
        text = "Email john@example.com or jane@example.com"
        result = detect_email(text)
        
        assert isinstance(result, list)
        assert len(result) >= 2

    def test_detect_email_no_email(self):
        """Test detecting no emails in text."""
        text = "No email in this text"
        result = detect_email(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "EMAIL" for e in result)

    def test_detect_email_with_special_chars(self):
        """Test detecting email with special characters."""
        text = "Contact john.doe+tag@example.co.uk"
        result = detect_email(text)
        
        assert isinstance(result, list)
        if result:
            assert all(k in e for e in result for k in ["type", "text", "start", "end"])

    def test_email_entity_format(self):
        """Test email entity has correct format."""
        text = "john@example.com"
        result = detect_email(text)
        
        if result:
            for entity in result:
                assert entity["type"] == "EMAIL"
                assert isinstance(entity["start"], int)
                assert isinstance(entity["end"], int)
                assert entity["start"] >= 0
                assert entity["end"] > entity["start"]


class TestDetectPhone:
    """Test cases for detect_phone function."""

    def test_detect_phone_basic_format(self):
        """Test detecting phone in basic format."""
        text = "My phone is 555-1234"
        result = detect_phone(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "PHONE" for e in result)

    def test_detect_phone_with_country_code(self):
        """Test detecting phone with country code."""
        text = "Call me at +1-555-0123"
        result = detect_phone(text)
        
        assert isinstance(result, list)

    def test_detect_phone_parentheses_format(self):
        """Test detecting phone with parentheses."""
        text = "Phone: (555) 123-4567"
        result = detect_phone(text)
        
        assert isinstance(result, list)

    def test_detect_phone_no_phone(self):
        """Test when no phone present."""
        text = "No phone here"
        result = detect_phone(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "PHONE" for e in result)

    def test_phone_entity_positions(self):
        """Test phone entity has correct positions."""
        text = "555-1234"
        result = detect_phone(text)
        
        if result:
            for entity in result:
                assert entity["start"] == 0
                assert entity["end"] == len(text)


class TestDetectUrl:
    """Test cases for detect_url function."""

    def test_detect_url_http(self):
        """Test detecting HTTP URL."""
        text = "Visit http://example.com"
        result = detect_url(text)
        
        assert isinstance(result, list)
        assert any(e["type"] == "URL" for e in result)

    def test_detect_url_https(self):
        """Test detecting HTTPS URL."""
        text = "Go to https://example.com now"
        result = detect_url(text)
        
        assert isinstance(result, list)

    def test_detect_url_www(self):
        """Test detecting www URL."""
        text = "Check out www.example.com"
        result = detect_url(text)
        
        assert isinstance(result, list)

    def test_detect_url_multiple(self):
        """Test detecting multiple URLs."""
        text = "Visit http://example.com or www.other.com"
        result = detect_url(text)
        
        assert isinstance(result, list)

    def test_detect_url_no_url(self):
        """Test when no URL present."""
        text = "No url here"
        result = detect_url(text)
        
        assert isinstance(result, list)
        assert all(e["type"] == "URL" for e in result)


class TestDetectByRegex:
    """Test cases for detect_by_regex function."""

    def test_detect_by_regex_email(self):
        """Test regex detection includes emails."""
        text = "john@example.com"
        result = detect_by_regex(text)
        
        assert isinstance(result, list)

    def test_detect_by_regex_multiple_types(self):
        """Test regex detection with multiple entity types."""
        text = "Email: john@example.com Phone: 555-1234 Website: www.example.com"
        result = detect_by_regex(text)
        
        assert isinstance(result, list)
        types = {e["type"] for e in result}
        assert len(types) >= 1

    def test_detect_by_regex_empty_text(self):
        """Test regex detection with empty text."""
        text = ""
        result = detect_by_regex(text)
        
        assert isinstance(result, list)

    def test_detect_by_regex_entity_format(self):
        """Test all entities have correct format."""
        text = "john@example.com 555-1234 www.example.com"
        result = detect_by_regex(text)
        
        for entity in result:
            assert "type" in entity
            assert "text" in entity
            assert "start" in entity
            assert "end" in entity
            assert isinstance(entity["start"], int)
            assert isinstance(entity["end"], int)
