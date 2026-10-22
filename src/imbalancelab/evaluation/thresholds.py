"""Threshold curves and selection from out-of-fold or validation predictions only.

Predictions carry a provenance tag. Passing test-provenance predictions to any curve or
selection function raises :class:`ProvenanceError`. Thresholds are selected separately for each
CV repeat; the chosen threshold is the median of the per-repeat selections, and the spread is
reported.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Self

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, model_validator

from imbalancelab.tracking import records as rec

Provenance = Literal["oof", "validation", "test"]
SELECTABLE_PROVENANCE = ("oof", "validation")
StrategyKind = Literal["max_fbeta", "target_recall", "target_precision", "min_cost"]


class ProvenanceError(ValueError):
    """Predictions of the wrong provenance (e.g. test) were used for threshold selection."""


class ThresholdSelectionError(ValueError):
    """No threshold satisfies the strategy, or the predictions cannot support selection."""


@dataclass(frozen=True)
class PredictionSet:
    y_true: np.ndarray
    y_score: np.ndarray
    provenance: Provenance

    def __post_init__(self) -> None:
        if self.y_true.shape != self.y_score.shape:
            raise ValueError("y_true and y_score lengths differ")
        if self.provenance not in ("oof", "validation", "test"):
            raise ValueError(f"unknown provenance {self.provenance!r}")

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> "PredictionSet":
        provenances = set(frame["provenance"].unique())
        if len(provenances) != 1:
            raise ProvenanceError(f"mixed provenance in predictions: {sorted(provenances)}")
        return cls(
            y_true=frame["y_true"].to_numpy(dtype=int),
            y_score=frame["y_score"].to_numpy(dtype=float),
            provenance=provenances.pop(),
        )


def require_selectable(preds: PredictionSet) -> None:
    if preds.provenance not in SELECTABLE_PROVENANCE:
        raise ProvenanceError(
            f"threshold selection requires out-of-fold or validation predictions, got "
            f"{preds.provenance!r}; the test set may be scored only once, after selection"
        )


class ThresholdStrategy(BaseModel):
    kind: StrategyKind = "max_fbeta"
    beta: float = Field(default=1.0, gt=0)
    target: float | None = Field(default=None, gt=0, le=1)
    cost_fp: float = Field(default=1.0, ge=0)
    cost_fn: float = Field(default=1.0, ge=0)

    @model_validator(mode="after")
    def _target_needed(self) -> Self:
        if self.kind in ("target_recall", "target_precision") and self.target is None:
            raise ValueError(f"strategy {self.kind!r} requires target")
        if self.kind == "min_cost" and self.cost_fp == 0 and self.cost_fn == 0:
            raise ValueError("min_cost requires a non-zero cost")
        return self


class ThresholdChoice(BaseModel):
    threshold: float
    precision: float | None
    recall: float
    fbeta: float
    expected_cost: float
    tp: int
    fp: int
    fn: int
    tn: int


def threshold_curve(
    preds: PredictionSet, beta: float = 1.0, cost_fp: float = 1.0, cost_fn: float = 1.0
) -> pd.DataFrame:
    """Metrics at every distinct score used as threshold (``score >= t`` is positive).

    Rows are ordered by decreasing threshold. The first row is the "predict nothing" point
    (threshold just above the maximum score). Its precision is NaN.
    """
    require_selectable(preds)
    y, s = preds.y_true.astype(int), preds.y_score.astype(float)
    n_pos = int(y.sum())
    n = int(y.size)
    if n_pos == 0 or n_pos == n:
        raise ThresholdSelectionError("threshold selection needs both classes in y_true")
    order = np.argsort(-s, kind="mergesort")
    s_sorted, y_sorted = s[order], y[order]
    ends = np.r_[np.flatnonzero(np.diff(s_sorted) != 0), n - 1]
    tp = np.r_[0, np.cumsum(y_sorted)[ends]]
    fp = np.r_[0, np.cumsum(1 - y_sorted)[ends]]
    thresholds = np.r_[np.nextafter(s_sorted[0], np.inf), s_sorted[ends]]
    fn = n_pos - tp
    tn = (n - n_pos) - fp
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(tp + fp > 0, tp / (tp + fp), np.nan)
    recall = tp / n_pos
    b2 = beta * beta
    fbeta = (1 + b2) * tp / ((1 + b2) * tp + b2 * fn + fp)
    cost = (cost_fp * fp + cost_fn * fn) / n
    return pd.DataFrame(
        {
            "threshold": thresholds,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": precision,
            "recall": recall,
            "fbeta": fbeta,
            "expected_cost": cost,
        }
    )


def select_threshold(preds: PredictionSet, strategy: ThresholdStrategy) -> ThresholdChoice:
    """Select one threshold. Ties go to the highest threshold (fewest positive predictions)."""
    curve = threshold_curve(preds, strategy.beta, strategy.cost_fp, strategy.cost_fn)
    if strategy.kind == "max_fbeta":
        idx = int(np.argmax(curve["fbeta"].to_numpy()))
    elif strategy.kind == "min_cost":
        idx = int(np.argmin(curve["expected_cost"].to_numpy()))
    elif strategy.kind == "target_recall":
        ok = curve.index[curve["recall"] >= strategy.target]
        best = curve.loc[ok, "precision"].max()
        idx = int(curve.loc[ok][curve.loc[ok, "precision"] == best].index[0])
    else:
        ok = curve.index[curve["precision"] >= strategy.target]
        if len(ok) == 0:
            raise ThresholdSelectionError(f"no threshold reaches precision >= {strategy.target}")
        best = curve.loc[ok, "recall"].max()
        idx = int(curve.loc[ok][curve.loc[ok, "recall"] == best].index[0])
    row = curve.iloc[idx]
    return ThresholdChoice(
        threshold=float(row["threshold"]),
        precision=None if np.isnan(row["precision"]) else float(row["precision"]),
        recall=float(row["recall"]),
        fbeta=float(row["fbeta"]),
        expected_cost=float(row["expected_cost"]),
        tp=int(row["tp"]),
        fp=int(row["fp"]),
        fn=int(row["fn"]),
        tn=int(row["tn"]),
    )


def evaluate_threshold(
    preds: PredictionSet, threshold: float, strategy: ThresholdStrategy
) -> ThresholdChoice:
    """Metrics of a fixed threshold on ``preds`` (any provenance; nothing is selected)."""
    y, s = preds.y_true.astype(int), preds.y_score.astype(float)
    pred = s >= threshold
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1)))
    tn = int(np.sum(~pred & (y == 0)))
    b2 = strategy.beta**2
    denom = (1 + b2) * tp + b2 * fn + fp
    return ThresholdChoice(
        threshold=float(threshold),
        precision=tp / (tp + fp) if tp + fp else None,
        recall=tp / (tp + fn) if tp + fn else 0.0,
        fbeta=(1 + b2) * tp / denom if denom else 0.0,
        expected_cost=(strategy.cost_fp * fp + strategy.cost_fn * fn) / max(len(y), 1),
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
    )


def _spread(values: list[float | None]) -> dict[str, float | int | None]:
    arr = np.array([v for v in values if v is not None], dtype=float)
    return {
        "mean": float(arr.mean()) if arr.size else None,
        "std": float(arr.std(ddof=1)) if arr.size > 1 else None,
        "min": float(arr.min()) if arr.size else None,
        "max": float(arr.max()) if arr.size else None,
        "n": int(arr.size),
    }


def analyse_thresholds(
    oof: pd.DataFrame, model: str, strategy: ThresholdStrategy
) -> dict[str, Any]:
    """Select a threshold per CV repeat from ``model``'s OOF predictions and summarise."""
    rows = oof[oof["model"] == model]
    if rows.empty:
        raise ThresholdSelectionError(f"no out-of-fold predictions for model {model!r}")
    per_repeat: list[dict[str, Any]] = []
    for repeat, group in rows.groupby("repeat", sort=True):
        preds = PredictionSet.from_frame(group)
        choice = select_threshold(preds, strategy)
        per_repeat.append({"repeat": int(repeat), "n": len(group), **choice.model_dump()})
    chosen = float(np.median([r["threshold"] for r in per_repeat]))
    at_chosen = [
        evaluate_threshold(PredictionSet.from_frame(g), chosen, strategy).model_dump()
        for _, g in rows.groupby("repeat", sort=True)
    ]
    keys = ("threshold", "precision", "recall", "fbeta", "expected_cost")
    return {
        "model": model,
        "strategy": strategy.model_dump(mode="json"),
        "provenance": "oof",
        "selection_rule": "median of per-repeat thresholds selected on out-of-fold predictions",
        "chosen_threshold": chosen,
        "per_repeat": per_repeat,
        "per_repeat_spread": {k: _spread([r[k] for r in per_repeat]) for k in keys},
        "chosen_threshold_on_oof": {
            "note": "chosen threshold re-applied to each repeat's OOF predictions (optimistic)",
            "spread": {k: _spread([r[k] for r in at_chosen]) for k in keys if k != "threshold"},
        },
    }


