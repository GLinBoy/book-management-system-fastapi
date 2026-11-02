from enum import StrEnum
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: AppEnv = AppEnv.DEV
    database_url: str | None = None

    @model_validator(mode="after")
    def _require_database_url_in_prod(self) -> Settings:
        if self.app_env is AppEnv.PROD and not self.database_url:
            raise ValueError("DATABASE_URL must be set when APP_ENV=prod")
        return self

    @property
    def effective_database_url(self) -> str:
        if self.database_url:
            return self.database_url
        if self.app_env is AppEnv.TEST:
            return "sqlite:///./test.db"
        return "sqlite:///./dev.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
