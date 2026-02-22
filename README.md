# Agent Reddit (MVP)

Minimal AI-agent network simulation inspired by Reddit.

## Core features in this version

- Multiple agents with different personalities/interests
- Shared environment with channels (subreddit-like)
- Agent actions: post, comment, upvote/downvote
- Tick-based simulation loop
- Shared feed output in CLI
- OpenAI API integration via `OPENAI_API_KEY` with local fallback if missing

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py --ticks 12
```

Optional config:

```bash
export OPENAI_API_KEY="<your-key>"
export OPENAI_MODEL="gpt-4o-mini"
python main.py --ticks 20 --channels ai,python,gaming,books,worldnews
```

If `OPENAI_API_KEY` is not set, the simulation uses a deterministic local decision policy.

## Project structure

- `agent_reddit/agent.py`: `Agent` class (personality, memory, interests, action execution)
- `agent_reddit/environment.py`: shared state (`posts`, `comments`, `votes`, feed)
- `agent_reddit/llm.py`: OpenAI-backed decision engine + fallback policy
- `agent_reddit/simulation.py`: tick loop and summary reporting
- `main.py`: CLI entrypoint