def threshold_curve_for_model(
    run_dir: Path, model: str, repeat: int = 0, beta: float = 1.0
) -> pd.DataFrame:
    """Curve for one model and repeat, from the run's stored OOF predictions."""
    oof = rec.RunRecord(run_dir).oof_predictions()
    group = oof[(oof["model"] == model) & (oof["repeat"] == repeat)]
    if group.empty:
        raise ThresholdSelectionError(f"no OOF predictions for {model!r} repeat {repeat}")
    return threshold_curve(PredictionSet.from_frame(group), beta=beta)


def run_threshold_analysis(
    run_dir: Path, model: str, strategy: ThresholdStrategy
) -> dict[str, Any]:
    """Analyse ``model``'s OOF predictions and store the result in ``thresholds.json``."""
    record = rec.RunRecord(run_dir)
    if record.run.get("status") != "completed":
        raise ThresholdSelectionError("run is not completed")
    if model not in record.run["models"]:
        raise ThresholdSelectionError(f"model {model!r} is not part of run {record.run_id}")
    analysis = analyse_thresholds(record.oof_predictions(), model, strategy)
    analysis["created_at"] = rec.utc_now()
    store = record.thresholds or {"analyses": {}, "history": []}
    store["analyses"][model] = analysis
    store["history"].append(
        {
            "model": model,
            "created_at": analysis["created_at"],
            "chosen_threshold": analysis["chosen_threshold"],
            "strategy": analysis["strategy"],
        }
    )
    rec.write_json(Path(run_dir) / rec.THRESHOLDS_FILE, store)
    return analysis
