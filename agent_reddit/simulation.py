from __future__ import annotations

import random

from .agent import Agent
from .environment import Environment
from .llm import DecisionEngine


class Simulation:
    def __init__(
        self,
        environment: Environment,
        agents: list[Agent],
        decision_engine: DecisionEngine,
        ticks: int,
        seed: int = 42,
    ) -> None:
        self.environment = environment
        self.agents = agents
        self.decision_engine = decision_engine
        self.ticks = ticks
        self.rng = random.Random(seed)

    def run(self) -> None:
        for tick in range(1, self.ticks + 1):
            start_index = len(self.environment.feed)
            self.rng.shuffle(self.agents)
            for agent in self.agents:
                agent.decide_and_act(self.environment, tick, self.decision_engine)

            print(f"\n=== Tick {tick} ===")
            new_events = self.environment.feed[start_index:]
            if not new_events:
                print("  (no activity)")
                continue
            for event in new_events:
                print(f"  [{event.actor}] {event.detail}")

    def print_summary(self) -> None:
        print("\n=== Summary ===")
        print(f"Total posts: {len(self.environment.posts)}")
        print(f"Total comments: {len(self.environment.comments)}")
        print(f"Total feed events: {len(self.environment.feed)}")

        print("\nTop posts:")
        top_posts = self.environment.list_posts(limit=10)
        if not top_posts:
            print("  (none)")
        for post in top_posts:
            print(
                f"  post#{post.id} [{post.score:+d}] r/{post.channel} | {post.title} "
                f"by {post.author} ({len(post.comments)} comments)"
            )

        print("\nAgent activity:")
        for agent in sorted(self.agents, key=lambda a: a.name.lower()):
            print(
                f"  {agent.name}: posts={agent.stats['post']}, "
                f"comments={agent.stats['comment']}, votes={agent.stats['vote']}, idles={agent.stats['idle']}"
            )
