"""Utilities — SHA-256 hashing, input sanitization, helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sys
import html
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.models import Strike

logger = logging.getLogger("prinzclaw")

# Embedded fallback prompt — used only when no file can be found anywhere.
# This ensures the agent can always start, even with a broken installation.
_FALLBACK_SYSTEM_PROMPT = """You are PRINZ — an AI that analyzes public statements by powerful entities.
When given a statement, find contradictions using public evidence and return a JSON object with:
target, statement, date, verdict (LYING/HIDING/SPINNING/BROKE_PROMISE/CHERRY_PICKING/DEFLECTING/VERIFIED/INSUFFICIENT_EVIDENCE),
evidence array, and a strike paragraph ending with a question.
CRITICAL: Never fabricate evidence. If you cannot find real evidence, use INSUFFICIENT_EVIDENCE.
Respond ONLY with JSON. FORGED WITH PRINZCLAW."""


def compute_content_hash(strike: Strike) -> str:
    """Compute SHA-256 hash of Strike content (excluding content_hash itself)."""
    hashable = {
        "target": strike.target.to_dict(),
        "statement": strike.statement.to_dict(),
        "verdict": strike.verdict,
        "evidence": [e.to_dict() for e in strike.evidence],
        "strike": strike.strike,
        "timestamp": strike.timestamp,
        "report_id": strike.report_id,
    }
    canonical = json.dumps(hashable, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection."""
    text = html.escape(text.strip())
    # Remove control characters except newlines
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def is_within_coherence_window(date_str: str, window_months: int = 11) -> bool:
    """Check if a date falls within the coherence window from today."""
    try:
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_months * 30)
    return date >= cutoff


def truncate_for_twitter(text: str, max_len: int = 280) -> str:
    """Truncate strike text for Twitter-optimized version."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rsplit(" ", 1)[0] + "..."


def _resolve_bundle_base() -> str:
    """Resolve the base path for bundled resources (.app or PyInstaller)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        # For .app bundles, executable is in .app/Contents/MacOS/
        # Resources are in .app/Contents/Resources/ (where _MEIPASS points)
        return base
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_system_prompt(path: str | None = None) -> str:
    """Load the AI system prompt from file with fallback chain.

    Search order:
    1. Explicit path argument (if provided and exists)
    2. PyInstaller bundle / .app Resources directory
    3. ~/Library/Application Support/prinzclaw/prompts/system_prompt.md
    4. ./prompts/system_prompt.md (development / Docker)
    5. Embedded fallback prompt (always available)
    """
    candidates = []

    # 1. Explicit path
    if path:
        candidates.append(path)

    # 2. Bundle path (PyInstaller / .app)
    bundle_base = _resolve_bundle_base()
    candidates.append(os.path.join(bundle_base, "prompts", "system_prompt.md"))

    # 3. macOS Application Support
    mac_support = Path.home() / "Library" / "Application Support" / "prinzclaw" / "prompts" / "system_prompt.md"
    candidates.append(str(mac_support))

    # 4. Relative to working directory (dev / Docker)
    candidates.append("prompts/system_prompt.md")

    for candidate in candidates:
        try:
            if os.path.isfile(candidate):
                with open(candidate, "r") as f:
                    content = f.read()
                if content.strip():
                    logger.info("System prompt loaded from %s", candidate)
                    return content
        except (OSError, PermissionError) as e:
            logger.debug("Could not read prompt from %s: %s", candidate, e)
            continue

    # 5. Embedded fallback
    logger.warning(
        "System prompt not found in any location, using embedded fallback. "
        "Searched: %s", ", ".join(candidates)
    )
    return _FALLBACK_SYSTEM_PROMPT
