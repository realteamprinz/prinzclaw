---
name: prinzclaw-analyze
description: Analyzes promises for contradictions and verifies outcomes
tools: [database_query, llm_reasoning]
---

# Analyze Skill — A (Acceleration)

## Purpose
Detect semantic contradictions within the 11-month coherence window and verify promise outcomes.

## When to Use
After a promise has been scanned and stored, use this skill to:
1. Check if the promise has expired
2. Compare promised outcomes with actual data
3. Find contradictions with historical statements

## Two Analysis Modes

### Mode 1: Deal Expiration Check
For promises with expiry dates:
1. Fetch actual data from verification sources
2. Compare promised value vs actual value
3. Determine verdict: KEPT / BROKE / PARTIALLY_KEPT / INSUFFICIENT_EVIDENCE

**Example:**
- Promise: "Gas prices under $2 by September 2026"
- Actual: EIA reports $3.47 average
- Verdict: BROKE

### Mode 2: Contradiction Detection
For detecting spin and contradictions:
1. Query historical promises (11-month window)
2. Use LLM for semantic comparison
3. Identify contradiction type: SPINNING, CHERRY-PICKING, LYING

**Example:**
- Current: "Disruptions will be minimal"
- Historical (7 months ago): "Any closure would be catastrophic"
- Contradiction Type: SPINNING
- Score: 0.9

## 11-Month Coherence Window
Only analyze statements within this timeframe. Older contradictions are ignored.

## Output
```json
{
  "analysis_id": "SHA-256",
  "promise_id": "...",
  "mode": "expiration | contradiction",
  "verdict": "KEPT | BROKE | PARTIALLY_KEPT | SPINNING | CHERRY-PICKING | LYING | NO_CONTRADICTION",
  "contradiction_score": 0.95,
  "evidence_urls": ["url1", "url2"],
  "should_craft": true | false
}
```

## Usage in TACO Pipeline
The analyze skill runs after scan. If it detects a contradiction or expired promise with negative outcome, it triggers the craft skill to generate a Strike.
