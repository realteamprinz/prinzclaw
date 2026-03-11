"""Stage A — Acceleration/Analyze: Search for contradicting evidence."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from src.config import Config
from src.models import Target, Statement, Evidence

logger = logging.getLogger("prinzclaw")


class Analyzer:
    """Searches public records for evidence contradicting a statement."""

    def __init__(self, config: Config):
        self.config = config
        self.coherence_window_months = config.coherence_window_months

    def analyze(self, target: Target, statement: Statement) -> dict:
        """Analyze a statement and search for contradicting evidence.

        Returns analysis result dict with evidence found and suggested verdict.
        """
        logger.info("Analyzing statement by %s: %s...", target.name, statement.text[:80])

        cutoff_date = self._get_cutoff_date()
        evidence = []

        # Search for prior contradictory statements by the same target
        prior = self._search_prior_statements(target, statement, cutoff_date)
        evidence.extend(prior)

        # Search SEC filings if target is corporate
        if target.type in ("person", "organization"):
            sec = self._search_sec_filings(target, statement, cutoff_date)
            evidence.extend(sec)

        # Search public records and third-party reports
        public = self._search_public_records(target, statement, cutoff_date)
        evidence.extend(public)

        # Determine suggested verdict based on evidence found
        verdict = self._suggest_verdict(statement, evidence)

        return {
            "target": target,
            "statement": statement,
            "evidence": evidence,
            "suggested_verdict": verdict,
            "evidence_count": len(evidence),
            "coherence_window_cutoff": cutoff_date.isoformat(),
        }

    def _get_cutoff_date(self) -> datetime:
        """Calculate the coherence window cutoff date."""
        return datetime.now(timezone.utc) - timedelta(
            days=self.coherence_window_months * 30
        )

    def _search_prior_statements(self, target: Target, statement: Statement,
                                  cutoff: datetime) -> list[Evidence]:
        """Search for the target's own prior contradictory statements.

        This is the integration point for search APIs (Google, Bing, etc.).
        Real implementation would query news APIs and social media archives.
        """
        logger.info("Searching prior statements by %s within %d-month window",
                     target.name, self.coherence_window_months)
        # Integration point — returns empty until search API is configured
        return []

    def _search_sec_filings(self, target: Target, statement: Statement,
                             cutoff: datetime) -> list[Evidence]:
        """Search SEC EDGAR filings for contradicting data.

        Integration point for SEC EDGAR full-text search API.
        """
        logger.info("Searching SEC filings for %s", target.name)
        return []

    def _search_public_records(self, target: Target, statement: Statement,
                                cutoff: datetime) -> list[Evidence]:
        """Search public records, court filings, FTC records.

        Integration point for public record APIs.
        """
        logger.info("Searching public records for %s", target.name)
        return []

    def _suggest_verdict(self, statement: Statement,
                          evidence: list[Evidence]) -> str:
        """Suggest a verdict based on the evidence found.

        If no evidence found, returns INSUFFICIENT_EVIDENCE.
        Final verdict is determined by the AI crafter with human review.
        """
        if not evidence:
            return "INSUFFICIENT_EVIDENCE"

        # With evidence, defer to the AI crafter for nuanced verdict
        # This returns a preliminary suggestion only
        return "PENDING_AI_REVIEW"

    def add_manual_evidence(self, claim: str, source: str,
                             source_url: str, date: str) -> Evidence:
        """Create an Evidence object from manually provided data."""
        return Evidence(
            claim=claim,
            source=source,
            source_url=source_url,
            date=date,
        )
