from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTSCOPE_", env_file=".env")

    app_name: str = "AgentScope"
    database_url: str = "sqlite:///./agentscope.db"
    cors_origins: str = "http://localhost:3001"
    seed_demo_data: bool = True

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
