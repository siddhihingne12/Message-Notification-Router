from collections import defaultdict
from datetime import datetime

def _parse_timestamp(ts_str):
    """Safely parse standard ISO/datetime strings into datetime object."""
    if not ts_str:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M'):
        try:
            return datetime.strptime(ts_str.strip(), fmt)
        except ValueError:
            pass
    return None

def build_user_profile(user_id, data_store):
    """Builds a comprehensive behavioral and engagement profile for a single user."""
    users = data_store.get('users', [])
    user_row = next((u for u in users if u.get('user_id') == user_id), None)
    users_stats = user_row if user_row else {}

    # DND Window
    dnd_start = 22
    dnd_end = 7
    if user_row:
        if 'dnd_start_time' in user_row and user_row['dnd_start_time']:
            try: dnd_start = int(user_row['dnd_start_time'].split(':')[0])
            except: pass
        if 'dnd_end_time' in user_row and user_row['dnd_end_time']:
            try: dnd_end = int(user_row['dnd_end_time'].split(':')[0])
            except: pass

    # 1. Engagement Rate Calculation
    replied = float(users_stats.get('messages_replied_30d', 0) or 0)
    opened = float(users_stats.get('messages_opened_30d', 0) or 0)
    engagement_rate = replied / opened if opened > 0 else 0.0

    messages_reported_30d = int(users_stats.get('messages_reported_30d', 0) or 0)

    # 2. Notification Fatigue Calculation
    daily_summary = data_store.get('daily_summary', [])
    fatigue_ratios = []
    for row in daily_summary:
        if row.get('user_id') == user_id:
            sent = float(row.get('notifications_sent', 0) or 0)
            dismissed = float(row.get('notifications_dismissed', 0) or 0)
            if sent > 0:
                fatigue_ratios.append(dismissed / sent)
    notification_fatigue = sum(fatigue_ratios) / len(fatigue_ratios) if fatigue_ratios else 0.0

    # 3. Contact Interaction & Sender Trust Score Calculations
    message_events = data_store.get('message_events', [])
    message_history = data_store.get('message_history', [])

    msg_history_map = {
        m['message_id']: {
            'sender': m.get('sender_user_id'),
            'timestamp': _parse_timestamp(m.get('created_at'))
        }
        for m in message_history if m.get('message_id') and m.get('sender_user_id')
    }

    replies_count = defaultdict(int)
    ignores_count = defaultdict(int)
    total_received_per_sender = defaultdict(int)
    reply_delays_mins = []

    for ev in message_events:
        if ev.get('user_id') == user_id:
            msg_id = ev.get('message_id')
            msg_meta = msg_history_map.get(msg_id)
            if msg_meta:
                sender = msg_meta['sender']
                msg_time = msg_meta['timestamp']
                event_time = _parse_timestamp(ev.get('event_timestamp'))

                if sender and sender != user_id:
                    total_received_per_sender[sender] += 1

                    is_reply = ev.get('message_replied') in ['1', 'True', True]
                    is_dismiss = ev.get('notification_dismissed') in ['1', 'True', True]
                    is_mute = ev.get('muted_after_message') in ['1', 'True', True]

                    if is_reply:
                        replies_count[sender] += 1
                        if msg_time and event_time and event_time > msg_time:
                            delay = (event_time - msg_time).total_seconds() / 60.0
                            if delay < 1440:  # within 24h
                                reply_delays_mins.append(delay)

                    if is_dismiss or is_mute:
                        ignores_count[sender] += 1

    favorite_contacts = [k for k, v in sorted(replies_count.items(), key=lambda item: item[1], reverse=True)[:5]]
    ignored_contacts = [k for k, v in ignores_count.items() if v >= 2]

    # Calculate exact Trust Score per sender (0.0 to 1.0)
    sender_trust_scores = {}
    for sender, total_msgs in total_received_per_sender.items():
        rep = replies_count[sender]
        ign = ignores_count[sender]
        raw_score = (rep * 1.0 - ign * 0.5) / max(1, total_msgs)
        # Normalize to 0.0 - 1.0 range
        norm_score = max(0.0, min(1.0, 0.5 + raw_score * 0.5))
        sender_trust_scores[sender] = round(norm_score, 2)

    avg_reply_delay_mins = round(sum(reply_delays_mins) / len(reply_delays_mins), 1) if reply_delays_mins else 15.0

    # 4. Group Activity & Role Calculations
    group_members = data_store.get('group_members', [])
    groups = data_store.get('groups', [])

    active_groups = []
    muted_groups = []
    group_activity_scores = {}

    for gm in group_members:
        if gm.get('user_id') == user_id:
            g_id = gm.get('group_id')
            is_muted = gm.get('group_muted_by_user') in ['1', 'True', True]
            if is_muted:
                muted_groups.append(g_id)

            replies_30d = int(gm.get('replies_sent_30d', 0) or 0)
            opened_30d = int(gm.get('messages_opened_30d', 0) or 1)
            group_act = round(replies_30d / max(1, opened_30d), 2)
            group_activity_scores[g_id] = group_act

            if replies_30d > 0:
                active_groups.append(g_id)

    work_related_groups = []
    group_map = {g['group_id']: g.get('group_type', '') for g in groups if g.get('group_id')}
    for g_id in active_groups + muted_groups:
        g_type = group_map.get(g_id, '').lower()
        if g_type in ['coworker', 'tech_community']:
            if g_id not in work_related_groups:
                work_related_groups.append(g_id)

    # 5. Shopping Interest Score Calculation
    shopping_interest = False
    shopping_activity_count = 0
    user_business_history = data_store.get('user_business_history', [])
    for ubh in user_business_history:
        if ubh.get('user_id') == user_id:
            msg_type = ubh.get('message_category', '').lower()
            allows_promos = ubh.get('allows_promotions') in ['1', 'True', True]
            if msg_type in ['sale', 'shopping', 'delivery']:
                shopping_interest = True
                shopping_activity_count += 1
            if allows_promos:
                shopping_activity_count += 1

    shopping_interest_score = min(1.0, round(shopping_activity_count / 4.0, 2))

    return {
        'user_id': user_id,
        'dnd_start': dnd_start,
        'dnd_end': dnd_end,
        'engagement_rate': round(engagement_rate, 2),
        'avg_reply_delay_mins': avg_reply_delay_mins,
        'notification_fatigue': round(notification_fatigue, 2),
        'messages_reported_30d': messages_reported_30d,
        'favorite_contacts': favorite_contacts,
        'ignored_contacts': ignored_contacts,
        'sender_trust_scores': sender_trust_scores,
        'active_groups': active_groups,
        'muted_groups': muted_groups,
        'group_activity_scores': group_activity_scores,
        'shopping_interest': shopping_interest,
        'shopping_interest_score': shopping_interest_score,
        'work_related_groups': work_related_groups
    }

def build_all_profiles(data_store):
    """Build profiles for all users in the dataset."""
    print("=" * 70)
    print("  STAGE 3: USER PROFILE BUILDING & ENGAGEMENT CALCULATIONS")
    print("=" * 70)

    users = data_store.get('users', [])
    profiles = {}

    for u in users:
        u_id = u.get('user_id')
        if u_id:
            profiles[u_id] = build_user_profile(u_id, data_store)

    print(f"  Built {len(profiles)} user behavioral & engagement profiles")
    print()
    return profiles
