---
name: prinzclaw-output
description: Manages the review queue and publishes approved strikes
tools: [database, notification, channel_router]
---

# Output Skill — O (Observer)

## Purpose
Manage the review queue and handle Strike publication after human approval.

## When to Use
After the craft skill generates a Strike, use this skill to:
1. Add Strike to review queue
2. Await human approval
3. Publish to configured channels on approval

## Core Principle
**"Nothing fires without a human trigger."**

This is inviolable. Every Strike must be reviewed and approved by a human before publishing.

## Queue Management

### Add to Queue
When a Strike is crafted:
1. Store in database with status "PENDING"
2. Notify via configured channels (dashboard, Telegram, etc.)
3. Wait for human approval

### Human Review
Reviewers can:
- **Approve**: Publish to channels, update status to "PUBLISHED"
- **Reject**: Add reason, update status to "REJECTED"
- **Request Changes**: Send back to craft with feedback

### On Approval
1. Update status to "APPROVED"
2. Publish to selected channels (Twitter, Telegram, Discord, Web)
3. Update status to "PUBLISHED"
4. Archive in database

## Channels

### Web Dashboard
- Real-time queue display
- One-click approve/reject
- Full evidence chain view

### Telegram Bot
- Notification on new Strike
- Inline approve/reject buttons
- /queue, /approve <id>, /reject <id> commands

### Discord Bot
- Slash commands: /strike queue, /approve, /reject
- Embed with full evidence

## Output
```json
{
  "strike_id": "...",
  "status": "PENDING | APPROVED | REJECTED | PUBLISHED",
  "published_at": "2026-03-16T12:30:00Z",
  "channels": ["telegram", "discord", "web"]
}
```

## Usage in TACO Pipeline
The output skill is the final stage. It ensures human oversight before any Strike is published.
