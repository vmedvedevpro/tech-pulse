# Tech Pulse
![Python](https://img.shields.io/badge/python-3.11+-blue?logo=python)
![License](https://img.shields.io/github/license/vmedvedevpro/tech-pulse)
![Last commit](https://img.shields.io/github/last-commit/vmedvedevpro/tech-pulse)
![Claude](https://img.shields.io/badge/powered%20by-Claude-orange?logo=anthropic)
[![Telegram](https://img.shields.io/badge/Telegram-bot-26A5E4?logo=telegram)](https://t.me/aitechpulsebot)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-store-4169E1?logo=postgresql)
![pgvector](https://img.shields.io/badge/pgvector-HNSW-4169E1?logo=postgresql)
![Voyage AI](https://img.shields.io/badge/embeddings-Voyage%20AI-7C3AED)
![CI](https://github.com/vmedvedevpro/tech-pulse/actions/workflows/ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/vmedvedevpro/tech-pulse/branch/main/graph/badge.svg)](https://codecov.io/gh/vmedvedevpro/tech-pulse)

Telegram bot for personalized tech digests powered by Claude. Tracks YouTube channels, GitHub repositories, and personal
interest topics — delivers structured summaries on demand or on a weekly schedule, and lets you semantically search
across everything you've already watched.

- 🌐 **Landing**: <https://vmedvedevpro.github.io/tech-pulse/>
- 🤖 **Try the bot**: [@aitechpulsebot](https://t.me/aitechpulsebot)

## Highlights

- **YouTube + GitHub digests** — collect new videos (with transcripts) and releases in parallel, on demand or weekly
- **Persistent video summaries** — every transcript is summarized once by Claude and reused everywhere
- **Semantic search over your history** — `search_my_videos` embeds queries with Voyage AI and runs cosine search via
  pgvector (HNSW)
- **Per-user agents** — one Claude agent per Telegram user with sliding-window memory, streaming replies, prompt
  caching, and idle-TTL eviction
- **Branded onboarding** — `/start` and `/help` are localized on the fly via a separate Claude model

```mermaid
flowchart LR
    User(["👤 User"]) <--> TG[Telegram] <--> Bot["Bot + per-user\nClaude agents"]
    Bot --> Tools["Tools:\nYouTube · GitHub · search"]
    Tools --> Workers["DigestWorker · GitHubWorker\nVideoSummarizer"]
    Workers --> PG[("PostgreSQL\n+ pgvector")]
    Workers --> Voyage["Voyage AI\nembeddings"]
    Cron["⏰ DigestScheduler"] -.-> Bot
```

Full diagram and component breakdown: [`documentation/architecture.md`](./documentation/architecture.md).

## Quickstart

```bash
uv sync                                # install
cp .env.example .env                   # fill in keys (see docs)
docker compose up -d                   # postgres + pgvector
uv run alembic upgrade head            # migrate
techpulse                              # run the bot
```

For development install extras with `uv sync --group dev` and run tests via `uv run pytest`.

## Documentation

- [Configuration](./documentation/configuration.md) — env vars and `.env` setup
- [Architecture](./documentation/architecture.md) — full diagram, components, tool table
- [Usage](./documentation/usage.md) — natural-language command examples
- [Deployment](./documentation/deployment.md) — Docker Compose, Railway, migrations
