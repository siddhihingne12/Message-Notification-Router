"""
Stage: Attention Budget
Tracks daily notification budget per user.
"""

import math

class AttentionBudgetManager:
    def __init__(self, data_store):
        self.budgets = {}
        self.overrides = 0
        self.downgrades = 0
        
        daily_summary = data_store.get('daily_notification_summary', [])
        
        # Group by user_id
        user_stats = {}
        for row in daily_summary:
            uid = row.get('user_id')
            if not uid:
                continue
            try:
                sent = int(row.get('notifications_sent', 0))
            except ValueError:
                sent = 0
                
            if uid not in user_stats:
                user_stats[uid] = []
            user_stats[uid].append(sent)
            
        # Compute budget_limit per user
        for uid, counts in user_stats.items():
            if not counts:
                limit = 10
            else:
                n = len(counts)
                avg = sum(counts) / n
                if n > 1:
                    variance = sum((x - avg) ** 2 for x in counts) / n
                    std_dev = math.sqrt(variance)
                else:
                    std_dev = 0
                limit = avg + 2 * std_dev
                
            # Clamp between 5 and 20
            limit = int(round(limit))
            limit = max(5, min(limit, 20))
            
            self.budgets[uid] = {'limit': limit, 'used': 0}
            
    def get_budget_info(self, user_id):
        """Return budget status for user."""
        budget = self.budgets.get(user_id, {'limit': 10, 'used': 0})
        return {
            'notifications_today': budget['used'],
            'budget_limit': budget['limit'],
            'budget_remaining': max(0, budget['limit'] - budget['used']),
            'budget_override': False
        }
        
    def apply_budget(self, user_id, action, urgency_score, sender_is_top_favorite, has_direct_mention_urgent):
        """Apply attention budget to a NOTIFY decision."""
        if action != 'notify':
            return action, self.get_budget_info(user_id)
            
        budget = self.budgets.get(user_id)
        if not budget:
            budget = {'limit': 10, 'used': 0}
            self.budgets[user_id] = budget
            
        budget_remaining = max(0, budget['limit'] - budget['used'])
        budget_info = self.get_budget_info(user_id)
        
        if budget_remaining > 0:
            budget['used'] += 1
            budget_info = self.get_budget_info(user_id)
            return 'notify', budget_info
            
        # budget_remaining == 0
        if (sender_is_top_favorite and urgency_score >= 0.8) or has_direct_mention_urgent:
            self.overrides += 1
            budget['used'] += 1
            budget_info = self.get_budget_info(user_id)
            budget_info['budget_override'] = True
            return 'notify', budget_info
        else:
            self.downgrades += 1
            return 'digest', budget_info
            
    def print_statistics(self):
        print(f"Attention Budget Stats: {self.overrides} overrides, {self.downgrades} downgrades")
