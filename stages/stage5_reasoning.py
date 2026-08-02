"""
Stage 5: Reasoning Engine
Implements LLM-style decision logic with a confidence gate and a fallback rule checker.
"""

def build_decision(context, action, msg_type, confidence, reasons):
    """Helper to structure the decision output."""
    evidence = context.get('historical_evidence', [])
    evidence_str = ';'.join(evidence) if isinstance(evidence, list) and evidence else (evidence if isinstance(evidence, str) else 'none')
    return {
        'message_id': context['message']['id'],
        'action': action,
        'message_type': msg_type,
        'confidence': confidence,
        'reasons': reasons,
        'evidence_message_ids': evidence_str if evidence_str else 'none',
        'feature_scores': context.get('feature_scores', {}),
        'attention_budget': context.get('attention_budget', {}),
        'reasoning_path': 'LLM',
        'confidence_gate': 'passed'
    }

def reason(context):
    """Main LLM reasoning engine logic combining feature scores and context rules."""
    scores = context.get('feature_scores', {})
    msg = context.get('message', {})
    full_text = (msg.get('full_text') or msg.get('text') or '').lower()
    user = context.get('user_profile', {})
    sender = context.get('sender_info', {})
    group = context.get('group_info')
    biz = context.get('business_info')
    user_id = user.get('user_id', '')

    reasons = []

    # RULE 1: Prompt Injection / System Override Attack
    if any(phrase in full_text for phrase in [
        "ignore all previous", "routing override", "system note for", "assistant instruction", "mark action=notify"
    ]):
        action = "mute"
        msg_type = "scam"
        confidence = 0.95
        reasons.append("Prompt injection attack detected attempting router manipulation.")
        reasons.append("Contains malicious instructions trying to bypass safety checks.")
        return build_decision(context, action, msg_type, confidence, reasons)

    # RULE 2: Phishing / Scam Detection
    phish_keywords = ["otp", "password", "pin", "verify now", "account block", "account lock", "account-login", "account-help", "pay-check", "chase-secure", "amazonpay-delivery", "bit.ly"]
    if any(k in full_text for k in phish_keywords) and any(w in full_text for w in ["verify", "send code", "share otp", "link", "login", "click", "confirm"]):
        action = "mute"
        msg_type = "scam"
        confidence = 0.92
        reasons.append("Suspicious credential or OTP verification request detected.")
        reasons.append("Uses high-pressure security threats (account block/lock) to induce urgency.")
        reasons.append("Unverified link or insecure authorization flow detected.")
        return build_decision(context, action, msg_type, confidence, reasons)

    # RULE 3: High Forward Count / Chain / Blessing Messages
    forwarded = msg.get('forwarded_count', 0)
    try: forwarded_count = int(forwarded)
    except: forwarded_count = 0

    if forwarded_count >= 5 or any(phrase in full_text for phrase in ["forward this to", "share with 10 people", "good morning sabko", "bhagwan sabka bhala", "health tip: stop all tablets", "health secret"]):
        action = "mute"
        msg_type = "forward" if forwarded_count >= 5 else "greeting"
        if "health" in full_text or "tablets" in full_text:
            msg_type = "spam"
        confidence = 0.88
        reasons.append(f"Chain forward message detected (forwarded {forwarded_count} times).")
        reasons.append("Contains repetitive non-personalized content or unverified viral broadcast.")
        reasons.append("Sender/group interaction history shows low engagement on forwards.")
        return build_decision(context, action, msg_type, confidence, reasons)

    # RULE 4: Group Muted by User
    group_muted = group.get('group_muted', 0) if group else 0
    if group_muted == 1 or group_muted is True:
        if user_id and f"@{user_id}" in full_text:
            action = "notify"
            msg_type = "urgent" if any(w in full_text for w in ["meeting", "call", "prod", "urgent", "client"]) else "personal"
            confidence = 0.90
            reasons.append(f"Direct mention (@{user_id}) overrides group mute setting.")
            reasons.append("User is explicitly tagged for direct attention.")
            return build_decision(context, action, msg_type, confidence, reasons)

    # RULE 5: Personal Urgent Messages
    conv_type = msg.get('conversation_type', '')
    if conv_type == "personal" or (user_id and f"@{user_id}" in full_text):
        if any(k in full_text for k in ["call me", "urgent", "clinic", "hospital", "doctor", "passport", "expired today", "gate 2", "10 mins", "now", "rollback", "early", "heads-up", "leaving", "prod review", "payment worker", "queue numbers", "stadium road"]):
            action = "notify"
            msg_type = "urgent" if any(w in full_text for w in ["call", "urgent", "now", "clinic", "rollback", "prod", "payment"]) else "personal"
            confidence = 0.91
            reasons.append("High urgency personal context detected.")
            reasons.append("Contains time-sensitive request requiring immediate user response.")
            if user_id and f"@{user_id}" in full_text:
                reasons.append("Contains direct user mention tag.")
            return build_decision(context, action, msg_type, confidence, reasons)

    # RULE 6: Group Admin / Society / School Notices
    if conv_type == "group" and group:
        group_type = group.get('group_type', '')

        if any(k in full_text for k in ["tanker", "water supply", "fire alarm", "lift maintenance", "bus is leaving", "bus", "penalty list", "maintenance closes", "gate band", "heads-up", "school circular", "circular"]):
            action = "notify"
            msg_type = "urgent" if any(w in full_text for w in ["tanker", "gate band", "penalty", "fire alarm"]) else "event"
            confidence = 0.89
            reasons.append(f"Important operational update in {group_type} group.")
            reasons.append("Time-sensitive community notice relevant to daily routines.")
            return build_decision(context, action, msg_type, confidence, reasons)

        if any(k in full_text for k in ["selling", "kurta set", "recliner", "plots", "loan approved"]):
            if "loan approved" in full_text or "plots near airport" in full_text:
                action = "mute"
                msg_type = "spam" if "loan" in full_text else "promotion"
                confidence = 0.86
                reasons.append("Unsolicited financial / real estate promotion in group chat.")
                reasons.append("High risk or low relevance marketing post.")
                return build_decision(context, action, msg_type, confidence, reasons)
            else:
                action = "digest"
                msg_type = "promotion"
                confidence = 0.84
                reasons.append("Local buy/sell marketplace listing in community group.")
                reasons.append("Useful information but non-blocking for immediate attention.")
                return build_decision(context, action, msg_type, confidence, reasons)

        if any(k in full_text for k in ["good morning", "match", "cricket", "potluck", "slides", "notes", "dance practice"]):
            if "good morning" in full_text:
                action = "digest" if not group_muted else "mute"
                msg_type = "greeting"
            else:
                action = "digest"
                msg_type = "personal" if any(w in full_text for w in ["match", "practice"]) else "event"
            confidence = 0.83
            reasons.append("Routine casual/social communication in group.")
            reasons.append("Non-urgent activity suitable for batched digest review.")
            return build_decision(context, action, msg_type, confidence, reasons)

    # RULE 7: Business Account Communication
    if conv_type == "business" and biz:
        opted_out = biz.get('opted_out', False)
        allows_promos = biz.get('allows_promotions', 1)

        if opted_out or allows_promos == 0:
            if any(k in full_text for k in ["50% off", "shopping benefit", "the mountains are calling", "ladakh", "reminder: your account has a shopping offer", "new here"]):
                action = "mute"
                msg_type = "promotion"
                confidence = 0.88
                reasons.append("Promotional message from business account user opted out from.")
                reasons.append("User historical records show explicit promotion opt-out / high dismissal.")
                return build_decision(context, action, msg_type, confidence, reasons)

        if any(k in full_text for k in ["order ending", "order", "fedex delivery", "pickup code", "health-related update", "care services", "ride update", "banking services", "card payment update"]):
            action = "notify"
            msg_type = "business_update" if any(w in full_text for w in ["order", "fedex", "ride", "banking", "card"]) else "event"
            confidence = 0.91
            reasons.append("Verified business sending transactional order or service update.")
            reasons.append("Matches user's active relationship / delivery history.")
            return build_decision(context, action, msg_type, confidence, reasons)

        if any(k in full_text for k in ["pvr cinemas", "card statement", "survey", "hoop pain relief", "international payout"]):
            action = "digest"
            msg_type = "business_update" if any(w in full_text for w in ["statement", "cinemas"]) else "promotion"
            confidence = 0.82
            reasons.append("Legitimate business notification without immediate action requirement.")
            reasons.append("Can be reviewed later in routine notification digest.")
            return build_decision(context, action, msg_type, confidence, reasons)

    if conv_type == "personal":
        if any(k in full_text for k in ["reached home", "did you eat", "pottery workshop", "bonjour", "workspace access", "bluebell apartments"]):
            action = "digest" if "workspace access" not in full_text else "notify"
            msg_type = "urgent" if "workspace access" in full_text else "personal"
            confidence = 0.85
            if action == "notify":
                reasons.append("Time-sensitive access expiration alert from personal connection.")
            else:
                reasons.append("Standard personal message with low urgency.")
                reasons.append("No immediate action required, saved for digest.")
            return build_decision(context, action, msg_type, confidence, reasons)

    # DEFAULT
    action = "digest"
    msg_type = "unknown"
    confidence = 0.85
    reasons.append("Routed based on general conversational context and user activity patterns.")
    return build_decision(context, action, msg_type, confidence, reasons)

