import io
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from conftest import make_imbalanced_frame
from imbalancelab.api.app import create_app
from imbalancelab.config import Settings
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import final_evaluate
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.models.persistence import (
    InputSchemaError,
    ModelIntegrityError,
    VersionMismatchWarning,
    load_model,
    predict,
    read_metadata,
    save_model,
    validate_input,
)
from imbalancelab.splitting import make_holdout
from imbalancelab.tracking import RecordNotFoundError

SCHEMA = {"target": "label", "positive_label": "yes", "id_column": "row_id"}


@pytest.fixture
def finalized(write_csv, tmp_path):
    ds = load_dataset(
        write_csv(make_imbalanced_frame(n=260, seed=21)), DatasetSchema.model_validate(SCHEMA)
    )
    holdout = make_holdout(ds)
    cfg = ExperimentConfig.model_validate(
        {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 1}}
    )
    run_dir = run_experiment(ds, holdout, cfg, tmp_path / "runs").run_dir
    run_threshold_analysis(run_dir, "hgb", ThresholdStrategy())
    result = final_evaluate(ds, run_dir, "hgb")
    meta = save_model(
        result.pipeline,
        tmp_path / "models",
        run_id=result.record["run_id"],
        model_name="hgb",
        threshold=result.threshold,
        threshold_provenance=result.record["threshold_provenance"],
        features=result.features,
        dataset_sha256=ds.sha256,
        test_sha256=holdout.test_sha256,
        n_train_rows=len(holdout.train_idx),
    )
    return ds, holdout, result, meta, tmp_path / "models"


def test_round_trip_predictions_identical(finalized) -> None:
    ds, holdout, result, meta, models_dir = finalized
    loaded = load_model(models_dir, meta.model_id)
    assert loaded.warnings == []
    X = ds.frame.iloc[holdout.test_idx]
    expected = result.pipeline.predict_proba(X)[:, 1]
    out = predict(loaded, X)
    np.testing.assert_array_equal(out["probability"].to_numpy(), expected)
    np.testing.assert_array_equal(out["label"].to_numpy(), (expected >= meta.threshold).astype(int))
    # stored test predictions from the final evaluation match the reloaded artifact exactly
    run_dir = models_dir.parent / "runs" / result.record["run_id"]
    stored = pd.read_parquet(run_dir / "final_predictions.parquet")
    hgb = stored[stored["model"] == "hgb"].sort_values("row_index")
    np.testing.assert_array_equal(hgb["y_score"].to_numpy(), expected)


def test_metadata_contents(finalized) -> None:
    _, holdout, result, meta, models_dir = finalized
    on_disk = read_metadata(models_dir, meta.model_id)
    assert on_disk == meta
    assert meta.trained_on == "outer-train rows only"
    assert meta.n_train_rows == len(holdout.train_idx)
    assert meta.threshold == result.threshold and meta.run_id == result.record["run_id"]
    assert meta.threshold_provenance["source"] == "out-of-fold predictions"
    assert len(meta.artifact_sha256) == 64 and meta.environment["packages"]["scikit-learn"]
    assert meta.feature_spec.used == result.features.used


def test_tampered_artifact_is_rejected_before_unpickling(finalized) -> None:
    _, _, _, meta, models_dir = finalized
    artifact = models_dir / meta.model_id / "model.joblib"
    artifact.write_bytes(artifact.read_bytes() + b"tampered")
    with pytest.raises(ModelIntegrityError):
        load_model(models_dir, meta.model_id)
    artifact.unlink()
    with pytest.raises(ModelIntegrityError):
        load_model(models_dir, meta.model_id)
    with pytest.raises(RecordNotFoundError):
        load_model(models_dir, "model-missing")


