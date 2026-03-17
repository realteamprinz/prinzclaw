# AGENTS.md — prinzclaw TACO Orchestration

## Overview
This file defines the four-step agent orchestration sequence for prinzclaw.
The sequence is LOCKED and cannot be modified without breaking the system.

## Agent Definitions

```yaml
agents:
  scanner:
    skill: prinzclaw-scan
    triggers: [heartbeat, manual]
    outputs_to: analyzer

  analyzer:
    skill: prinzclaw-analyze
    triggers: [scanner_output]
    outputs_to: crafter

  crafter:
    skill: prinzclaw-craft
    triggers: [analyzer_output]
    outputs_to: reviewer

  reviewer:
    skill: prinzclaw-output
    triggers: [crafter_output]
    outputs_to: [channels]
    requires: human_approval
```

## Sequence Flow
```
scanner → analyzer → crafter → reviewer → channels
```

## Constraints
- **breakable: false** - The four steps cannot be skipped or reordered
- **human_required: true** - Output phase requires human approval
- **rule_zero_enforced: true** - Every Strike must pass Rule Zero verification
