"""End-to-end smoke test against a real uvicorn process.

    python scripts/smoke_api.py [--port 8765]

Starts `uvicorn imbalancelab.api.app:app` in a subprocess with a temporary workspace, then:
GET /health -> POST /datasets (synthetic CSV, clearly labelled synthetic) -> POST /runs ->
POST thresholds -> POST final-evaluation -> GET report. Prints each real response.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests


def synthetic_csv(path: Path, n: int = 400, seed: int = 0) -> None:
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.1).astype(int)
    pd.DataFrame(
        {
            "x1": rng.normal(size=n) + 1.2 * y,
            "x2": rng.normal(size=n),
            "cat": rng.choice(["a", "b", "c"], size=n),
            "label": y,
        }
    ).to_csv(path, index=False)


def show(title: str, resp: requests.Response, max_chars: int = 1500) -> None:
    print(f"\n### {title}\n{resp.request.method} {resp.request.url} -> HTTP {resp.status_code}")
    ctype = resp.headers.get("content-type", "")
    print(f"content-type: {ctype}")
    body = json.dumps(resp.json(), indent=2) if "json" in ctype else resp.text
    print(body[:max_chars] + ("\n... [truncated]" if len(body) > max_chars else ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        env = {
            **os.environ,
            "IMBALANCELAB_DATASETS_DIR": str(root / "datasets"),
            "IMBALANCELAB_RUNS_DIR": str(root / "runs"),
            "IMBALANCELAB_MODELS_DIR": str(root / "models"),
        }
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "imbalancelab.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
        ]
        print("$ " + " ".join(cmd))
        server = subprocess.Popen(cmd, env=env, cwd=root)
        try:
            for _ in range(200):
                try:
                    requests.get(f"{base}/health", timeout=1)
                    break
                except requests.ConnectionError:
                    time.sleep(0.1)
            show("health", requests.get(f"{base}/health", timeout=10))

            csv = root / "synthetic_smoke.csv"
            synthetic_csv(csv)
            schema = {"target": "label", "positive_label": 1}
            with csv.open("rb") as fh:
                resp = requests.post(
                    f"{base}/datasets",
                    data={"schema": json.dumps(schema), "holdout": json.dumps({"test_size": 0.2})},
                    files={"file": ("synthetic_smoke.csv", fh, "text/csv")},
                    timeout=120,
                )
            show("upload synthetic CSV (SYNTHETIC DATA, smoke test only)", resp)
            dataset_id = resp.json()["dataset_id"]

            config: dict[str, Any] = {
                "candidates": [{"model": "hgb"}],
                "cv": {"n_splits": 3, "n_repeats": 2},
            }
            resp = requests.post(
                f"{base}/runs", json={"dataset_id": dataset_id, "config": config}, timeout=600
            )
            show("launch run", resp)
            run_id = resp.json()["run_id"]

            resp = requests.post(
                f"{base}/runs/{run_id}/thresholds",
                json={"model": "hgb", "strategy": {"kind": "max_fbeta", "beta": 2}},
                timeout=120,
            )
            show("threshold analysis (OOF)", resp, max_chars=800)
            resp = requests.post(
                f"{base}/runs/{run_id}/final-evaluation", json={"model": "hgb"}, timeout=600
            )
            show("final evaluation", resp, max_chars=800)
            resp = requests.post(
                f"{base}/runs/{run_id}/final-evaluation", json={"model": "hgb"}, timeout=60
            )
            show("second final evaluation (must be refused)", resp)
            resp = requests.get(
                f"{base}/runs/{run_id}/report", params={"format": "markdown"}, timeout=120
            )
            show("report (markdown)", resp, max_chars=2500)
            html = requests.get(f"{base}/runs/{run_id}/report", timeout=120)
            print(
                f"\nGET report html -> HTTP {html.status_code}, {len(html.text)} chars, "
                f"content-type {html.headers['content-type']}"
            )
        finally:
            server.terminate()
            server.wait(timeout=20)
    return 0


if __name__ == "__main__":
    sys.exit(main())
