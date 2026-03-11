"""Stage T — Tension/Scan: Monitor public channels for statements."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from src.config import Config
from src.models import Target, Statement

logger = logging.getLogger("prinzclaw")

# Claim-indicating keywords — statements containing these are more likely falsifiable
CLAIM_INDICATORS = [
    "never", "always", "guarantee", "promise", "zero", "100%", "no one",
    "everyone", "nobody", "all", "none", "will not", "did not", "have not",
    "is not", "are not", "was not", "safe", "secure", "transparent",
    "revenue", "growth", "profit", "declined", "increased", "reduced",
    "eliminated", "committed", "pledged", "vowed", "ensured",
]


class Scanner:
    """Monitors public channels for verifiable claims by tracked targets."""

    def __init__(self, config: Config):
        self.config = config
        self.platforms = config.scan_platforms
        self._targets = self._load_targets()

    def _load_targets(self) -> list[dict]:
        """Load targets from config."""
        targets = self.config.targets
        logger.info("Loaded %d scan targets", len(targets))
        return targets

    def scan_statement(self, text: str, target_name: str = "",
                       target_role: str = "", target_type: str = "person",
                       source_url: str = "", date: str = "") -> dict | None:
        """Evaluate a single statement for verifiable claims.

        Returns a scan result dict if the statement contains claims, or None.
        """
        if not text or not text.strip():
            return None

        confidence = self._assess_claim_confidence(text)
        if confidence < self.config.min_claim_confidence:
            logger.debug("Statement below confidence threshold (%.2f): %s...",
                         confidence, text[:80])
            return None

        if not date:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        target = Target(
            name=target_name or "Unknown",
            role=target_role or "Unknown",
            type=target_type if target_type in ("person", "organization", "government") else "person",
        )
        statement = Statement(
            text=text.strip(),
            source_url=source_url or "",
            date=date,
        )

        return {
            "target": target,
            "statement": statement,
            "claim_confidence": confidence,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }

    def _assess_claim_confidence(self, text: str) -> float:
        """Score how likely a statement contains a verifiable factual claim.

        Returns a float between 0.0 and 1.0.
        """
        text_lower = text.lower()
        score = 0.0

        # Check for claim-indicating keywords
        keyword_hits = sum(1 for kw in CLAIM_INDICATORS if kw in text_lower)
        score += min(keyword_hits * 0.15, 0.6)

        # Check for numbers/statistics (suggests verifiable data)
        if re.search(r"\d+%|\$\d+|\d+\s*(million|billion|trillion|percent)", text_lower):
            score += 0.25

        # Check for temporal claims (dates, timeframes)
        if re.search(r"\b(never|always|every|will|by \d{4}|this year|last year|next)\b", text_lower):
            score += 0.15

        # Penalize short statements (less likely to contain substantive claims)
        word_count = len(text.split())
        if word_count < 10:
            score *= 0.5
        elif word_count < 5:
            score *= 0.2

        # Penalize questions (not claims)
        if text.strip().endswith("?"):
            score *= 0.3

        return min(score, 1.0)

    async def scan_twitter(self, target: dict) -> list[dict]:
        """Scan Twitter/X for statements by a target.

        Requires TWITTER_BEARER_TOKEN env var. Returns list of scan results.
        This is a stub — real implementation requires Twitter API v2 access.
        """
        handle = target.get("twitter_handle", "")
        if not handle:
            return []

        logger.info("Twitter scan for %s — requires TWITTER_BEARER_TOKEN", handle)
        # Twitter API integration point — returns empty until configured
        # Real implementation would use tweepy or httpx to call Twitter API v2
        return []

    async def scan_rss(self, feeds: list[str] | None = None) -> list[dict]:
        """Scan RSS feeds for statements.

        This is a stub — real implementation uses feedparser.
        """
        logger.info("RSS scan — requires feed URLs in config")
        return []

    async def scan_sec_edgar(self, company_cik: str = "") -> list[dict]:
        """Scan SEC EDGAR for corporate filings.

        This is a stub — real implementation uses SEC EDGAR API.
        """
        logger.info("SEC EDGAR scan — requires company CIK")
        return []
