"""
Stage 6: Evaluation
Evaluates reasoning decisions against ground truth labels from sample_messages.csv.
"""
import csv
import os
from stages.stage2_preprocessing import preprocess_all
from stages.stage4_features import compute_all_features
from stages.stage4b_context_builder import build_all_contexts
from stages.stage5_reasoning import reason_all, apply_confidence_gate

def run_evaluation_on_samples(data_store):
    """Run pipeline on sample_messages benchmark set and return ground truth vs predictions."""
    sample_msgs = data_store.get('sample_messages', [])
    if not sample_msgs:
        return {}, []

    ground_truth = {row['message_id']: row['action'] for row in sample_msgs if 'message_id' in row and 'action' in row}

    preprocessed_samples = preprocess_all(sample_msgs)
    user_profiles = data_store.get('user_profiles', {})

    sample_features = compute_all_features(preprocessed_samples, user_profiles, data_store)

    budget_mgr = data_store.get('budget_manager')
    sample_contexts = build_all_contexts(preprocessed_samples, user_profiles, sample_features, data_store, budget_mgr)

    sample_decisions = reason_all(sample_contexts)

    return ground_truth, sample_decisions

def evaluate(decisions, data_store, latency_ms=0):
    """Calculates accuracy, precision, recall, f1 and confusion matrix."""
    print("=" * 40)
    print("STAGE 6: Evaluation")
    print("=" * 40)

    ground_truth = {}
    sample_msgs = data_store.get('sample_messages', []) if isinstance(data_store, dict) else []

    if sample_msgs:
        ground_truth = {row['message_id']: row['action'] for row in sample_msgs if 'message_id' in row and 'action' in row}

    eval_decisions = decisions

    matched_count = sum(1 for d in decisions if d['message_id'] in ground_truth)

    if matched_count == 0 and sample_msgs:
        gt, sample_decs = run_evaluation_on_samples(data_store)
        if gt and sample_decs:
            ground_truth = gt
            eval_decisions = sample_decs

    classes = ['notify', 'digest', 'mute']
    metrics = {
        'total': 0,
        'correct': 0,
        'latency_ms': latency_ms,
        'classes': {c: {'TP': 0, 'FP': 0, 'FN': 0, 'support': 0} for c in classes},
        'confusion_matrix': {actual: {pred: 0 for pred in classes} for actual in classes}
    }

    for d in eval_decisions:
        msg_id = d['message_id']
        pred_action = d['action']
        actual_action = ground_truth.get(msg_id)

        if actual_action and actual_action in classes:
            metrics['total'] += 1
            metrics['classes'][actual_action]['support'] += 1
            metrics['confusion_matrix'][actual_action][pred_action] += 1

            if pred_action == actual_action:
                metrics['correct'] += 1
                metrics['classes'][actual_action]['TP'] += 1
            else:
                metrics['classes'][pred_action]['FP'] += 1
                metrics['classes'][actual_action]['FN'] += 1

    if metrics['total'] > 0:
        metrics['accuracy'] = metrics['correct'] / metrics['total']
    else:
        metrics['accuracy'] = 0.0

    macro_f1_sum = 0
    weighted_f1_sum = 0

    for c in classes:
        tp = metrics['classes'][c]['TP']
        fp = metrics['classes'][c]['FP']
        fn = metrics['classes'][c]['FN']

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        metrics['classes'][c]['precision'] = precision
        metrics['classes'][c]['recall'] = recall
        metrics['classes'][c]['f1'] = f1

        macro_f1_sum += f1
        weighted_f1_sum += f1 * metrics['classes'][c]['support']

    metrics['macro_f1'] = macro_f1_sum / len(classes)
    if metrics['total'] > 0:
        metrics['weighted_f1'] = weighted_f1_sum / metrics['total']
    else:
        metrics['weighted_f1'] = 0.0

    return metrics

def print_evaluation(metrics):
    """Print formatted evaluation metrics with ASCII tables for terminal compatibility."""
    total = metrics.get('total', 0)
    if total == 0:
        print("  No ground truth found for evaluation.")
        return

    acc = metrics['accuracy']
    correct = metrics['correct']
    print(f"  Accuracy: {acc*100:.2f}% ({correct}/{total})\n")

    print("  Per-Class Metrics:")
    print("  +----------+-----------+--------+--------+---------+")
    print("  | Class    | Precision | Recall | F1     | Support |")
    print("  +----------+-----------+--------+--------+---------+")

    for c in ['notify', 'digest', 'mute']:
        cm = metrics['classes'][c]
        print(f"  | {c:<8} | {cm['precision']:<9.2f} | {cm['recall']:<6.2f} | {cm['f1']:<6.2f} | {cm['support']:<7} |")

    print("  +----------+-----------+--------+--------+---------+")
    print(f"  | Macro    | -         | -      | {metrics['macro_f1']:<6.2f} | {total:<7} |")
    print(f"  | Weighted | -         | -      | {metrics['weighted_f1']:<6.2f} | {total:<7} |")
    print("  +----------+-----------+--------+--------+---------+\n")

    print("  Confusion Matrix:")
    print("  +--------------+----------+----------+----------+")
    print("  | Actual\\Pred  | notify   | digest   | mute     |")
    print("  +--------------+----------+----------+----------+")

    for actual in ['notify', 'digest', 'mute']:
        row = metrics['confusion_matrix'][actual]
        print(f"  | {actual:<12} | {row['notify']:<8} | {row['digest']:<8} | {row['mute']:<8} |")

    print("  +--------------+----------+----------+----------+\n")

def save_evaluation(metrics, path='evaluation_report.txt'):
    """Save the evaluation report to a file."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"Accuracy: {metrics.get('accuracy', 0)*100:.2f}%\n")
        f.write(f"Macro F1: {metrics.get('macro_f1', 0):.2f}\n")
        f.write(f"Weighted F1: {metrics.get('weighted_f1', 0):.2f}\n")
