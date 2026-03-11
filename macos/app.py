"""prinzclaw macOS menubar application.

Launches the agent gateway and provides a menubar status icon.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import webbrowser
from pathlib import Path

import rumps

from macos import paths
from macos.keychain import get_api_key_for_provider, store_key
from macos.gateway_mac import create_mac_gateway

logger = logging.getLogger("prinzclaw")

DASHBOARD_URL = "http://localhost:8100"
SETUP_URL = "http://localhost:8100/setup"


class PrinzclawApp(rumps.App):
    """macOS menubar application for prinzclaw agent."""

    def __init__(self):
        super().__init__(
            name="prinzclaw",
            title="P",  # Red P in menubar (styled by the icon if available)
            quit_button=None,  # Custom quit to do cleanup
        )

        # Try to load a proper icon if bundled
        icon_path = self._find_icon()
        if icon_path:
            self.icon = icon_path

        self._gateway_thread: threading.Thread | None = None
        self._running = False

        self.menu = [
            rumps.MenuItem("Open Dashboard", callback=self.open_dashboard),
            rumps.MenuItem("Agent Status: Starting...", callback=None),
            None,  # Separator
            rumps.MenuItem("View Logs", callback=self.open_logs),
            rumps.MenuItem("Open Config", callback=self.open_config),
            None,  # Separator
            rumps.MenuItem("Quit prinzclaw", callback=self.quit_app),
        ]

    def _find_icon(self) -> str | None:
        """Find the app icon from various locations."""
        candidates = [
            Path(__file__).parent / "resources" / "icon.png",
            Path(getattr(sys, "_MEIPASS", "")) / "resources" / "icon.png",
        ]
        # If running as .app bundle
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "icon.png")

        for c in candidates:
            if c.exists():
                return str(c)
        return None

    def _setup_environment(self) -> None:
        """Set up macOS paths and install defaults."""
        paths.ensure_dirs()
        paths.install_default_config(
            getattr(sys, "_MEIPASS", None)
        )

    def _inject_keychain_key(self) -> None:
        """Load API key from Keychain into environment for the agent."""
        # Read provider from config
        import yaml
        provider = "gemini"
        if paths.CONFIG_PATH.exists():
            with open(paths.CONFIG_PATH) as f:
                cfg = yaml.safe_load(f) or {}
            provider = cfg.get("ai", {}).get("provider", "gemini")

        env_map = {
            "gemini": "GEMINI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        env_var = env_map.get(provider, "GEMINI_API_KEY")

        # Only inject if not already set
        if not os.environ.get(env_var):
            key = get_api_key_for_provider(provider)
            if key:
                os.environ[env_var] = key
                logger.info("Loaded %s from Keychain", env_var)

    def _start_gateway(self) -> None:
        """Start the agent gateway in a background thread."""
        self._running = True

        def run():
            try:
                create_mac_gateway()
            except Exception as e:
                logger.error("Gateway error: %s", e)
                rumps.notification(
                    "prinzclaw",
                    "Gateway Error",
                    str(e),
                )

        self._gateway_thread = threading.Thread(target=run, daemon=True)
        self._gateway_thread.start()

        # Update status
        self.menu["Agent Status: Starting..."].title = "Agent Status: Running (port 8100)"

    @rumps.clicked("Open Dashboard")
    def open_dashboard(self, _=None):
        if paths.is_first_run():
            webbrowser.open(SETUP_URL)
        else:
            webbrowser.open(DASHBOARD_URL)

    @rumps.clicked("View Logs")
    def open_logs(self, _=None):
        log_file = paths.LOG_DIR / "prinzclaw.log"
        if log_file.exists():
            os.system(f'open -a Console "{log_file}"')
        else:
            os.system(f'open "{paths.LOG_DIR}"')

    @rumps.clicked("Open Config")
    def open_config(self, _=None):
        if paths.CONFIG_PATH.exists():
            os.system(f'open -t "{paths.CONFIG_PATH}"')
        else:
            os.system(f'open "{paths.APP_SUPPORT}"')

    @rumps.clicked("Quit prinzclaw")
    def quit_app(self, _=None):
        self._running = False
        logger.info("prinzclaw agent shutting down")
        rumps.quit_application()


def setup_mac_logging() -> None:
    """Configure logging for macOS app."""
    paths.ensure_dirs()
    log_file = paths.LOG_DIR / "prinzclaw.log"

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(str(log_file))
    file_handler.setFormatter(formatter)

    root = logging.getLogger("prinzclaw")
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)


def main():
    """Launch the prinzclaw macOS app."""
    setup_mac_logging()
    logger.info("prinzclaw macOS app starting")

    app = PrinzclawApp()
    app._setup_environment()
    app._inject_keychain_key()
    app._start_gateway()

    # Open dashboard on first launch
    if paths.is_first_run():
        threading.Timer(1.5, lambda: webbrowser.open(SETUP_URL)).start()
    else:
        threading.Timer(1.5, lambda: webbrowser.open(DASHBOARD_URL)).start()

    app.run()


if __name__ == "__main__":
    main()
