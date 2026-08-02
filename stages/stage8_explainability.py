"""
Stage 8: Explainability
Generates decision logs and pipeline summary.
"""
import json

def generate_decision_log(decisions):
    """Generate structured JSON log entries for all decisions."""
    log = []
    for d in decisions:
        entry = {
            'message_id': d['message_id'],
            'decision': d['action'],
            'confidence': d['confidence'],
            'message_type': d['message_type'],
            'reasoning_path': d.get('reasoning_path', 'LLM'),
            'confidence_gate': d.get('confidence_gate', 'passed'),
            'feature_scores': d.get('feature_scores', {}),
            'attention_budget': d.get('attention_budget', {}),
            'evidence': d.get('reasons', [])  # the reason strings serve as evidence
        }
        log.append(entry)
    return log

def save_decision_log(log, path='decision_log.json'):
    """Save decision log as formatted JSON."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(log)} decision logs to {path}")

def print_pipeline_summary(decisions, metrics=None):
    """Print final pipeline summary."""
    print("="*40)
    print("STAGE 8: Explainability & Summary")
    print("="*40)
    
    # Count stats
    stats = {'notify': 0, 'digest': 0, 'mute': 0}
    llm = 0
    fallback = 0
    for d in decisions:
        stats[d.get('action', 'digest')] += 1
        if d.get('reasoning_path') == 'LLM': llm += 1
        else: fallback += 1
    
    print("  Pipeline Summary:")
    print(f"    Total messages processed: {len(decisions)}")
    print(f"    NOTIFY: {stats['notify']} | DIGEST: {stats['digest']} | MUTE: {stats['mute']}")
    print(f"    LLM decisions: {llm} | Rule checker fallbacks: {fallback}")
    if metrics:
        print(f"    Evaluation Accuracy: {metrics.get('accuracy', 0)*100:.1f}%")
        print(f"    Macro F1: {metrics.get('macro_f1', 0):.2f}")
    print()
    print("  Future Work:")
    print("    - Integrate real LLM API (Gemini/GPT) for reasoning")
    print("    - Add real OCR (Tesseract) and Whisper ASR")
    print("    - Implement online learning from user feedback")
    print("    - Add multi-language support")
    print("    - Deploy as WhatsApp Business API webhook")
    print()
