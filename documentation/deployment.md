# Deployment

## Local with Docker Compose

The bundled `docker-compose.yml` starts a PostgreSQL instance with the `pgvector` extension preinstalled
(`pgvector/pgvector:pg16`):

```bash
docker compose up -d
uv run alembic upgrade head
techpulse
```

The migration step enables the `vector` extension, creates the `videos.summary_embedding` column, and builds the
HNSW index used by `search_my_videos`.

## Railway

A `railway.toml` and `Dockerfile` are included for one-click deployment to Railway.

- Add the Railway PostgreSQL plugin and bind its `DATABASE_URL` to the bot service. The `postgres://` prefix Railway
  injects is normalized to `postgresql+asyncpg://` by the settings loader.
- Railway's default Postgres image does **not** ship with `pgvector`. Either switch to a Postgres flavor that bundles
  it (e.g. a Supabase or Neon instance) or run `CREATE EXTENSION vector;` manually before applying migrations.
- Set every required env var listed in [`configuration.md`](./configuration.md) in the Railway dashboard.
- If you need yt-dlp to bypass YouTube's bot checks, generate a `cookies.txt` and set `YT_COOKIES_B64` to its
  base64-encoded contents.

## Database migrations

Migrations live under `migrations/versions/` and are managed by Alembic:

```bash
uv run alembic upgrade head            # apply
uv run alembic downgrade -1            # rollback last
uv run alembic revision -m "message"   # new migration
```

Set `ALEMBIC_DATABASE_URL` if Alembic needs a different connection (e.g. a sync driver or a different role) than
the runtime app.
