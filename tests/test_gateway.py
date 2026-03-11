"""Tests for the OpenClaw gateway endpoints."""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from src.config import Config
from src.database import Database
from src.scanner import Scanner
from src.analyzer import Analyzer
from src.crafter import Crafter
from src.publisher import Publisher
from src.gateway import Gateway


def make_test_config(db_path: str) -> Config:
    config = Config.__new__(Config)
    config._data = {
        "ai": {"provider": "gemini", "model": "gemini-2.5-flash", "api_key_env": "GEMINI_API_KEY"},
        "scan": {
            "platforms": ["twitter"],
            "scan_interval_minutes": 15,
            "min_claim_confidence": 0.3,  # Low threshold for testing
            "coherence_window_months": 11,
        },
        "targets": [],
        "style": "surgical",
        "output": {
            "mode": "semi_auto",
            "review_required": True,
            "publish_to": ["local_db"],
            "local_db_path": db_path,
        },
        "archive": {"enabled": False, "api_url": ""},
        "gateway": {"host": "0.0.0.0", "port": 8100},
        "logging": {"level": "INFO", "file": "/tmp/prinzclaw_test.log"},
    }
    return config


@pytest.fixture
def gateway_app(tmp_path):
    db_path = str(tmp_path / "test.db")
    config = make_test_config(db_path)
    db = Database(db_path)
    scanner = Scanner(config)
    analyzer = Analyzer(config)

    with patch("src.crafter.load_system_prompt", return_value="test prompt"):
        crafter = Crafter(config)

    publisher = Publisher(config, db)
    gw = Gateway(config, db, scanner, analyzer, crafter, publisher)
    return gw.app


@pytest.mark.asyncio
async def test_health(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.get("/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "operational"
    assert data["agent"] == "prinzclaw"
    assert data["protocol"] == "openclaw-v1"


@pytest.mark.asyncio
async def test_stats(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.get("/stats")
    assert resp.status == 200
    data = await resp.json()
    assert "total_strikes" in data
    assert "unique_targets" in data


@pytest.mark.asyncio
async def test_queue_empty(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.get("/queue")
    assert resp.status == 200
    data = await resp.json()
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_archive_empty(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.get("/archive")
    assert resp.status == 200
    data = await resp.json()
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_analyze_missing_statement(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.post("/analyze", json={})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_scan_target(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.post("/scan", json={
        "target_name": "Test CEO",
        "twitter_handle": "@testceo",
        "keywords": ["revenue", "growth"],
    })
    assert resp.status == 201
    data = await resp.json()
    assert data["status"] == "scanning"


@pytest.mark.asyncio
async def test_scan_missing_target(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.post("/scan", json={})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_approve_nonexistent(aiohttp_client, gateway_app):
    client = await aiohttp_client(gateway_app)
    resp = await client.post("/approve/nonexistent-id")
    assert resp.status == 404