def test_version_mismatch_warns(finalized) -> None:
    _, _, _, meta, models_dir = finalized
    path = models_dir / meta.model_id / "metadata.json"
    data = json.loads(path.read_text())
    data["environment"]["packages"]["scikit-learn"] = "0.0.1"
    data["environment"]["python"] = "3.0.0"
    path.write_text(json.dumps(data))
    with pytest.warns(VersionMismatchWarning) as caught:
        loaded = load_model(models_dir, meta.model_id)
    messages = sorted(str(w.message) for w in caught)
    assert len(messages) == 2
    assert "python: saved 3.0.0" in messages[0] and "scikit-learn: saved 0.0.1" in messages[1]
    assert len(loaded.warnings) == 2


def test_input_validation(finalized) -> None:
    ds, holdout, _, meta, models_dir = finalized
    loaded = load_model(models_dir, meta.model_id)
    X = ds.frame.iloc[holdout.test_idx[:5]]
    with pytest.raises(InputSchemaError, match="missing"):
        predict(loaded, X.drop(columns=["x_signal"]))
    bad = X.copy()
    bad["x_noise"] = bad["x_noise"].astype(object)
    bad.iloc[0, bad.columns.get_loc("x_noise")] = "not a number"
    with pytest.raises(InputSchemaError, match="non-numeric"):
        predict(loaded, bad)
    with pytest.raises(InputSchemaError, match="no records"):
        predict(loaded, [])
    extra = X.assign(unexpected=1)
    _, notes = validate_input(extra, meta.feature_spec)
    assert any("unexpected" in n for n in notes)
    as_records = json.loads(X.to_json(orient="records"))
    as_records[0]["color"] = "never-seen-category"
    out = predict(loaded, as_records)  # numeric strings/ints coerced; unknown category ignored
    assert len(out) == 5 and out["probability"].between(0, 1).all()


# ------------------------------------------------------------------------------ API


def test_api_final_evaluation_persists_and_predicts(tmp_path) -> None:
    settings = Settings(
        _env_file=None,
        datasets_dir=tmp_path / "d",
        runs_dir=tmp_path / "r",
        models_dir=tmp_path / "m",
    )
    client = TestClient(create_app(settings))
    frame = make_imbalanced_frame(n=260, seed=21)
    files = {"file": ("data.csv", io.BytesIO(frame.to_csv(index=False).encode()), "text/csv")}
    ds_id = client.post("/datasets", data={"schema": json.dumps(SCHEMA)}, files=files).json()[
        "dataset_id"
    ]
    run_id = client.post(
        "/runs",
        json={
            "dataset_id": ds_id,
            "config": {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 1}},
        },
    ).json()["run_id"]
    client.post(f"/runs/{run_id}/thresholds", json={"model": "hgb"})
    final = client.post(f"/runs/{run_id}/final-evaluation", json={"model": "hgb"}).json()
    model_id = final["model_id"]
    assert final["persisted_model_id"] == model_id
    detail = client.get(f"/runs/{run_id}").json()
    assert detail["final_evaluation"]["persisted_model_id"] == model_id
    assert [m["model_id"] for m in client.get("/models").json()] == [model_id]

    records = json.loads(frame.drop(columns=["label"]).head(4).to_json(orient="records"))
    resp = client.post(f"/models/{model_id}/predict", json={"records": records})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["threshold"] == final["threshold"] and len(body["predictions"]) == 4
    assert any("ignored columns" in w for w in body["warnings"])  # row_id, group, ts unused
    loaded = load_model(settings.models_dir, model_id)
    expected = predict(loaded, records)
    got = [p["probability"] for p in body["predictions"]]
    np.testing.assert_allclose(got, expected["probability"].to_numpy(), rtol=0, atol=1e-12)

    missing = client.post(f"/models/{model_id}/predict", json={"records": [{"x_signal": 1}]})
    assert missing.status_code == 422 and missing.json()["error"] == "input_schema_error"
    nopersist = client.post(
        f"/runs/{run_id}/final-evaluation",
        json={"force": True, "reason": "t", "persist_model": False},
    ).json()
    assert "model_id" not in nopersist
    (settings.models_dir / model_id / "model.joblib").write_bytes(b"x")
    tampered = client.post(f"/models/{model_id}/predict", json={"records": records})
    assert tampered.status_code == 409 and tampered.json()["error"] == "model_integrity_error"
