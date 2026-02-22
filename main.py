from __future__ import annotations

import argparse

from agent_reddit import Agent, DecisionEngine, Environment, Simulation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Agent Reddit simulation")
    parser.add_argument("--ticks", type=int, default=12, help="Number of simulation ticks")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--channels",
        type=str,
        default="ai,python,gaming,books,worldnews",
        help="Comma-separated channels/subreddits",
    )
    return parser.parse_args()


def build_default_agents() -> list[Agent]:
    return [
        Agent(
            name="Ada",
            personality="analytical, calm, likes evidence",
            interests=["ai", "python", "worldnews"],
        ),
        Agent(
            name="Blaze",
            personality="chaotic, high-energy, contrarian",
            interests=["gaming", "ai", "worldnews"],
        ),
        Agent(
            name="Nova",
            personality="friendly explainer, educator",
            interests=["python", "books", "ai"],
        ),
        Agent(
            name="Moss",
            personality="curious beginner, asks lots of questions",
            interests=["python", "gaming", "books"],
        ),
    ]


def main() -> None:
    args = parse_args()
    channels = [name.strip().lower() for name in args.channels.split(",") if name.strip()]

    env = Environment(channels=channels)
    agents = build_default_agents()
    engine = DecisionEngine(seed=args.seed)

    sim = Simulation(
        environment=env,
        agents=agents,
        decision_engine=engine,
        ticks=max(1, args.ticks),
        seed=args.seed,
    )
    sim.run()
    sim.print_summary()


if __name__ == "__main__":
    main()
