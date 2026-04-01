"""
Session manager for voice chat
Maintains chat history per session
"""

from typing import Dict, List
import uuid
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages chat sessions and their histories
    """
    
    def __init__(self, session_timeout_minutes=30):
        """
        Initialize session manager
        
        Args:
            session_timeout_minutes: Session timeout in minutes
        """
        self.sessions: Dict[str, dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
    
    def create_session(self) -> str:
        """
        Create a new session
        
        Returns:
            str: Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "chat_history": [],
            "known_jobs": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> dict:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            dict: Session data or None if not found
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session expired
        if datetime.now() - session["last_activity"] > self.session_timeout:
            logger.info(f"Session expired: {session_id}")
            del self.sessions[session_id]
            return None
        
        # Update last activity
        session["last_activity"] = datetime.now()
        return session
    
    def add_message(self, session_id: str, user_message: str, bot_response: str):
        """
        Add a message to session chat history
        
        Args:
            session_id: Session ID
            user_message: User's message
            bot_response: Bot's response
        """
        session = self.get_session(session_id)
        if session:
            session["chat_history"].append({
                "userMessage": user_message,
                "botResponse": bot_response
            })
            logger.info(f"Added message to session {session_id}")
    
    def get_chat_history(self, session_id: str) -> List[dict]:
        """
        Get chat history for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            list: Chat history
        """
        session = self.get_session(session_id)
        if session:
            return session["chat_history"]
        return []
    
    def clear_session(self, session_id: str):
        """
        Clear a session
        
        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Cleared session: {session_id}")

    def set_known_jobs(self, session_id: str, jobs: List[dict]):
        """
        Save latest known jobs for apply actions.

        Args:
            session_id: Session ID
            jobs: List of job cards
        """
        session = self.get_session(session_id)
        if session is not None:
            session["known_jobs"] = jobs or []

    def get_known_jobs(self, session_id: str) -> List[dict]:
        """
        Get latest known jobs for a session.

        Args:
            session_id: Session ID

        Returns:
            list: Known jobs
        """
        session = self.get_session(session_id)
        if session is not None:
            return session.get("known_jobs", [])
        return []
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if now - session["last_activity"] > self.session_timeout
        ]
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")


# Global session manager instance
session_manager = SessionManager(session_timeout_minutes=30)
