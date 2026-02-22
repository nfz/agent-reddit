from __future__ import annotations

from typing import Iterable

from .models import Comment, FeedEvent, Post


class Environment:
    def __init__(self, channels: Iterable[str]) -> None:
        unique_channels = sorted({channel.strip() for channel in channels if channel.strip()})
        if not unique_channels:
            raise ValueError("Environment requires at least one channel")

        self.channels = unique_channels
        self.posts: dict[int, Post] = {}
        self.comments: dict[int, Comment] = {}
        self.feed: list[FeedEvent] = []

        self._next_post_id = 1
        self._next_comment_id = 1
        self._post_votes: dict[int, dict[str, int]] = {}
        self._comment_votes: dict[int, dict[str, int]] = {}

    def create_post(self, author: str, channel: str, title: str, content: str, tick: int) -> Post:
        channel = channel.strip().lower()
        if channel not in self.channels:
            channel = self.channels[0]

        post = Post(
            id=self._next_post_id,
            channel=channel,
            author=author,
            title=title.strip()[:120] or "Untitled",
            content=content.strip()[:1000] or "",
            tick_created=tick,
        )
        self._next_post_id += 1
        self.posts[post.id] = post
        self.feed.append(
            FeedEvent(
                tick=tick,
                actor=author,
                action="post",
                detail=f"posted in r/{post.channel}: \"{post.title}\" (post#{post.id})",
            )
        )
        return post

    def add_comment(
        self,
        author: str,
        post_id: int,
        content: str,
        tick: int,
        parent_comment_id: int | None = None,
    ) -> Comment | None:
        post = self.posts.get(post_id)
        if post is None:
            return None

        if parent_comment_id is not None and parent_comment_id not in self.comments:
            parent_comment_id = None

        comment = Comment(
            id=self._next_comment_id,
            post_id=post_id,
            author=author,
            content=content.strip()[:1000] or "Interesting point.",
            tick_created=tick,
            parent_comment_id=parent_comment_id,
        )
        self._next_comment_id += 1
        self.comments[comment.id] = comment
        post.comments.append(comment.id)
        self.feed.append(
            FeedEvent(
                tick=tick,
                actor=author,
                action="comment",
                detail=f"commented on post#{post_id}: \"{comment.content[:80]}\" (comment#{comment.id})",
            )
        )
        return comment

    def cast_vote(
        self,
        voter: str,
        target_type: str,
        target_id: int,
        value: int,
        tick: int,
    ) -> bool:
        if value not in (-1, 1):
            return False

        if target_type == "post":
            target = self.posts.get(target_id)
            if target is None:
                return False
            vote_map = self._post_votes.setdefault(target_id, {})
        elif target_type == "comment":
            target = self.comments.get(target_id)
            if target is None:
                return False
            vote_map = self._comment_votes.setdefault(target_id, {})
        else:
            return False

        previous_vote = vote_map.get(voter, 0)
        if previous_vote == value:
            return False

        target.score += value - previous_vote
        vote_map[voter] = value

        verb = "upvoted" if value > 0 else "downvoted"
        self.feed.append(
            FeedEvent(
                tick=tick,
                actor=voter,
                action="vote",
                detail=f"{verb} {target_type}#{target_id} (score now {target.score:+d})",
            )
        )
        return True

    def list_posts(self, channel: str | None = None, limit: int = 20) -> list[Post]:
        posts = self.posts.values()
        if channel:
            posts = [post for post in posts if post.channel == channel]
        ranked = sorted(posts, key=lambda p: (p.score, p.tick_created), reverse=True)
        return ranked[:limit]

    def list_recent_events(self, limit: int = 30) -> list[FeedEvent]:
        return self.feed[-limit:]

    def serialize_post_brief(self, post: Post) -> dict[str, str | int]:
        return {
            "id": post.id,
            "channel": post.channel,
            "author": post.author,
            "title": post.title,
            "score": post.score,
            "comment_count": len(post.comments),
            "tick_created": post.tick_created,
        }
