"""Tests for SQLite database operations."""

import json
import os
import tempfile

from src.database import Database
from src.models import Strike, Target, Statement, Evidence


class TestDatabase:
    def _make_db(self) -> Database:
        db_path = os.path.join(tempfile.mkdtemp(), "test.db")
        return Database(db_path)

    def _make_strike(self, report_id: str = "test-001") -> Strike:
        return Strike(
            target=Target(name="Test Target", role="CEO", type="person"),
            statement=Statement(text="Test statement", source_url="https://test.com", date="2026-03-01"),
            verdict="SPINNING",
            evidence=[Evidence(claim="Contradicting data", source="SEC", source_url="https://sec.gov", date="2026-01-01")],
            strike="Test strike text. Question?",
            report_id=report_id,
            content_hash="deadbeef",
        )

    def test_save_and_retrieve(self):
        db = self._make_db()
        strike = self._make_strike()
        db.save_strike(strike)

        result = db.get_strike("test-001")
        assert result is not None
        assert result["verdict"] == "SPINNING"
        assert result["target"]["name"] == "Test Target"
        db.close()

    def test_get_nonexistent(self):
        db = self._make_db()
        result = db.get_strike("does-not-exist")
        assert result is None
        db.close()

    def test_queue(self):
        db = self._make_db()
        db.save_strike(self._make_strike("q-001"))
        db.save_strike(self._make_strike("q-002"))

        queue = db.get_queue()
        assert len(queue) == 2
        db.close()

    def test_approve(self):
        db = self._make_db()
        db.save_strike(self._make_strike("a-001"))

        assert db.approve_strike("a-001") is True
        queue = db.get_queue()
        assert len(queue) == 0

        data = db.get_strike("a-001")
        assert data["reviewed"] is True
        db.close()

    def test_approve_nonexistent(self):
        db = self._make_db()
        assert db.approve_strike("nope") is False
        db.close()

    def test_archive(self):
        db = self._make_db()
        db.save_strike(self._make_strike("arch-001"))
        db.approve_strike("arch-001")

        archive = db.get_archive()
        assert len(archive) == 1
        assert archive[0]["report_id"] == "arch-001"
        db.close()

    def test_stats(self):
        db = self._make_db()
        db.save_strike(self._make_strike("s-001"))
        db.save_strike(self._make_strike("s-002"))

        stats = db.get_stats()
        assert stats["total_strikes"] == 2
        assert stats["unique_targets"] == 1
        db.close()

    def test_add_scan_target(self):
        db = self._make_db()
        tid = db.add_scan_target(
            name="Senator Test",
            target_type="person",
            role="Senator",
            twitter_handle="@sentest",
            keywords=["economy", "jobs"],
        )
        assert tid > 0

        targets = db.get_scan_targets()
        assert len(targets) == 1
        assert targets[0]["name"] == "Senator Test"
        assert "economy" in targets[0]["keywords"]
        db.close()

    def test_mark_published(self):
        db = self._make_db()
        db.save_strike(self._make_strike("pub-001"))
        db.approve_strike("pub-001")
        db.mark_published("pub-001")
        # No error = success
        db.close()
