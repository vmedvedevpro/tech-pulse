from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    anthropic_model: str
    telegram_bot_token: str
    database_url: str
    youtube_api_key: str
    youtube_api_base_url: str = "https://www.googleapis.com/youtube/v3"
    youtube_oembed_url: str = "https://www.youtube.com/oembed"
    log_level: str
    github_token: str | None = None
    agent_ttl: float = 1800.0
    agent_sweep_interval: float = 300.0

    alembic_database_url: str | None = None

    model_config = {"env_file": ".env"}

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


# noinspection PyArgumentList
settings = Settings()
