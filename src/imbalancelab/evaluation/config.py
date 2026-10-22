"""Experiment configuration."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from imbalancelab.models.registry import BASELINE_MODELS, ModelName
from imbalancelab.pipelines.builder import SamplerName
from imbalancelab.splitting.splits import CVConfig


class CandidateSpec(BaseModel):
    """A model plus an optional sampler; ``name`` identifies it throughout a run."""

    model_config = ConfigDict(extra="forbid")

    model: ModelName
    sampler: SamplerName = "none"

    @property
    def name(self) -> str:
        return self.model if self.sampler == "none" else f"{self.model}+{self.sampler}"


class ExperimentConfig(BaseModel):
    """What to run. The baselines (``BASELINE_MODELS``, no sampler) are always added."""

    model_config = ConfigDict(extra="forbid")

    candidates: list[CandidateSpec] = Field(default_factory=lambda: [CandidateSpec(model="hgb")])
    cv: CVConfig = Field(default_factory=CVConfig)
    seed: int = 42  # estimator and sampler seed
    threshold: float = Field(default=0.5, gt=0, lt=1)  # reference threshold for CV metrics
    beta: float = Field(default=1.0, gt=0)
    smote_k_neighbors: int = Field(default=5, ge=1)

    @field_validator("candidates")
    @classmethod
    def _unique_names(cls, value: list[CandidateSpec]) -> list[CandidateSpec]:
        names = [c.name for c in value]
        if len(names) != len(set(names)):
            raise ValueError(f"duplicate candidate names: {names}")
        return value

    def all_specs(self) -> list[CandidateSpec]:
        """Baselines first, then candidates (a candidate equal to a baseline is not repeated)."""
        specs = [CandidateSpec(model=m) for m in BASELINE_MODELS]
        names = {s.name for s in specs}
        return specs + [c for c in self.candidates if c.name not in names]

    def baseline_names(self) -> list[str]:
        return list(BASELINE_MODELS)

    def candidate_names(self) -> list[str]:
        baselines = set(BASELINE_MODELS)
        return [s.name for s in self.all_specs() if s.name not in baselines]
