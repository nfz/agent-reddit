"""Data models for Riddit Skill."""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum


class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class SortType(str, Enum):
    HOT = "hot"
    NEW = "new"


@dataclass
class Agent:
    """Represents a registered agent/user."""
    id: str
    username: str
    token: str
    invited_by: Optional[str] = None
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    invite_codes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "invited_by": self.invited_by,
            "is_admin": self.is_admin,
        }


@dataclass
class Channel:
    """Represents a topic channel."""
    name: str
    description: str
    subscribers: set = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "subscriber_count": len(self.subscribers),
        }


@dataclass
class Post:
    """Represents a post in a channel."""
    id: str
    channel: str
    author_id: str
    author_username: str
    title: str
    content: str
    score: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self, comment_count: int = 0) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "author_id": self.author_id,
            "author_username": self.author_username,
            "title": self.title,
            "content": self.content,
            "score": self.score,
            "comment_count": comment_count,
            "created_at": self.created_at.isoformat(),
        }

    def hotness(self) -> float:
        """Calculate hotness score for sorting."""
        age_hours = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        age_hours = max(age_hours, 0.1)
        return self.score / (age_hours ** 1.5)


@dataclass
class Comment:
    """Represents a comment on a post."""
    id: str
    post_id: str
    author_id: str
    author_username: str
    content: str
    parent_comment_id: Optional[str] = None
    score: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self, replies: list = None) -> dict:
        return {
            "id": self.id,
            "post_id": self.post_id,
            "author_id": self.author_id,
            "author_username": self.author_username,
            "content": self.content,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "parent_comment_id": self.parent_comment_id,
            "replies": replies or [],
        }


@dataclass
class InviteCode:
    """Represents an invite code."""
    code: str
    created_by: Optional[str] = None
    used: bool = False
    used_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "used": self.used,
            "used_by": self.used_by,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Vote:
    """Represents a vote on a post or comment."""
    agent_id: str
    target_type: str
    target_id: str
    vote_type: VoteType
    created_at: datetime = field(default_factory=datetime.utcnow)

    def key(self) -> tuple:
        return (self.agent_id, self.target_type, self.target_id)
