"""Persist refit pipelines with metadata, load them safely, and predict.

Security note: joblib artifacts are pickles. Only load artifacts this workspace produced. The
artifact's SHA-256 (stored in its metadata) is verified *before* unpickling, so an artifact
replaced on disk is rejected rather than executed.
"""

import hashlib
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel

from imbalancelab.pipelines.builder import FeatureSpec
from imbalancelab.tracking import records as rec

ARTIFACT_FILE = "model.joblib"
METADATA_FILE = "metadata.json"
VERSION_CHECKED = ("numpy", "pandas", "scikit-learn", "imbalanced-learn", "joblib")


class ModelIntegrityError(RuntimeError):
    """The artifact on disk does not match its recorded SHA-256."""


class InputSchemaError(ValueError):
    """Prediction input does not match the model's feature schema."""


class VersionMismatchWarning(UserWarning):
    """The artifact was saved with different library versions than are installed now."""


class ModelMetadata(BaseModel):
    model_id: str
    run_id: str
    model_name: str
    created_at: str
    threshold: float
    threshold_provenance: dict[str, Any]
    trained_on: str
    n_train_rows: int
    dataset_sha256: str
    test_sha256: str
    feature_spec: FeatureSpec
    environment: dict[str, Any]
    artifact_file: str
    artifact_sha256: str


@dataclass
class LoadedModel:
    pipeline: Any
    metadata: ModelMetadata
    warnings: list[str] = field(default_factory=list)


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_model(
    pipeline: Any,
    models_dir: Path,
    *,
    run_id: str,
    model_name: str,
    threshold: float,
    threshold_provenance: dict[str, Any],
    features: FeatureSpec,
    dataset_sha256: str,
    test_sha256: str,
    n_train_rows: int,
    model_id: str | None = None,
) -> ModelMetadata:
    """Write ``models_dir/<model_id>/{model.joblib, metadata.json}``."""
    model_id = rec.validate_id(model_id or rec.new_id("model-"))
    out = Path(models_dir) / model_id
    out.mkdir(parents=True, exist_ok=False)
    artifact = out / ARTIFACT_FILE
    joblib.dump(pipeline, artifact)
    meta = ModelMetadata(
        model_id=model_id,
        run_id=run_id,
        model_name=model_name,
        created_at=rec.utc_now(),
        threshold=threshold,
        threshold_provenance=threshold_provenance,
        trained_on="outer-train rows only",
        n_train_rows=n_train_rows,
        dataset_sha256=dataset_sha256,
        test_sha256=test_sha256,
        feature_spec=features,
        environment=rec.environment_info(),
        artifact_file=ARTIFACT_FILE,
        artifact_sha256=_sha256(artifact),
    )
    rec.write_json(out / METADATA_FILE, meta.model_dump(mode="json"))
    return meta


def read_metadata(models_dir: Path, model_id: str) -> ModelMetadata:
    path = Path(models_dir) / rec.validate_id(model_id) / METADATA_FILE
    if not path.is_file():
        raise rec.RecordNotFoundError(f"model {model_id!r} not found")
    return ModelMetadata.model_validate(rec.read_json(path))


def version_mismatches(saved: dict[str, Any], current: dict[str, Any]) -> list[str]:
    out = []
    if saved.get("python") != current.get("python"):
        out.append(f"python: saved {saved.get('python')}, installed {current.get('python')}")
    for pkg in VERSION_CHECKED:
        a, b = saved.get("packages", {}).get(pkg), current.get("packages", {}).get(pkg)
        if a != b:
            out.append(f"{pkg}: saved {a}, installed {b}")
    return out


def load_model(models_dir: Path, model_id: str) -> LoadedModel:
    """Verify the artifact hash, warn on version mismatch, then unpickle."""
    meta = read_metadata(models_dir, model_id)
    artifact = Path(models_dir) / meta.model_id / meta.artifact_file
    if not artifact.is_file() or _sha256(artifact) != meta.artifact_sha256:
        raise ModelIntegrityError(
            f"artifact for {model_id!r} is missing or fails its SHA-256 check"
        )
    mismatches = version_mismatches(meta.environment, rec.environment_info())
    for m in mismatches:
        warnings.warn(f"model {model_id}: {m}", VersionMismatchWarning, stacklevel=2)
    return LoadedModel(pipeline=joblib.load(artifact), metadata=meta, warnings=mismatches)


def validate_input(frame: pd.DataFrame, features: FeatureSpec) -> tuple[pd.DataFrame, list[str]]:
    """Check required columns and coerce numeric ones; return (frame, notes)."""
    notes: list[str] = []
    missing = [c for c in features.used if c not in frame.columns]
    if missing:
        raise InputSchemaError(f"missing required feature columns: {missing}")
    extra = [c for c in frame.columns if c not in features.used]
    if extra:
        notes.append(f"ignored columns not used by the model: {sorted(map(str, extra))}")
    out = frame[features.used].copy()
    bad: list[str] = []
    for col in features.numeric:
        try:
            out[col] = pd.to_numeric(out[col], errors="raise").astype(float)
        except (ValueError, TypeError):
            bad.append(col)
    if bad:
        raise InputSchemaError(f"non-numeric values in numeric feature columns: {bad}")
    for col in features.categorical:
        out[col] = out[col].astype(object)
    return out, notes


def predict(model: LoadedModel, data: pd.DataFrame | list[dict[str, Any]]) -> pd.DataFrame:
    """Probabilities of the positive class and labels at the stored threshold."""
    frame = data if isinstance(data, pd.DataFrame) else pd.DataFrame(list(data))
    if frame.empty:
        raise InputSchemaError("no records to predict")
    X, _ = validate_input(frame, model.metadata.feature_spec)
    proba = model.pipeline.predict_proba(X)
    classes = list(model.pipeline.classes_)
    p = np.asarray(proba[:, classes.index(1)], dtype=float)
    return pd.DataFrame({"probability": p, "label": (p >= model.metadata.threshold).astype(int)})
