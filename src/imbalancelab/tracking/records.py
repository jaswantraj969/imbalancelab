"""File-based run records: one directory per run, JSON/Parquet files inside.

Every file a report or API response reads lives in the run directory, so a run can be audited
(or a report regenerated) from the directory alone.
"""

import json
import platform
import re
import sys
import uuid
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path
from typing import Any

import pandas as pd

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
TRACKED_PACKAGES = (
    "imbalancelab",
    "numpy",
    "pandas",
    "scikit-learn",
    "imbalanced-learn",
    "scipy",
    "joblib",
    "pyarrow",
    "pydantic",
    "matplotlib",
)

# file names inside a run directory
RUN_FILE = "run.json"
CONFIG_FILE = "config.json"
ENVIRONMENT_FILE = "environment.json"
DATASET_SHA_FILE = "dataset_sha256.txt"
HOLDOUT_FILE = "holdout.json"
FOLDS_FILE = "fold_indices.json"
PROFILE_FILE = "profile.json"
FOLD_METRICS_FILE = "fold_metrics.json"
SUMMARY_FILE = "summary.json"
OOF_FILE = "oof_predictions.parquet"
THRESHOLDS_FILE = "thresholds.json"
FINAL_FILE = "final_evaluation.json"
FINAL_PREDICTIONS_FILE = "final_predictions.parquet"
FINAL_LOG_FILE = "final_evaluation_log.jsonl"


class InvalidIdError(ValueError):
    """An identifier is not safe to use as a path component."""


class RecordNotFoundError(LookupError):
    """The requested run/dataset/model does not exist."""


def validate_id(value: str) -> str:
    """Return ``value`` if it is a safe single path component, else raise."""
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        raise InvalidIdError(f"invalid identifier: {value!r}")
    return value


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def new_id(prefix: str = "") -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}{stamp}-{uuid.uuid4().hex[:8]}"


def write_json(path: Path, obj: Any) -> None:
    Path(path).write_text(
        json.dumps(obj, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def environment_info() -> dict[str, Any]:
    versions: dict[str, str | None] = {}
    for pkg in TRACKED_PACKAGES:
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = None
    return {
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": versions,
    }


class RunStore:
    """Creates and resolves run directories under ``runs_dir``."""

    def __init__(self, runs_dir: Path) -> None:
        self.runs_dir = Path(runs_dir)

    def create(self, run_id: str | None = None) -> tuple[str, Path]:
        run_id = validate_id(run_id or new_id("run-"))
        path = self.runs_dir / run_id
        path.mkdir(parents=True, exist_ok=False)
        return run_id, path

    def path(self, run_id: str) -> Path:
        path = self.runs_dir / validate_id(run_id)
        if not (path / RUN_FILE).is_file():
            raise RecordNotFoundError(f"run {run_id!r} not found")
        return path

    def list(self) -> list[str]:
        if not self.runs_dir.is_dir():
            return []
        return sorted(
            p.name for p in self.runs_dir.iterdir() if p.is_dir() and (p / RUN_FILE).is_file()
        )


class RunRecord:
    """Read-only view of a run directory."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if not (self.path / RUN_FILE).is_file():
            raise RecordNotFoundError(f"no run record at {self.path}")

    @property
    def run_id(self) -> str:
        return str(self.run["run_id"])

    def _json(self, name: str) -> Any:
        return read_json(self.path / name)

    def _optional_json(self, name: str) -> Any | None:
        p = self.path / name
        return read_json(p) if p.is_file() else None

    @property
    def run(self) -> dict[str, Any]:
        return dict(self._json(RUN_FILE))

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._json(CONFIG_FILE))

    @property
    def environment(self) -> dict[str, Any]:
        return dict(self._json(ENVIRONMENT_FILE))

    @property
    def summary(self) -> dict[str, Any]:
        return dict(self._json(SUMMARY_FILE))

    @property
    def fold_metrics(self) -> list[dict[str, Any]]:
        return list(self._json(FOLD_METRICS_FILE))

    @property
    def folds(self) -> dict[str, Any]:
        return dict(self._json(FOLDS_FILE))

    @property
    def holdout(self) -> dict[str, Any]:
        return dict(self._json(HOLDOUT_FILE))

    @property
    def profile(self) -> dict[str, Any] | None:
        return self._optional_json(PROFILE_FILE)

    @property
    def thresholds(self) -> dict[str, Any] | None:
        return self._optional_json(THRESHOLDS_FILE)

    @property
    def final_evaluation(self) -> dict[str, Any] | None:
        return self._optional_json(FINAL_FILE)

    def oof_predictions(self) -> pd.DataFrame:
        return pd.read_parquet(self.path / OOF_FILE)

    def final_predictions(self) -> pd.DataFrame | None:
        p = self.path / FINAL_PREDICTIONS_FILE
        return pd.read_parquet(p) if p.is_file() else None

    def final_log(self) -> list[dict[str, Any]]:
        p = self.path / FINAL_LOG_FILE
        if not p.is_file():
            return []
        lines = p.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]
