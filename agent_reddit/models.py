from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Post:
    id: int
    channel: str
    author: str
    title: str
    content: str
    tick_created: int
    score: int = 0
    comments: list[int] = field(default_factory=list)


@dataclass
class Comment:
    id: int
    post_id: int
    author: str
    content: str
    tick_created: int
    parent_comment_id: Optional[int] = None
    score: int = 0


@dataclass
class FeedEvent:
    tick: int
    actor: str
    action: str
    detail: str
