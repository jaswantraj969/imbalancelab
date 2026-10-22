import ast
import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import make_imbalanced_frame
from imbalancelab import __version__
from imbalancelab.api.app import create_app
from imbalancelab.config import Settings

SCHEMA = {"target": "label", "positive_label": "yes", "id_column": "row_id"}
FAST_CONFIG = {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 2}}


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        datasets_dir=tmp_path / "ws" / "datasets",
        runs_dir=tmp_path / "ws" / "runs",
        models_dir=tmp_path / "ws" / "models",
        max_upload_bytes=200_000,
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def _csv_bytes(n: int = 260, seed: int = 21) -> bytes:
    return make_imbalanced_frame(n=n, seed=seed).to_csv(index=False).encode()


def _upload(
    client: TestClient,
    data: bytes | None = None,
    name: str = "data.csv",
    schema: dict | str = SCHEMA,
    holdout: dict | None = None,
):
    form = {"schema": schema if isinstance(schema, str) else json.dumps(schema)}
    if holdout is not None:
        form["holdout"] = json.dumps(holdout)
    files = {"file": (name, io.BytesIO(_csv_bytes() if data is None else data), "text/csv")}
    return client.post("/datasets", data=form, files=files)


@pytest.fixture
def dataset_id(client: TestClient) -> str:
    resp = _upload(client, name="upload.csv", holdout={"test_size": 0.25, "seed": 3})
    assert resp.status_code == 201, resp.text
    return resp.json()["dataset_id"]


@pytest.fixture
def run_id(client: TestClient, dataset_id: str) -> str:
    resp = client.post("/runs", json={"dataset_id": dataset_id, "config": FAST_CONFIG})
    assert resp.status_code == 201, resp.text
    return resp.json()["run_id"]


def test_health(client) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200 and resp.json() == {"status": "ok", "version": __version__}


def test_dataset_upload_profile_and_list(client, dataset_id, settings) -> None:
    reg = client.get("/datasets").json()
    assert [d["dataset_id"] for d in reg] == [dataset_id]
    d = reg[0]
    assert d["n_rows"] == 260 and d["source_name"] == "upload.csv" and len(d["sha256"]) == 64
    assert d["holdout_config"]["test_size"] == 0.25 and d["n_test"] + d["n_outer_train"] == 260
    profile = client.get(f"/datasets/{dataset_id}/profile")
    assert profile.status_code == 200
    assert profile.json()["class_balance"]["n_rows"] == 260
    stored = settings.datasets_dir / dataset_id
    assert {p.name for p in stored.iterdir()} == {
        "data.csv",
        "dataset.json",
        "holdout.json",
        "profile.json",
    }
    assert list((settings.datasets_dir / "_incoming").iterdir()) == []  # temp upload removed


def test_upload_validation_errors(client, settings) -> None:
    bad_json = _upload(client, schema="{not json")
    assert bad_json.status_code == 422 and "not valid JSON" in bad_json.text
    bad_schema = _upload(client, schema={"target": "label"})
    assert bad_schema.status_code == 422
    wrong_ext = _upload(client, name="data.xlsx")
    assert wrong_ext.status_code == 422
    missing = _upload(client, schema={**SCHEMA, "target": "nope"})
    assert missing.status_code == 422 and missing.json()["error"] == "data_validation_error"
    empty = _upload(client, data=b"")
    assert empty.status_code == 422
    too_big = _upload(client, data=b"a,b\n" + b"1,2\n" * 60_000)
    assert too_big.status_code == 413
    single = _upload(
        client,
        data=b"label,x\nyes,1\nyes,2\nno,3\n",
        schema={"target": "label", "positive_label": "yes"},
    )
    assert single.status_code == 422 and single.json()["error"] == "split_error"
    # failed registrations leave nothing behind
    assert [p.name for p in settings.datasets_dir.iterdir()] == ["_incoming"]
    assert list((settings.datasets_dir / "_incoming").iterdir()) == []


def test_client_filename_cannot_escape_workspace(client, settings, tmp_path) -> None:
    resp = _upload(client, name="../../../evil.csv")
    assert resp.status_code == 201
    assert resp.json()["source_name"] == "evil.csv"
    assert not (tmp_path / "evil.csv").exists()
    assert not any(p.name == "evil.csv" for p in tmp_path.rglob("*"))


