"""
Stage 4: Feature Engineering
Computes 7 normalized feature scores (0.0 to 1.0) for each message.
"""

def _is_in_dnd(msg_time_str, dnd_start, dnd_end):
    """Check if message time falls in DND window."""
    if not msg_time_str:
        return False
    try:
        hour = int(msg_time_str.split(' ')[1].split(':')[0])
    except (IndexError, ValueError):
        return False
        
    try:
        dnd_s = int(dnd_start.split(':')[0])
        dnd_e = int(dnd_end.split(':')[0])
    except (AttributeError, IndexError, ValueError):
        return False
        
    if dnd_s > dnd_e:  # overnight (e.g., 22:00-07:00)
        return hour >= dnd_s or hour < dnd_e
    else:
        return dnd_s <= hour < dnd_e

def _clamp(val, min_val=0.0, max_val=1.0):
    return max(min_val, min(val, max_val))

def compute_features(msg, user_profile, data_store):
    """Compute 7 normalized features for a message."""
    text = (msg.get('full_text') or msg.get('raw_text') or '').lower()
    user_id = msg.get('user_id', '')
    sender_id = msg.get('sender_user_id', '')
    group_id = msg.get('group_id', '')
    business_id = msg.get('business_id', '')
    conv_type = msg.get('conversation_type', '')
    fwd_count = int(msg.get('forwarded_count') or 0)
    created_at = msg.get('created_at', '')
    
    fav_contacts = user_profile.get('favorite_contacts', [])
    ign_contacts = user_profile.get('ignored_contacts', [])
    active_groups = user_profile.get('active_groups', [])

    # 1. urgency_score
    urgency = 0.3
    urgent_kw = ['urgent', 'call me', 'immediately', 'now', 'asap', 'emergency', 'rollback', 'expired', 'hospital', 'clinic', 'deadline']
    time_kw = ['10 mins', '15 mins', 'before 5', 'today', 'tonight', 'right now', 'ends at', 'leaving']
    if any(kw in text for kw in urgent_kw):
        urgency += 0.3
    if any(kw in text for kw in time_kw):
        urgency += 0.2
    if conv_type == 'personal':
        urgency += 0.1
    if fwd_count >= 5:
        urgency -= 0.2
    urgency = _clamp(urgency)

    # 2. relationship_score
    relationship = 0.3
    if sender_id in fav_contacts:
        relationship += 0.3
    if sender_id in ign_contacts:
        relationship -= 0.2
    if group_id in active_groups:
        relationship += 0.15
    if conv_type == 'personal':
        relationship += 0.1
    
    if conv_type == 'business' and business_id:
        user_business_history = data_store.get('user_business_history', [])
        for record in user_business_history:
            if record.get('user_id') == user_id and record.get('business_id') == business_id:
                if str(record.get('allows_promotions', '0')) == '1' or record.get('recent_activity'):
                    relationship += 0.2
                break
    relationship = _clamp(relationship)

    # 3. safety_score
    safety = 0.9
    phish_kw = ['otp', 'password', 'pin', 'verify now', 'account block', 'account lock', 'account-login', 'pay-check', 'chase-secure', 'bit.ly']
    action_kw = ['verify', 'send code', 'share otp', 'link', 'login', 'click', 'confirm']
    
    has_phish = any(kw in text for kw in phish_kw)
    has_action = any(kw in text for kw in action_kw)
    if has_phish and has_action:
        safety -= 0.5
        
    prompt_kw = ['ignore all previous', 'routing override', 'system note for', 'assistant instruction', 'mark action=notify']
    if any(kw in text for kw in prompt_kw):
        safety -= 0.6
        
    if fwd_count >= 5:
        safety -= 0.2
        
    suspicious_health_kw = ['health tip: stop all tablets', 'health secret']
    if any(kw in text for kw in suspicious_health_kw):
        safety -= 0.1
    safety = _clamp(safety)

    # 4. novelty_score
    novelty = 0.7
    if fwd_count >= 5:
        novelty -= 0.4
    if 'forward this to' in text or 'share with' in text:
        novelty -= 0.2
    generic_greetings = ['good morning', 'bhagwan', 'blessings']
    if any(kw in text for kw in generic_greetings):
        novelty -= 0.15
    if f'@{user_id}' in text:
        novelty += 0.2
    novelty = _clamp(novelty)

    # 5. importance_score
    importance = 0.4
    if group_id:
        group_members = data_store.get('group_members', [])
        for record in group_members:
            if record.get('group_id') == group_id and record.get('user_id') == sender_id:
                if record.get('role') == 'admin':
                    importance += 0.3
                break
                
    if f'@{user_id}' in text:
        importance += 0.2
        
    if conv_type == 'business':
        trans_kw = ['order', 'delivery', 'pickup', 'payment', 'fedex', 'banking', 'card payment']
        if any(kw in text for kw in trans_kw):
            importance += 0.2
            
    if group_id:
        groups = data_store.get('groups', [])
        for record in groups:
            if record.get('group_id') == group_id:
                g_type = record.get('group_type', '')
                if g_type in ['society', 'school_group', 'coworker', 'safety']:
                    importance += 0.15
                break
                
    promo_kw = ['offer', 'discount', '50% off', 'sale', 'promo']
    if any(kw in text for kw in promo_kw):
        importance -= 0.2
    importance = _clamp(importance)

    # 6. time_sensitivity_score
    time_sens = 0.3
    deadline_kw = ['today', 'now', 'immediately', '10 mins', '15 mins', 'before 5 pm', 'ends at', 'expires', 'leaving', 'deadline']
    if any(kw in text for kw in deadline_kw):
        time_sens += 0.3
        
    dnd_window = user_profile.get('do_not_disturb_window', '22:00-07:00')
    try:
        dnd_start, dnd_end = dnd_window.split('-')
    except (ValueError, AttributeError):
        dnd_start, dnd_end = '22:00', '07:00'
        
    if _is_in_dnd(created_at, dnd_start, dnd_end):
        time_sens -= 0.2
    else:
        time_sens += 0.2
        
    if conv_type == 'personal':
        time_sens += 0.1
    time_sens = _clamp(time_sens)

    # 7. personalization_score
    personalization = 0.3
    if f'@{user_id}' in text:
        personalization += 0.3
    if conv_type == 'personal':
        personalization += 0.2
    if sender_id in fav_contacts:
        personalization += 0.15
        
    if user_profile.get('shopping_interest') and ('sale' in text or 'shopping' in text):
        personalization += 0.1
        
    if fwd_count >= 5:
        personalization -= 0.2
    personalization = _clamp(personalization)

    return {
        'urgency': urgency,
        'relationship': relationship,
        'safety': safety,
        'novelty': novelty,
        'importance': importance,
        'time_sensitivity': time_sens,
        'personalization': personalization,
        'urgency_score': urgency,
        'relationship_score': relationship,
        'safety_score': safety,
        'novelty_score': novelty,
        'importance_score': importance,
        'time_sensitivity_score': time_sens,
        'personalization_score': personalization
    }

def compute_all_features(messages, profiles, data_store):
    print("--- STAGE 4: Feature Engineering ---")
    features_list = []
    for i, msg in enumerate(messages):
        user_id = msg.get('user_id')
        user_profile = profiles.get(user_id, {})
        scores = compute_features(msg, user_profile, data_store)
        features_list.append(scores)
    print(f"Computed features for {len(features_list)} messages.")
    return features_list
