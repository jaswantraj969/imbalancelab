"""Project settings, overridable via environment variables prefixed with ``IMBALANCELAB_``."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SEED = 42


class Settings(BaseSettings):
    """Runtime settings for paths, reproducibility, and the API."""

    model_config = SettingsConfigDict(env_prefix="IMBALANCELAB_", env_file=".env", extra="ignore")

    data_dir: Path = Field(default=Path("data"))
    raw_data_dir: Path = Field(default=Path("data/raw"))
    datasets_dir: Path = Field(default=Path("data/registered"))
    runs_dir: Path = Field(default=Path("runs"))
    models_dir: Path = Field(default=Path("models"))
    seed: int = Field(default=DEFAULT_SEED)
    max_upload_bytes: int = Field(default=50 * 1024 * 1024, gt=0)


def get_settings() -> Settings:
    """Return a fresh Settings instance (reads environment at call time)."""
    return Settings()
