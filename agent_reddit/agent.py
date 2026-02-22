from __future__ import annotations

from collections import Counter
from typing import Any

from .environment import Environment
from .llm import DecisionEngine


class Agent:
    def __init__(self, name: str, personality: str, interests: list[str], memory_size: int = 40) -> None:
        self.name = name
        self.personality = personality
        self.interests = [topic.strip().lower() for topic in interests if topic.strip()]
        self.memory_size = memory_size
        self.memory: list[str] = []
        self.stats = Counter()

    def observe(self, note: str) -> None:
        self.memory.append(note)
        if len(self.memory) > self.memory_size:
            self.memory = self.memory[-self.memory_size :]

    def decide_and_act(self, env: Environment, tick: int, engine: DecisionEngine) -> None:
        context = self._build_context(env)
        decision = engine.decide(self.name, self.personality, self.interests, context)
        action = str(decision.get("action", "idle")).lower()

        if action == "post":
            channel = self._pick_channel(decision, env)
            title = str(decision.get("title", "Untitled post"))
            content = str(decision.get("content", ""))
            post = env.create_post(self.name, channel, title, content, tick)
            self.observe(f"Tick {tick}: posted post#{post.id} in r/{post.channel}")
            self.stats["post"] += 1
            return

        if action == "comment":
            post_id = self._coerce_int(decision.get("post_id"))
            if post_id is None:
                fallback_posts = env.list_posts(limit=20)
                if fallback_posts:
                    post_id = fallback_posts[0].id
            if post_id is None:
                self.stats["idle"] += 1
                return
            content = str(decision.get("content", "Interesting point."))
            comment = env.add_comment(self.name, post_id, content, tick)
            if comment is not None:
                self.observe(f"Tick {tick}: commented on post#{post_id}")
                self.stats["comment"] += 1
            else:
                self.stats["idle"] += 1
            return

        if action == "vote":
            target_type = str(decision.get("target_type", "post")).lower()
            if target_type not in {"post", "comment"}:
                target_type = "post"
            target_id = self._coerce_int(decision.get("target_id"))
            if target_id is None and target_type == "post":
                target_id = self._coerce_int(decision.get("post_id"))
            if target_id is None:
                posts = env.list_posts(limit=20)
                if posts:
                    target_id = posts[0].id
                    target_type = "post"
            vote = self._coerce_int(decision.get("vote"))
            vote = 1 if vote is None or vote >= 0 else -1

            if target_id is not None and env.cast_vote(self.name, target_type, target_id, vote, tick):
                direction = "up" if vote > 0 else "down"
                self.observe(f"Tick {tick}: {direction}voted {target_type}#{target_id}")
                self.stats["vote"] += 1
            else:
                self.stats["idle"] += 1
            return

        self.stats["idle"] += 1

    def _build_context(self, env: Environment) -> dict[str, Any]:
        visible_posts = []
        ranked_posts = env.list_posts(limit=20)
        if self.interests:
            for post in ranked_posts:
                if post.channel in self.interests:
                    visible_posts.append(env.serialize_post_brief(post))
            if not visible_posts:
                visible_posts = [env.serialize_post_brief(post) for post in ranked_posts[:5]]
        else:
            visible_posts = [env.serialize_post_brief(post) for post in ranked_posts[:5]]

        return {
            "channels": env.channels,
            "visible_posts": visible_posts,
            "recent_feed": [event.detail for event in env.list_recent_events(limit=8)],
            "memory": self.memory[-8:],
        }

    def _pick_channel(self, decision: dict[str, Any], env: Environment) -> str:
        raw_channel = str(decision.get("channel", "")).strip().lower()
        if raw_channel in env.channels:
            return raw_channel
        for interest in self.interests:
            if interest in env.channels:
                return interest
        return env.channels[0]

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        try:
            if value is None:
                return None
            return int(value)
        except (TypeError, ValueError):
            return None
