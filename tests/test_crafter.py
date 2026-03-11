"""Tests for Stage C — Crafter (unit tests without AI calls)."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from src.config import Config
from src.crafter import Crafter
from src.models import Target, Statement, Evidence, Strike


class TestCrafter:
    def _make_config(self) -> Config:
        config = Config.__new__(Config)
        config._data = {
            "ai": {
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "api_key_env": "GEMINI_API_KEY",
            },
            "style": "surgical",
        }
        return config

    def _make_target(self) -> Target:
        return Target(name="Test CEO", role="CEO of TestCorp", type="person")

    def _make_statement(self) -> Statement:
        return Statement(
            text="We have never shared user data.",
            source_url="https://twitter.com/testceo/123",
            date="2026-03-01",
        )

    def _make_evidence(self) -> list[Evidence]:
        return [
            Evidence(
                claim="TestCorp shared data with 47 third parties",
                source="FTC",
                source_url="https://ftc.gov/cases/testcorp",
                date="2025-09-01",
            ),
        ]

    def test_build_user_prompt(self):
        config = self._make_config()
        with patch("src.crafter.load_system_prompt", return_value="test prompt"):
            crafter = Crafter(config)

        prompt = crafter._build_user_prompt(
            self._make_target(),
            self._make_statement(),
            self._make_evidence(),
            "surgical",
        )
        assert "Test CEO" in prompt
        assert "never shared user data" in prompt
        assert "FTC" in prompt
        assert "surgical" in prompt

    def test_parse_valid_ai_response(self):
        config = self._make_config()
        with patch("src.crafter.load_system_prompt", return_value="test prompt"):
            crafter = Crafter(config)

        ai_json = json.dumps({
            "target": "Test CEO",
            "statement": "We have never shared user data.",
            "verdict": "LYING",
            "evidence": [
                {"claim": "Data was shared", "source": "FTC",
                 "source_url": "https://ftc.gov", "date": "2025-09-01"}
            ],
            "strike": "You said X. The FTC says Y. Which is it?",
        })

        strike = crafter._parse_ai_response(
            ai_json, self._make_target(), self._make_statement(), self._make_evidence()
        )
        assert isinstance(strike, Strike)
        assert strike.verdict == "LYING"
        assert "FTC" in strike.strike

    def test_parse_invalid_json_returns_fallback(self):
        config = self._make_config()
        with patch("src.crafter.load_system_prompt", return_value="test prompt"):
            crafter = Crafter(config)

        strike = crafter._parse_ai_response(
            "not valid json at all",
            self._make_target(), self._make_statement(), self._make_evidence()
        )
        assert isinstance(strike, Strike)
        assert strike.verdict == "INSUFFICIENT_EVIDENCE"

    def test_parse_markdown_wrapped_json(self):
        config = self._make_config()
        with patch("src.crafter.load_system_prompt", return_value="test prompt"):
            crafter = Crafter(config)

        ai_response = '```json\n{"verdict": "SPINNING", "evidence": [], "strike": "Test strike"}\n```'
        strike = crafter._parse_ai_response(
            ai_response, self._make_target(), self._make_statement(), []
        )
        assert strike.verdict == "SPINNING"

    def test_invalid_verdict_falls_back(self):
        config = self._make_config()
        with patch("src.crafter.load_system_prompt", return_value="test prompt"):
            crafter = Crafter(config)

        ai_json = json.dumps({
            "verdict": "TOTALLY_MADE_UP",
            "evidence": [],
            "strike": "test",
        })
        strike = crafter._parse_ai_response(
            ai_json, self._make_target(), self._make_statement(), []
        )
        assert strike.verdict == "INSUFFICIENT_EVIDENCE"

    def test_verdict_normalization(self):
        config = self._make_config()
        with patch("src.crafter.load_system_prompt", return_value="test prompt"):
            crafter = Crafter(config)

        # AI might return "BROKE PROMISE" with space instead of underscore
        ai_json = json.dumps({
            "verdict": "BROKE PROMISE",
            "evidence": [],
            "strike": "test",
        })
        strike = crafter._parse_ai_response(
            ai_json, self._make_target(), self._make_statement(), []
        )
        assert strike.verdict == "BROKE_PROMISE"
