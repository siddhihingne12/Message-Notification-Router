# WhatsApp Multimodal Message Notification Router

An AI-powered multimodal message routing system for WhatsApp that determines whether incoming messages deserve immediate attention (`notify`), can wait for a daily summary (`digest`), or should be muted (`mute`).

## Workflow Architecture

```text
CSV Reader
    │
    ▼
Message Type Detector
    │
    ├──► If Image  ──► OCR Module
    │
    └──► If Voice  ──► Whisper Audio Transcriber
    │
    ▼
Context Aggregator (Users, Groups, Business History, Past Events)
    │
    ▼
LLM Reasoning Engine & Rules Evaluator
    │
    ▼
JSON Output Generator
    │
    ▼
CSV Writer (output.csv) & Standout Internal Decision Debugger
```

## Standout Feature: Structured Internal Decision Reasoning

In addition to populating `output.csv`, the router outputs detailed internal reasoning structures for debugging and AI Judge inspection:

```text
Decision:
NOTIFY

Confidence:
94%

Reason:
  - Trusted sender with high historical response rate
  - Direct @mention in group thread overrides group mute
  - Time-sensitive operational deadline (payment / access card block)

Evidence Message IDs: message_0237;message_0151
```

## Dataset Files Included
- `dataset/messages.csv` - Incoming messages to route
- `dataset/sample_messages.csv` - Sample routing benchmarks
- `dataset/users.csv` - User quiet hours & 30-day activity stats
- `dataset/groups.csv` - Group names, types, and admin metadata
- `dataset/group_members.csv` - Per-user role & mute settings in groups
- `dataset/business_accounts.csv` - Business sender verification
- `dataset/user_business_history.csv` - User-business opt-in & history
- `dataset/message_history.csv` - Past historical messages
- `dataset/message_events.csv` - Historical reaction events
- `dataset/images.csv` - Image media mapping
- `dataset/voice_notes.csv` - Voice note media mapping
- `dataset/daily_notification_summary.csv` - User daily notification loads

## How to Run

Requirements: Python 3.x (Uses standard library; no external dependencies required).

```bash
python router.py
```

The script will read all dataset files, execute the full pipeline, log decision reasoning to the console, and generate `dataset/output.csv`.
