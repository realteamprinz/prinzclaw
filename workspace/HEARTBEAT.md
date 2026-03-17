# HEARTBEAT.md — Scheduled Tasks

## Overview
This file defines automated checks that run on the heartbeat interval (default: 30 minutes).

## Scheduled Checks

### 1. Expiry Check
- Query all promises with expiry_date within 7 days
- Trigger analyze skill to verify outcomes
- Flag any BROKE promises for immediate review

### 2. Entity Scan
- Check configured RSS feeds for tracked entities
- Scan for new statements containing verifiable promises
- Queue new promises for analysis

### 3. DEAL Score Update
- Recalculate DEAL scores for all tracked entities
- Update score based on new judgments

### 4. Memory Cleanup
- Check if daily log needs to be summarized
- Flag old logs for memory compaction

### 5. Queue Monitor
- Check for stale pending strikes (> 48 hours)
- Send reminders to reviewers

## Heartbeat Configuration

In `prinzclaw.json`:
```json
{
  "heartbeat": {
    "interval": 30,
    "enabled": true
  }
}
```

## Execution

Each heartbeat tick:
1. Read this file for checklist
2. Execute each check
3. Log results to daily memory
4. Report significant findings to human

## Override

To disable automatic scanning while keeping heartbeat:
```json
{
  "heartbeat": {
    "interval": 30,
    "enabled": true,
    "auto_scan": false,
    "check_expiry": true
  }
}
```
