"""
Stage 4B: Context Builder
Assembles everything into one structured context dict per message.
"""

def build_context(msg, user_profile, feature_scores, data_store, attention_info):
    user_id = msg.get('user_id', '')
    sender_id = msg.get('sender_user_id', '')
    group_id = msg.get('group_id', '')
    business_id = msg.get('business_id', '')

    # sender_info
    fav_contacts = user_profile.get('favorite_contacts', [])
    ign_contacts = user_profile.get('ignored_contacts', [])
    
    is_group_admin = False
    if group_id:
        group_members = data_store.get('group_members', [])
        for record in group_members:
            if record.get('group_id') == group_id and record.get('user_id') == sender_id:
                if record.get('role') == 'admin':
                    is_group_admin = True
                break
                
    trust_level = 'neutral'
    if sender_id in fav_contacts:
        trust_level = 'high'
    elif sender_id in ign_contacts:
        trust_level = 'low'
        
    sender_info = {
        'sender_id': sender_id,
        'is_favorite': sender_id in fav_contacts,
        'is_ignored': sender_id in ign_contacts,
        'is_group_admin': is_group_admin,
        'trust_level': trust_level
    }

    # group_info
    group_info = None
    if group_id:
        g_name = ''
        g_type = ''
        groups = data_store.get('groups', [])
        for record in groups:
            if record.get('group_id') == group_id:
                g_name = record.get('group_name', '')
                g_type = record.get('group_type', '')
                break
                
        user_role = 'member'
        group_muted = 0
        group_members = data_store.get('group_members', [])
        for record in group_members:
            if record.get('group_id') == group_id and record.get('user_id') == user_id:
                user_role = record.get('role', 'member')
                group_muted = int(record.get('group_muted_by_user', 0))
                break
                
        group_info = {
            'group_id': group_id,
            'group_name': g_name,
            'group_type': g_type,
            'user_role': user_role,
            'group_muted': group_muted
        }

    # business_info
    business_info = None
    if business_id:
        relationship = ''
        allows_promotions = 0
        opted_out = False
        user_business_history = data_store.get('user_business_history', [])
        for record in user_business_history:
            if record.get('user_id') == user_id and record.get('business_id') == business_id:
                relationship = record.get('why_user_knows_account', '')
                allows_promotions = int(record.get('allows_promotions', 0))
                opted_out = bool(record.get('promotions_opted_out_at'))
                break
                
        business_info = {
            'business_id': business_id,
            'relationship': relationship,
            'allows_promotions': allows_promotions,
            'opted_out': opted_out
        }

    # historical_evidence
    historical_evidence = []
    messages = data_store.get('message_history', [])
    count = 0
    for m in reversed(messages):  # look at recent first assuming order
        if m.get('message_id') == msg.get('message_id'):
            continue  # skip self
        if m.get('user_id') == user_id:
            match = False
            if business_id and m.get('business_id') == business_id:
                match = True
            elif group_id and m.get('group_id') == group_id:
                match = True
            elif sender_id and m.get('sender_user_id') == sender_id:
                match = True
            
            if match:
                historical_evidence.append(m.get('message_id'))
                count += 1
                if count >= 2:
                    break

    return {
        'message': {
            'id': msg.get('message_id', ''),
            'text': msg.get('raw_text', ''),
            'full_text': msg.get('full_text', ''),
            'conversation_type': msg.get('conversation_type', ''),
            'group_id': group_id,
            'business_id': business_id,
            'sender_user_id': sender_id,
            'media_type': msg.get('media_type', ''),
            'media_id': msg.get('media_id', ''),
            'forwarded_count': int(msg.get('forwarded_count') or 0),
            'created_at': msg.get('created_at', '')
        },
        'user_profile': user_profile,
        'sender_info': sender_info,
        'group_info': group_info,
        'business_info': business_info,
        'feature_scores': feature_scores,
        'attention_budget': attention_info,
        'historical_evidence': historical_evidence
    }

def build_all_contexts(messages, profiles, all_features, data_store, budget_manager):
    print("--- STAGE 4B: Context Builder ---")
    contexts = []
    for i, msg in enumerate(messages):
        user_id = msg.get('user_id')
        user_profile = profiles.get(user_id, {})
        feature_scores = all_features[i]
        attention_info = budget_manager.get_budget_info(user_id)
        ctx = build_context(msg, user_profile, feature_scores, data_store, attention_info)
        contexts.append(ctx)
    print(f"Built contexts for {len(contexts)} messages.")
    return contexts
