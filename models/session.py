import json
import os
import uuid
import time
import asyncio

class Session:
    def __init__(self, user_id: str, session_id=None):

        if not self.session_exists(session_id):
            self.user_id = user_id
            self.session_id = session_id or str(uuid.uuid4())
            self.events = []
            self.context_state = {}
            self.path = f"./sessions/{session_id}.json"  # file-based storage
            self.current_dom_summary = None
            self.current_interaction_dom = None
        else:
            with open(f"./sessions/{session_id}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.user_id = data["user_id"]
                self.path = f"./sessions/{session_id}.json"
                self.session_id = data["session_id"]
                self.events = data["events"]
                self.context_state = data["context_state"]
                self.current_dom_summary = data.get("current_dom_summary")
                self.current_interaction_dom = data.get("current_interaction_dom")

    def add_event(self, event_type, agent, data):
        event = {
            "type": event_type,
            "agent": agent,
            "data": data,
            "timestamp": time.time(),
        }
        self.events.append(event)
        return event

    def get_recent_context(self, n=5):
        context = ""
        for ev in self.events[-n:]:
            context += f"[{ev['type']}] {ev['agent']}: {ev['data']}\n"
        return context

    def update_state(self, key, value):
        self.context_state[key] = value

    def get_state(self, key, default=None):
        return self.context_state.get(key, default)

    def update_current_dom_summary(self, current_dom_summary):
        self.current_dom_summary = current_dom_summary
    
    def update_current_interaction_dom(self, current_interaction_dom):
        self.current_interaction_dom = current_interaction_dom

    # ---- persistence methods ----
    def save(self):
        os.makedirs("./sessions", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "user_id": self.user_id,
                    "session_id": self.session_id,
                    "events": self.events,
                    "context_state": self.context_state,
                    "current_dom_summary": self.current_dom_summary,
                    "current_interaction_dom": self.current_interaction_dom,
                },
                f,
                indent=2,
            )

    @classmethod
    def session_exists(self,session_id):
        path = f"./sessions/{session_id}.json"
        return os.path.exists(path)

    @classmethod
    def load(cls, session_id):
        path = f"./sessions/{session_id}.json"
        if not os.path.exists(path):
            raise FileNotFoundError("No session found with that ID.")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        session = cls(user_id=data["user_id"], session_id=data["session_id"])
        session.events = data.get("events", [])
        session.context_state = data.get("context_state", {})
        return session