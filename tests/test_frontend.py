import ast
import socket
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
import uvicorn

from conftest import make_imbalanced_frame
from imbalancelab.api.app import create_app
from imbalancelab.config import Settings

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
sys.path.insert(0, str(FRONTEND))

from api_client import ApiClient, ApiError, api_url_from_env  # noqa: E402

FAST_CONFIG = {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 2}}
SCHEMA = {"target": "label", "positive_label": "yes", "id_column": "row_id"}


def test_frontend_never_imports_imbalancelab() -> None:
    files = sorted(FRONTEND.glob("*.py"))
    assert {f.name for f in files} >= {"app.py", "api_client.py"}
    for f in files:
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "__import__":
                names = [getattr(a, "value", "") for a in node.args]
            assert not any(str(n).split(".")[0] == "imbalancelab" for n in names), f.name


def test_api_url_from_env(monkeypatch) -> None:
    monkeypatch.delenv("IMBALANCELAB_API_URL", raising=False)
    assert api_url_from_env() == "http://localhost:8000"
    monkeypatch.setenv("IMBALANCELAB_API_URL", "http://example:9000/")
    assert api_url_from_env() == "http://example:9000"
    assert ApiClient().base_url == "http://example:9000"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@pytest.fixture(scope="module")
def live_api(tmp_path_factory) -> Iterator[str]:
    root = tmp_path_factory.mktemp("ws")
    settings = Settings(
        _env_file=None,
        datasets_dir=root / "datasets",
        runs_dir=root / "runs",
        models_dir=root / "models",
    )
    port = _free_port()
    server = uvicorn.Server(
        uvicorn.Config(create_app(settings), host="127.0.0.1", port=port, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.time() + 20
    while not server.started:
        if time.time() > deadline:
            raise RuntimeError("uvicorn did not start")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture(scope="module")
def populated(live_api: str) -> dict[str, str]:
    client = ApiClient(live_api)
    data = make_imbalanced_frame(n=260, seed=21).to_csv(index=False).encode()
    reg = client.upload_dataset("demo.csv", data, SCHEMA, {"test_size": 0.25})
    run = client.create_run(reg["dataset_id"], FAST_CONFIG)
    client.thresholds(run["run_id"], "hgb", {"kind": "max_fbeta", "beta": 2.0})
    return {"dataset_id": reg["dataset_id"], "run_id": run["run_id"]}


def test_api_client_round_trip(live_api, populated) -> None:
    client = ApiClient(live_api)
    assert client.health()["status"] == "ok"
    assert [d["dataset_id"] for d in client.list_datasets()] == [populated["dataset_id"]]
    assert client.profile(populated["dataset_id"])["class_balance"]["n_rows"] == 260
    runs = client.list_runs()
    assert runs[0]["run_id"] == populated["run_id"]
    detail = client.get_run(populated["run_id"])
    assert detail["thresholds"]["analyses"]["hgb"]["provenance"] == "oof"
    assert client.report(populated["run_id"], "markdown").startswith("# ImbalanceLab")
    with pytest.raises(ApiError) as exc:
        client.get_run("run-missing")
    assert exc.value.status == 404 and exc.value.error == "not_found"
    with pytest.raises(ApiError) as exc2:
        client.predict("model-missing", [{"x": 1}])
    assert exc2.value.status == 404


def _app_test(live_api: str, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv("IMBALANCELAB_API_URL", live_api)
    monkeypatch.syspath_prepend(str(FRONTEND))
    return AppTest.from_file(str(FRONTEND / "app.py"), default_timeout=120)


@pytest.mark.parametrize(
    "page",
    ["Upload & profile", "Run experiment", "Results & thresholds", "Final evaluation", "Report"],
)
def test_every_page_renders_against_live_api(live_api, populated, monkeypatch, page) -> None:
    at = _app_test(live_api, monkeypatch).run()
    assert not at.exception
    assert any("API ok" in s.value for s in at.sidebar.success)
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception
    assert not at.error, [e.value for e in at.error]
    assert at.header[0].value


def test_app_reports_unreachable_api(monkeypatch) -> None:
    at = _app_test(f"http://127.0.0.1:{_free_port()}", monkeypatch).run()
    assert not at.exception
    assert any("unreachable" in e.value for e in at.sidebar.error)


def test_threshold_then_final_evaluation_through_ui(live_api, populated, monkeypatch) -> None:
    at = _app_test(live_api, monkeypatch).run()
    at.sidebar.radio[0].set_value("Results & thresholds").run()
    form_model = next(s for s in at.selectbox if s.label == "Model")
    form_model.set_value("hgb")
    next(s for s in at.selectbox if s.label == "Strategy").set_value("target_recall")
    at.button[0].click().run()
    assert not at.exception and not at.error, [e.value for e in at.error]
    assert any("Chosen threshold" in s.value for s in at.success)

    at.sidebar.radio[0].set_value("Final evaluation").run()
    next(b for b in at.button if b.label == "Run final evaluation").click().run()
    assert not at.exception and not at.error, [e.value for e in at.error]
    assert any("Test set scored once" in s.value for s in at.success)
    detail = ApiClient(live_api).get_run(populated["run_id"])
    assert detail["final_evaluation"]["threshold_provenance"]["strategy"]["kind"] == "target_recall"

    at.run()  # reload: the page now warns that a final evaluation exists
    assert any("already has a final evaluation" in w.value for w in at.warning)
    next(b for b in at.button if b.label == "Run final evaluation").click().run()
    assert any("409" in e.value for e in at.error)  # refused without force
