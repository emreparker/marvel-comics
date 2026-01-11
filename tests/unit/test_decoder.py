"""Tests for the SvelteKit payload decoder."""

import pytest

from marvel_metadata.core.decoder import (
    decode_refs,
    extract_pool,
    iter_packed_issue_dicts,
    decode_issues_from_payload,
)


class TestDecodeRefs:
    """Tests for decode_refs function."""

    def test_primitive_passthrough(self, sample_pool: list):
        """Primitive values pass through unchanged."""
        assert decode_refs(sample_pool, "raw_string") == "raw_string"
        assert decode_refs(sample_pool, 3.14) == 3.14
        assert decode_refs(sample_pool, True) is True
        assert decode_refs(sample_pool, None) is None

    def test_index_resolution(self, sample_pool: list):
        """Integer references resolve to pool values."""
        assert decode_refs(sample_pool, 0) == "Avengers"
        assert decode_refs(sample_pool, 1) == "(2012)"
        assert decode_refs(sample_pool, 2) == "#1"
        assert decode_refs(sample_pool, 3) == "https://www.marvel.com/comics/issue/12345"

    def test_nested_dict_resolution(self, sample_pool: list):
        """Nested dictionaries with integer refs are resolved."""
        result = decode_refs(sample_pool, 4)  # {"title": 0, "year": 1}
        assert result == {"title": "Avengers", "year": "(2012)"}

    def test_nested_list_resolution(self, sample_pool: list):
        """Lists with integer refs are resolved."""
        result = decode_refs(sample_pool, 5)  # [0, 1, 2]
        assert result == ["Avengers", "(2012)", "#1"]

    def test_out_of_bounds_returns_none(self, sample_pool: list):
        """Out-of-bounds index returns None."""
        assert decode_refs(sample_pool, 999) is None
        assert decode_refs(sample_pool, -1) is None

    def test_deep_nesting(self, sample_pool: list):
        """Deeply nested structures are resolved correctly."""
        # Add a deeply nested structure
        pool = sample_pool + [{"outer": {"inner": 0}}]
        result = decode_refs(pool, len(pool) - 1)
        assert result == {"outer": {"inner": "Avengers"}}

    def test_numeric_value_resolved(self, sample_pool: list):
        """Numeric values in pool are returned correctly."""
        result = decode_refs(sample_pool, 6)  # 12345
        assert result == 12345

    def test_null_value_resolved(self, sample_pool: list):
        """Null values in pool are returned correctly."""
        result = decode_refs(sample_pool, 7)  # None
        assert result is None

    def test_boolean_value_resolved(self, sample_pool: list):
        """Boolean values in pool are returned correctly."""
        result = decode_refs(sample_pool, 8)  # True
        assert result is True


class TestExtractPool:
    """Tests for extract_pool function."""

    def test_extracts_from_standard_structure(self, sample_payload: dict):
        """Extracts pool from standard SvelteKit payload structure."""
        pool = extract_pool(sample_payload)
        assert isinstance(pool, list)
        assert len(pool) > 0
        assert "Avengers" in pool

    def test_raises_on_empty_payload(self):
        """Raises ValueError for empty payload."""
        with pytest.raises(ValueError, match="Could not locate pool"):
            extract_pool({})

    def test_raises_on_invalid_structure(self):
        """Raises ValueError for invalid structure."""
        with pytest.raises(ValueError, match="Could not locate pool"):
            extract_pool({"nodes": "not a list"})

    def test_fallback_search(self):
        """Falls back to searching for pool if not in expected location."""
        # Payload with pool in unexpected location
        payload = {
            "something": {
                "else": [
                    {"detailUrl": 0, "title": 1},
                    "url_value",
                    "title_value",
                ]
            }
        }
        pool = extract_pool(payload)
        assert isinstance(pool, list)


class TestIterPackedIssueDicts:
    """Tests for iter_packed_issue_dicts function."""

    def test_finds_issue_dicts(self, sample_payload: dict):
        """Finds packed issue dictionaries in pool."""
        pool = extract_pool(sample_payload)
        issues = list(iter_packed_issue_dicts(pool))

        assert len(issues) >= 1
        assert all("detailUrl" in i for i in issues)
        assert all("title" in i for i in issues)

    def test_filters_non_issue_items(self):
        """Filters out non-issue items from pool."""
        pool = [
            "string",
            123,
            {"other": "dict"},
            {"detailUrl": 0, "title": 1},  # Valid issue
            {"detailUrl": "not_int", "title": 1},  # Invalid - detailUrl not int
        ]
        issues = list(iter_packed_issue_dicts(pool))

        assert len(issues) == 1


class TestDecodeIssuesFromPayload:
    """Tests for decode_issues_from_payload function."""

    def test_decodes_issues(self, sample_payload: dict):
        """Decodes issues from payload."""
        issues = decode_issues_from_payload(sample_payload)

        assert len(issues) >= 1
        assert all("title" in i for i in issues)
        assert all("detailUrl" in i for i in issues)

    def test_normalizes_urls(self, sample_payload: dict):
        """URLs are normalized to https://www.marvel.com format."""
        issues = decode_issues_from_payload(sample_payload)

        for issue in issues:
            url = issue["detailUrl"]
            assert url.startswith("https://www.marvel.com/")

    def test_adds_year_page(self, sample_payload: dict):
        """Adds year_page field when provided."""
        issues = decode_issues_from_payload(sample_payload, year_page=2022)

        assert all(i.get("_year_page") == 2022 for i in issues)

    def test_handles_empty_payload(self):
        """Returns empty list for payload with no issues."""
        payload = {
            "nodes": [
                {"type": "skip"},
                {"type": "skip"},
                {"type": "data", "data": ["no", "issues", "here"]},
            ]
        }
        issues = decode_issues_from_payload(payload)
        assert issues == []
