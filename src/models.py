"""Data models for prinzclaw v1.0 Strike format."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Literal


VALID_VERDICTS = (
    "LYING",
    "HIDING",
    "SPINNING",
    "BROKE_PROMISE",
    "CHERRY_PICKING",
    "DEFLECTING",
    "VERIFIED",
    "INSUFFICIENT_EVIDENCE",
)

VALID_TARGET_TYPES = ("person", "organization", "government")

VALID_STYLES = ("surgical", "prosecutor", "street", "broadcast")


@dataclass
class Target:
    name: str
    role: str
    type: Literal["person", "organization", "government"] = "person"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Statement:
    text: str
    source_url: str
    date: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Evidence:
    claim: str
    source: str
    source_url: str
    date: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Strike:
    target: Target
    statement: Statement
    verdict: str
    evidence: list[Evidence]
    strike: str
    prinzclaw_version: str = "1.0"
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    content_hash: str = ""
    agent_id: str = "prinzclaw-agent"
    reviewed: bool = False
    signature: str = "FORGED WITH PRINZCLAW"

    def to_dict(self) -> dict:
        return {
            "prinzclaw_version": self.prinzclaw_version,
            "report_id": self.report_id,
            "timestamp": self.timestamp,
            "target": self.target.to_dict(),
            "statement": self.statement.to_dict(),
            "verdict": self.verdict,
            "evidence": [e.to_dict() for e in self.evidence],
            "strike": self.strike,
            "content_hash": self.content_hash,
            "agent_id": self.agent_id,
            "reviewed": self.reviewed,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Strike:
        target = Target(**data["target"])
        statement = Statement(**data["statement"])
        evidence = [Evidence(**e) for e in data.get("evidence", [])]
        return cls(
            target=target,
            statement=statement,
            verdict=data["verdict"],
            evidence=evidence,
            strike=data["strike"],
            prinzclaw_version=data.get("prinzclaw_version", "1.0"),
            report_id=data.get("report_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", ""),
            content_hash=data.get("content_hash", ""),
            agent_id=data.get("agent_id", "prinzclaw-agent"),
            reviewed=data.get("reviewed", False),
            signature=data.get("signature", "FORGED WITH PRINZCLAW"),
        )
