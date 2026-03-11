"""macOS-native path management for prinzclaw."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

APP_SUPPORT = Path.home() / "Library" / "Application Support" / "prinzclaw"
LOG_DIR = Path.home() / "Library" / "Logs" / "prinzclaw"
CONFIG_PATH = APP_SUPPORT / "prinzclaw.yaml"
DB_PATH = APP_SUPPORT / "data" / "strikes.db"
PROMPTS_DIR = APP_SUPPORT / "prompts"
FIRST_RUN_MARKER = APP_SUPPORT / ".setup_complete"


def ensure_dirs() -> None:
    """Create all required macOS directories."""
    (APP_SUPPORT / "data").mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)


def is_first_run() -> bool:
    """Check if this is the first launch."""
    return not FIRST_RUN_MARKER.exists()


def mark_setup_complete() -> None:
    """Mark first-run setup as complete."""
    FIRST_RUN_MARKER.touch()


def install_default_config(bundle_resources: str | None = None) -> None:
    """Copy default config and prompts if they don't exist."""
    if bundle_resources:
        res = Path(bundle_resources)
    else:
        # Fallback: relative to this file's location for dev mode
        res = Path(__file__).parent.parent

    # Copy config template
    if not CONFIG_PATH.exists():
        src_config = res / "prinzclaw.example.yaml"
        if src_config.exists():
            shutil.copy2(src_config, CONFIG_PATH)

    # Copy system prompt
    dest_prompt = PROMPTS_DIR / "system_prompt.md"
    if not dest_prompt.exists():
        src_prompt = res / "prompts" / "system_prompt.md"
        if src_prompt.exists():
            shutil.copy2(src_prompt, dest_prompt)
