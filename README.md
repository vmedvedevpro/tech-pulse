# Tech Pulse
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![License](https://img.shields.io/github/license/vmedvedevpro/tech-pulse)
![Last commit](https://img.shields.io/github/last-commit/vmedvedevpro/tech-pulse)
![Claude](https://img.shields.io/badge/powered%20by-Claude-orange?logo=anthropic)
![Telegram](https://img.shields.io/badge/Telegram-bot-26A5E4?logo=telegram)
![Redis](https://img.shields.io/badge/Redis-store-DC382D?logo=redis)
![CI](https://github.com/vmedvedevpro/tech-pulse/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/vmedvedevpro/tech-pulse/branch/main/graph/badge.svg)](https://codecov.io/gh/vmedvedevpro/tech-pulse)

Telegram bot for personalized YouTube tech digests powered by Claude.

Subscribe to channels and TechPulse will automatically collect new videos, download transcripts, and deliver a structured digest right in Telegram.

## Features

- **Subscription management** — add, remove, and list tracked YouTube channels via chat
- **New video digest** — the `/check` command collects recent videos from all subscriptions, downloads transcripts, and generates summaries
- **Deduplication** — already seen videos are remembered and excluded from future digests
- **Streaming response** — agent responses are streamed to Telegram in real time
- **Claude agent with tool use** — the agent decides which tools to call and composes the response

## Architecture

```
Telegram ↔ Bot ↔ Agent (Claude) ↔ Tools
                                    ├── add_channel / remove_channel / list_channels
                                    ├── check_digest
                                    ├── fetch_video_metadata
                                    ├── list_transcripts / fetch_transcript
                                    └── submit_summary
                  Agent ↔ Redis (subscriptions, seen videos)
                  Agent ↔ YouTube Data API (channels, videos)
                  Agent ↔ youtube-transcript-api (transcripts)
```

## Requirements

- Python 3.11+
- Redis (can be started via `docker compose up -d`)
- API keys: Anthropic, Telegram Bot, YouTube Data API

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

| Variable             | Description                                        |
|----------------------|----------------------------------------------------|
| `ANTHROPIC_API_KEY`  | Anthropic API key (required)                       |
| `ANTHROPIC_MODEL`    | Claude model (e.g. `claude-haiku-4-5-20251001`)    |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token (required)                      |
| `YOUTUBE_API_KEY`    | YouTube Data API v3 key (required)                 |
| `REDIS_URL`          | Redis connection URL (required)                    |
| `LOG_LEVEL`          | Logging level (e.g. `INFO`)                        |

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

- **Subscribe to a channel** — `Add channel @nickchapsas`
- **List subscriptions** — `Show my channels`
- **Remove a channel** — `Remove @channel_handle`
- **Get a digest** — `/check` or `Check for new videos`

## Tests

```bash
pytest
```

```bash
pytest --cov=techpulse
```
