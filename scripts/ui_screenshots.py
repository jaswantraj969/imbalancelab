"""Drive every Streamlit page against a live API with a headless browser; save screenshots.

    pip install playwright        # optional dev tool, not a project dependency
    python scripts/ui_screenshots.py

Starts uvicorn (temporary workspace) and Streamlit as subprocesses, then uses Playwright with
the locally installed Microsoft Edge (``channel="msedge"``; no browser download needed). Uses a
SYNTHETIC dataset. Writes docs/screenshots/*.png and docs/screenshots/ui_check.json (per page:
error elements found, browser console errors). Exit code 0 only if no page shows an unexpected
error.
"""

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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
API_PORT, UI_PORT = 8766, 8502


def synthetic_csv(path: Path, n: int = 600, seed: int = 0) -> None:
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


def wait_http(url: str, timeout: float = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if requests.get(url, timeout=2).status_code < 500:
                return
        except requests.ConnectionError:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"{url} did not come up")


def main() -> int:
    from playwright.sync_api import sync_playwright

    OUT.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        csv = root / "synthetic_ui_demo.csv"
        synthetic_csv(csv)
        env = {
            **os.environ,
            "IMBALANCELAB_DATASETS_DIR": str(root / "datasets"),
            "IMBALANCELAB_RUNS_DIR": str(root / "runs"),
            "IMBALANCELAB_MODELS_DIR": str(root / "models"),
            "IMBALANCELAB_API_URL": f"http://127.0.0.1:{API_PORT}",
        }
        api = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "imbalancelab.api.app:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(API_PORT),
                "--log-level",
                "warning",
            ],
            env=env,
            cwd=root,
        )
        ui = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(ROOT / "frontend" / "app.py"),
                "--server.headless",
                "true",
                "--server.port",
                str(UI_PORT),
                "--browser.gatherUsageStats",
                "false",
            ],
            env=env,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_http(f"http://127.0.0.1:{API_PORT}/health")
            wait_http(f"http://127.0.0.1:{UI_PORT}")
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel="msedge", headless=True)
                # tall viewport: Streamlit scrolls inside its own container, so full_page alone
                # would only capture the first screen
                page = browser.new_page(viewport={"width": 1400, "height": 2400})
                console: list[str] = []
                page.on(
                    "console",
                    lambda m: console.append(m.text) if m.type == "error" else None,
                )
                page.goto(f"http://127.0.0.1:{UI_PORT}")
                page.get_by_text("API ok").wait_for(timeout=60_000)

                def settle() -> None:
                    page.wait_for_timeout(500)
                    page.locator('[data-testid="stStatusWidget"]').wait_for(
                        state="hidden", timeout=600_000
                    )
                    page.wait_for_timeout(800)

                def record(name: str, expected_errors: int = 0) -> None:
                    settle()
                    errors = page.locator('[data-testid="stAlertContentError"]').all_inner_texts()
                    exceptions = page.locator('[data-testid="stException"]').all_inner_texts()
                    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
                    checks.append(
                        {
                            "screenshot": f"{name}.png",
                            "error_elements": errors,
                            "exceptions": exceptions,
                            "console_errors": list(console),
                            "expected_error_elements": expected_errors,
                            "ok": len(exceptions) == 0 and len(errors) == expected_errors,
                        }
                    )
                    print(
                        f"{name}: errors={errors} exceptions={len(exceptions)} "
                        f"console_errors={len(console)}"
                    )
                    console.clear()

                def goto(label: str) -> None:
                    page.locator('[data-testid="stSidebar"]').get_by_text(label, exact=True).click()
                    settle()

                def choose(select_label: str, option: str) -> None:
                    box = page.locator('[data-testid="stSelectbox"]').filter(has_text=select_label)
                    box.first.click()
                    page.get_by_role("option", name=option, exact=True).click()
                    settle()

                # 1. upload + profile
                goto("Upload & profile")
                page.locator('input[type="file"]').set_input_files(str(csv))
                page.get_by_label("Target column").fill("label")
                page.get_by_label("Positive label").fill("1")
                page.get_by_role("button", name="Register dataset").click()
                page.get_by_text("Registered ds-").wait_for(timeout=120_000)
                record("01_upload_and_profile")

                # 2. run experiment
                goto("Run experiment")
                for label, value in (("Folds", "3"), ("Repeats", "2")):
                    field = page.get_by_label(label, exact=True)
                    field.fill(value)
                    field.press("Enter")
                    settle()
                page.get_by_role("button", name="Launch run").click()
                page.get_by_text("completed.").wait_for(timeout=600_000)
                record("02_run_experiment")

                # 3. results + thresholds
                goto("Results & thresholds")
                choose("Model", "hgb")
                page.get_by_role("button", name="Select threshold").click()
                page.get_by_text("Chosen threshold").wait_for(timeout=120_000)
                record("03_results_and_thresholds")

                # 4. final evaluation, then a second attempt that must be refused (409)
                goto("Final evaluation")
                page.get_by_role("button", name="Run final evaluation").click()
                page.get_by_text("Test set scored once").wait_for(timeout=600_000)
                record("04_final_evaluation")
                page.reload()
                page.get_by_text("API ok").wait_for(timeout=60_000)
                goto("Final evaluation")
                page.get_by_role("button", name="Run final evaluation").click()
                page.get_by_text("API error 409").wait_for(timeout=60_000)
                record("05_final_evaluation_refused", expected_errors=1)

                # 5. report
                goto("Report")
                page.frame_locator("iframe").first.get_by_text(
                    "ImbalanceLab audit report"
                ).first.wait_for(timeout=120_000)
                record("06_report")
                browser.close()
        finally:
            for proc in (ui, api):
                proc.terminate()
                proc.wait(timeout=20)
    (OUT / "ui_check.json").write_text(json.dumps(checks, indent=2) + "\n")
    ok = all(c["ok"] for c in checks) and len(checks) == 6
    print("ALL PAGES OK" if ok else "SOME PAGES FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
