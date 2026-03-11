"""Configuration loader — reads prinzclaw.yaml and environment variables."""

from __future__ import annotations

import os
import yaml
import logging
from pathlib import Path

logger = logging.getLogger("prinzclaw")

DEFAULT_CONFIG = {
    "ai": {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "api_key_env": "GEMINI_API_KEY",
    },
    "scan": {
        "platforms": ["twitter", "rss"],
        "scan_interval_minutes": 15,
        "min_claim_confidence": 0.7,
        "coherence_window_months": 11,
    },
    "targets": [],
    "style": "surgical",
    "output": {
        "mode": "semi_auto",
        "review_required": True,
        "publish_to": ["local_db"],
        "local_db_path": "./data/strikes.db",
    },
    "archive": {
        "enabled": False,
        "api_url": "https://prinzit.ai/api/v1",
    },
    "gateway": {
        "host": "0.0.0.0",
        "port": 8100,
    },
    "logging": {
        "level": "INFO",
        "file": "./logs/prinzclaw.log",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    """Loads and provides access to prinzclaw configuration."""

    def __init__(self, config_path: str | None = None):
        self._data = DEFAULT_CONFIG.copy()
        self._config_path = config_path or self._find_config()
        if self._config_path and Path(self._config_path).exists():
            self._load_file(self._config_path)
        else:
            logger.warning("No prinzclaw.yaml found — using defaults")

    def _find_config(self) -> str | None:
        candidates = [
            "prinzclaw.yaml",
            "prinzclaw.yml",
            os.environ.get("PRINZCLAW_CONFIG", ""),
        ]
        for c in candidates:
            if c and Path(c).exists():
                return c
        return None

    def _load_file(self, path: str) -> None:
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}
        self._data = _deep_merge(self._data, raw)
        logger.info("Loaded config from %s", path)

    def get_ai_api_key(self) -> str:
        env_var = self._data["ai"]["api_key_env"]
        key = os.environ.get(env_var, "")
        if not key:
            logger.warning("API key env var %s is not set", env_var)
        return key

    @property
    def ai_provider(self) -> str:
        return self._data["ai"]["provider"]

    @property
    def ai_model(self) -> str:
        return self._data["ai"]["model"]

    @property
    def scan_interval(self) -> int:
        return self._data["scan"]["scan_interval_minutes"]

    @property
    def scan_platforms(self) -> list[str]:
        return self._data["scan"]["platforms"]

    @property
    def coherence_window_months(self) -> int:
        return self._data["scan"]["coherence_window_months"]

    @property
    def min_claim_confidence(self) -> float:
        return self._data["scan"]["min_claim_confidence"]

    @property
    def targets(self) -> list[dict]:
        return self._data.get("targets", [])

    @property
    def style(self) -> str:
        return self._data.get("style", "surgical")

    @property
    def output_mode(self) -> str:
        return self._data["output"]["mode"]

    @property
    def review_required(self) -> bool:
        return self._data["output"]["review_required"]

    @property
    def publish_to(self) -> list[str]:
        return self._data["output"]["publish_to"]

    @property
    def db_path(self) -> str:
        return self._data["output"]["local_db_path"]

    @property
    def archive_enabled(self) -> bool:
        return self._data["archive"]["enabled"]

    @property
    def archive_api_url(self) -> str:
        return self._data["archive"]["api_url"]

    @property
    def gateway_host(self) -> str:
        return self._data["gateway"]["host"]

    @property
    def gateway_port(self) -> int:
        return self._data["gateway"]["port"]

    @property
    def log_level(self) -> str:
        return self._data["logging"]["level"]

    @property
    def log_file(self) -> str:
        return self._data["logging"]["file"]

    @property
    def raw(self) -> dict:
        return self._data
