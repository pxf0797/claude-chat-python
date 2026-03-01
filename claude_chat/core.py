"""
Core data models for Claude chat conversations.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Message:
    """Single message in a conversation."""
    message_id: str
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime
    model: Optional[str] = None
    thinking: Optional[str] = None  # Assistant's thinking process

    def __str__(self) -> str:
        """Human-readable representation of the message."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        role_icon = "👤" if self.role == "user" else "🤖"
        return f"{role_icon} [{time_str}] {self.content[:100]}..."


@dataclass
class Conversation:
    """Complete conversation session."""
    session_id: str
    display_title: str
    project_path: str
    start_time: datetime
    end_time: datetime
    messages: List[Message]
    total_tokens: Optional[int] = None

    @property
    def duration_seconds(self) -> float:
        """Conversation duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()

    @property
    def duration_minutes(self) -> float:
        """Conversation duration in minutes."""
        return self.duration_seconds / 60

    @property
    def user_messages(self) -> List[Message]:
        """Get all user messages."""
        return [msg for msg in self.messages if msg.role == "user"]

    @property
    def assistant_messages(self) -> List[Message]:
        """Get all assistant messages."""
        return [msg for msg in self.messages if msg.role == "assistant"]

    def __str__(self) -> str:
        """Human-readable representation of the conversation."""
        date_str = self.start_time.strftime("%Y-%m-%d %H:%M")
        return f"💬 {self.display_title} ({date_str}, {len(self.messages)} messages)"

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "display_title": self.display_title,
            "project_path": self.project_path,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "message_count": len(self.messages),
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.total_tokens
        }