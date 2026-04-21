# Tech Pulse
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![License](https://img.shields.io/github/license/vmedvedevpro/tech-pulse)
![Last commit](https://img.shields.io/github/last-commit/vmedvedevpro/tech-pulse)
![Claude](https://img.shields.io/badge/powered%20by-Claude-orange?logo=anthropic)
![Telegram](https://img.shields.io/badge/Telegram-bot-26A5E4?logo=telegram)
![Redis](https://img.shields.io/badge/Redis-store-DC382D?logo=redis)
![CI](https://github.com/vmedvedevpro/tech-pulse/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/vmedvedevpro/tech-pulse/branch/main/graph/badge.svg)](https://codecov.io/gh/vmedvedevpro/tech-pulse)

Telegram bot for personalized tech digests powered by Claude. Tracks YouTube channels, GitHub repositories, and personal
interest topics — and delivers structured summaries right in Telegram.

## Features

- **YouTube subscriptions** — add, remove, and list tracked YouTube channels via natural language
- **GitHub repository tracking** — watch GitHub repos and get notified about new releases
- **Interest topics** — save personal topics (e.g. "Rust", "LLM agents") to shape digest relevance
- **Unified digest** — `/check` collects new YouTube videos (with transcripts) and new GitHub releases in parallel
- **Deduplication** — seen videos and releases are remembered in Redis and excluded from future digests
- **On-demand repo info** — ask the agent about any GitHub repo: description, stars, language, topics
- **Streaming responses** — agent replies are streamed to Telegram in real time
- **Claude agent with tool use** — the agent autonomously decides which tools to call and composes the response

## Architecture

```
Telegram ↔ Bot ↔ Agent (Claude)
                    │
                    ├── YouTube tools
                    │     ├── add_channel / remove_channel / list_channels
                    │     ├── fetch_video_metadata
                    │     └── list_transcripts / fetch_transcript
                    │
                    ├── GitHub tools
                    │     ├── add_repo / remove_repo / list_repos
                    │     ├── get_repo_info
                    │     └── get_latest_release
                    │
                    ├── Interest tools
                    │     ├── add_interest / remove_interest / list_interests
                    │
                    └── check_digest  ←── DigestWorker (YouTube)
                                      ←── GitHubWorker  (releases)

Persistence (Redis)
  ├── ChannelRepository     — subscribed YouTube channels
  ├── VideoRepository       — seen video IDs
  ├── RepoRepository        — watched GitHub repos
  ├── ReleaseRepository     — seen GitHub releases
  └── InterestsRepository   — user interest topics

Integrations
  ├── YouTube Data API v3   — channel / video metadata
  ├── youtube-transcript-api — video transcripts
  └── GitHub REST API       — repo info, releases
```

## Requirements

- Python 3.11+
- Redis (can be started via `docker compose up -d`)
- API keys: Anthropic, Telegram Bot, YouTube Data API
- GitHub token (optional, raises rate limits)

## Installation

```bash
uv sync
```

For development:

```bash
uv sync --extra dev
```

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

| Variable             | Description                                     |
|----------------------|-------------------------------------------------|
| `ANTHROPIC_API_KEY`  | Anthropic API key (required)                    |
| `ANTHROPIC_MODEL`    | Claude model (e.g. `claude-haiku-4-5-20251001`) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (required)                   |
| `YOUTUBE_API_KEY`    | YouTube Data API v3 key (required)              |
| `REDIS_URL`          | Redis connection URL (required)                 |
| `GITHUB_TOKEN`       | GitHub personal access token (optional)         |
| `LOG_LEVEL`          | Logging level (e.g. `INFO`)                     |

## Running

1. Start Redis:

```bash
docker compose up -d
```

2. Start the bot:

```bash
techpulse
```

## Usage

Chat with the bot in Telegram using natural language:

**YouTube channels**

- `Add channel @nickchapsas`
- `Show my channels`
- `Remove @channel_handle`

**GitHub repositories**

- `Track microsoft/vscode`
- `Show my repos`
- `Stop tracking vercel/next.js`
- `What's the latest release of astral-sh/uv?`
- `Tell me about the facebook/react repo`

**Interest topics**

- `Add interest: distributed systems`
- `I'm interested in Rust`
- `Show my interests`
- `Remove interest LLM agents`

**Digest**

- `/check` — get all new YouTube videos and GitHub releases since last check
- `Check for new videos`

## Tests

```bash
pytest
```

```bash
pytest --cov=techpulse
```
