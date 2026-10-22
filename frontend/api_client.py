"""HTTP client for the ImbalanceLab API. The frontend talks to the backend only through this.

This module must never import ``imbalancelab``: the UI is a pure API client.
"""

import json
import os
from typing import Any

import requests

DEFAULT_API_URL = "http://localhost:8000"
API_URL_ENV = "IMBALANCELAB_API_URL"


def api_url_from_env() -> str:
    return os.environ.get(API_URL_ENV, DEFAULT_API_URL).rstrip("/")


class ApiError(Exception):
    def __init__(self, status: int, error: str, detail: str) -> None:
        self.status, self.error, self.detail = status, error, detail
        super().__init__(f"HTTP {status} {error}: {detail}")


class ApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 1800.0) -> None:
        self.base_url = (base_url or api_url_from_env()).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        resp = self.session.request(
            method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs
        )
        if resp.status_code >= 400:
            try:
                body = resp.json()
                error = str(body.get("error", "http_error"))
                detail = body.get("detail", resp.text)
            except ValueError:
                error, detail = "http_error", resp.text
            raise ApiError(resp.status_code, error, str(detail))
        return resp

    def _json(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._request(method, path, **kwargs).json()

    def health(self) -> dict[str, Any]:
        return dict(self._json("GET", "/health"))

    def upload_dataset(
        self,
        file_name: str,
        data: bytes,
        schema: dict[str, Any],
        holdout: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        form = {"schema": json.dumps(schema)}
        if holdout:
            form["holdout"] = json.dumps(holdout)
        files = {"file": (file_name, data)}
        return dict(self._json("POST", "/datasets", data=form, files=files))

    def list_datasets(self) -> list[dict[str, Any]]:
        return list(self._json("GET", "/datasets"))

    def profile(self, dataset_id: str) -> dict[str, Any]:
        return dict(self._json("GET", f"/datasets/{dataset_id}/profile"))

    def create_run(self, dataset_id: str, config: dict[str, Any]) -> dict[str, Any]:
        body = {"dataset_id": dataset_id, "config": config}
        return dict(self._json("POST", "/runs", json=body))

    def list_runs(self) -> list[dict[str, Any]]:
        return list(self._json("GET", "/runs"))

    def get_run(self, run_id: str) -> dict[str, Any]:
        return dict(self._json("GET", f"/runs/{run_id}"))

    def thresholds(self, run_id: str, model: str, strategy: dict[str, Any]) -> dict[str, Any]:
        body = {"model": model, "strategy": strategy}
        return dict(self._json("POST", f"/runs/{run_id}/thresholds", json=body))

    def final_evaluation(
        self,
        run_id: str,
        model: str | None = None,
        force: bool = False,
        reason: str | None = None,
    ) -> dict[str, Any]:
        body = {"model": model, "force": force, "reason": reason}
        return dict(self._json("POST", f"/runs/{run_id}/final-evaluation", json=body))

    def report(self, run_id: str, fmt: str = "html") -> str:
        return self._request("GET", f"/runs/{run_id}/report", params={"format": fmt}).text

    def predict(self, model_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
        body = {"records": records}
        return dict(self._json("POST", f"/models/{model_id}/predict", json=body))
