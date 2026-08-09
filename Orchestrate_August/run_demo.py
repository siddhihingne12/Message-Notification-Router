import os
import time
from router import MessageNotificationRouter

def run_visual_demo():
    print("=" * 80)
    print("   WHATSAPP MULTIMODAL MESSAGE NOTIFICATION ROUTER — DEMO ENGINE   ")
    print("=" * 80)
    print()
    print("  Pipeline Stages:")
    print("  [1] Data Ingestion  [2] Multimodal Preprocessing  [3] User Profile Builder")
    print("  [4] Feature Engineering  [4B] Context Builder  [5] LLM Reasoning + Confidence Gate")
    print("  [Attention Budget Manager]  [6] Evaluation  [7] Output  [8] Decision Explainability")
    print()
    time.sleep(0.3)

    router = MessageNotificationRouter("dataset")
    decisions, metrics = router.run_pipeline()

    # Visual per-message decision log
    print()
    print("=" * 80)
    print("                      ROUTING DECISIONS LOG                          ")
    print("=" * 80)

    from stages.stage1_ingestion import load_all_data
    data_store = load_all_data("dataset")
    messages = data_store['messages']

    msg_map = {d['message_id']: d for d in decisions}

    stats = {"notify": 0, "digest": 0, "mute": 0}

    for idx, msg in enumerate(messages, 1):
        mid = msg.get('message_id', '')
        d = msg_map.get(mid)
        if not d:
            continue

        action = d['action']
        stats[action] += 1
        msg_type = d['message_type']
        confidence = d['confidence']
        reasons = d['reasons']
        evidence = d['evidence_message_ids']
        reasoning_path = d.get('reasoning_path', 'LLM')
        conf_gate = d.get('confidence_gate', 'passed')
        feat = d.get('feature_scores', {})
        budget = d.get('attention_budget', {})

        media_info = ""
        mt = msg.get('media_type', '')
        mi = msg.get('media_id', '')
        if mt:
            media_info = f" [{mt.upper()}: {mi}]"

        text_preview = (msg.get('message_text') or '').replace('\n', ' ')
        if len(text_preview) > 80:
            text_preview = text_preview[:80] + "..."

        print(f"\n[MSG #{idx:03d} | ID: {mid}] User: {msg.get('user_id')} | Type: {msg.get('conversation_type')}{media_info}")
        if text_preview:
            print(f'  Text: "{text_preview}"')

        print("+----------------------- DECISION BREAKDOWN -----------------------+")
        print(f"| Decision:       {action.upper():<50} |")
        print(f"| Confidence:     {int(confidence * 100)}%{'':<48} |")
        print(f"| Message Type:   {msg_type:<50} |")
        print(f"| Reasoning Path: {reasoning_path:<50} |")
        print(f"| Confidence Gate:{conf_gate:<50} |")
        print("+-------------------------------------------------------------------+")
        print("| Feature Scores:                                                   |")
        print(f"|   Urgency={feat.get('urgency', 0):.2f}  Relationship={feat.get('relationship', 0):.2f}  Safety={feat.get('safety', 0):.2f}  Novelty={feat.get('novelty', 0):.2f}  |")
        print(f"|   Importance={feat.get('importance', 0):.2f}  TimeSensitivity={feat.get('time_sensitivity', 0):.2f}  Personalization={feat.get('personalization', 0):.2f}  |")
        print("+-------------------------------------------------------------------+")
        print(f"| Attention Budget: Used={budget.get('notifications_today', 0)} / Limit={budget.get('budget_limit', 10)} | Remaining={budget.get('budget_remaining', 10)} | Override={budget.get('budget_override', False)} |")
        print("+-------------------------------------------------------------------+")
        print("| Reasons:                                                          |")
        for r_item in reasons:
            wrapped = r_item[:65]
            print(f"|   - {wrapped:<64}|")
        print(f"| Evidence: {evidence[:55]:<58}|")
        print("+-------------------------------------------------------------------+")

    print("\n" + "=" * 80)
    print("                        FINAL ROUTING SUMMARY                        ")
    print("=" * 80)
    print(f"  Total Messages Processed: {len(messages)}")
    print(f"  * NOTIFY (Immediate Interrupt): {stats['notify']} messages")
    print(f"  * DIGEST (Daily Batch):         {stats['digest']} messages")
    print(f"  * MUTE   (Noise / Scam / Spam): {stats['mute']} messages")
    print()
    if metrics.get('total', 0) > 0:
        print(f"  Evaluation vs Ground Truth ({metrics['total']} samples):")
        print(f"  * Accuracy:  {metrics['accuracy']*100:.1f}%")
        print(f"  * Macro F1:  {metrics['macro_f1']:.2f}")
        print(f"  * Weighted F1: {metrics['weighted_f1']:.2f}")
    print("=" * 80)
    print("\n[OK] output.csv written. decision_log.json saved. evaluation_report.txt saved.")

if __name__ == "__main__":
    run_visual_demo()
