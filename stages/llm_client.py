"""
LLM Client Module
Provides API integrations for Large Language Model (LLM) reasoning using standard urllib.request.
Supports Google Gemini API, OpenAI API, and local heuristic reasoning fallback.
"""
import json
import os
import urllib.request
import urllib.error

class LLMClient:
    """Client for querying LLMs (Gemini / OpenAI / Heuristic Fallback)."""
    def __init__(self):
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        self.provider = "none"

        if self.gemini_api_key:
            self.provider = "gemini"
        elif self.openai_api_key:
            self.provider = "openai"

    def is_api_available(self):
        """Returns True if a live LLM API key is configured."""
        return self.provider in ["gemini", "openai"]

    def build_prompt(self, context):
        """Constructs a structured reasoning prompt from a MessageContext object."""
        msg = context.get('message', {})
        features = context.get('feature_scores', {})
        profile = context.get('user_profile', {})
        sender = context.get('sender_info', {})
        group = context.get('group_info')
        budget = context.get('attention_budget', {})

        prompt = f"""You are an AI notification secretary for WhatsApp messages.
Analyze the following message and user context to decide whether to NOTIFY immediately, batch into a DIGEST, or MUTE.

=== MESSAGE DETAILS ===
- Message ID: {msg.get('id')}
- Text: "{msg.get('full_text') or msg.get('text')}"
- Conversation Type: {msg.get('conversation_type')}
- Forwarded Count: {msg.get('forwarded_count', 0)}
- Media: {msg.get('media_type', 'none')}

=== SENDER & COMMUNITY CONTEXT ===
- Sender ID: {sender.get('sender_id')}
- Is Favorite Contact: {sender.get('is_favorite')}
- Is Ignored Contact: {sender.get('is_ignored')}
- Trust Level: {sender.get('trust_level')}
- Group Info: {json.dumps(group) if group else "None"}

=== FEATURE SCORES (0.0 - 1.0) ===
- Urgency: {features.get('urgency', 0.5):.2f}
- Relationship: {features.get('relationship', 0.5):.2f}
- Safety: {features.get('safety', 0.9):.2f}
- Novelty: {features.get('novelty', 0.7):.2f}
- Importance: {features.get('importance', 0.5):.2f}
- Time Sensitivity: {features.get('time_sensitivity', 0.5):.2f}
- Personalization: {features.get('personalization', 0.5):.2f}

=== USER PROFILE & ATTENTION BUDGET ===
- User ID: {profile.get('user_id')}
- Notifications Today: {budget.get('notifications_today', 0)} / {budget.get('budget_limit', 10)}
- DND Active: {features.get('time_sensitivity', 0.5) < 0.3}

Respond strictly in valid JSON format:
{{
  "action": "notify" | "digest" | "mute",
  "message_type": "urgent" | "personal" | "event" | "business_update" | "promotion" | "greeting" | "forward" | "scam" | "spam",
  "confidence": float_between_0_and_1,
  "reasons": ["reason sentence 1", "reason sentence 2"]
}}
"""
        return prompt

    def query_gemini(self, prompt):
        """Queries Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                res_json = json.loads(res_body)
                text = res_json['candidates'][0]['content']['parts'][0]['text']
                return json.loads(text)
        except Exception as e:
            print(f"Gemini API query warning: {e}")
            return None

    def query_openai(self, prompt):
        """Queries OpenAI Chat Completion API."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}"
        }
        payload = {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode('utf-8')
                res_json = json.loads(res_body)
                text = res_json['choices'][0]['message']['content']
                return json.loads(text)
        except Exception as e:
            print(f"OpenAI API query warning: {e}")
            return None

    def query(self, context):
        """
        Executes LLM reasoning for a given message context.
        Returns parsed JSON dict if API available, else None (triggering local engine).
        """
        if not self.is_api_available():
            return None

        prompt = self.build_prompt(context)
        if self.provider == "gemini":
            return self.query_gemini(prompt)
        elif self.provider == "openai":
            return self.query_openai(prompt)
            
        return None
