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
from stages.stage7_output import write_output
from stages.stage8_explainability import generate_decision_log, save_decision_log, print_pipeline_summary

class MessageNotificationRouter:
    """Main orchestrator for the 8-stage WhatsApp Multimodal Message Notification Router."""
    def __init__(self, data_dir="dataset"):
        self.data_dir = data_dir

    def run_pipeline(self):
        start_time = time.time()
        print("=" * 80)
        print("  WHATSAPP MULTIMODAL MESSAGE NOTIFICATION ROUTER — 8-STAGE PIPELINE  ")
        print("=" * 80)
        print()

        # Stage 1: Data Ingestion
        data_store = load_all_data(self.data_dir)

        # Stage 2: Multimodal Preprocessing (OCR + Whisper + Text Clean)
        preprocessed_messages = preprocess_all(data_store['messages'])

        # Stage 3: User Profile Builder
        user_profiles = build_all_profiles(data_store)
        data_store['user_profiles'] = user_profiles

        # Stage 4: Feature Engineering
        all_features = compute_all_features(preprocessed_messages, user_profiles, data_store)

        # Attention Budget Manager Initializer
        budget_manager = AttentionBudgetManager(data_store)
        data_store['budget_manager'] = budget_manager

        # Stage 4B: Context Builder
        contexts = build_all_contexts(preprocessed_messages, user_profiles, all_features, data_store, budget_manager)

        # Stage 5: LLM Reasoning + Confidence Gate + Rule Checker Fallback
        decisions = reason_all(contexts)

        # Apply Attention Budget Adjustments to final decisions
        for i, decision in enumerate(decisions):
            ctx = contexts[i]
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
        latency_ms = (end_time - start_time) * 1000 / max(1, len(preprocessed_messages))

        # Stage 6: Evaluation
        metrics = evaluate(decisions, data_store, latency_ms=latency_ms)
        print_evaluation(metrics)
        save_evaluation(metrics, os.path.join(self.data_dir, "evaluation_report.txt"))

        # Stage 7: Output Generation
        write_output(decisions, self.data_dir)

        # Stage 8: Decision Logging & Explainability
        decision_log = generate_decision_log(decisions)
        save_decision_log(decision_log, os.path.join(self.data_dir, "decision_log.json"))
        save_decision_log(decision_log, "decision_log.json")
        print_pipeline_summary(decisions, metrics)

        return decisions, metrics

def main():
    router = MessageNotificationRouter("dataset")
    router.run_pipeline()

if __name__ == "__main__":
    main()
