# Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

## Environment variables

| Variable                    | Description                                                       | Default                                 |
|-----------------------------|-------------------------------------------------------------------|-----------------------------------------|
| `ANTHROPIC_API_KEY`         | Anthropic API key (required)                                      |                                         |
| `ANTHROPIC_MODEL`           | Claude model for the main agent and summarizer (required)         |                                         |
| `LOCALIZER_MODEL`           | Claude model used to localize `/start` and `/help`                | `claude-haiku-4-5-20251001`             |
| `TELEGRAM_BOT_TOKEN`        | Telegram bot token (required)                                     |                                         |
| `YOUTUBE_API_KEY`           | YouTube Data API v3 key (required)                                |                                         |
| `YOUTUBE_API_BASE_URL`      | YouTube Data API base URL                                         | `https://www.googleapis.com/youtube/v3` |
| `YT_COOKIES_B64`            | Base64-encoded `cookies.txt` for yt-dlp (optional)                |                                         |
| `DATABASE_URL`              | PostgreSQL connection URL (required; `postgres://` is normalized) |                                         |
| `ALEMBIC_DATABASE_URL`      | Override URL used by Alembic migrations (optional)                |                                         |
| `GITHUB_TOKEN`              | GitHub personal access token (optional)                           |                                         |
| `LOG_LEVEL`                 | Logging level (e.g. `INFO`)                                       |                                         |
| `AGENT_TTL`                 | Seconds before an idle agent is evicted                           | `1800`                                  |
| `AGENT_SWEEP_INTERVAL`      | How often (seconds) the eviction loop runs                        | `300`                                   |
| `AGENT_MAX_TURNS`           | Max user turns kept in agent history before sliding-window trim   | `20`                                    |
| `WEEKLY_DIGEST_DOW`         | Day of week for auto-digest (0=Mon … 6=Sun)                       | `0`                                     |
| `WEEKLY_DIGEST_HOUR`        | UTC hour for auto-digest delivery                                 | `9`                                     |
| `DIGEST_SCHEDULER_INTERVAL` | How often (seconds) the scheduler checks for due subscribers      | `60`                                    |
| `EMBEDDING_PROVIDER`        | Embedding provider (currently `voyage`)                           | `voyage`                                |
| `EMBEDDING_API_KEY`         | API key for the embedding provider (required)                     |                                         |
| `EMBEDDING_MODEL`           | Embedding model name                                              | `voyage-3.5-lite`                       |
| `EMBEDDING_DIMENSION`       | Embedding vector dimension (must match the pgvector column)       | `1024`                                  |

## Notes

- `DATABASE_URL` is normalized automatically: `postgres://` and `postgresql://` prefixes are rewritten to
  `postgresql+asyncpg://` so the same URL works locally, on Railway, and inside Alembic.
- `ALEMBIC_DATABASE_URL` is useful when migrations need a different driver/role than the runtime app.
- `EMBEDDING_DIMENSION` must match the `Vector(...)` column declared in the migrations
  (`migrations/versions/3_pgvector.py`). Changing it requires a new migration.
- `YT_COOKIES_B64` should be the base64-encoded contents of a Netscape-format `cookies.txt`. It is decoded once at
  startup, written to a temp file, and registered for cleanup on exit.
