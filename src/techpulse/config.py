from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    anthropic_model: str
    telegram_bot_token: str
    redis_url: str
    youtube_api_key: str
    youtube_api_base_url: str = "https://www.googleapis.com/youtube/v3"
    youtube_oembed_url: str = "https://www.youtube.com/oembed"
    log_level: str
    github_token: str | None = None
    agent_ttl: float = 1800.0
    agent_sweep_interval: float = 300.0

    model_config = {"env_file": ".env"}


# noinspection PyArgumentList
settings = Settings()
