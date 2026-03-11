"""Tests for utility functions."""

from src.models import Strike, Target, Statement, Evidence
from src.utils import (
    compute_content_hash,
    sanitize_input,
    is_within_coherence_window,
    truncate_for_twitter,
)


class TestContentHash:
    def test_hash_is_sha256(self):
        strike = Strike(
            target=Target(name="Test", role="CEO", type="person"),
            statement=Statement(text="Test", source_url="https://x.com", date="2026-01-01"),
            verdict="LYING",
            evidence=[],
            strike="Strike text",
        )
        h = compute_content_hash(strike)
        assert len(h) == 64  # SHA-256 hex length
        assert all(c in "0123456789abcdef" for c in h)

    def test_same_input_same_hash(self):
        kwargs = dict(
            target=Target(name="X", role="Y", type="person"),
            statement=Statement(text="Z", source_url="", date="2026-01-01"),
            verdict="VERIFIED",
            evidence=[],
            strike="Test",
            report_id="fixed-id",
            timestamp="2026-03-10T00:00:00Z",
        )
        s1 = Strike(**kwargs)
        s2 = Strike(**kwargs)
        assert compute_content_hash(s1) == compute_content_hash(s2)

    def test_different_verdict_different_hash(self):
        base = dict(
            target=Target(name="X", role="Y", type="person"),
            statement=Statement(text="Z", source_url="", date="2026-01-01"),
            evidence=[],
            strike="Test",
            report_id="fixed",
            timestamp="2026-03-10T00:00:00Z",
        )
        s1 = Strike(verdict="LYING", **base)
        s2 = Strike(verdict="VERIFIED", **base)
        assert compute_content_hash(s1) != compute_content_hash(s2)


class TestSanitizeInput:
    def test_strips_whitespace(self):
        assert sanitize_input("  hello  ") == "hello"

    def test_escapes_html(self):
        result = sanitize_input('<script>alert("xss")</script>')
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_removes_control_chars(self):
        result = sanitize_input("hello\x00world\x08test")
        assert "\x00" not in result
        assert "\x08" not in result
        assert "helloworld" in result


class TestCoherenceWindow:
    def test_recent_date_is_within(self):
        assert is_within_coherence_window("2026-03-01T00:00:00Z", 11) is True

    def test_old_date_is_outside(self):
        assert is_within_coherence_window("2020-01-01T00:00:00Z", 11) is False

    def test_invalid_date_returns_false(self):
        assert is_within_coherence_window("not-a-date") is False

    def test_empty_string_returns_false(self):
        assert is_within_coherence_window("") is False


class TestTruncateForTwitter:
    def test_short_text_unchanged(self):
        text = "This is short."
        assert truncate_for_twitter(text) == text

    def test_long_text_truncated(self):
        text = "x " * 200
        result = truncate_for_twitter(text, max_len=280)
        assert len(result) <= 280
        assert result.endswith("...")

    def test_exactly_280_unchanged(self):
        text = "x" * 280
        assert truncate_for_twitter(text) == text
