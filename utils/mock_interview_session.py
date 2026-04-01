import uuid
from datetime import datetime
from typing import Dict, List


class MockInterviewSessionManager:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "target_field": "",
            "max_rounds": 5,
            "rounds_done": 0,
            "started": False,
            "chat_history": [],
        }
        return session_id

    def get(self, session_id: str) -> dict:
        return self.sessions.get(session_id)

    def clear(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]

    def start_interview(self, session_id: str, target_field: str, max_rounds: int = 5):
        session = self.get(session_id)
        if not session:
            return
        session["target_field"] = (target_field or "General").strip()
        session["max_rounds"] = max(1, min(int(max_rounds or 5), 10))
        session["rounds_done"] = 0
        session["started"] = True
        session["chat_history"] = []

    def add_turn(self, session_id: str, user_text: str, interviewer_text: str):
        session = self.get(session_id)
        if not session:
            return
        session["chat_history"].append(
            {
                "userMessage": user_text,
                "botResponse": interviewer_text,
            }
        )

    def get_chat_history(self, session_id: str) -> List[dict]:
        session = self.get(session_id)
        if not session:
            return []
        return session.get("chat_history", [])


mock_interview_session_manager = MockInterviewSessionManager()
