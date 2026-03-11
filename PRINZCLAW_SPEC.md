# PRINZCLAW — The Open Standard for Truth-Strike Weapons

> "They don't want you to see. We show you. You hit back."

## What is Prinzclaw?

Prinzclaw is an open standard for building AI-powered agents that automatically detect lies, contradictions, and deception in public statements by powerful entities (CEOs, politicians, institutions) and generate evidence-based counter-strikes.

Any developer can build a prinzclaw-compliant agent on their own machine. All agents following this standard produce interoperable Strikes that can be published, archived, and verified.

**prinzit.ai** is the flagship implementation — the public-facing weapon anyone can use manually.
**prinzclaw** is the standard — the protocol developers follow to build automated agents.

---

## Core Principles

### Rule Zero — NEVER Fabricate Evidence
One fake citation destroys everything. A prinzclaw agent MUST:
- Only cite verifiable, public sources
- Include source URLs for every piece of evidence
- Output `INSUFFICIENT EVIDENCE` when evidence cannot be found
- Never hallucinate, infer, or extrapolate beyond what sources state

### Punch Up, Never Down
Prinzclaw agents target **public figures and institutions with power over others**:
- CEOs and corporate executives (public statements, earnings calls, press releases)
- Politicians (speeches, social media, official statements)
- Government agencies (press releases, official reports)
- Large institutions (banks, pharma, tech companies)

Never target: private individuals, small businesses, vulnerable populations.

### Transparency Over Secrecy
Every Strike is public. Every source is cited. Every report can be independently verified. This is the opposite of Kaisheng Rongying's black box.

---

## Strike Format (v1.0)

Every prinzclaw-compliant Strike MUST contain these fields:

```json
{
  "prinzclaw_version": "1.0",
  "report_id": "uuid-v4",
  "timestamp": "ISO-8601 UTC",
  "target": {
    "name": "String — Full name of person or entity",
    "role": "String — Title/position",
    "type": "person | organization | government"
  },
  "statement": {
    "text": "String — The exact statement being analyzed",
    "source_url": "String — Where the statement was made (URL)",
    "date": "String — When the statement was made"
  },
  "verdict": "LYING | HIDING | SPINNING | BROKE_PROMISE | CHERRY_PICKING | DEFLECTING | VERIFIED | INSUFFICIENT_EVIDENCE",
  "evidence": [
    {
      "claim": "String — What the evidence shows",
      "source": "String — Source name",
      "source_url": "String — Direct URL to source",
      "date": "String — Date of evidence"
    }
  ],
  "strike": "String — The copy-paste counter-strike text",
  "content_hash": "SHA-256 hash of the entire report JSON (excluding this field)",
  "agent_id": "String — Identifier of the agent that generated this Strike",
  "reviewed": false,
  "signature": "FORGED WITH PRINZCLAW"
}
```

### Verdict Definitions

| Verdict | Definition |
|---------|-----------|
| LYING | Statement directly contradicts verifiable public evidence |
| HIDING | Statement omits critical context that changes its meaning |
| SPINNING | Statement uses misleading framing of true facts |
| BROKE_PROMISE | Statement contradicts a previous public commitment by the same entity |
| CHERRY_PICKING | Statement selectively uses data while ignoring contradictory data |
| DEFLECTING | Statement redirects attention from the actual issue |
| VERIFIED | Statement is supported by available public evidence |
| INSUFFICIENT_EVIDENCE | Cannot verify or refute — not enough public data |

---

## Agent Architecture

A prinzclaw-compliant agent has four stages, following the TACO cycle:

### Stage 1: T — Tension (Scan)
The agent monitors public channels for statements by powerful entities.

**Required capabilities:**
- Monitor Twitter/X API for statements by tracked targets
- Monitor RSS feeds of major news outlets
- Monitor SEC EDGAR for corporate filings
- Monitor government press release feeds
- Filter: only process statements containing verifiable factual claims

**Configuration:**
```yaml
# prinzclaw.yaml
scan:
  platforms:
    - twitter
    - rss
    - sec_edgar
  targets:
    - name: "Example CEO"
      twitter_handle: "@example"
      keywords: ["revenue", "growth", "safe", "secure"]
  scan_interval_minutes: 15
  min_claim_confidence: 0.7
```

### Stage 2: A — Acceleration (Analyze)
The agent analyzes detected statements and searches for contradicting evidence.

**Required capabilities:**
- Extract verifiable factual claims from statements
- Search public databases for contradicting evidence
- Search the target's own previous statements (within 11-month coherence window)
- Compare current statement against historical archive
- Assign verdict based on evidence found

**The 11-Month Coherence Window:**
Prinzclaw agents search for contradictions within an 11-month window of the target's public statements. Beyond 11 months, statements lose public relevance and causal coherence. Within 11 months, contradictions are sharp and actionable.

### Stage 3: C — Curvature (Craft)
The agent generates the Strike.

**Required capabilities:**
- Generate Strike text following the format specification
- Strike MUST be copy-paste ready (no more than 280 characters for Twitter-optimized version, full version unlimited)
- Strike MUST reference specific evidence with dates
- Strike MUST end with a question directed at the target
- Compute SHA-256 content hash
- Assign unique report_id (UUID v4)

