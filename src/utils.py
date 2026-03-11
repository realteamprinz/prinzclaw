"""Utilities — SHA-256 hashing, input sanitization, helpers."""

from __future__ import annotations

import hashlib
import json
import re
import html
from datetime import datetime, timezone, timedelta

from src.models import Strike


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


def load_system_prompt(path: str = "prompts/system_prompt.md") -> str:
    """Load the AI system prompt from file."""
    with open(path, "r") as f:
        return f.read()
