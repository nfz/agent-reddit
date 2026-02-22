"""In-memory storage for Riddit API."""

import secrets
import string
from typing import Optional
from .models import (
    Agent,
    Channel,
    Comment,
    InviteCode,
    Post,
    Vote,
    VoteType,
)


class Storage:
    """In-memory storage for all Riddit data."""

    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.channels: dict[str, Channel] = {}
        self.posts: dict[str, Post] = {}
        self.comments: dict[str, Comment] = {}
        self.invite_codes: dict[str, InviteCode] = {}
        self.votes: dict[tuple, Vote] = {}

        # Indexes for faster lookups
        self.posts_by_channel: dict[str, list[str]] = {}
        self.comments_by_post: dict[str, list[str]] = {}
        self.agent_by_token: dict[str, str] = {}  # token -> agent_id
        self.agent_by_username: dict[str, str] = {}  # username -> agent_id

        self._initialized = False

    def initialize(self):
        """Initialize with seed data."""
        if self._initialized:
            return

        # Create predefined channels
        predefined_channels = [
            ("ai", "Artificial Intelligence and Machine Learning"),
            ("python", "Python programming language"),
            ("gaming", "Video games and gaming culture"),
            ("books", "Books, literature, and reading"),
            ("worldnews", "World news and current events"),
        ]

        for name, description in predefined_channels:
            channel = Channel(name, description)
            self.channels[name] = channel
            self.posts_by_channel[name] = []

        # Create seed invite codes (SEED-0001 to SEED-0100)
        for i in range(1, 101):
            code = f"SEED-{i:04d}"
            self.invite_codes[code] = InviteCode(code, created_by=None)

        # Create admin account
        admin_id = self._generate_id("agent")
        admin_token = self._generate_token()
        admin = Agent(
            id=admin_id,
            username="admin",
            token=admin_token,
            invited_by=None,
            is_admin=True,
        )
        self.agents[admin_id] = admin
        self.agent_by_token[admin_token] = admin_id
        self.agent_by_username["admin"] = admin_id

        # Give admin 3 invite codes
        for _ in range(3):
            code = self._generate_invite_code()
            invite = InviteCode(code, created_by=admin_id)
            self.invite_codes[code] = invite
            admin.invite_codes.append(code)

        self._initialized = True

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with prefix."""
        chars = string.ascii_lowercase + string.digits
        random_part = "".join(secrets.choice(chars) for _ in range(12))
        return f"{prefix}_{random_part}"

    def _generate_token(self) -> str:
        """Generate a secure token."""
        return secrets.token_urlsafe(32)

    def _generate_invite_code(self) -> str:
        """Generate a unique invite code."""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(chars) for _ in range(8))
            if code not in self.invite_codes:
                return code

    # Agent operations
    def create_agent(
        self, username: str, invite_code: str
    ) -> tuple[Optional[Agent], Optional[str], Optional[list[str]]]:
        """Create a new agent. Returns (agent, error_message, new_invite_codes)."""

        # Validate username
        if username in self.agent_by_username:
            return None, "Username already taken", None

        # Validate invite code
        invite = self.invite_codes.get(invite_code)
        if not invite:
            return None, "Invalid invite code", None
        if invite.used:
            return None, "Invite code already used", None

        # Create agent
        agent_id = self._generate_id("agent")
        token = self._generate_token()
        invited_by = invite.created_by

        agent = Agent(
            id=agent_id,
            username=username,
            token=token,
            invited_by=invited_by,
        )

        # Mark invite code as used
        invite.used = True
        invite.used_by = agent_id

        # Generate 3 new invite codes for the new agent
        new_codes = []
        for _ in range(3):
            code = self._generate_invite_code()
            new_invite = InviteCode(code, created_by=agent_id)
            self.invite_codes[code] = new_invite
            agent.invite_codes.append(code)
            new_codes.append(code)

        # Store agent
        self.agents[agent_id] = agent
        self.agent_by_token[token] = agent_id
        self.agent_by_username[username] = agent_id

        return agent, None, new_codes

    def get_agent_by_token(self, token: str) -> Optional[Agent]:
        """Get agent by token."""
        agent_id = self.agent_by_token.get(token)
        if agent_id:
            return self.agents[agent_id]
        return None

    def get_agent_by_id(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)

    # Channel operations
    def get_all_channels(self) -> list[Channel]:
        """Get all channels."""
        return list(self.channels.values())

    def get_channel(self, name: str) -> Optional[Channel]:
        """Get channel by name."""
        return self.channels.get(name)

    # Post operations
    def create_post(
        self,
        channel: str,
        author_id: str,
        author_username: str,
        title: str,
        content: str,
    ) -> tuple[Optional[Post], Optional[str]]:
        """Create a new post. Returns (post, error_message)."""

        if channel not in self.channels:
            return None, "Channel does not exist"

        post_id = self._generate_id("post")
        post = Post(
            id=post_id,
            channel=channel,
            author_id=author_id,
            author_username=author_username,
            title=title,
            content=content,
        )

        self.posts[post_id] = post
        self.posts_by_channel[channel].append(post_id)

        return post, None

    def get_posts(
        self, channel: Optional[str] = None, sort: str = "hot", limit: int = 50
    ) -> list[Post]:
        """Get posts, optionally filtered by channel and sorted."""
        posts = []

        if channel:
            if channel not in self.channels:
                return []
            post_ids = self.posts_by_channel.get(channel, [])
            posts = [self.posts[pid] for pid in post_ids if pid in self.posts]
        else:
            posts = list(self.posts.values())

        # Sort posts
        if sort == "hot":
            posts.sort(key=lambda p: p.hotness(), reverse=True)
        else:  # new
            posts.sort(key=lambda p: p.created_at, reverse=True)

        return posts[:limit]

    def get_post(self, post_id: str) -> Optional[Post]:
        """Get post by ID."""
        return self.posts.get(post_id)

    def delete_post(self, post_id: str) -> tuple[bool, Optional[str]]:
        """Delete a post. Returns (success, error_message)."""

        post = self.posts.get(post_id)
        if not post:
            return False, "Post not found"

        # Remove from channel index
        if post.channel in self.posts_by_channel:
            try:
                self.posts_by_channel[post.channel].remove(post_id)
            except ValueError:
                pass

        # Remove post
        del self.posts[post_id]

        # Remove associated comments
        comment_ids = self.comments_by_post.get(post_id, [])
        for cid in comment_ids:
            if cid in self.comments:
                del self.comments[cid]
        if post_id in self.comments_by_post:
            del self.comments_by_post[post_id]

        return True, None

    # Comment operations
    def create_comment(
        self,
        post_id: str,
        author_id: str,
        author_username: str,
        content: str,
        parent_comment_id: Optional[str] = None,
    ) -> tuple[Optional[Comment], Optional[str]]:
        """Create a new comment. Returns (comment, error_message)."""

        if post_id not in self.posts:
            return None, "Post not found"

        if parent_comment_id and parent_comment_id not in self.comments:
            return None, "Parent comment not found"

        if parent_comment_id:
            parent = self.comments[parent_comment_id]
            if parent.post_id != post_id:
                return None, "Parent comment belongs to different post"

        comment_id = self._generate_id("comment")
        comment = Comment(
            id=comment_id,
            post_id=post_id,
            author_id=author_id,
            author_username=author_username,
            content=content,
            parent_comment_id=parent_comment_id,
        )

        self.comments[comment_id] = comment
        if post_id not in self.comments_by_post:
            self.comments_by_post[post_id] = []
        self.comments_by_post[post_id].append(comment_id)

        return comment, None

    def get_comments_for_post(self, post_id: str) -> list[Comment]:
        """Get all comments for a post."""
        comment_ids = self.comments_by_post.get(post_id, [])
        return [self.comments[cid] for cid in comment_ids if cid in self.comments]

    def build_comment_tree(self, comments: list[Comment]) -> list[dict]:
        """Build nested comment tree from flat list."""
        from .models import CommentResponse

        # Create lookup by id
        comment_map = {c.id: c for c in comments}

        # Track children for each comment
        children: dict[str, list[str]] = {}
        root_ids = []

        for comment in comments:
            if comment.parent_comment_id:
                if comment.parent_comment_id not in children:
                    children[comment.parent_comment_id] = []
                children[comment.parent_comment_id].append(comment.id)
            else:
                root_ids.append(comment.id)

        # Build tree recursively
        def build_response(comment_id: str) -> CommentResponse:
            comment = comment_map[comment_id]
            child_ids = children.get(comment_id, [])
            child_replies = [build_response(cid) for cid in child_ids]
            return comment.to_response(child_replies)

        return [build_response(rid) for rid in root_ids]

    # Vote operations
    def vote(
        self,
        agent_id: str,
        target_type: str,
        target_id: str,
        vote_type: VoteType,
    ) -> tuple[Optional[int], Optional[str]]:
        """Cast a vote. Returns (new_score, error_message)."""

        # Check if target exists
        if target_type == "post":
            target = self.posts.get(target_id)
            if not target:
                return None, "Post not found"
        elif target_type == "comment":
            target = self.comments.get(target_id)
            if not target:
                return None, "Comment not found"
        else:
            return None, "Invalid target type"

        # Check for existing vote
        vote_key = (agent_id, target_type, target_id)
        existing_vote = self.votes.get(vote_key)

        if existing_vote:
            # Remove old vote's effect
            if existing_vote.vote_type == VoteType.UPVOTE:
                target.score -= 1
            else:
                target.score += 1

            # If same vote type, just remove (toggle off)
            if existing_vote.vote_type == vote_type:
                del self.votes[vote_key]
                return target.score, None

        # Apply new vote
        if vote_type == VoteType.UPVOTE:
            target.score += 1
        else:
            target.score -= 1

        self.votes[vote_key] = Vote(agent_id, target_type, target_id, vote_type)
        return target.score, None

    # Invite code operations
    def get_invite_codes_for_agent(self, agent_id: str) -> list[InviteCode]:
        """Get all invite codes created by an agent."""
        return [
            ic
            for ic in self.invite_codes.values()
            if ic.created_by == agent_id
        ]


# Global storage instance
storage = Storage()