**Strike Style Options:**
```yaml
styles:
  surgical:    # Cold, precise, evidence-only
  prosecutor:  # Cross-examination, legal tone
  street:      # Direct, Twitter-native, sharp
  broadcast:   # News anchor style, neutral but devastating
```

### Stage 4: O — Observer (Output)
The agent outputs the Strike for review and/or publication.

**Required capabilities:**
- Save Strike to local SQLite database
- Place Strike in review queue (if human review enabled)
- Publish Strike to configured platforms (after review)
- Submit Strike to prinzit.ai public archive API (optional)
- Log all actions for audit trail

**Output modes:**
```yaml
output:
  mode: "semi_auto"  # Options: manual, semi_auto, full_auto (NOT RECOMMENDED)
  review_required: true  # STRONGLY RECOMMENDED
  publish_to:
    - twitter
    - prinzit_archive
  archive:
    local_db: "./data/strikes.db"
    submit_to_prinzit: true
```

---

## Directory Structure

```
prinzclaw-agent/
├── prinzclaw.yaml          # Agent configuration
├── SKILL.md                # Skill file for Claude Code / OpenClaw
├── README.md               # Documentation
├── LICENSE                  # MIT License
├── src/
│   ├── scanner.py          # Stage 1: T — Monitor platforms
│   ├── analyzer.py         # Stage 2: A — Find evidence
│   ├── crafter.py          # Stage 3: C — Generate Strike
│   ├── publisher.py        # Stage 4: O — Output and publish
│   ├── database.py         # SQLite operations
│   ├── models.py           # Data models (Strike, Target, Evidence)
│   └── config.py           # Configuration loader
├── prompts/
│   ├── system_prompt.md    # Core system prompt for AI
│   ├── surgical.md         # Surgical style prompt
│   ├── prosecutor.md       # Prosecutor style prompt
│   ├── street.md           # Street style prompt
│   └── broadcast.md        # Broadcast style prompt
├── data/
│   └── strikes.db          # Local SQLite database
├── tests/
│   ├── test_scanner.py
│   ├── test_analyzer.py
│   ├── test_crafter.py
│   └── test_publisher.py
└── examples/
    ├── example_strike.json  # Example Strike output
    └── quickstart.md        # Quick start guide
```

---

## SKILL.md (OpenClaw / Claude Code Compatible)

```markdown
# Prinzclaw Agent Skill

## Description
Build and operate a prinzclaw-compliant truth-strike agent that monitors
public statements by powerful entities and generates evidence-based
counter-strikes.

## Triggers
- "scan for lies", "monitor statements", "prinz it", "generate strike"
- "find contradictions", "fact check", "counter-strike"
- Any reference to analyzing public figures' statements

## Instructions
1. Load configuration from prinzclaw.yaml
2. Follow the TACO cycle: Scan → Analyze → Craft → Output
3. ALWAYS comply with Rule Zero: Never fabricate evidence
4. ALWAYS require human review before publishing (unless explicitly overridden)
5. ALWAYS include source URLs for every piece of evidence
6. Output Strikes in prinzclaw v1.0 format
```

---

## API Endpoints (for prinzit.ai archive integration)

Agents can optionally submit Strikes to the public prinzit.ai archive:

```
POST https://prinzit.ai/api/v1/submit
Content-Type: application/json
Body: { Strike JSON in prinzclaw v1.0 format }
Response: { "accepted": true, "archive_id": "..." }

GET https://prinzit.ai/api/v1/target/{name}
Response: { "strikes": [...], "total": N }

GET https://prinzit.ai/api/v1/stats
Response: { "total_strikes": N, "unique_targets": N, "verdicts": {...} }
```

---

## Compliance Checklist

A prinzclaw-compliant agent MUST:

- [ ] Follow Rule Zero — never fabricate evidence
- [ ] Output Strikes in prinzclaw v1.0 JSON format
- [ ] Include SHA-256 content hash in every Strike
- [ ] Include source URLs for every piece of evidence
- [ ] Punch up, never down — only target public figures with power
- [ ] Support human review mode
- [ ] Maintain local SQLite archive of all generated Strikes
- [ ] Include "FORGED WITH PRINZCLAW" signature
- [ ] Respect the 11-month coherence window for historical comparisons
- [ ] Log all actions for audit trail

A prinzclaw-compliant agent SHOULD:

- [ ] Submit Strikes to prinzit.ai public archive
- [ ] Support multiple Strike styles (surgical, prosecutor, street, broadcast)
- [ ] Support multiple scan platforms (Twitter, RSS, SEC, government feeds)
- [ ] Include both Twitter-optimized (≤280 char) and full-length Strike versions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-10 | Initial release. Genesis. |

---

## License

MIT — Free to use, modify, and distribute.
The weapon is free. The truth is yours.

---

## Origin

Created by **Louie Grant Prinz** (@realteamprinz)

> "I spent a year inside a company that weaponized information against ordinary people.
> Today I reversed the machine."

prinzit.ai — They don't want you to see. We show you. You hit back.