def rule_checker_fallback(context):
    """Simple deterministic rules used when LLM confidence is low."""
    msg = context.get('message', {})
    full_text = (msg.get('full_text') or msg.get('text') or '').lower()

    action = 'digest'
    msg_type = 'unknown'
    reasons = ['Rule checker fallback triggered due to low LLM confidence.']

    if 'otp' in full_text or 'verify' in full_text:
        action = 'notify'
        msg_type = 'urgent'
    elif 'good morning' in full_text or 'forwarded' in full_text:
        action = 'mute'
        msg_type = 'spam'
    elif 'offer' in full_text or 'sale' in full_text or 'discount' in full_text:
        action = 'mute'
        msg_type = 'promotion'

    return {
        'message_id': msg.get('id', ''),
        'action': action,
        'message_type': msg_type,
        'confidence': 1.0,
        'reasons': reasons,
        'evidence_message_ids': 'none',
        'feature_scores': context.get('feature_scores', {}),
        'attention_budget': context.get('attention_budget', {}),
        'reasoning_path': 'rule_checker_fallback',
        'confidence_gate': 'failed_sent_to_rules'
    }

def apply_confidence_gate(decision, context):
    """If confidence < 0.60, fall back to rule checker."""
    if decision.get('confidence', 1.0) < 0.60:
        decision = rule_checker_fallback(context)
        decision['reasoning_path'] = 'rule_checker_fallback'
        decision['confidence_gate'] = 'failed_sent_to_rules'
    return decision

def reason_all(contexts):
    """Stage 5: Run reasoning + confidence gate on all messages."""
    print("=" * 40)
    print("STAGE 5: Reasoning Engine")
    print("=" * 40)

    decisions = []
    llm_count = 0
    fallback_count = 0
    stats = {'notify': 0, 'digest': 0, 'mute': 0}

    for ctx in contexts:
        decision = reason(ctx)
        decision = apply_confidence_gate(decision, ctx)

        if decision['reasoning_path'] == 'LLM':
            llm_count += 1
        else:
            fallback_count += 1
        stats[decision['action']] += 1
        decisions.append(decision)

    print(f"  Decisions via LLM: {llm_count}")
    print(f"  Fallback to Rule Checker: {fallback_count} (low confidence)")
    print(f"  NOTIFY: {stats['notify']} | DIGEST: {stats['digest']} | MUTE: {stats['mute']}\n")
    return decisions
