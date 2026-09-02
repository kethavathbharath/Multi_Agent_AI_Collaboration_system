import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    APP_TITLE: str = "Multi-Agent AI Collaboration System"

    HOST: str = os.getenv(
        "HOST",
        "127.0.0.1"
    )

    PORT: int = int(
        os.getenv(
            "PORT",
            "8000"
        )
    )

    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "ollama"

    DEFAULT_MODEL_NAME: str = "llama3.2:3b"

    # Ollama Settings
    OLLAMA_BASE_URL: str = os.getenv(
        "OLLAMA_BASE_URL",
        "http://127.0.0.1:11434"
    )

    # Kept for compatibility with existing project code.
    # They are not required when using Ollama.
    OPENAI_API_KEY: Optional[str] = os.getenv(
        "OPENAI_API_KEY"
    )

    GOOGLE_API_KEY: Optional[str] = os.getenv(
        "GOOGLE_API_KEY"
    )

    # Database Settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./collaboration_system.db"
    )

    # Workflow Settings
    # Keep this at 1 for faster local Ollama testing.
    MAX_REVIEW_ITERATIONS: int = int(
        os.getenv(
            "MAX_REVIEW_ITERATIONS",
            "1"
        )
    )

    DEBUG: bool = (
        os.getenv(
            "DEBUG",
            "True"
        ).lower() == "true"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()