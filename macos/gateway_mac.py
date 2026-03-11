"""macOS-adapted gateway — serves dashboard UI and handles first-run setup."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import yaml
from aiohttp import web

from macos import paths
from macos.keychain import store_key
from src.config import Config
from src.database import Database
from src.scanner import Scanner
from src.analyzer import Analyzer
from src.crafter import Crafter
from src.publisher import Publisher
from src.gateway import Gateway

logger = logging.getLogger("prinzclaw")


def _find_dashboard_dir() -> Path:
    """Locate the dashboard HTML files."""
    candidates = [
        Path(__file__).parent / "dashboard",
        Path(getattr(sys, "_MEIPASS", "")) / "dashboard",
    ]
    for c in candidates:
        if c.exists() and (c / "index.html").exists():
            return c
    # Fallback
    return Path(__file__).parent / "dashboard"


def _build_mac_config() -> Config:
    """Build a Config pointing to macOS-native paths."""
    config = Config(str(paths.CONFIG_PATH))
    # Override paths to macOS locations
    config._data["output"]["local_db_path"] = str(paths.DB_PATH)
    config._data["logging"]["file"] = str(paths.LOG_DIR / "prinzclaw.log")
    config._data["gateway"]["host"] = "127.0.0.1"
    config._data["gateway"]["port"] = 8100
    return config


class MacGateway(Gateway):
    """Extended gateway that serves the web dashboard and setup endpoint."""

    def __init__(self, config, db, scanner, analyzer, crafter, publisher):
        super().__init__(config, db, scanner, analyzer, crafter, publisher)
        self._dashboard_dir = _find_dashboard_dir()
        self._add_mac_routes()

    def _add_mac_routes(self):
        # Dashboard routes (must come after API routes)
        self.app.router.add_post("/setup", self.handle_setup)
        self.app.router.add_get("/setup", self.serve_setup_page)
        self.app.router.add_get("/", self.serve_dashboard)
        # Static fallback for dashboard assets
        if self._dashboard_dir.exists():
            self.app.router.add_static("/static/", self._dashboard_dir)

    async def serve_dashboard(self, request: web.Request) -> web.Response:
        """Serve the main dashboard HTML."""
        html_path = self._dashboard_dir / "index.html"
        if html_path.exists():
            return web.FileResponse(html_path)
        return web.Response(text="Dashboard not found", status=404)

    async def serve_setup_page(self, request: web.Request) -> web.Response:
        """Serve the first-run setup page."""
        html_path = self._dashboard_dir / "setup.html"
        if html_path.exists():
            return web.FileResponse(html_path)
        return web.Response(text="Setup page not found", status=404)

    async def handle_setup(self, request: web.Request) -> web.Response:
        """POST /setup — Handle first-run configuration."""
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        provider = body.get("provider", "gemini")
        model = body.get("model", "gemini-2.5-flash")
        api_key = body.get("api_key", "")

        # Store API key in Keychain
        if api_key:
            env_map = {
                "gemini": "GEMINI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
            }
            account = env_map.get(provider, "GEMINI_API_KEY")
            store_key(account, api_key)
            os.environ[account] = api_key
            logger.info("API key stored in Keychain for %s", provider)

        # Update config file
        config_data = {}
        if paths.CONFIG_PATH.exists():
            with open(paths.CONFIG_PATH) as f:
                config_data = yaml.safe_load(f) or {}

        if "ai" not in config_data:
            config_data["ai"] = {}
        config_data["ai"]["provider"] = provider
        config_data["ai"]["model"] = model
        config_data["ai"]["api_key_env"] = env_map.get(provider, "GEMINI_API_KEY")

        # Add target if provided
        target = body.get("target")
        if target and target.get("name"):
            if "targets" not in config_data:
                config_data["targets"] = []
            config_data["targets"].append({
                "name": target["name"],
                "type": "person",
                "twitter_handle": target.get("twitter_handle", ""),
                "keywords": target.get("keywords", []),
            })

            # Also add to database
            self.db.add_scan_target(
                name=target["name"],
                twitter_handle=target.get("twitter_handle", ""),
                keywords=target.get("keywords", []),
            )

        with open(paths.CONFIG_PATH, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        # Mark setup as complete
        paths.mark_setup_complete()

        # Reload crafter with new API key
        self.crafter._api_key = api_key
        self.crafter._provider = provider
        self.crafter._model = model

        logger.info("First-run setup complete: provider=%s", provider)
        return web.json_response({"status": "ok", "provider": provider})


def create_mac_gateway() -> None:
    """Create and run the macOS-adapted gateway."""
    config = _build_mac_config()

    # Ensure prompts are accessible
    prompt_path = paths.PROMPTS_DIR / "system_prompt.md"
    if not prompt_path.exists():
        paths.install_default_config()

    # Point the system prompt loader to the right place
    os.environ["PRINZCLAW_PROMPTS_DIR"] = str(paths.PROMPTS_DIR)

    db = Database(str(paths.DB_PATH))
    scanner = Scanner(config)
    analyzer = Analyzer(config)

    # Patch prompt loading to use macOS path
    import src.utils
    original_load = src.utils.load_system_prompt

    def mac_load_prompt(path: str = None) -> str:
        mac_path = str(paths.PROMPTS_DIR / "system_prompt.md")
        if Path(mac_path).exists():
            return original_load(mac_path)
        return original_load(path or "prompts/system_prompt.md")

    src.utils.load_system_prompt = mac_load_prompt

    crafter = Crafter(config)
    publisher = Publisher(config, db)

    gateway = MacGateway(config, db, scanner, analyzer, crafter, publisher)

    logger.info("macOS gateway starting on 127.0.0.1:8100")
    web.run_app(gateway.app, host="127.0.0.1", port=8100, print=None)
