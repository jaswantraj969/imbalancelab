"""High-level workflow over a workspace (datasets, runs, models directories).

This is the library entry point used by the API: every route handler validates its input and
calls one function here. No HTTP concerns live in this module, and no ML logic lives in routes.
"""

import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from imbalancelab.config import Settings
from imbalancelab.data.loader import LoadedDataset, load_dataset
from imbalancelab.data.schema import DatasetSchema
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import final_evaluate
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.profiling.profile import DatasetProfile, ProfileThresholds, profile_dataset
from imbalancelab.reporting.report import generate_report
from imbalancelab.splitting.splits import Holdout, HoldoutConfig, get_or_create_holdout
from imbalancelab.tracking import records as rec

ALLOWED_SUFFIXES = (".csv", ".parquet")


class DatasetRegistration(BaseModel):
    dataset_id: str
    created_at: str
    source_name: str
    sha256: str
    n_rows: int
    n_features: int
    positive_rate: float
    dataset_schema: DatasetSchema
    holdout_config: HoldoutConfig
    n_outer_train: int
    n_test: int
    test_sha256: str
    n_warnings: int
    notes: list[str]


class Workspace:
    """Directory layout for registered datasets, runs, and persisted models."""

    def __init__(self, datasets_dir: Path, runs_dir: Path, models_dir: Path) -> None:
        self.datasets_dir = Path(datasets_dir)
        self.runs_dir = Path(runs_dir)
        self.models_dir = Path(models_dir)  # directories are created on first write

    @classmethod
    def from_settings(cls, settings: Settings) -> "Workspace":
        return cls(settings.datasets_dir, settings.runs_dir, settings.models_dir)

    @classmethod
    def at(cls, root: Path) -> "Workspace":
        root = Path(root)
        return cls(root / "datasets", root / "runs", root / "models")

    def dataset_dir(self, dataset_id: str) -> Path:
        path = self.datasets_dir / rec.validate_id(dataset_id)
        if not (path / "dataset.json").is_file():
            raise rec.RecordNotFoundError(f"dataset {dataset_id!r} not found")
        return path

    def run_dir(self, run_id: str) -> Path:
        return rec.RunStore(self.runs_dir).path(run_id)


# --------------------------------------------------------------------------- datasets


def register_dataset(
    ws: Workspace,
    source: Path,
    suffix: str,
    schema: DatasetSchema,
    holdout_config: HoldoutConfig | None = None,
    profile_thresholds: ProfileThresholds | None = None,
    source_name: str | None = None,
) -> DatasetRegistration:
    """Copy ``source`` into the workspace, validate, profile, and create its holdout once."""
    suffix = suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError(f"unsupported file type {suffix!r}; expected {ALLOWED_SUFFIXES}")
    dataset_id = rec.new_id("ds-")
    ds_dir = ws.datasets_dir / dataset_id
    ds_dir.mkdir(parents=True)
    try:
        data_path = ds_dir / f"data{suffix}"
        shutil.copyfile(source, data_path)
        dataset = load_dataset(data_path, schema)
        profile = profile_dataset(dataset, profile_thresholds)
        holdout = get_or_create_holdout(
            dataset, holdout_config or HoldoutConfig(), ds_dir / "holdout.json"
        )
    except Exception:
        shutil.rmtree(ds_dir, ignore_errors=True)
        raise
    reg = DatasetRegistration(
        dataset_id=dataset_id,
        created_at=rec.utc_now(),
        source_name=source_name or Path(source).name,
        sha256=dataset.sha256,
        n_rows=dataset.n_rows,
        n_features=profile.n_features,
        positive_rate=profile.class_balance.positive_rate,
        dataset_schema=schema,
        holdout_config=holdout.config,
        n_outer_train=len(holdout.train_idx),
        n_test=len(holdout.test_idx),
        test_sha256=holdout.test_sha256,
        n_warnings=len(profile.warnings),
        notes=list(dataset.notes),
    )
    rec.write_json(ds_dir / "profile.json", profile.model_dump(mode="json"))
    rec.write_json(ds_dir / "dataset.json", reg.model_dump(mode="json"))
    return reg


