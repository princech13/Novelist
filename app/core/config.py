from functools import lru_cache
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Novelist"
    port: int = 8081
    log_level: str = "INFO"          # DEBUG | INFO | WARNING | ERROR

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    jwt_secret_key: str = "change-this-secret"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60           # access token lifetime
    jwt_refresh_expiry_days: int = 7       # refresh token lifetime

    # CORS — set as plain text: CORS_ORIGINS=* or CORS_ORIGINS=http://a.com,http://b.com
    # Stored as str so pydantic-settings never tries to JSON-decode it.
    cors_origins: str = "*"

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins_list(self) -> list[str]:
        value = self.cors_origins.strip()
        if value.startswith("["):
            import json
            return json.loads(value)
        return [v.strip() for v in value.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
