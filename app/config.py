from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    openai_api_key: str = Field(default="")
    llm_provider: Literal["openai", "mistral", "ollama"] = "openai"

    qdrant_url: str = "http://qdrant:6333"
    redis_url: str = "redis://redis:6379/0"

    mcp_datagouv_url: str = "https://mcp.data.gouv.fr/mcp"
    mcp_hubspot_url: str = ""

    hubspot_token: str = ""
    tavily_api_key: str = ""

    langfuse_host: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    cors_allowed_origins: str = "http://localhost"
    rate_limit_per_minute: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def hubspot_enabled(self) -> bool:
        return bool(self.hubspot_token)


settings = Settings()
