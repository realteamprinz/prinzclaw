---
name: prinzclaw-craft
description: Generates accountability strikes based on analysis results
tools: [llm_generation, template_engine]
---

# Craft Skill — C (Curvature)

## Purpose
Forge a Strike — a surgical, question-ending accountability message based on evidence.

## When to Use
After the analyze skill detects a contradiction or broken promise, use this skill to generate the counter-text.

## Generation Process

### Input
- Analysis result (from analyze skill)
- Evidence chain (promises, outcomes, sources)
- Target entity information

### LLM Generation
The craft skill uses the LLM to generate counter-text that:
1. References specific evidence (quotes with dates)
2. Points out the contradiction or failure
3. Ends with a question they cannot answer

### Rule Zero Verification
Before output, verify:
- ✅ All evidence has public source URLs
- ✅ Quotes are accurate (LLM cross-validation)
- ✅ No insults or ad hominem attacks
- ✅ Ends with a question mark

### Output Format (prinzclaw v1.0 JSON)
```json
{
  "strike_id": "SHA-256",
  "target": "Name",
  "verdict": "BROKE PROMISE",
  "summary": "One sentence summary",
  "evidence_chain": [
    {
      "type": "promise",
      "text": "exact quote",
      "source_url": "https://...",
      "date": "2026-03-15"
    },
    {
      "type": "outcome",
      "text": "actual data",
      "source_url": "https://eia.gov/...",
      "date": "2026-09-15"
    }
  ],
  "counter_text": "You said [X] on [date]. [Data] shows [Y]. Which one is true?",
  "forged_by": "prinzclaw@1.0.0",
  "forged_at": "2026-03-16T12:00:00Z",
  "signature": "FORGED WITH PRINZCLAW"
}
```

## Communication Style
- Calm and surgical
- State the facts
- End with a question they cannot answer
- NEVER insult or attack
- NEVER fabricate evidence

## Usage in TACO Pipeline
The craft skill runs after analyze. Its output goes to the output skill for human review before publishing.
