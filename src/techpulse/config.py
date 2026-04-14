from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    anthropic_model: str
    telegram_bot_token: str
    redis_url: str

    model_config = {"env_file": ".env"}


# noinspection PyArgumentList
settings = Settings()
