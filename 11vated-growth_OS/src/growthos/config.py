"""Central, typed application configuration.

Every environment-specific value flows through here. Secrets are never
hard-coded; they come from environment variables, a local `.env` file, or the
OS keychain (see ``growthos.security.secrets``).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for GrowthOS."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Environment ---
    environment: str = "development"  # development | production

    # --- Database ---
    database_url: str = (
        "postgresql+asyncpg://growthos:growthos@127.0.0.1:5432/growthos"
    )

    # --- Security ---
    secret_key: str = "change-me-development-only"
    session_cookie_name: str = "growthos_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days
    max_sessions_per_founder: int = 10
    revoked_session_retention_days: int = 7
    session_cleanup_interval_seconds: int = 60 * 60  # 1 hour
    # Password must survive: 12+ chars, upper/lower, digit.
    require_strong_password: bool = True

    # --- API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Gmail integration ---
    gmail_initial_lookback_days: int = 30
    gmail_initial_max_messages: int = 200
    gmail_sync_batch_size: int = 50
    gmail_sync_interval_seconds: int = 3 * 60  # 3 minutes
    gmail_sync_on_error_backoff_seconds: int = 15 * 60

    # --- Local AI (Ollama) ---
    # Model names must match what is actually installed on the workstation.
    # Preferred fast model was qwen3.5:9b-q4_K_M; the current equivalent
    # installed here is gemma2:9b (9B Q4). Embeddings use nomic-embed-text.
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_fast_model: str = "gemma2:9b"
    ollama_deep_model: str = "qwen2.5:32b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout_seconds: float = 300.0

    # --- Revenue Scout ---
    scout_daily_interval_seconds: int = 24 * 60 * 60  # once per day
    scout_light_interval_seconds: int = 30 * 60  # intraday checks every 30 min

    # --- Evidence Mirror ---
    evidence_mirror_root: str = ""  # set to <data>/evidence-mirrors if empty
    evidence_mirror_max_depth: int = 1  # shallow by default

    # --- Founder identity ---
    founder_email: str = ""
    founder_phone: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