def get_registration(ws: Workspace, dataset_id: str) -> DatasetRegistration:
    return DatasetRegistration.model_validate(
        rec.read_json(ws.dataset_dir(dataset_id) / "dataset.json")
    )


def list_datasets(ws: Workspace) -> list[DatasetRegistration]:
    out: list[DatasetRegistration] = []
    if not ws.datasets_dir.is_dir():
        return out
    for p in sorted(ws.datasets_dir.iterdir()):
        if (p / "dataset.json").is_file():
            out.append(DatasetRegistration.model_validate(rec.read_json(p / "dataset.json")))
    return out


def get_profile(ws: Workspace, dataset_id: str) -> dict[str, Any]:
    return dict(rec.read_json(ws.dataset_dir(dataset_id) / "profile.json"))


def load_registered(
    ws: Workspace, dataset_id: str
) -> tuple[LoadedDataset, Holdout, DatasetProfile]:
    """Reload a registered dataset with its stored (never re-drawn) holdout."""
    ds_dir = ws.dataset_dir(dataset_id)
    reg = get_registration(ws, dataset_id)
    data_path = next(p for p in ds_dir.iterdir() if p.stem == "data")
    dataset = load_dataset(data_path, reg.dataset_schema)
    holdout = get_or_create_holdout(dataset, reg.holdout_config, ds_dir / "holdout.json")
    profile = DatasetProfile.model_validate(rec.read_json(ds_dir / "profile.json"))
    return dataset, holdout, profile


# --------------------------------------------------------------------------- runs


def run_brief(record: rec.RunRecord) -> dict[str, Any]:
    run = record.run
    best = None
    if run.get("status") == "completed":
        best = record.summary.get("best_candidate_by_mean_oof_ap")
    return {
        "run_id": run["run_id"],
        "status": run["status"],
        "dataset_id": run.get("dataset_id"),
        "created_at": run["created_at"],
        "finished_at": run.get("finished_at"),
        "models": run["models"],
        "best_candidate_by_mean_oof_ap": best,
        "has_final_evaluation": record.final_evaluation is not None,
        "error": run.get("error"),
    }


def start_run(ws: Workspace, dataset_id: str, config: ExperimentConfig) -> dict[str, Any]:
    """Run an experiment synchronously and return its brief."""
    dataset, holdout, profile = load_registered(ws, dataset_id)
    result = run_experiment(
        dataset, holdout, config, ws.runs_dir, profile=profile, dataset_id=dataset_id
    )
    return run_brief(rec.RunRecord(result.run_dir))


def list_runs(ws: Workspace) -> list[dict[str, Any]]:
    store = rec.RunStore(ws.runs_dir)
    return [run_brief(rec.RunRecord(store.path(r))) for r in store.list()]


def get_run(ws: Workspace, run_id: str) -> dict[str, Any]:
    record = rec.RunRecord(ws.run_dir(run_id))
    completed = record.run.get("status") == "completed"
    return {
        "run": record.run,
        "config": record.config,
        "summary": record.summary if completed else None,
        "thresholds": record.thresholds,
        "final_evaluation": record.final_evaluation,
    }


def analyse_thresholds(
    ws: Workspace, run_id: str, model: str, strategy: ThresholdStrategy
) -> dict[str, Any]:
    return run_threshold_analysis(ws.run_dir(run_id), model, strategy)


def finalize_run(
    ws: Workspace,
    run_id: str,
    model: str | None = None,
    force: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    """Final evaluation of a run on its dataset's stored test rows."""
    run_dir = ws.run_dir(run_id)
    dataset_id = rec.RunRecord(run_dir).run.get("dataset_id")
    if not dataset_id:
        raise rec.RecordNotFoundError("run has no registered dataset_id")
    dataset, _, _ = load_registered(ws, dataset_id)
    result = final_evaluate(dataset, run_dir, model=model, force=force, reason=reason)
    return result.record


def report_path(ws: Workspace, run_id: str, fmt: str = "html") -> Path:
    """(Re)generate the run's report from its records and return the requested file."""
    paths = generate_report(ws.run_dir(run_id))
    return paths.html if fmt == "html" else paths.markdown
