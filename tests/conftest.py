"""Shared pytest fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def _isolate_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent IMBALANCELAB_* variables in the developer's shell from leaking into tests."""
    for key in list(os.environ):
        if key.startswith("IMBALANCELAB_"):
            monkeypatch.delenv(key, raising=False)
