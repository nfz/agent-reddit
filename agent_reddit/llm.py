from __future__ import annotations

import json
import os
import random
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - import failure is handled gracefully
    OpenAI = None  # type: ignore[assignment]


class DecisionEngine:
    def __init__(self, seed: int = 7) -> None:
        self.rng = random.Random(seed)
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = None

        if self.api_key and OpenAI is not None:
            self.client = OpenAI(api_key=self.api_key)

    def decide(self, agent_name: str, personality: str, interests: list[str], context: dict[str, Any]) -> dict[str, Any]:
        if self.client is None:
            return self._fallback_decision(agent_name, personality, interests, context)

        try:
            return self._openai_decision(agent_name, personality, interests, context)
        except Exception:
            return self._fallback_decision(agent_name, personality, interests, context)

    def _openai_decision(
        self,
        agent_name: str,
        personality: str,
        interests: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        system_prompt = (
            "You are simulating one Reddit-like AI agent action. "
            "Return JSON only with fields: action, channel, title, content, post_id, comment_id, target_type, target_id, vote. "
            "Allowed actions: post, comment, vote, idle. "
            "For vote use vote=1 or vote=-1 and target_type in ['post','comment']. "
            "Keep title under 80 chars and content under 220 chars."
        )

        payload = {
            "agent": {
                "name": agent_name,
                "personality": personality,
                "interests": interests,
            },
            "context": context,
        }

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)
        if not isinstance(parsed, dict):
            return self._fallback_decision(agent_name, personality, interests, context)
        return parsed

    def _fallback_decision(
        self,
        agent_name: str,
        personality: str,
        interests: list[str],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        visible_posts = context.get("visible_posts", [])
        channels = context.get("channels") or interests or ["general"]

        energy = 0.65
        personality_l = personality.lower()
        if "analytical" in personality_l or "reserved" in personality_l:
            energy = 0.45
        if "hyper" in personality_l or "chaotic" in personality_l:
            energy = 0.85

        roll = self.rng.random()
        if not visible_posts or roll < energy * 0.45:
            channel = self.rng.choice(channels)
            topic = self.rng.choice(interests or [channel])
            stance = self.rng.choice(
                [
                    "hot take",
                    "quick guide",
                    "beginner question",
                    "weekly thread",
                    "thought experiment",
                ]
            )
            return {
                "action": "post",
                "channel": channel,
                "title": f"{topic.title()} {stance}",
                "content": f"{agent_name} shares a {stance} about {topic}.",
            }

        if roll < energy * 0.8 and visible_posts:
            post = self.rng.choice(visible_posts)
            voice = self.rng.choice(
                [
                    "I agree with this and would add...",
                    "Counterpoint: maybe consider the tradeoff.",
                    "Can you expand on the implementation details?",
                    "This reminds me of a related trend.",
                ]
            )
            return {
                "action": "comment",
                "post_id": post.get("id"),
                "content": voice,
            }

        if visible_posts:
            post = self.rng.choice(visible_posts)
            vote = 1 if self.rng.random() > 0.25 else -1
            return {
                "action": "vote",
                "target_type": "post",
                "target_id": post.get("id"),
                "vote": vote,
            }

        return {"action": "idle"}
