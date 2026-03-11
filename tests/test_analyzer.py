"""Tests for Stage A — Analyzer."""

from src.config import Config
from src.analyzer import Analyzer
from src.models import Target, Statement, Evidence


class TestAnalyzer:
    def _make_analyzer(self) -> Analyzer:
        config = Config.__new__(Config)
        config._data = {
            "scan": {"coherence_window_months": 11},
        }
        return Analyzer(config)

    def test_analyze_returns_structure(self):
        analyzer = self._make_analyzer()
        target = Target(name="Test CEO", role="CEO", type="person")
        statement = Statement(
            text="We never share data",
            source_url="https://example.com",
            date="2026-03-01",
        )
        result = analyzer.analyze(target, statement)
        assert "evidence" in result
        assert "suggested_verdict" in result
        assert "evidence_count" in result
        assert "coherence_window_cutoff" in result

    def test_no_evidence_gives_insufficient(self):
        analyzer = self._make_analyzer()
        target = Target(name="Test", role="CEO", type="person")
        statement = Statement(text="X", source_url="", date="2026-01-01")
        result = analyzer.analyze(target, statement)
        assert result["suggested_verdict"] == "INSUFFICIENT_EVIDENCE"
        assert result["evidence_count"] == 0

    def test_add_manual_evidence(self):
        analyzer = self._make_analyzer()
        e = analyzer.add_manual_evidence(
            claim="Data was shared",
            source="FTC",
            source_url="https://ftc.gov/test",
            date="2025-08-01",
        )
        assert isinstance(e, Evidence)
        assert e.claim == "Data was shared"
        assert e.source_url == "https://ftc.gov/test"

    def test_coherence_window_cutoff(self):
        analyzer = self._make_analyzer()
        cutoff = analyzer._get_cutoff_date()
        # Cutoff should be roughly 11 months ago
        from datetime import datetime, timezone, timedelta
        expected = datetime.now(timezone.utc) - timedelta(days=330)
        diff = abs((cutoff - expected).total_seconds())
        assert diff < 86400  # Within one day
