"""Shared pytest fixtures."""

import os
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def _isolate_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent IMBALANCELAB_* variables in the developer's shell from leaking into tests."""
    for key in list(os.environ):
        if key.startswith("IMBALANCELAB_"):
            monkeypatch.delenv(key, raising=False)


WriteCsv = Callable[..., Path]


@pytest.fixture
def write_csv(tmp_path: Path) -> WriteCsv:
    """Write a DataFrame to ``tmp_path/<name>`` and return the path."""

    def _write(frame: pd.DataFrame, name: str = "data.csv") -> Path:
        path = tmp_path / name
        if path.suffix == ".parquet":
            frame.to_parquet(path, index=False)
        else:
            frame.to_csv(path, index=False)
        return path

    return _write


def make_imbalanced_frame(
    n: int = 300, positive_rate: float = 0.15, seed: int = 0, n_groups: int = 30
) -> pd.DataFrame:
    """Small synthetic imbalanced dataset with an informative signal and a categorical."""
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < positive_rate).astype(int)
    y[:2] = 1  # guarantee positives even for tiny n
    signal = rng.normal(size=n) + 1.5 * y
    noise = rng.normal(size=n)
    cat = rng.choice(["a", "b", "c"], size=n)
    frame = pd.DataFrame(
        {
            "row_id": np.arange(n),
            "x_signal": signal,
            "x_noise": noise,
            "color": cat,
            "group": rng.integers(0, n_groups, size=n),
            "ts": pd.date_range("2024-01-01", periods=n, freq="D").astype(str),
            "label": np.where(y == 1, "yes", "no"),
        }
    )
    frame.loc[rng.random(n) < 0.05, "x_noise"] = np.nan
    return frame


@pytest.fixture
def imbalanced_frame() -> pd.DataFrame:
    return make_imbalanced_frame()
