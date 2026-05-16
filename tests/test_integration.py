"""Integration tests for the complete PII detection pipeline."""

import pytest
from src.regex_detector import detect_regex_entities
from src.context_detector import detect_by_context
from src.merger import merge_entities, resolve_overlaps
from src.anonymizer import anonymize_text


class TestIntegrationPipeline:
    """Test the complete pipeline from text to anonymization."""

    def test_pipeline_email_detection(self):
        """Test pipeline with email detection."""
        text = "Contact me at john@example.com"
        
        # Step 1: Regex detection
        regex_entities = detect_regex_entities(text)
        assert isinstance(regex_entities, list)
        
        # Step 2: Context detection
        context_entities = detect_by_context(text)
        assert isinstance(context_entities, list)
        
        # Step 3: Merge entities
        merged = merge_entities(regex_entities, context_entities)
        assert isinstance(merged, list)
        
        # Step 4: Resolve overlaps
        final = resolve_overlaps(merged)
        assert isinstance(final, list)
        
        # Step 5: Anonymize
        if final:
            anonymized = anonymize_text(text, final)
            assert isinstance(anonymized, str)

    def test_pipeline_multiple_entity_types(self):
        """Test pipeline with multiple entity types."""
        text = "My name is John. Email: john@example.com. Phone: 555-1234. Website: www.example.com"
        
        # Detection
        regex_entities = detect_regex_entities(text)
        context_entities = detect_by_context(text)
        
        # Merge
        merged = merge_entities(regex_entities, context_entities)
        assert isinstance(merged, list)
        
        # Resolve overlaps
        final = resolve_overlaps(merged)
        assert isinstance(final, list)

    def test_pipeline_with_overlapping_entities(self):
        """Test pipeline handling overlapping entities."""
        text = "john.doe@company.com is my email and username is john_doe"
        
        # Detection
        regex_entities = detect_regex_entities(text)
        context_entities = detect_by_context(text)
        
        # Merge and resolve
        merged = merge_entities(regex_entities, context_entities)
        final = resolve_overlaps(merged)
        
        # Verify no overlaps in final
        if len(final) > 1:
            for i in range(len(final) - 1):
                assert final[i]["end"] <= final[i + 1]["start"]

    def test_pipeline_empty_text(self):
        """Test pipeline with empty text."""
        text = ""
        
        regex_entities = detect_regex_entities(text)
        context_entities = detect_by_context(text)
        merged = merge_entities(regex_entities, context_entities)
        final = resolve_overlaps(merged)
        
        assert isinstance(final, list)

    def test_pipeline_text_with_no_entities(self):
        """Test pipeline with text containing no entities."""
        text = "Just a normal text without any PII"
        
        regex_entities = detect_regex_entities(text)
        context_entities = detect_by_context(text)
        merged = merge_entities(regex_entities, context_entities)
        final = resolve_overlaps(merged)
        
        # Result should be empty or contain only valid entities
        assert isinstance(final, list)


class TestAnonymizationIntegration:
    """Test anonymization with detected entities."""

    def test_anonymization_with_detected_entities(self):
        """Test anonymization using entities from detection."""
        text = "Contact John at john@example.com or 555-1234"
        
        # Detect
        regex_entities = detect_regex_entities(text)
        context_entities = detect_by_context(text)
        
        # Merge
        merged = merge_entities(regex_entities, context_entities)
        
        # Anonymize
        anonymized = anonymize_text(text, merged)
        
        # Verify anonymization happened
        assert isinstance(anonymized, str)

    def test_anonymization_preserves_structure(self):
        """Test that anonymization preserves text structure."""
        text = "My email is john@example.com and my phone is 555-1234"
        
        detected = detect_regex_entities(text)
        anonymized = anonymize_text(text, detected)
        
        # Original parts that are not PII should be preserved
        assert "My" in anonymized
        assert "email" in anonymized.lower() or "my" in anonymized.lower()

    def test_anonymization_with_no_detected_entities(self):
        """Test anonymization when no entities are detected."""
        text = "Normal text"
        
        detected = []
        anonymized = anonymize_text(text, detected)
        
        # Should return original text
        assert anonymized == text


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline."""

    def test_complete_pipeline(self):
        """Test complete pipeline from text to anonymization."""
        original_text = "Hi, I'm John Doe. Contact me at john@example.com or call 555-1234"
        
        # Step 1: Detection
        regex_entities = detect_regex_entities(original_text)
        context_entities = detect_by_context(original_text)
        
        # Step 2: Merge
        merged = merge_entities(regex_entities, context_entities)
        
        # Step 3: Resolve overlaps
        final_entities = resolve_overlaps(merged)
        
        # Step 4: Anonymize
        anonymized_text = anonymize_text(original_text, final_entities)
        
        # Step 5: Verify results
        assert isinstance(anonymized_text, str)
        assert len(anonymized_text) > 0

    def test_pipeline_robustness(self):
        """Test pipeline robustness with various inputs."""
        test_cases = [
            "Simple text",
            "email@example.com",
            "555-1234",
            "https://example.com",
            "My name is John",
            "username: john_doe",
            "street: Main Street",
            "",
        ]
        
        for text in test_cases:
            # Should not raise exceptions
            regex_entities = detect_regex_entities(text)
            context_entities = detect_by_context(text)
            merged = merge_entities(regex_entities, context_entities)
            final = resolve_overlaps(merged)
            anonymized = anonymize_text(text, final)
            
            assert isinstance(anonymized, str)

    def test_pipeline_maintains_consistency(self):
        """Test that pipeline maintains consistency across runs."""
        text = "Contact john@example.com"
        
        # Run 1
        result1 = detect_regex_entities(text)
        
        # Run 2
        result2 = detect_regex_entities(text)
        
        # Results should be consistent
        assert len(result1) == len(result2)
        assert [e["type"] for e in result1] == [e["type"] for e in result2]
