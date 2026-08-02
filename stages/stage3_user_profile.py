from collections import defaultdict

def build_user_profile(user_id, data_store):
    """Builds a behavioral profile for a single user."""
    users = data_store.get('users', [])
    user_row = next((u for u in users if u.get('user_id') == user_id), None)
    
    dnd_start = 22
    dnd_end = 7
    if user_row:
        if 'dnd_start_time' in user_row and user_row['dnd_start_time']:
            try: dnd_start = int(user_row['dnd_start_time'].split(':')[0])
            except: pass
        if 'dnd_end_time' in user_row and user_row['dnd_end_time']:
            try: dnd_end = int(user_row['dnd_end_time'].split(':')[0])
            except: pass
            
    # Calculate engagement_rate
    users_stats = user_row if user_row else {}
    replied = float(users_stats.get('messages_replied_30d', 0)) if users_stats.get('messages_replied_30d') else 0
    opened = float(users_stats.get('messages_opened_30d', 0)) if users_stats.get('messages_opened_30d') else 0
    engagement_rate = replied / opened if opened > 0 else 0.0
    
    messages_reported_30d = int(users_stats.get('messages_reported_30d', 0)) if users_stats.get('messages_reported_30d') else 0
    
    # Notification fatigue
    daily_summary = data_store.get('daily_summary', [])
    fatigue_ratios = []
    for row in daily_summary:
        if row.get('user_id') == user_id:
            sent = float(row.get('notifications_sent', 0))
            dismissed = float(row.get('notifications_dismissed', 0))
            if sent > 0:
                fatigue_ratios.append(dismissed / sent)
    notification_fatigue = sum(fatigue_ratios) / len(fatigue_ratios) if fatigue_ratios else 0.0
    
    # Favorite and Ignored Contacts
    message_events = data_store.get('message_events', [])
    message_history = data_store.get('message_history', [])
    
    msg_history_map = {m['message_id']: m['sender_user_id'] for m in message_history if m.get('message_id') and m.get('sender_user_id')}
    
    replies_count = defaultdict(int)
    ignores_count = defaultdict(int)
    
    for ev in message_events:
        if ev.get('user_id') == user_id:
            msg_id = ev.get('message_id')
            sender = msg_history_map.get(msg_id)
            if sender and sender != user_id:
                if ev.get('message_replied') == '1' or ev.get('message_replied') == 'True':
                    replies_count[sender] += 1
                if ev.get('notification_dismissed') == '1' or ev.get('notification_dismissed') == 'True' or ev.get('muted_after_message') == '1' or ev.get('muted_after_message') == 'True':
                    ignores_count[sender] += 1
                    
    favorite_contacts = [k for k, v in sorted(replies_count.items(), key=lambda item: item[1], reverse=True)[:5]]
    ignored_contacts = [k for k, v in ignores_count.items() if v >= 2]
    
    # Active and muted groups
    group_members = data_store.get('group_members', [])
    groups = data_store.get('groups', [])
    
    active_groups = []
    muted_groups = []
    
    for gm in group_members:
        if gm.get('user_id') == user_id:
            g_id = gm.get('group_id')
            if gm.get('group_muted_by_user') == '1' or gm.get('group_muted_by_user') == 'True':
                muted_groups.append(g_id)
            replies_30d = int(gm.get('replies_sent_30d', 0)) if gm.get('replies_sent_30d') else 0
            if replies_30d > 0:
                active_groups.append(g_id)
                
    work_related_groups = []
    group_map = {g['group_id']: g.get('group_type', '') for g in groups if g.get('group_id')}
    for g_id in active_groups + muted_groups: # Check all groups the user is part of
        g_type = group_map.get(g_id, '').lower()
        if g_type in ['coworker', 'tech_community']:
            if g_id not in work_related_groups:
                work_related_groups.append(g_id)
                
    # Shopping interest
    shopping_interest = False
    user_business_history = data_store.get('user_business_history', [])
    for ubh in user_business_history:
        if ubh.get('user_id') == user_id:
            msg_type = ubh.get('message_category', '').lower()
            if msg_type in ['sale', 'shopping', 'delivery']:
                shopping_interest = True
                break
                
    return {
        'user_id': user_id,
        'dnd_start': dnd_start,
        'dnd_end': dnd_end,
        'engagement_rate': round(engagement_rate, 2),
        'notification_fatigue': round(notification_fatigue, 2),
        'messages_reported_30d': messages_reported_30d,
        'favorite_contacts': favorite_contacts,
        'ignored_contacts': ignored_contacts,
        'active_groups': active_groups,
        'muted_groups': muted_groups,
        'shopping_interest': shopping_interest,
        'work_related_groups': work_related_groups
    }

def build_all_profiles(data_store):
    """Build profiles for all users in the dataset."""
    print("="*70)
    print("  STAGE 3: USER PROFILE BUILDING")
    print("="*70)
    
    users = data_store.get('users', [])
    profiles = {}
    
    for u in users:
        u_id = u.get('user_id')
        if u_id:
            profiles[u_id] = build_user_profile(u_id, data_store)
            
    print(f"  Built {len(profiles)} user profiles")
    print()
    return profiles
