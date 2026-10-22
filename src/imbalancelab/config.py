"""Project settings, overridable via environment variables prefixed with ``IMBALANCELAB_``."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SEED = 42


class Settings(BaseSettings):
    """Runtime settings for paths and reproducibility."""

    model_config = SettingsConfigDict(env_prefix="IMBALANCELAB_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default=Path("data"))
    raw_data_dir: Path = Field(default=Path("data/raw"))
    runs_dir: Path = Field(default=Path("runs"))
    seed: int = Field(default=DEFAULT_SEED)


def get_settings() -> Settings:
    """Return a fresh Settings instance (reads environment at call time)."""
    return Settings()
