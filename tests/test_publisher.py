"""Tests for Stage O — Publisher."""

import os
import tempfile

from src.config import Config
from src.database import Database
from src.models import Strike, Target, Statement, Evidence
from src.publisher import Publisher


class TestPublisher:
    def _setup(self):
        db_path = os.path.join(tempfile.mkdtemp(), "test_strikes.db")
        config = Config.__new__(Config)
        config._data = {
            "output": {
                "mode": "semi_auto",
                "review_required": True,
                "publish_to": ["local_db"],
                "local_db_path": db_path,
            },
            "archive": {"enabled": False, "api_url": ""},
        }
        db = Database(db_path)
        publisher = Publisher(config, db)
        return publisher, db

    def _make_strike(self) -> Strike:
        return Strike(
            target=Target(name="Test CEO", role="CEO", type="person"),
            statement=Statement(
                text="Revenue grew 500%",
                source_url="https://example.com",
                date="2026-03-01",
            ),
            verdict="LYING",
            evidence=[
                Evidence(
                    claim="Revenue actually declined 10%",
                    source="SEC Filing",
                    source_url="https://sec.gov/test",
                    date="2026-02-15",
                ),
            ],
            strike="You said revenue grew 500%. Your SEC filing shows a 10% decline. Which is it?",
            content_hash="abc123",
        )

    def test_queue_for_review(self):
        publisher, db = self._setup()
        strike = self._make_strike()
        report_id = publisher.queue_for_review(strike)
        assert report_id == strike.report_id

        queue = publisher.get_queue()
        assert len(queue) == 1
        assert queue[0]["report_id"] == strike.report_id
        db.close()

    def test_approve_strike(self):
        publisher, db = self._setup()
        strike = self._make_strike()
        publisher.queue_for_review(strike)

        result = publisher.approve(strike.report_id)
        assert result is not None
        assert result["reviewed"] is True

        # Queue should be empty after approval
        queue = publisher.get_queue()
        assert len(queue) == 0
        db.close()

    def test_approve_nonexistent(self):
        publisher, db = self._setup()
        result = publisher.approve("nonexistent-id")
        assert result is None
        db.close()

    def test_get_archive(self):
        publisher, db = self._setup()
        strike = self._make_strike()
        publisher.queue_for_review(strike)
        publisher.approve(strike.report_id)

        archive = publisher.get_archive()
        assert len(archive) == 1
        assert archive[0]["verdict"] == "LYING"
        db.close()

    def test_get_stats(self):
        publisher, db = self._setup()
        strike = self._make_strike()
        publisher.queue_for_review(strike)

        stats = publisher.get_stats()
        assert stats["total_strikes"] == 1
        assert stats["unique_targets"] == 1
        assert "LYING" in stats["verdicts"]
        db.close()
