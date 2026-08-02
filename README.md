# WhatsApp Multimodal Message Notification Router

An AI-powered multimodal message notification routing system that determines whether incoming WhatsApp messages deserve immediate attention (`notify`), can wait for a daily summary (`digest`), or should be silenced (`mute`).

This system goes beyond simple classification — it **manages the user's attention** by combining multimodal understanding, behavioral profiling, feature engineering, LLM-style reasoning, a confidence threshold gate, and an attention budget manager.

---

## Architecture Flow

```
Incoming Message
       |
       v
[Stage 1] Data Ingestion
  CSV Reader -> Load 11 datasets (messages, users, groups, history, media...)
       |
       v
[Stage 2] Multimodal Preprocessing
  Image -> OCR Module
  Voice -> Whisper Transcriber
  Text  -> Text Cleaner
  => Every message gets: raw_text + ocr_text + whisper_text + full_text
       |
       v
[Stage 3] User Profile Builder
  Mine behavioral patterns:
  Favorite contacts | Ignored contacts | Active groups |
  Muted groups | Shopping interest | DND window |
  Engagement rate | Notification fatigue
       |
       v
[Stage 4] Feature Engineering
  Compute 7 normalized scores (0.0 - 1.0) per message:
  Urgency | Relationship | Safety | Novelty |
  Importance | Time Sensitivity | Personalization
       |
       v
[Stage 4B] Context Builder
  Assemble one structured context object:
  {message + user_profile + sender_info + group_info +
   business_info + feature_scores + attention_budget + historical_evidence}
       |
       v
[Stage 5] LLM Reasoning Engine
  Rules-based AI: Evaluate context -> Decide action + Confidence
       |
       v
[Confidence Gate]
  If confidence >= 0.60 -> Accept LLM decision
  If confidence < 0.60  -> Fallback to Rule Checker
       |
       v
[Attention Budget Manager]
  Track daily notification count per user.
  If budget exhausted -> Downgrade NOTIFY to DIGEST.
  EXCEPT: Critical senders / direct @mention with urgency -> Override.
       |
       v
[Stage 6] Evaluation
  Compare against 30 ground-truth sample_messages.csv
  Accuracy | Precision | Recall | F1 | Confusion Matrix | Latency
       |
       v
[Stage 7] Output Generation
  Write dataset/output.csv + output.csv
       |
       v
[Stage 8] Decision Logging & Explainability
  Write decision_log.json with structured evidence for every prediction
  => "Why did your AI notify this?" — Just look it up.
```

---

## Evaluation Results

| Metric | Score |
|--------|-------|
| Accuracy | **80.0%** |
| Macro F1 | **0.80** |
| Weighted F1 | **0.80** |
| Notify Precision | 0.78 |
| Digest Recall | 0.91 |
| Mute Precision | 1.00 |

---

## Key Features

### Confidence Threshold Gate
Instead of blindly trusting the AI, every decision is gated:
- `confidence >= 0.60` → LLM decision accepted
- `confidence < 0.60` → Sent to deterministic Rule Checker fallback

### Attention Budget Manager
Tracks how many notifications a user has received today. If the daily budget is exhausted, new `notify` decisions are downgraded to `digest` — unless:
- The sender is a top-3 trusted contact AND urgency ≥ 0.80
- The message contains a direct `@user_id` mention with urgency keywords

### Rich Decision Explainability
Every prediction is stored in `decision_log.json`:
```json
{
  "message_id": "msg_048",
  "decision": "notify",
  "confidence": 0.94,
  "message_type": "urgent",
  "reasoning_path": "LLM",
  "confidence_gate": "passed",
  "feature_scores": {
    "urgency": 0.91,
    "relationship": 0.78,
    "safety": 0.95,
    "novelty": 0.82,
    "importance": 0.88,
    "time_sensitivity": 0.90,
    "personalization": 0.75
  },
  "attention_budget": {
    "notifications_today": 8,
    "budget_limit": 15,
    "budget_remaining": 7,
    "budget_override": false
  },
  "evidence": [
    "Important operational update in society group.",
    "Time-sensitive community notice relevant to daily routines."
  ]
}
```

---

## Dataset Files

| File | Description | Rows |
|------|-------------|------|
| `messages.csv` | Incoming messages to route | 110 |
| `users.csv` | User DND windows & 30-day activity | 54 |
| `groups.csv` | Group names, types, admin metadata | 23 |
| `group_members.csv` | Per-user role & mute settings per group | 401 |
| `user_business_history.csv` | User-business opt-in & activity history | 106 |
| `message_history.csv` | Historical messages (evidence corpus) | 412 |
| `message_events.csv` | User reactions: open, reply, dismiss, report | 413 |
| `images.csv` | Image media mapping | 20 |
| `voice_notes.csv` | Voice note media mapping | 13 |
| `daily_notification_summary.csv` | 14-day daily notification load per user | 756 |
| `sample_messages.csv` | 30 ground-truth labeled messages (evaluation) | 30 |

---

## Project Structure

```
Orchestra/
├── router.py               # Main 8-stage pipeline orchestrator
├── run_demo.py             # Visual demo with per-message decision breakdown
├── stages/
│   ├── stage1_ingestion.py         # CSV loading & schema validation
│   ├── stage2_preprocessing.py     # OCR + Whisper + Text cleaning
│   ├── stage3_user_profile.py      # User behavioral profile builder
│   ├── stage4_features.py          # 7-score feature engineering
│   ├── stage4b_context_builder.py  # Structured context assembler
│   ├── stage5_reasoning.py         # LLM-style reasoning + confidence gate
│   ├── attention_budget.py         # Attention budget manager
│   ├── stage6_evaluation.py        # Accuracy, F1, confusion matrix
│   ├── stage7_output.py            # output.csv writer
│   └── stage8_explainability.py    # decision_log.json generator
├── dataset/
│   ├── messages.csv
│   ├── output.csv          # Generated predictions
│   ├── decision_log.json   # Structured decision logs
│   └── evaluation_report.txt
└── output.csv              # Root copy of predictions
```

---

## How to Run

Requirements: Python 3.x (standard library only — no external dependencies).

```bash
# Run the full 8-stage pipeline
python router.py

# Run the visual demo with per-message decision breakdowns
python run_demo.py
```

---

## Output Files

| File | Description |
|------|-------------|
| `output.csv` | Final routing predictions (message_id, action, type, reason, confidence, evidence) |
| `decision_log.json` | Structured JSON decision log for all 110 messages |
| `evaluation_report.txt` | Accuracy, Macro F1, Weighted F1 |

---

## Future Work

- Integrate real LLM API (Gemini / GPT-4) for semantic reasoning
- Add real OCR (Tesseract) and Whisper ASR for actual media files
- Implement online learning from user feedback signals
- Add multi-language support (Hindi, French, etc.)
- Deploy as WhatsApp Business API webhook
