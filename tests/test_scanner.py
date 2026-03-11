"""Tests for Stage T — Scanner."""

from src.config import Config
from src.scanner import Scanner


class TestScanner:
    def _make_scanner(self) -> Scanner:
        config = Config.__new__(Config)
        config._data = {
            "scan": {
                "platforms": ["twitter", "rss"],
                "scan_interval_minutes": 15,
                "min_claim_confidence": 0.7,
                "coherence_window_months": 11,
            },
            "targets": [],
        }
        return Scanner(config)

    def test_scan_verifiable_statement(self):
        scanner = self._make_scanner()
        result = scanner.scan_statement(
            text="Our revenue grew 200% this quarter and we will never lay off employees",
            target_name="Test CEO",
            target_role="CEO",
            source_url="https://example.com",
        )
        assert result is not None
        assert result["target"].name == "Test CEO"
        assert result["claim_confidence"] > 0

    def test_scan_filters_out_opinion(self):
        scanner = self._make_scanner()
        result = scanner.scan_statement(
            text="Nice weather today",
            target_name="Someone",
        )
        assert result is None

    def test_scan_filters_out_empty(self):
        scanner = self._make_scanner()
        result = scanner.scan_statement(text="")
        assert result is None

    def test_scan_filters_out_question(self):
        scanner = self._make_scanner()
        result = scanner.scan_statement(text="What do you think about this?")
        assert result is None

    def test_claim_confidence_with_numbers(self):
        scanner = self._make_scanner()
        score = scanner._assess_claim_confidence(
            "Revenue increased 50% to $2 billion this quarter"
        )
        assert score > 0.2

    def test_claim_confidence_with_absolutes(self):
        scanner = self._make_scanner()
        score = scanner._assess_claim_confidence(
            "We have never and will never share user data with third parties"
        )
        assert score >= 0.3

    def test_claim_confidence_low_for_pleasantries(self):
        scanner = self._make_scanner()
        score = scanner._assess_claim_confidence("Thanks for having me")
        assert score < 0.7

    def test_scan_assigns_date_if_missing(self):
        scanner = self._make_scanner()
        # Use a statement with high confidence to ensure it passes the threshold
        result = scanner.scan_statement(
            text="We guarantee 100% uptime for all customers and we will never have any downtime ever again, revenue grew 200%",
            target_name="CTO",
        )
        assert result is not None
        assert result["statement"].date != ""
