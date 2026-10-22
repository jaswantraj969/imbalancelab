"""FastAPI application. Handlers validate input and call :mod:`imbalancelab.workflow` only.

Execution is synchronous for the MVP: ``POST /runs`` and ``POST /runs/{id}/final-evaluation``
block until the work finishes. FastAPI runs these ``def`` handlers in a worker thread, so
other requests are still served meanwhile.
"""

import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import ValidationError

from imbalancelab import __version__, workflow
from imbalancelab.api.schemas import (
    FinalEvaluationRequest,
    Health,
    PredictRequest,
    PredictResponse,
    RunBrief,
    RunCreate,
    ThresholdRequest,
)
from imbalancelab.config import Settings
from imbalancelab.data.errors import DataValidationError
from imbalancelab.data.schema import DatasetSchema
from imbalancelab.evaluation.final import FinalEvaluationError, FinalEvaluationExistsError
from imbalancelab.evaluation.runner import RunError
from imbalancelab.evaluation.thresholds import ProvenanceError, ThresholdSelectionError
from imbalancelab.splitting.splits import HoldoutConfig, SplitError
from imbalancelab.tracking.records import InvalidIdError, RecordNotFoundError
from imbalancelab.workflow import DatasetRegistration, Workspace

_CHUNK = 1 << 20

# exception type -> (status code, short error code); first match wins
ERROR_MAP: list[tuple[type[Exception], int, str]] = [
    (InvalidIdError, 400, "invalid_id"),
    (RecordNotFoundError, 404, "not_found"),
    (FinalEvaluationExistsError, 409, "final_evaluation_exists"),
    (FinalEvaluationError, 409, "final_evaluation_precondition"),
    (ProvenanceError, 422, "provenance_error"),
    (ThresholdSelectionError, 422, "threshold_selection_error"),
    (DataValidationError, 422, "data_validation_error"),
    (SplitError, 422, "split_error"),
    (RunError, 422, "run_error"),
    (ValidationError, 422, "validation_error"),
    (ValueError, 422, "invalid_request"),
]


def _workspace(request: Request) -> Workspace:
    ws: Workspace = request.app.state.workspace
    return ws


WorkspaceDep = Annotated[Workspace, Depends(_workspace)]


def _parse_json_form(raw: str | None, model: Callable[..., Any], field: str) -> Any:
    if raw is None or raw == "":
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(422, detail=f"field {field!r} is not valid JSON: {exc}") from exc
    try:
        return model(**payload)
    except ValidationError as exc:
        raise HTTPException(422, detail=f"field {field!r}: {exc}") from exc


def _save_upload(upload: UploadFile, dest_dir: Path, limit: int) -> tuple[Path, str]:
    """Stream the upload to a temp file inside ``dest_dir``; never trust the client filename."""
    name = upload.filename or ""
    suffix = Path(name).suffix.lower()
    if suffix not in workflow.ALLOWED_SUFFIXES:
        raise HTTPException(422, detail=f"file must be one of {workflow.ALLOWED_SUFFIXES}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(suffix=suffix, dir=dest_dir)
    tmp = Path(tmp_name)
    size = 0
    with open(fd, "wb") as out:
        while chunk := upload.file.read(_CHUNK):
            size += len(chunk)
            if size > limit:
                out.close()
                tmp.unlink(missing_ok=True)
                raise HTTPException(413, detail=f"upload exceeds limit of {limit} bytes")
            out.write(chunk)
    if size == 0:
        tmp.unlink(missing_ok=True)
        raise HTTPException(422, detail="uploaded file is empty")
    return tmp, suffix


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(
        title="ImbalanceLab API",
        version=__version__,
        description="Leakage-safe experiments for imbalanced binary classification. "
        "Runs execute synchronously (MVP).",
    )
    app.state.settings = settings
    app.state.workspace = Workspace.from_settings(settings)

    for exc_type, status, code in ERROR_MAP:

        def _handler(
            request: Request, exc: Exception, status: int = status, code: str = code
        ) -> JSONResponse:
            return JSONResponse(status_code=status, content={"error": code, "detail": str(exc)})

        app.add_exception_handler(exc_type, _handler)

    @app.get("/health", response_model=Health)
    def health() -> Health:
        return Health(status="ok", version=__version__)

    @app.post("/datasets", response_model=DatasetRegistration, status_code=201)
    def create_dataset(
        ws: WorkspaceDep,
        file: Annotated[UploadFile, File(description="CSV or Parquet file")],
        schema_text: Annotated[str, Form(alias="schema", description="DatasetSchema as JSON")],
        holdout_json: Annotated[
            str | None, Form(alias="holdout", description="HoldoutConfig as JSON")
        ] = None,
    ) -> DatasetRegistration:
        ds_schema = _parse_json_form(schema_text, DatasetSchema, "schema")
        holdout_cfg = _parse_json_form(holdout_json, HoldoutConfig, "holdout")
        tmp, suffix = _save_upload(file, ws.datasets_dir / "_incoming", settings.max_upload_bytes)
        try:
            return workflow.register_dataset(
                ws,
                tmp,
                suffix,
                ds_schema,
                holdout_cfg,
                source_name=Path(file.filename or f"upload{suffix}").name,
            )
        finally:
            tmp.unlink(missing_ok=True)

    @app.get("/datasets", response_model=list[DatasetRegistration])
    def list_datasets(ws: WorkspaceDep) -> list[DatasetRegistration]:
        return workflow.list_datasets(ws)

    @app.get("/datasets/{dataset_id}/profile")
    def dataset_profile(ws: WorkspaceDep, dataset_id: str) -> dict[str, Any]:
        return workflow.get_profile(ws, dataset_id)

    @app.post("/runs", response_model=RunBrief, status_code=201)
    def create_run(ws: WorkspaceDep, body: RunCreate) -> dict[str, Any]:
        return workflow.start_run(ws, body.dataset_id, body.config)

    @app.get("/runs", response_model=list[RunBrief])
    def list_runs(ws: WorkspaceDep) -> list[dict[str, Any]]:
        return workflow.list_runs(ws)

    @app.get("/runs/{run_id}")
    def get_run(ws: WorkspaceDep, run_id: str) -> dict[str, Any]:
        return workflow.get_run(ws, run_id)

    @app.post("/runs/{run_id}/thresholds")
    def thresholds(ws: WorkspaceDep, run_id: str, body: ThresholdRequest) -> dict[str, Any]:
        return workflow.analyse_thresholds(ws, run_id, body.model, body.strategy)

    @app.post("/runs/{run_id}/final-evaluation")
    def final_evaluation(
        ws: WorkspaceDep, run_id: str, body: FinalEvaluationRequest
    ) -> dict[str, Any]:
        return workflow.finalize_run(
            ws, run_id, model=body.model, force=body.force, reason=body.reason
        )

    @app.get("/runs/{run_id}/report", response_model=None)
    def report(
        ws: WorkspaceDep,
        run_id: str,
        format: Annotated[str, Query(pattern="^(html|markdown)$")] = "html",
    ) -> HTMLResponse | PlainTextResponse:
        path = workflow.report_path(ws, run_id, format)
        text = path.read_text(encoding="utf-8")
        if format == "html":
            return HTMLResponse(text)
        return PlainTextResponse(text, media_type="text/markdown")

    @app.post("/models/{model_id}/predict", response_model=PredictResponse)
    def predict(ws: WorkspaceDep, model_id: str, body: PredictRequest) -> PredictResponse:
        raise RecordNotFoundError(f"model {model_id!r} not found (persistence arrives in M9)")

    return app


app = create_app()
