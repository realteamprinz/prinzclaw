"""Stage O — Observer/Output: Review queue, approval, publishing."""

from __future__ import annotations

import json
import logging

import httpx

from src.config import Config
from src.database import Database
from src.models import Strike

logger = logging.getLogger("prinzclaw")


class Publisher:
    """Manages the review queue and publishes approved Strikes."""

    def __init__(self, config: Config, db: Database):
        self.config = config
        self.db = db

    def queue_for_review(self, strike: Strike) -> str:
        """Save a Strike draft to the database for human review.

        Returns the report_id.
        """
        self.db.save_strike(strike)
        logger.info("Strike %s queued for review — target: %s, verdict: %s",
                     strike.report_id, strike.target.name, strike.verdict)
        return strike.report_id

    def get_queue(self) -> list[dict]:
        """Get all pending Strike drafts."""
        return self.db.get_queue()

    def approve(self, report_id: str) -> dict | None:
        """Approve a Strike for publication.

        Returns the approved Strike dict, or None if not found.
        """
        success = self.db.approve_strike(report_id)
        if not success:
            logger.warning("Strike %s not found for approval", report_id)
            return None

        strike_data = self.db.get_strike(report_id)
        logger.info("Strike %s APPROVED", report_id)

        # Auto-publish to configured platforms
        self._publish(report_id, strike_data)

        return strike_data

    def _publish(self, report_id: str, strike_data: dict) -> None:
        """Publish an approved Strike to configured platforms."""
        platforms = self.config.publish_to

        for platform in platforms:
            if platform == "local_db":
                self.db.mark_published(report_id)
                logger.info("Strike %s saved to local archive", report_id)

            elif platform == "prinzit_archive" and self.config.archive_enabled:
                self._submit_to_prinzit(strike_data)

            elif platform == "twitter":
                self._publish_to_twitter(strike_data)

    def _submit_to_prinzit(self, strike_data: dict) -> None:
        """Submit a Strike to the prinzit.ai public archive."""
        url = f"{self.config.archive_api_url}/submit"
        try:
            response = httpx.post(url, json=strike_data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                logger.info("Strike submitted to prinzit.ai — archive_id: %s",
                             result.get("archive_id"))
            else:
                logger.warning("prinzit.ai submission failed: %d %s",
                                response.status_code, response.text)
        except httpx.RequestError as e:
            logger.error("Failed to reach prinzit.ai: %s", e)

    def _publish_to_twitter(self, strike_data: dict) -> None:
        """Publish a Strike to Twitter/X.

        Stub — requires Twitter API OAuth credentials.
        """
        logger.info("Twitter publishing stub — requires TWITTER_API_KEY configuration")

    def get_archive(self) -> list[dict]:
        """Get all published Strikes."""
        return self.db.get_archive()

    def get_stats(self) -> dict:
        """Get agent statistics."""
        return self.db.get_stats()
