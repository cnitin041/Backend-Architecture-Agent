import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and .env file.
    Utilises Pydantic BaseSettings for validation and type-safety.
    """
    # --- API Keys ---
    openai_api_key: str = ""
    hf_token: str = ""
    app_env: str = "development"
    debug: bool = True

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    model_name: str = "gpt-4o"

    # --- Fallback Model ---
    # Used automatically when openai_api_key is empty.
    local_model_name: str = "Qwen/Qwen2-1.5B-Instruct"
    # Maximum new tokens the local model may generate per request.
    local_model_max_tokens: int = 2048

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global settings singleton
settings = Settings()
