"""
Session management for multi-turn conversational orchestration
Tracks user context, conversation history, and preferences across requests
"""
from __future__ import annotations

import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class SessionContext:
    """Individual user session state"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    # Conversation state
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    last_query: Optional[str] = None
    last_intent: Optional[Dict[str, Any]] = None
    last_results: Optional[List[Dict]] = None
    
    # User preferences and context
    preferences: Dict[str, Any] = field(default_factory=dict)
    cart_items: List[Dict[str, Any]] = field(default_factory=list)
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def add_exchange(self, user_input: str, intent: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Add a conversation exchange to history"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "intent": intent,
            "response": response
        })
        # Keep last 10 exchanges to prevent unbounded growth
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        self.last_query = user_input
        self.last_intent = intent
        if response.get("event") == "search_results":
            self.last_results = response.get("data", {}).get("results", [])


class SessionManager:
    """Manages user sessions with automatic cleanup"""
    
    def __init__(self, session_timeout_minutes: int = 30):
        self._sessions: Dict[str, SessionContext] = {}
        self._timeout_minutes = session_timeout_minutes
    
    def create_session(self) -> str:
        """Create a new session and return session_id"""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = SessionContext(session_id=session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get session by ID, return None if expired or not found"""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        
        if session.is_expired(self._timeout_minutes):
            # Clean up expired session
            del self._sessions[session_id]
            return None
        
        session.update_activity()
        return session
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Get existing session or create new one"""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        
        # Create new session
        new_id = self.create_session()
        return self._sessions[new_id]
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions, return count of removed sessions"""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired(self._timeout_minutes)
        ]
        
        for sid in expired_ids:
            del self._sessions[sid]
        
        return len(expired_ids)
    
    def get_session_count(self) -> int:
        """Get current active session count"""
        return len(self._sessions)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session manager stats for health checks"""
        active_count = len(self._sessions)
        oldest_session = None
        if self._sessions:
            oldest = min(self._sessions.values(), key=lambda s: s.created_at)
            oldest_session = oldest.created_at.isoformat()
        
        return {
            "active_sessions": active_count,
            "oldest_session": oldest_session,
            "timeout_minutes": self._timeout_minutes
        }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get global session manager singleton"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager