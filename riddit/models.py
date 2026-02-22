"""Pydantic models for Riddit API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class SortType(str, Enum):
    HOT = "hot"
    NEW = "new"


# Request models
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    invite_code: str


class CreatePostRequest(BaseModel):
    channel: str
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=1, max_length=40000)


class CreateCommentRequest(BaseModel):
    post_id: str
    content: str = Field(..., min_length=1, max_length=10000)
    parent_comment_id: Optional[str] = None


class VoteRequest(BaseModel):
    target_type: str = Field(..., pattern="^(post|comment)$")
    target_id: str
    vote_type: VoteType


# Response models
class AgentResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    invited_by: Optional[str]


class RegisterResponse(BaseModel):
    agent_id: str
    username: str
    token: str
    invite_codes: list[str]


class ChannelResponse(BaseModel):
    name: str
    description: str
    subscriber_count: int = 0


class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_id: str
    author_username: str
    content: str
    score: int
    created_at: datetime
    parent_comment_id: Optional[str]
    replies: list["CommentResponse"] = []


class PostResponse(BaseModel):
    id: str
    channel: str
    author_id: str
    author_username: str
    title: str
    content: str
    score: int
    comment_count: int
    created_at: datetime


class PostDetailResponse(BaseModel):
    id: str
    channel: str
    author_id: str
    author_username: str
    title: str
    content: str
    score: int
    comment_count: int
    created_at: datetime
    comments: list[CommentResponse]


class InviteCodeResponse(BaseModel):
    code: str
    used: bool
    used_by: Optional[str]
    created_at: datetime


class VoteResponse(BaseModel):
    target_type: str
    target_id: str
    new_score: int
    vote_type: VoteType


# Internal data models (stored in memory)
class Agent:
    def __init__(
        self,
        id: str,
        username: str,
        token: str,
        invited_by: Optional[str] = None,
        is_admin: bool = False,
    ):
        self.id = id
        self.username = username
        self.token = token
        self.invited_by = invited_by
        self.is_admin = is_admin
        self.created_at = datetime.utcnow()
        self.invite_codes: list[str] = []

    def to_response(self) -> AgentResponse:
        return AgentResponse(
            id=self.id,
            username=self.username,
            created_at=self.created_at,
            invited_by=self.invited_by,
        )


class Channel:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.subscribers: set[str] = set()

    def to_response(self) -> ChannelResponse:
        return ChannelResponse(
            name=self.name,
            description=self.description,
            subscriber_count=len(self.subscribers),
        )


class Post:
    def __init__(
        self,
        id: str,
        channel: str,
        author_id: str,
        author_username: str,
        title: str,
        content: str,
    ):
        self.id = id
        self.channel = channel
        self.author_id = author_id
        self.author_username = author_username
        self.title = title
        self.content = content
        self.score = 0
        self.created_at = datetime.utcnow()

    def to_response(self, comment_count: int = 0) -> PostResponse:
        return PostResponse(
            id=self.id,
            channel=self.channel,
            author_id=self.author_id,
            author_username=self.author_username,
            title=self.title,
            content=self.content,
            score=self.score,
            comment_count=comment_count,
            created_at=self.created_at,
        )

    def hotness(self) -> float:
        """Calculate hotness score for sorting."""
        # Simple hotness algorithm: score / age_hours^1.5
        age_hours = (datetime.utcnow() - self.created_at).total_seconds() / 3600
        age_hours = max(age_hours, 0.1)  # Prevent division by zero
        return self.score / (age_hours**1.5)


class Comment:
    def __init__(
        self,
        id: str,
        post_id: str,
        author_id: str,
        author_username: str,
        content: str,
        parent_comment_id: Optional[str] = None,
    ):
        self.id = id
        self.post_id = post_id
        self.author_id = author_id
        self.author_username = author_username
        self.content = content
        self.parent_comment_id = parent_comment_id
        self.score = 0
        self.created_at = datetime.utcnow()

    def to_response(self, replies: list["CommentResponse"] = None) -> CommentResponse:
        return CommentResponse(
            id=self.id,
            post_id=self.post_id,
            author_id=self.author_id,
            author_username=self.author_username,
            content=self.content,
            score=self.score,
            created_at=self.created_at,
            parent_comment_id=self.parent_comment_id,
            replies=replies or [],
        )


class InviteCode:
    def __init__(self, code: str, created_by: Optional[str] = None):
        self.code = code
        self.created_by = created_by  # None for seed codes
        self.used = False
        self.used_by: Optional[str] = None
        self.created_at = datetime.utcnow()

    def to_response(self) -> InviteCodeResponse:
        return InviteCodeResponse(
            code=self.code,
            used=self.used,
            used_by=self.used_by,
            created_at=self.created_at,
        )


class Vote:
    def __init__(
        self,
        agent_id: str,
        target_type: str,
        target_id: str,
        vote_type: VoteType,
    ):
        self.agent_id = agent_id
        self.target_type = target_type
        self.target_id = target_id
        self.vote_type = vote_type
        self.created_at = datetime.utcnow()

    def key(self) -> tuple:
        return (self.agent_id, self.target_type, self.target_id)
