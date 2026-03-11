# SUPPLEMENTAL INSTRUCTIONS FOR BUILDING PRINZCLAW

## What to build
A standalone agent named **prinzclaw** that inherits the OpenClaw agent framework standard. This is NOT a skill or plugin. It is an independent agent with its own gateway, lifecycle, and state management.

## Architecture requirements

1. **Standalone agent, NOT a skill/plugin.**
   - Must have its own gateway (OpenClaw-compatible, see agent.yaml)
   - Must have its own lifecycle management (start, run, stop, restart)
   - Must maintain its own state (SQLite database, scan queue, review queue)
   - Must be able to run independently as a daemon process
   - Must also expose an OpenClaw-compatible gateway so other agents can invoke it

2. **TACO four-stage engine** (see PRINZCLAW_SPEC.md)
   - T (Tension/Scan): Monitor Twitter API, RSS feeds, SEC EDGAR for target statements
   - A (Acceleration/Analyze): Search public records for contradicting evidence within 11-month window
   - C (Curvature/Craft): Generate Strike in prinzclaw v1.0 JSON format
   - O (Observer/Output): Save to local DB, queue for review, publish after approval

3. **Human review is REQUIRED before any Strike is published.**
   - The agent generates drafts. A human approves or rejects.
   - Default mode is semi_auto (auto-scan, auto-craft, manual-publish)
   - full_auto mode exists but is NOT RECOMMENDED and must be explicitly enabled

4. **Security constraints**
   - Never hardcode API keys. Always read from environment variables or prinzclaw.yaml
   - Never store API keys in the repository
   - All external API calls must use HTTPS
   - Input sanitization on all user-facing endpoints

5. **Deployment**
   - Include a working Dockerfile for easy deployment
   - Include a docker-compose.yaml for one-command startup
   - Include a systemd service file for Linux server deployment
   - Must work on a basic 2GB RAM VPS

## File structure to create

```
prinzclaw/
├── agent.yaml              # OpenClaw agent registration
├── prinzclaw.yaml          # User configuration (from prinzclaw.example.yaml)
├── MANIFESTO.md            # Why this exists
├── PRINZCLAW_SPEC.md       # Technical specification
├── SKILL.md                # OpenClaw skill description
├── README.md               # GitHub README
├── LICENSE                  # MIT
├── Dockerfile              # Container deployment
├── docker-compose.yaml     # One-command startup
├── requirements.txt        # Python dependencies (minimal)
├── src/
│   ├── __init__.py
│   ├── main.py             # Entry point — starts the agent
│   ├── gateway.py          # OpenClaw-compatible HTTP gateway
│   ├── scanner.py          # Stage T — Monitor platforms for statements
│   ├── analyzer.py         # Stage A — Search for contradicting evidence
│   ├── crafter.py          # Stage C — Generate Strike using AI
│   ├── publisher.py        # Stage O — Output, review queue, publish
│   ├── database.py         # SQLite operations
│   ├── models.py           # Data models (Strike, Target, Evidence)
│   ├── config.py           # Configuration loader (reads prinzclaw.yaml)
│   └── utils.py            # SHA-256 hashing, sanitization, helpers
├── prompts/
│   └── system_prompt.md    # AI system prompt (the soul of the weapon)
├── data/                   # Local database directory (gitignored)
│   └── .gitkeep
├── logs/                   # Log directory (gitignored)
│   └── .gitkeep
├── tests/
│   ├── test_scanner.py
│   ├── test_analyzer.py
│   ├── test_crafter.py
│   ├── test_publisher.py
│   └── test_models.py
└── examples/
    └── example_strike.json
```

## Key implementation notes

- **AI Provider**: Default to Gemini (gemini-2.5-flash). Support Anthropic and OpenAI as alternatives. Read provider from prinzclaw.yaml.
- **System Prompt**: Load from prompts/system_prompt.md. This is the soul — do not hardcode it.
- **Strike Format**: Must follow prinzclaw v1.0 exactly (see PRINZCLAW_SPEC.md and example_strike.json)
- **11-Month Window**: When searching for contradictions, only look at statements from the last 11 months.
- **SHA-256 Hash**: Every Strike gets a content hash computed from the canonical JSON of target+statement+date+verdict+evidence+strike.
- **Signature**: Every Strike ends with "FORGED WITH PRINZCLAW"
- **Gateway Port**: Default 8100 (configurable in prinzclaw.yaml)
- **Database**: SQLite. File at ./data/strikes.db. No external database dependencies.
- **Logging**: All actions logged to ./logs/prinzclaw.log and stdout.

## What NOT to do

- Do NOT use blockchain or any chain integration
- Do NOT require any accounts, signups, or authentication for the gateway
- Do NOT use localStorage or browser APIs (this is a server-side agent)
- Do NOT hardcode any API keys
- Do NOT skip the human review step in the default configuration
- Do NOT create a frontend — the gateway is API-only. prinzit.ai is the frontend.
