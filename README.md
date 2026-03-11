# 🔥 PRINZCLAW

**The Open Standard for AI Truth-Strike Weapons**

> They lie. You had no weapon. Now you do.

---

## What is this?

**prinzclaw** is an open standard for building AI agents that detect lies in public statements and generate evidence-based counter-strikes.

**prinzit.ai** is where anyone can use the weapon manually.
**prinzclaw** is how developers build automated agents that do it at scale.

## How it works

Every prinzclaw agent follows the TACO cycle:

| Step | Name | What it does |
|------|------|-------------|
| **T** | Tension | Scan public channels for statements by powerful entities |
| **A** | Acceleration | Search for contradicting evidence in public records |
| **C** | Curvature | Generate an evidence-based counter-strike |
| **O** | Observer | Output for review, then publish |

## Quick Start

```bash
git clone https://github.com/realteamprinz/prinzclaw.git
cd prinzclaw
cp prinzclaw.example.yaml prinzclaw.yaml
# Edit prinzclaw.yaml with your API keys and targets
python src/scanner.py
```

## Rule Zero

**NEVER fabricate evidence.** One fake citation destroys everything.

If evidence cannot be found, the verdict is `INSUFFICIENT_EVIDENCE`. Not `LYING`. Not `SPINNING`. Insufficient evidence. Period.

## Who gets targeted?

CEOs. Politicians. Institutions. Anyone with power over others who makes public statements.

Never: private individuals, small businesses, vulnerable people.

**Punch up. Never down.**

## Strike Format

Every Strike follows the prinzclaw v1.0 format:

```json
{
  "verdict": "LYING",
  "target": { "name": "...", "role": "..." },
  "evidence": [{ "claim": "...", "source_url": "..." }],
  "strike": "Copy-paste counter-strike text",
  "content_hash": "SHA-256"
}
```

See [PRINZCLAW_SPEC.md](./PRINZCLAW_SPEC.md) for the full specification.

## Architecture

```
You (or your agent) → prinzclaw standard → Strike → Twitter / Archive
                                                          ↓
                                              prinzit.ai public archive
```

## Contributing

Build your own prinzclaw agent. Follow the spec. Submit Strikes to the public archive. Make the weapon stronger.

## License

MIT — The weapon is free. The truth is yours.

---

Created by **Louie Grant Prinz** ([@realteamprinz](https://x.com/realteamprinz))

[prinzit.ai](https://prinzit.ai) — They don't want you to see. We show you. You hit back.

**#PrinzIt**
