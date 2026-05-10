# Tech Pulse
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![License](https://img.shields.io/github/license/vmedvedevpro/tech-pulse)
![Last commit](https://img.shields.io/github/last-commit/vmedvedevpro/tech-pulse)
![Claude](https://img.shields.io/badge/powered%20by-Claude-orange?logo=anthropic)
[![Telegram](https://img.shields.io/badge/Telegram-bot-26A5E4?logo=telegram)](https://t.me/aitechpulsebot)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-store-4169E1?logo=postgresql)
![CI](https://github.com/vmedvedevpro/tech-pulse/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/vmedvedevpro/tech-pulse/branch/main/graph/badge.svg)](https://codecov.io/gh/vmedvedevpro/tech-pulse)

Telegram bot for personalized tech digests powered by Claude. Tracks YouTube channels, GitHub repositories, and personal
interest topics — delivers structured summaries on demand or automatically on a weekly schedule.

## Features

- **YouTube subscriptions** — add, remove, and list tracked YouTube channels via natural language
- **GitHub repository tracking** — watch GitHub repos and get notified about new releases
- **Interest topics** — save personal topics (e.g. "Rust", "LLM agents") to shape digest relevance
- **On-demand digest** — `/check` collects new YouTube videos (with transcripts) and new GitHub releases in parallel
- **Weekly digest scheduler** — subscribe to automatic weekly delivery; the bot runs a background cron loop and sends
  digests to all subscribers at a configured day and time
- **Deduplication** — seen videos and releases are stored in PostgreSQL and excluded from future digests
- **Video cache** — video metadata and transcripts are persisted as a standalone `videos` entity; subsequent digests
  (including for other users subscribed to the same channel) reuse cached transcripts instead of hitting yt-dlp
- **On-demand repo info** — ask the agent about any GitHub repo: description, stars, language, topics
- **Per-user agents with conversation history** — each Telegram user gets a dedicated agent instance that retains full
  message history across turns
- **Agent eviction** — idle agents are evicted after a configurable TTL to free memory
- **Streaming responses** — agent replies are streamed to Telegram in real time via draft messages
- **Prompt caching** — system prompt is cached with `cache_control: ephemeral` to reduce token costs
- **Retry on overload** — automatically retries on Anthropic HTTP 529 with linear backoff (up to 4 attempts)

## Architecture

```mermaid
flowchart LR
    User(["👤 User"]) <--> TG[Telegram]

    subgraph bot [Bot layer]
        TG <--> BotApp
        BotApp --> AR["AgentRegistry\n(per user_id)"]
        AR --> A["Agent (Claude)"]
        A --> TR[ToolRegistry]
    end

    subgraph tools [Tools]
        TR --> YT[YouTube tools]
        TR --> GH[GitHub tools]
        TR --> MGMT["Channel / Interests\n/ Repo tools"]
        TR --> SUB[Subscription tools]
    end

    subgraph workers [Workers & storage]
        YT & GH --> DW[DigestWorker] & GW[GitHubWorker]
        MGMT & SUB & DW & GW --> PG[(PostgreSQL)]
        DW --> YTAPI[YouTube Data API]
        DW --> YTTR[Transcript API]
        GW --> GHAPI[GitHub REST API]
    end

    PG -.->|"due subscribers"| DS
    DS -.->|"create agent\nper subscriber"| AR
    DS -.->|"send digest"| TG

    DS["⏰ DigestScheduler\nweekly cron"]
```

### Tools registered per agent

| Group              | Tool                                                                                 | Description                                 |
|--------------------|--------------------------------------------------------------------------------------|---------------------------------------------|
| YouTube data       | `resolve_channel_id`                                                                 | Resolve a channel handle to its ID          |
|                    | `get_recent_videos`                                                                  | Fetch recent videos from a channel          |
| YouTube transcript | `fetch_video_metadata`                                                               | Get video title and metadata                |
|                    | `list_transcripts`                                                                   | List available transcript languages         |
|                    | `fetch_transcript`                                                                   | Download full video transcript              |
| Channels           | `add_channel` / `remove_channel` / `list_channels`                                   | Manage YouTube subscriptions                |
| Interests          | `add_interest` / `remove_interest` / `list_interests`                                | Manage interest topics                      |
| GitHub             | `get_repo_info`                                                                      | Repo description, stars, language, topics   |
|                    | `get_latest_release`                                                                 | Latest release tag and notes                |
| Repos              | `add_repo` / `remove_repo` / `list_repos`                                            | Manage tracked repos                        |
| Digest             | `check_digest`                                                                       | Run DigestWorker + GitHubWorker in parallel |
| Weekly digest      | `subscribe_weekly_digest` / `unsubscribe_weekly_digest` / `get_weekly_digest_status` | Manage automatic weekly delivery            |
| Summary            | `submit_summary`                                                                     | Submit structured content analysis          |

## Requirements

- Python 3.11+
- PostgreSQL (can be started via `docker compose up -d`)
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

| Variable                    | Description                                     | Default |
|-----------------------------|-------------------------------------------------|---------|
| `ANTHROPIC_API_KEY`         | Anthropic API key (required)                    |         |
| `ANTHROPIC_MODEL`           | Claude model (e.g. `claude-haiku-4-5-20251001`) |         |
| `TELEGRAM_BOT_TOKEN`        | Telegram bot token (required)                   |         |
| `YOUTUBE_API_KEY`           | YouTube Data API v3 key (required)              |         |
| `DATABASE_URL`              | PostgreSQL connection URL (required)            |         |
| `GITHUB_TOKEN`              | GitHub personal access token (optional)         |         |
| `LOG_LEVEL`                 | Logging level (e.g. `INFO`)                     |         |
| `AGENT_TTL`                 | Seconds before an idle agent is evicted         | `1800`  |
| `AGENT_SWEEP_INTERVAL`      | How often (seconds) the eviction loop runs      | `300`   |
| `WEEKLY_DIGEST_DOW`         | Day of week for auto-digest (0=Mon … 6=Sun)     | `0`     |
| `WEEKLY_DIGEST_HOUR`        | UTC hour for auto-digest delivery               | `9`     |
| `DIGEST_SCHEDULER_INTERVAL` | How often (seconds) the scheduler checks        | `60`    |

## Running

1. Start PostgreSQL:

```bash
docker compose up -d
```

2. Apply database migrations:

```bash
uv run alembic upgrade head
```

3. Start the bot:

```bash
techpulse
```

## Usage

Try it: [@aitechpulsebot](https://t.me/aitechpulsebot)

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

**Weekly digest subscription**

- `Enable weekly digest` — subscribe to automatic weekly delivery
- `Disable weekly digest` — unsubscribe
- `Am I subscribed to weekly digest?` — check subscription status

## Tests

```bash
uv run pytest
```

```bash
uv run pytest --cov=techpulse
```
