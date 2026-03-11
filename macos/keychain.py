"""macOS Keychain integration for secure API key storage."""

from __future__ import annotations

import subprocess
import logging

logger = logging.getLogger("prinzclaw")

SERVICE_NAME = "prinzclaw"


def store_key(account: str, password: str) -> bool:
    """Store an API key in the macOS Keychain."""
    # Delete existing entry first (ignore errors if not found)
    subprocess.run(
        ["security", "delete-generic-password", "-s", SERVICE_NAME, "-a", account],
        capture_output=True,
    )
    result = subprocess.run(
        [
            "security", "add-generic-password",
            "-s", SERVICE_NAME,
            "-a", account,
            "-w", password,
            "-U",  # Update if exists
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        logger.info("API key stored in Keychain for %s", account)
        return True
    logger.error("Failed to store key in Keychain: %s", result.stderr)
    return False


def retrieve_key(account: str) -> str | None:
    """Retrieve an API key from the macOS Keychain."""
    result = subprocess.run(
        [
            "security", "find-generic-password",
            "-s", SERVICE_NAME,
            "-a", account,
            "-w",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def delete_key(account: str) -> bool:
    """Delete an API key from the macOS Keychain."""
    result = subprocess.run(
        ["security", "delete-generic-password", "-s", SERVICE_NAME, "-a", account],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_api_key_for_provider(provider: str) -> str | None:
    """Get the API key for a specific provider from Keychain."""
    account_map = {
        "gemini": "GEMINI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    account = account_map.get(provider)
    if not account:
        return None
    return retrieve_key(account)
