"""
Standalone Evaluation Script for WhatsApp Multimodal Message Notification Router
Runs full pipeline evaluation against 30 ground-truth sample messages benchmark dataset.
Generates terminal tables, evaluation_report.txt, and evaluation_report.json.
"""
import json
import os
import time
from stages.stage1_ingestion import load_all_data
from stages.stage2_preprocessing import preprocess_all
from stages.stage3_user_profile import build_all_profiles
from stages.stage4_features import compute_all_features
from stages.attention_budget import AttentionBudgetManager
from stages.stage4b_context_builder import build_all_contexts
from stages.stage5_reasoning import reason_all
from stages.stage6_evaluation import evaluate, print_evaluation, save_evaluation

def run_standalone_evaluation(data_dir="dataset"):
    print("=" * 80)
    print("      WHATSAPP MULTIMODAL MESSAGE NOTIFICATION ROUTER — EVALUATION SUITE      ")
    print("=" * 80)
    print()

    start_time = time.time()

    # Stage 1: Load Data
    data_store = load_all_data(data_dir)
    sample_msgs = data_store.get('sample_messages', [])

    if not sample_msgs:
        print("[ERROR] No sample_messages.csv ground truth data found.")
        return

    # Stage 2: Multimodal Preprocessing
    preprocessed_samples = preprocess_all(sample_msgs)

    # Stage 3: User Profiles & Engagement Calculations
    user_profiles = build_all_profiles(data_store)
    data_store['user_profiles'] = user_profiles

    # Stage 4: Feature Engineering
    sample_features = compute_all_features(preprocessed_samples, user_profiles, data_store)

    # Attention Budget Manager
    budget_manager = AttentionBudgetManager(data_store)
    data_store['budget_manager'] = budget_manager

    # Stage 4B: Context Builder
    sample_contexts = build_all_contexts(preprocessed_samples, user_profiles, sample_features, data_store, budget_manager)

    # Stage 5: Reasoning Engine
    sample_decisions = reason_all(sample_contexts)

    # Apply Attention Budget
    for i, decision in enumerate(sample_decisions):
        ctx = sample_contexts[i]
        user_id = ctx['user_profile'].get('user_id', '')
        action = decision['action']
        urgency = ctx['feature_scores'].get('urgency', 0.5)
        sender_is_top_fav = ctx['sender_info'].get('is_favorite', False)
        has_mention_urgent = f"@{user_id}" in ctx['message'].get('full_text', '') and urgency >= 0.7

        adjusted_action, updated_budget_info = budget_manager.apply_budget(
            user_id=user_id,
            action=action,
            urgency_score=urgency,
            sender_is_top_favorite=sender_is_top_fav,
            has_direct_mention_urgent=has_mention_urgent
        )

        decision['action'] = adjusted_action
        decision['attention_budget'] = updated_budget_info

    end_time = time.time()
    total_time_ms = (end_time - start_time) * 1000
    latency_per_msg_ms = total_time_ms / max(1, len(sample_msgs))

    # Stage 6: Compute Metrics
    metrics = evaluate(sample_decisions, data_store, latency_ms=latency_per_msg_ms)

    # Print Visual Report
    print_evaluation(metrics)

    print(f"  Latency Performance:")
    print(f"  * Total Evaluation Time: {total_time_ms:.2f} ms")
    print(f"  * Latency per Message:   {latency_per_msg_ms:.2f} ms/msg\n")

    # Save evaluation_report.txt & dataset/evaluation_report.txt
    txt_path1 = os.path.join(data_dir, "evaluation_report.txt")
    txt_path2 = "evaluation_report.txt"
    save_evaluation(metrics, txt_path1)
    save_evaluation(metrics, txt_path2)

    # Save JSON metrics report
    json_report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_benchmark_samples": metrics.get('total', 0),
        "accuracy": round(metrics.get('accuracy', 0) * 100, 2),
        "macro_f1": round(metrics.get('macro_f1', 0), 2),
        "weighted_f1": round(metrics.get('weighted_f1', 0), 2),
        "latency_per_msg_ms": round(latency_per_msg_ms, 2),
        "per_class_metrics": metrics.get('classes', {}),
        "confusion_matrix": metrics.get('confusion_matrix', {})
    }

    json_path1 = os.path.join(data_dir, "evaluation_report.json")
    json_path2 = "evaluation_report.json"

    for jp in [json_path1, json_path2]:
        with open(jp, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2)

    print(f"  [OK] Saved evaluation_report.txt to {txt_path1} and {txt_path2}")
    print(f"  [OK] Saved evaluation_report.json to {json_path1} and {json_path2}")
    print("=" * 80)

if __name__ == "__main__":
    run_standalone_evaluation("dataset")
