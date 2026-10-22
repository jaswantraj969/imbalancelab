"""Pydantic request/response models for the HTTP API."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.thresholds import ThresholdStrategy


class Health(BaseModel):
    status: str
    version: str


class ErrorBody(BaseModel):
    error: str
    detail: str


class RunCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: str
    config: ExperimentConfig = Field(default_factory=ExperimentConfig)


class RunBrief(BaseModel):
    run_id: str
    status: str
    dataset_id: str | None
    created_at: str
    finished_at: str | None
    models: list[str]
    best_candidate_by_mean_oof_ap: str | None
    has_final_evaluation: bool
    error: str | None


class ThresholdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    strategy: ThresholdStrategy = Field(default_factory=ThresholdStrategy)


class FinalEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str | None = None
    force: bool = False
    reason: str | None = None
    persist_model: bool = True
    bootstrap_resamples: int = Field(default=2000, ge=100, le=20_000)
    bootstrap_seed: int = 42


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[dict[str, Any]] = Field(min_length=1, max_length=10_000)


class Prediction(BaseModel):
    probability: float
    label: int


class PredictResponse(BaseModel):
    model_id: str
    threshold: float
    predictions: list[Prediction]
    warnings: list[str] = Field(default_factory=list)
