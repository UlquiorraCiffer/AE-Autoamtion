from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANIMEEDIT_", case_sensitive=False)

    app_name: str = "AnimeEdit AI Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "127.0.0.1"
    port: int = 8000

    cors_origins: list[str] = ["*"]

    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s"

    max_prompt_length: int = 2000
    request_timeout: int = 30


settings = Settings()
