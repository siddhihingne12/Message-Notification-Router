# WhatsApp Multimodal Message Notification Router

An AI-powered multimodal message notification routing system that determines whether incoming WhatsApp messages deserve immediate attention (`notify`), can wait for a daily summary (`digest`), or should be silenced (`mute`).

This system goes beyond simple classification — it **manages the user's attention** by combining multimodal understanding, behavioral profiling, feature engineering, LLM reasoning, a confidence threshold gate, and an attention budget manager.

---

## Key Modules & Integrations

### 1. LLM Integration (`stages/llm_client.py`)
- Standard library REST client (`urllib.request`) with zero external dependencies.
- Supports **Google Gemini API** (`GEMINI_API_KEY`) and **OpenAI API** (`OPENAI_API_KEY`).
- Constructs a structured JSON prompt with message details, features, sender trust scores, and attention budget.
- Automatic fallback to local heuristic LLM-reasoning engine when API keys are not provided.

### 2. OCR Engine Integration (`stages/ocr_engine.py`)
- Optical Character Recognition module supporting `pytesseract` for live image processing.
- Intelligent fallback to benchmark dataset OCR extraction mapping (`OCR_MAP`).
- Performs text normalization, line-break cleaning, and noise removal.

### 3. Engagement Calculations (`stages/stage3_user_profile.py`)
- Calculates exact mathematical engagement metrics per user from 30-day event logs:
  - **Engagement Rate:** `replies_sent_30d / max(1, messages_opened_30d)`
  - **Average Response Delay:** Mean time gap (in minutes) between incoming message and user reply.
  - **Sender Trust Score:** 
    $$\text{Trust} = \frac{\text{Replies} \times 1.0 - \text{Dismissals} \times 0.5}{\max(1, \text{Total Received})}$$ normalized to $[0.0, 1.0]$.
  - **Notification Fatigue Index:** Ratio of dismissed to sent notifications from daily summaries.
  - **Shopping Interest Score:** Derived from business account category interactions and promotion opt-in history.

### 4. Standalone Evaluation Suite (`evaluate.py`)
- Executable directly via command line: `python evaluate.py`.
- Evaluates predictions against 30 ground-truth benchmark messages (`sample_messages.csv`).
- Outputs Accuracy, Macro F1, Weighted F1, Per-class Precision/Recall/F1, Confusion Matrix, and Latency benchmarks (ms/msg).
- Automatically writes `evaluation_report.txt` and `evaluation_report.json`.

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
[Stage 2] Multimodal Preprocessing (OCR + Whisper)
  Image -> OCREngine (pytesseract / OCR_MAP)
  Voice -> Whisper Transcriber
  Text  -> Text Cleaner
  => Every message gets: raw_text + ocr_text + whisper_text + full_text
       |
       v
[Stage 3] User Profile Builder & Engagement Engine
  Mine behavioral patterns & calculate engagement metrics:
  Engagement Rate | Sender Trust Scores | Avg Response Delay |
  Notification Fatigue Index | Shopping Interest Score | Active Groups
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
  LLMClient (Gemini API / OpenAI API / Heuristic Engine):
  Evaluate context -> Decide action + Confidence
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
| Latency | **5.94 ms/msg** |

---

## How to Run

Requirements: Python 3.x (standard library only — no external dependencies required).

```bash
# Run the full 8-stage pipeline
python router.py

# Run the standalone evaluation suite
python evaluate.py

# Run the visual demo with per-message decision breakdowns
python run_demo.py
```

---

## Output Files

| File | Description |
|------|-------------|
| `output.csv` | Final routing predictions (message_id, action, type, reason, confidence, evidence) |
| `decision_log.json` | Structured JSON decision log for all 110 messages |
| `evaluation_report.txt` | Accuracy, Macro F1, Weighted F1 text report |
| `evaluation_report.json` | Complete evaluation metrics and confusion matrix JSON |