def test_invalid_and_unknown_ids(client) -> None:
    assert client.get("/datasets/..%5C..%5Cx/profile").status_code == 400
    assert client.get("/datasets/ds-missing/profile").status_code == 404
    assert client.get("/runs/run-missing").status_code == 404
    assert client.get("/runs/bad.id").status_code == 400
    unknown = client.post("/runs", json={"dataset_id": "ds-nope", "config": FAST_CONFIG})
    assert unknown.status_code == 404
    bad_cfg = client.post(
        "/runs", json={"dataset_id": "x", "config": {"candidates": [{"model": "xgboost"}]}}
    )
    assert bad_cfg.status_code == 422


def test_full_run_lifecycle(client, dataset_id, run_id) -> None:
    runs = client.get("/runs").json()
    assert [r["run_id"] for r in runs] == [run_id]
    assert runs[0]["status"] == "completed" and runs[0]["dataset_id"] == dataset_id
    detail = client.get(f"/runs/{run_id}").json()
    assert detail["run"]["holdout"]["test_sha256"]
    assert detail["summary"]["primary_metric"] == "average_precision"
    assert detail["run"]["dataset"]["source_name"] == "upload.csv"  # registered upload name
    assert detail["final_evaluation"] is None

    early = client.post(f"/runs/{run_id}/final-evaluation", json={"model": "hgb"})
    assert early.status_code == 409 and early.json()["error"] == "final_evaluation_precondition"

    th = client.post(
        f"/runs/{run_id}/thresholds",
        json={"model": "hgb", "strategy": {"kind": "max_fbeta", "beta": 2}},
    )
    assert th.status_code == 200, th.text
    assert len(th.json()["per_repeat"]) == 2
    bad_th = client.post(f"/runs/{run_id}/thresholds", json={"model": "nope"})
    assert bad_th.status_code == 422
    bad_strategy = client.post(
        f"/runs/{run_id}/thresholds", json={"model": "hgb", "strategy": {"kind": "target_recall"}}
    )
    assert bad_strategy.status_code == 422

    final = client.post(f"/runs/{run_id}/final-evaluation", json={"model": "hgb"})
    assert final.status_code == 200, final.text
    body = final.json()
    assert body["model"] == "hgb" and body["threshold"] == th.json()["chosen_threshold"]
    again = client.post(f"/runs/{run_id}/final-evaluation", json={"model": "hgb"})
    assert again.status_code == 409 and again.json()["error"] == "final_evaluation_exists"
    no_reason = client.post(f"/runs/{run_id}/final-evaluation", json={"force": True})
    assert no_reason.status_code == 409
    forced = client.post(
        f"/runs/{run_id}/final-evaluation",
        json={"model": "hgb", "force": True, "reason": "api test"},
    )
    assert forced.status_code == 200 and forced.json()["forced"] is True
    history = client.get(f"/runs/{run_id}").json()["test_scoring_history"]
    assert history["n_test_scorings"] == 2 and history["repeated_test_use"] is True
    assert history["forced_reevaluations"][0]["reason"] == "api test"

    html = client.get(f"/runs/{run_id}/report")
    assert html.status_code == 200 and html.headers["content-type"].startswith("text/html")
    assert "Final test evaluation" in html.text
    md = client.get(f"/runs/{run_id}/report", params={"format": "markdown"})
    assert md.status_code == 200 and md.headers["content-type"].startswith("text/markdown")
    assert md.text.startswith("# ImbalanceLab audit report")
    assert client.get(f"/runs/{run_id}/report", params={"format": "pdf"}).status_code == 422


def test_predict_unknown_model_is_404(client) -> None:
    resp = client.post("/models/model-x/predict", json={"records": [{"x_signal": 1.0}]})
    assert resp.status_code == 404
    assert client.post("/models/model-x/predict", json={"records": []}).status_code == 422


def test_routes_contain_no_ml_code() -> None:
    """Route module imports only web/validation code and the workflow layer."""
    import imbalancelab.api.app as app_module

    tree = ast.parse(Path(app_module.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"sklearn", "imblearn", "numpy", "pandas", "joblib"}
