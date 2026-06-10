from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Feed Tren Scrapper"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    frontend_origin: str = "http://localhost:5173"
    enable_mock_results: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

