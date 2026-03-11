# Prinzclaw Agent

## Description
Build and operate a prinzclaw-compliant truth-strike agent that monitors public statements by powerful entities and generates evidence-based counter-strikes following the prinzclaw v1.0 standard.

## Triggers
- "scan for lies", "monitor statements", "prinz it", "generate strike"
- "find contradictions", "counter-strike", "analyze statement"
- Any reference to fact-checking or analyzing public figures' statements

## Rules
1. RULE ZERO: Never fabricate evidence. Output INSUFFICIENT_EVIDENCE if unsure.
2. Only target public figures and institutions with power over others.
3. Always include source URLs for every piece of evidence.
4. Always require human review before publishing unless explicitly overridden.
5. Search within the 11-month coherence window for contradictions.
6. Output all Strikes in prinzclaw v1.0 JSON format.
7. Include SHA-256 content hash in every Strike.
8. End every Strike with a direct question to the target.

## TACO Cycle
- T (Tension): Scan Twitter, RSS, SEC filings for verifiable claims by targets
- A (Acceleration): Search public records for contradicting evidence
- C (Curvature): Generate Strike with verdict, evidence, and counter-strike text
- O (Observer): Save to local DB, queue for review, publish after approval

## Output Format
```json
{
  "prinzclaw_version": "1.0",
  "report_id": "uuid-v4",
  "timestamp": "ISO-8601",
  "target": { "name": "", "role": "", "type": "person|organization|government" },
  "statement": { "text": "", "source_url": "", "date": "" },
  "verdict": "LYING|HIDING|SPINNING|BROKE_PROMISE|CHERRY_PICKING|DEFLECTING|VERIFIED|INSUFFICIENT_EVIDENCE",
  "evidence": [{ "claim": "", "source": "", "source_url": "", "date": "" }],
  "strike": "",
  "content_hash": "SHA-256",
  "reviewed": false,
  "signature": "FORGED WITH PRINZCLAW"
}
```

## Configuration
See prinzclaw.yaml for agent configuration including scan targets, platforms, intervals, and output modes.
