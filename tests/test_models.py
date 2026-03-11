"""Tests for prinzclaw data models."""

import json
import uuid
from src.models import Strike, Target, Statement, Evidence, VALID_VERDICTS


class TestTarget:
    def test_create_target(self):
        t = Target(name="Test CEO", role="CEO", type="person")
        assert t.name == "Test CEO"
        assert t.role == "CEO"
        assert t.type == "person"

    def test_target_to_dict(self):
        t = Target(name="Test CEO", role="CEO", type="organization")
        d = t.to_dict()
        assert d == {"name": "Test CEO", "role": "CEO", "type": "organization"}


class TestStatement:
    def test_create_statement(self):
        s = Statement(text="We never share data", source_url="https://example.com", date="2026-01-01")
        assert s.text == "We never share data"
        assert s.source_url == "https://example.com"

    def test_statement_to_dict(self):
        s = Statement(text="Test", source_url="https://x.com", date="2026-03-01")
        d = s.to_dict()
        assert "text" in d
        assert "source_url" in d
        assert "date" in d


class TestEvidence:
    def test_create_evidence(self):
        e = Evidence(
            claim="Data was shared with third parties",
            source="FTC",
            source_url="https://ftc.gov/example",
            date="2025-06-15",
        )
        assert e.claim == "Data was shared with third parties"
        assert e.source == "FTC"

    def test_evidence_to_dict(self):
        e = Evidence(claim="X", source="Y", source_url="https://y.com", date="2026-01-01")
        d = e.to_dict()
        assert d["claim"] == "X"
        assert d["source_url"] == "https://y.com"


class TestStrike:
    def _make_strike(self, verdict="LYING") -> Strike:
        return Strike(
            target=Target(name="Test CEO", role="CEO of TestCorp", type="person"),
            statement=Statement(
                text="We have never shared user data.",
                source_url="https://twitter.com/testceo/status/123",
                date="2026-03-01",
            ),
            verdict=verdict,
            evidence=[
                Evidence(
                    claim="TestCorp shared data with 47 third parties",
                    source="FTC",
                    source_url="https://ftc.gov/cases/testcorp",
                    date="2025-09-01",
                ),
            ],
            strike="You said you never shared user data. The FTC found 47 third-party data sharing agreements. Which is it?",
        )

    def test_strike_has_uuid(self):
        s = self._make_strike()
        uuid.UUID(s.report_id)  # Raises if not valid UUID

    def test_strike_has_timestamp(self):
        s = self._make_strike()
        assert s.timestamp.endswith("Z")

    def test_strike_signature(self):
        s = self._make_strike()
        assert s.signature == "FORGED WITH PRINZCLAW"

    def test_strike_version(self):
        s = self._make_strike()
        assert s.prinzclaw_version == "1.0"

    def test_strike_to_dict(self):
        s = self._make_strike()
        d = s.to_dict()
        assert d["prinzclaw_version"] == "1.0"
        assert d["verdict"] == "LYING"
        assert d["signature"] == "FORGED WITH PRINZCLAW"
        assert d["target"]["name"] == "Test CEO"
        assert len(d["evidence"]) == 1
        assert d["reviewed"] is False

    def test_strike_to_dict_valid_json(self):
        s = self._make_strike()
        d = s.to_dict()
        raw = json.dumps(d)
        parsed = json.loads(raw)
        assert parsed["report_id"] == s.report_id

    def test_strike_from_dict(self):
        s = self._make_strike()
        d = s.to_dict()
        restored = Strike.from_dict(d)
        assert restored.report_id == s.report_id
        assert restored.verdict == s.verdict
        assert restored.target.name == s.target.name
        assert len(restored.evidence) == len(s.evidence)

    def test_all_verdicts_valid(self):
        for v in VALID_VERDICTS:
            s = self._make_strike(verdict=v)
            assert s.verdict == v

    def test_strike_default_reviewed_false(self):
        s = self._make_strike()
        assert s.reviewed is False
