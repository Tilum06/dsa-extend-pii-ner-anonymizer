"""Tests for regex detector module – DATE entity detection."""

from src.regex_detector import (
    detect_date,
    detect_regex_entities,
)


class TestDetectDate:
    """Test cases for detect_date function."""

    # -- Numeric date formats --

    def test_dd_mm_yyyy_slash(self):
        """Test DD/MM/YYYY format."""
        text = "Date: 01/02/2024"
        result = detect_date(text)
        assert len(result) == 1
        assert result[0]["text"] == "01/02/2024"
        assert result[0]["type"] == "DATE"

    def test_d_m_yyyy_slash(self):
        """Test D/M/YYYY format with single-digit day/month."""
        result = detect_date("On 1/2/2024 we met.")
        assert len(result) == 1
        assert result[0]["text"] == "1/2/2024"

    def test_dd_mm_yyyy_dash(self):
        """Test DD-MM-YYYY format."""
        result = detect_date("01-02-2024")
        assert len(result) == 1
        assert result[0]["text"] == "01-02-2024"

    def test_d_m_yy_dash(self):
        """Test D-M-YY format with 2-digit year."""
        result = detect_date("1-2-24")
        assert len(result) == 1
        assert result[0]["text"] == "1-2-24"

    def test_yyyy_mm_dd_dash(self):
        """Test YYYY-MM-DD ISO format."""
        result = detect_date("2024-02-01")
        assert len(result) == 1
        assert result[0]["text"] == "2024-02-01"

    def test_yyyy_mm_dd_slash(self):
        """Test YYYY/MM/DD format."""
        result = detect_date("2024/02/01")
        assert len(result) == 1
        assert result[0]["text"] == "2024/02/01"

    def test_dd_mm_yyyy_dot(self):
        """Test DD.MM.YYYY format."""
        result = detect_date("02.01.2024")
        assert len(result) == 1
        assert result[0]["text"] == "02.01.2024"

    # -- English month-name formats --

    def test_month_day_year(self):
        """Test 'January 2, 2024' format."""
        result = detect_date("On January 2, 2024.")
        assert len(result) == 1
        assert result[0]["text"] == "January 2, 2024"

    def test_abbr_month_day_year(self):
        """Test 'Jan 2, 2024' format."""
        result = detect_date("On Jan 2, 2024.")
        assert len(result) == 1
        assert result[0]["text"] == "Jan 2, 2024"

    def test_day_month_year(self):
        """Test '2 January 2024' format."""
        result = detect_date("On 2 January 2024.")
        assert len(result) == 1
        assert result[0]["text"] == "2 January 2024"

    def test_day_abbr_month_year(self):
        """Test '2 Jan 2024' format."""
        result = detect_date("On 2 Jan 2024.")
        assert len(result) == 1
        assert result[0]["text"] == "2 Jan 2024"

    # -- Vietnamese formats --

    def test_vietnamese_full(self):
        """Test 'ngày DD tháng MM năm YYYY' format."""
        result = detect_date("Sinh ngày 02 tháng 01 năm 2024.")
        assert len(result) == 1
        assert "ngày 02 tháng 01 năm 2024" in result[0]["text"]

    def test_vietnamese_no_ngay_prefix(self):
        """Test 'DD tháng MM năm YYYY' without 'ngày' prefix."""
        result = detect_date("02 tháng 01 năm 2024")
        assert len(result) == 1
        assert result[0]["text"] == "02 tháng 01 năm 2024"

    def test_vietnamese_ngay_slash(self):
        """Test 'ngày D/M/YYYY' format."""
        result = detect_date("ngày 2/1/2024")
        assert len(result) == 1
        assert result[0]["text"] == "ngày 2/1/2024"

    def test_vietnamese_thang_nam(self):
        """Test 'tháng MM năm YYYY' format."""
        result = detect_date("tháng 01 năm 2024")
        assert len(result) == 1
        assert result[0]["text"] == "tháng 01 năm 2024"

    # -- Month/year --

    def test_mm_yyyy_slash(self):
        """Test MM/YYYY numeric month/year."""
        result = detect_date("Published 01/2024.")
        assert len(result) == 1
        assert result[0]["text"] == "01/2024"

    def test_month_name_year(self):
        """Test 'January 2024' month/year."""
        result = detect_date("In January 2024.")
        assert len(result) == 1
        assert result[0]["text"] == "January 2024"

    # -- Contextual year-only --

    def test_nam_yyyy(self):
        """Test Vietnamese contextual year 'năm YYYY'."""
        result = detect_date("năm 2024")
        assert len(result) == 1
        assert result[0]["text"] == "năm 2024"

    def test_year_yyyy(self):
        """Test English contextual year 'year YYYY'."""
        result = detect_date("year 2024")
        assert len(result) == 1
        assert result[0]["text"] == "year 2024"

    # -- False-positive guards --

    def test_bare_4digit_not_detected(self):
        """Bare 4-digit numbers should NOT be detected as DATE."""
        result = detect_date("The code is 2024.")
        assert len(result) == 0

    def test_date_inside_url_not_detected(self):
        """Date-like segment inside a URL should NOT be detected."""
        from src.regex_detector import detect_email, detect_url

        text = "Visit https://example.com/2024/01/02 now."
        excluded = detect_email(text) + detect_url(text)
        result = detect_date(text, excluded)
        assert len(result) == 0

    def test_date_entity_format(self):
        """Test DATE entity has correct schema keys."""
        result = detect_date("01/02/2024")
        assert len(result) == 1
        entity = result[0]
        assert entity["type"] == "DATE"
        assert isinstance(entity["start"], int)
        assert isinstance(entity["end"], int)
        assert entity["start"] >= 0
        assert entity["end"] > entity["start"]

    def test_date_position_accuracy(self):
        """Test DATE entity start/end positions are correct."""
        text = "Date: 01/02/2024"
        result = detect_date(text)
        assert len(result) == 1
        assert text[result[0]["start"]:result[0]["end"]] == "01/02/2024"

    def test_no_date_in_empty_text(self):
        """Test no dates detected in empty string."""
        result = detect_date("")
        assert result == []


class TestDetectRegexEntitiesWithDate:
    """Test that DATE integrates correctly in detect_regex_entities."""

    def test_date_appears_in_combined_output(self):
        """Dates should appear in the combined regex output."""
        result = detect_regex_entities("Meeting on January 2, 2024.")
        types = {e["type"] for e in result}
        assert "DATE" in types

    def test_email_beats_date_on_overlap(self):
        """EMAIL should win over DATE when spans overlap."""
        result = detect_regex_entities("Contact john@01.02.2024.com")
        types = {e["type"] for e in result}
        assert "EMAIL" in types

    def test_url_beats_date_on_overlap(self):
        """URL should win over DATE when spans overlap."""
        result = detect_regex_entities("See https://example.com/2024/01/02")
        types = {e["type"] for e in result}
        assert "URL" in types
        assert "DATE" not in types

    def test_mixed_entities_all_detected(self):
        """All entity types should coexist when non-overlapping."""
        text = "Email john@a.com, born 01/02/2024, call +84 912 345 678."
        result = detect_regex_entities(text)
        types = {e["type"] for e in result}
        assert "EMAIL" in types
        assert "DATE" in types
        assert "PHONE" in types
