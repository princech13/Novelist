import os
from functools import lru_cache
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Guarantee a writable HuggingFace cache directory even when the container
# user has no writable home.  Set before any import that touches HF Hub.
if not os.environ.get("HF_HOME"):
    _hf_cache = os.path.join(os.path.dirname(__file__), "..", "..", ".cache", "huggingface")
    os.environ["HF_HOME"] = os.path.abspath(_hf_cache)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Novelist"
    port: int = 8081
    log_level: str = "INFO"          # DEBUG | INFO | WARNING | ERROR

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    rabbitmq_enabled: bool = True
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "novelist"
    rabbitmq_password: str = "password"

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

    # RAG
    rag_embedding_model: str = "all-MiniLM-L6-v2"  # 384-dim, fast local model
    rag_chunk_size: int = 512        # characters per chunk
    rag_chunk_overlap: int = 64      # overlap between consecutive chunks
    rag_top_k: int = 5               # default number of results returned


@lru_cache
def get_settings() -> Settings:
    return Settings()
