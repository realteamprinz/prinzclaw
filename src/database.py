"""SQLite database operations for Strike storage and retrieval."""

from __future__ import annotations

import json
import sqlite3
import logging
from pathlib import Path

from src.models import Strike

logger = logging.getLogger("prinzclaw")


class Database:
    """SQLite database for prinzclaw Strikes."""

    def __init__(self, db_path: str = "./data/strikes.db"):
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS strikes (
                report_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                target_name TEXT NOT NULL,
                target_role TEXT,
                target_type TEXT,
                statement_text TEXT NOT NULL,
                statement_source_url TEXT,
                statement_date TEXT,
                verdict TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                strike_text TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                reviewed INTEGER NOT NULL DEFAULT 0,
                approved INTEGER NOT NULL DEFAULT 0,
                published INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                full_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scan_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                role TEXT,
                twitter_handle TEXT,
                keywords_json TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                action TEXT NOT NULL,
                details TEXT,
                strike_id TEXT
            );
        """)
        self._conn.commit()
        logger.info("Database initialized at %s", self._db_path)

    def save_strike(self, strike: Strike) -> None:
        """Save a Strike to the database."""
        data = strike.to_dict()
        self._conn.execute(
            """INSERT OR REPLACE INTO strikes
               (report_id, timestamp, target_name, target_role, target_type,
                statement_text, statement_source_url, statement_date,
                verdict, evidence_json, strike_text, content_hash,
                agent_id, reviewed, full_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                strike.report_id,
                strike.timestamp,
                strike.target.name,
                strike.target.role,
                strike.target.type,
                strike.statement.text,
                strike.statement.source_url,
                strike.statement.date,
                strike.verdict,
                json.dumps([e.to_dict() for e in strike.evidence]),
                strike.strike,
                strike.content_hash,
                strike.agent_id,
                1 if strike.reviewed else 0,
                json.dumps(data),
            ),
        )
        self._conn.commit()
        self._log_action("strike_saved", strike.report_id)

    def get_strike(self, report_id: str) -> dict | None:
        """Get a Strike by report_id."""
        row = self._conn.execute(
            "SELECT full_json FROM strikes WHERE report_id = ?", (report_id,)
        ).fetchone()
        if row:
            return json.loads(row["full_json"])
        return None

    def get_queue(self) -> list[dict]:
        """Get pending Strikes awaiting review (reviewed=0, approved=0)."""
        rows = self._conn.execute(
            "SELECT full_json FROM strikes WHERE reviewed = 0 AND approved = 0 ORDER BY timestamp DESC"
        ).fetchall()
        return [json.loads(r["full_json"]) for r in rows]

    def approve_strike(self, report_id: str) -> bool:
        """Approve a Strike for publication."""
        cur = self._conn.execute(
            "UPDATE strikes SET reviewed = 1, approved = 1 WHERE report_id = ?",
            (report_id,),
        )
        self._conn.commit()
        if cur.rowcount > 0:
            # Update the full_json too
            row = self._conn.execute(
                "SELECT full_json FROM strikes WHERE report_id = ?", (report_id,)
            ).fetchone()
            if row:
                data = json.loads(row["full_json"])
                data["reviewed"] = True
                self._conn.execute(
                    "UPDATE strikes SET full_json = ? WHERE report_id = ?",
                    (json.dumps(data), report_id),
                )
                self._conn.commit()
            self._log_action("strike_approved", report_id)
            return True
        return False

    def mark_published(self, report_id: str) -> None:
        """Mark a Strike as published."""
        self._conn.execute(
            "UPDATE strikes SET published = 1 WHERE report_id = ?", (report_id,)
        )
        self._conn.commit()
        self._log_action("strike_published", report_id)

    def get_archive(self) -> list[dict]:
        """Get all approved/published Strikes."""
        rows = self._conn.execute(
            "SELECT full_json FROM strikes WHERE approved = 1 ORDER BY timestamp DESC"
        ).fetchall()
        return [json.loads(r["full_json"]) for r in rows]

    def get_stats(self) -> dict:
        """Get aggregate statistics."""
        total = self._conn.execute("SELECT COUNT(*) as c FROM strikes").fetchone()["c"]
        targets = self._conn.execute(
            "SELECT COUNT(DISTINCT target_name) as c FROM strikes"
        ).fetchone()["c"]
        verdicts_rows = self._conn.execute(
            "SELECT verdict, COUNT(*) as c FROM strikes GROUP BY verdict"
        ).fetchall()
        verdicts = {r["verdict"]: r["c"] for r in verdicts_rows}
        pending = self._conn.execute(
            "SELECT COUNT(*) as c FROM strikes WHERE reviewed = 0"
        ).fetchone()["c"]
        return {
            "total_strikes": total,
            "unique_targets": targets,
            "verdicts": verdicts,
            "pending_review": pending,
        }

    def add_scan_target(self, name: str, target_type: str = "person",
                        role: str = "", twitter_handle: str = "",
                        keywords: list[str] | None = None) -> int:
        """Add a target to scan."""
        cur = self._conn.execute(
            """INSERT INTO scan_targets (name, type, role, twitter_handle, keywords_json)
               VALUES (?, ?, ?, ?, ?)""",
            (name, target_type, role, twitter_handle, json.dumps(keywords or [])),
        )
        self._conn.commit()
        self._log_action("target_added", details=name)
        return cur.lastrowid

    def get_scan_targets(self) -> list[dict]:
        """Get all active scan targets."""
        rows = self._conn.execute(
            "SELECT * FROM scan_targets WHERE active = 1"
        ).fetchall()
        return [
            {
                "id": r["id"],
                "name": r["name"],
                "type": r["type"],
                "role": r["role"],
                "twitter_handle": r["twitter_handle"],
                "keywords": json.loads(r["keywords_json"]) if r["keywords_json"] else [],
            }
            for r in rows
        ]

    def _log_action(self, action: str, strike_id: str = None, details: str = None) -> None:
        self._conn.execute(
            "INSERT INTO audit_log (action, strike_id, details) VALUES (?, ?, ?)",
            (action, strike_id, details),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
