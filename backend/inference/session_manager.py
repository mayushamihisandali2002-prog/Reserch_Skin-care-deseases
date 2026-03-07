"""
Session State Management
Stores conversation context per user session
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime
import uuid

@dataclass
class SessionState:
    """Stores conversation state for a single session"""
    session_id: str
    last_predicted_disease: Optional[str] = None
    last_confidence: float = 0.0
    pending_followup: bool = False
    followup_answers: Dict[str, str] = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)
    last_accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """Add message to history and update activity"""
        self.update_activity()
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
    
    def update_activity(self):
        """Update last accessed timestamp"""
        self.last_accessed_at = datetime.now().isoformat()
    
    def is_active(self) -> bool:
        """Check if session is still active (within 30 min of last activity)"""
        last_acc = datetime.fromisoformat(self.last_accessed_at)
        elapsed = (datetime.now() - last_acc).total_seconds()
        return elapsed < 3600  # Extended to 60 minutes of inactivity


class SessionManager:
    """Manages multiple user sessions"""
    
    def __init__(self, max_sessions: int = 1000):
        self.sessions: Dict[str, SessionState] = {}
        self.max_sessions = max_sessions
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create new session and return session_id"""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Clean up old sessions if needed
        if len(self.sessions) > self.max_sessions:
            self._cleanup_inactive()
        
        self.sessions[session_id] = SessionState(session_id=session_id)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get session by ID"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            if session.is_active():
                return session
            else:
                # Clean up expired session
                del self.sessions[session_id]
        return None
    
    def update_session(self, session_id: str, **kwargs):
        """Update session attributes"""
        session = self.get_session(session_id)
        if session:
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
    
    def _cleanup_inactive(self):
        """Remove inactive sessions"""
        active = {sid: s for sid, s in self.sessions.items() if s.is_active()}
        self.sessions = active
    
    def clear_session(self, session_id: str):
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]


# Global singleton
_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get global session manager"""
    return _session_manager
