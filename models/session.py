import json
import os
import uuid
import time
import asyncio

class Session:
    def __init__(self, user_id: str, session_id=None):
        print(f"\n📂 SESSION INITIALIZATION")
        print(f"   User ID: {user_id}")
        print(f"   Session ID: {session_id}")

        if not self.session_exists(session_id):
            print("   📝 Creating new session...")
            self.user_id = user_id
            self.session_id = session_id or str(uuid.uuid4())
            self.events = []
            self.context_state = {}
            self.path = f"./sessions/{session_id}.json"  # file-based storage
            self.current_dom_summary = None
            self.current_interaction_dom = None
            print(f"   ✅ New session created: {self.session_id}")
        else:
            print("   📖 Loading existing session...")
            with open(f"./sessions/{session_id}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.user_id = data["user_id"]
                self.path = f"./sessions/{session_id}.json"
                self.session_id = data["session_id"]
                self.events = data["events"]
                self.context_state = data["context_state"]
                self.current_dom_summary = data.get("current_dom_summary")
                self.current_interaction_dom = data.get("current_interaction_dom")
            print(f"   ✅ Session loaded: {self.session_id} ({len(self.events)} events)")

    def add_event(self, event_type, agent, data):
        print(f"📝 ADDING EVENT")
        print(f"   Type: {event_type}")
        print(f"   Agent: {agent}")
        print(f"   Data Length: {len(str(data))} chars")
        
        event = {
            "type": event_type,
            "agent": agent,
            "data": data,
            "timestamp": time.time(),
        }
        self.events.append(event)
        print(f"   ✅ Event added (Total events: {len(self.events)})")
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
        print(f"🔄 UPDATING DOM SUMMARY")
        print(f"   Summary Length: {len(current_dom_summary)} chars")
        self.current_dom_summary = current_dom_summary
        print(f"   ✅ DOM summary updated")
    
    def update_current_interaction_dom(self, current_interaction_dom):
        print(f"🔄 UPDATING INTERACTION DOM")
        print(f"   Interaction DOM Type: {type(current_interaction_dom)}")
        if isinstance(current_interaction_dom, dict):
            print(f"   Keys: {list(current_interaction_dom.keys())}")
        self.current_interaction_dom = current_interaction_dom
        print(f"   ✅ Interaction DOM updated")

    # ---- persistence methods ----
    def save(self):
        print(f"💾 SAVING SESSION")
        print(f"   Session ID: {self.session_id}")
        print(f"   Events Count: {len(self.events)}")
        print(f"   Path: {self.path}")
        
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
        print(f"   ✅ Session saved successfully")

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