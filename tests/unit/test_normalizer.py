"""Tests for URL and title normalization."""

import pytest

from marvel_metadata.core.normalizer import (
    normalize_marvel_url,
    normalize_title_spacing,
    normalize_title_for_match,
    extract_issue_number,
    extract_series_name,
    extract_year,
)


class TestNormalizeMarvelUrl:
    """Tests for normalize_marvel_url function."""

    def test_http_to_https(self):
        """Converts HTTP to HTTPS."""
        url = "http://marvel.com/comics/issue/123"
        assert normalize_marvel_url(url) == "https://www.marvel.com/comics/issue/123"

    def test_adds_www(self):
        """Adds www to marvel.com domain."""
        url = "https://marvel.com/comics/issue/123"
        assert normalize_marvel_url(url) == "https://www.marvel.com/comics/issue/123"

    def test_already_normalized(self):
        """Already normalized URL stays the same."""
        url = "https://www.marvel.com/comics/issue/123"
        assert normalize_marvel_url(url) == url

    def test_preserves_path(self):
        """Preserves the full path after domain."""
        url = "http://marvel.com/comics/issue/12345/avengers_2012_1"
        result = normalize_marvel_url(url)
        assert "12345/avengers_2012_1" in result


class TestNormalizeTitleSpacing:
    """Tests for normalize_title_spacing function."""

    def test_collapses_multiple_spaces(self):
        """Collapses multiple spaces to single space."""
        assert normalize_title_spacing("Avengers  #1") == "Avengers #1"
        assert normalize_title_spacing("New   Avengers  #5") == "New Avengers #5"

    def test_fixes_parenthesis_hash_spacing(self):
        """Ensures space before # after parenthesis."""
        assert normalize_title_spacing("Avengers (2012)#1") == "Avengers (2012) #1"

    def test_trims_whitespace(self):
        """Trims leading and trailing whitespace."""
        assert normalize_title_spacing("  Avengers #1  ") == "Avengers #1"


class TestNormalizeTitleForMatch:
    """Tests for normalize_title_for_match function."""

    def test_lowercase(self):
        """Converts to lowercase."""
        result = normalize_title_for_match("AVENGERS (2012) #1")
        assert "avengers" in result
        assert "AVENGERS" not in result

    def test_removes_parentheses(self):
        """Removes parentheses but keeps content."""
        result = normalize_title_for_match("Avengers (2012) #1")
        assert "(" not in result
        assert ")" not in result
        assert "2012" in result

    def test_normalizes_issue_numbers(self):
        """Normalizes issue numbers (#001 -> #1)."""
        assert "#1" in normalize_title_for_match("Avengers (2012) #001")
        assert "#1" in normalize_title_for_match("Avengers (2012) #01")

    def test_preserves_decimal_issue_numbers(self):
        """Preserves decimal issue numbers (#0.1)."""
        result = normalize_title_for_match("Amazing Spider-Man #0.1")
        assert "#0.1" in result

    def test_collapses_whitespace(self):
        """Collapses all whitespace."""
        result = normalize_title_for_match("New  Avengers  (2013)  #1")
        assert "  " not in result


class TestExtractIssueNumber:
    """Tests for extract_issue_number function."""

    def test_extracts_simple_number(self):
        """Extracts simple issue number."""
        assert extract_issue_number("Avengers (2012) #5") == "5"
        assert extract_issue_number("Avengers #123") == "123"

    def test_extracts_decimal_number(self):
        """Extracts decimal issue number."""
        assert extract_issue_number("Amazing Spider-Man #0.1") == "0.1"
        assert extract_issue_number("Avengers #1.5") == "1.5"

    def test_extracts_with_suffix(self):
        """Extracts issue number with letter suffix."""
        assert extract_issue_number("Avengers #1AU") == "1AU"

    def test_returns_none_for_no_number(self):
        """Returns None when no issue number found."""
        assert extract_issue_number("Avengers Annual") is None


class TestExtractSeriesName:
    """Tests for extract_series_name function."""

    def test_extracts_series_with_year(self):
        """Extracts series name before year."""
        assert extract_series_name("Avengers (2012) #1") == "Avengers"
        assert extract_series_name("Amazing Spider-Man (1963) #129") == "Amazing Spider-Man"

    def test_extracts_series_before_hash(self):
        """Extracts series name before # when no year."""
        assert extract_series_name("Avengers #1") == "Avengers"

    def test_handles_complex_names(self):
        """Handles complex series names."""
        assert extract_series_name("New Avengers (2013) #1") == "New Avengers"


class TestExtractYear:
    """Tests for extract_year function."""

    def test_extracts_year(self):
        """Extracts 4-digit year from parentheses."""
        assert extract_year("Avengers (2012) #1") == 2012
        assert extract_year("Amazing Spider-Man (1963) #129") == 1963

    def test_returns_none_for_no_year(self):
        """Returns None when no year found."""
        assert extract_year("Avengers #1") is None
        assert extract_year("Avengers Annual") is None
