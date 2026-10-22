"""Final evaluation: refit on outer-train rows, score the test set once.

Model and threshold must already be fixed (threshold from OOF analysis). A second final
evaluation of the same run is refused unless ``force=True`` with a reason. Every final
evaluation, forced or not, is appended to ``final_evaluation_log.jsonl``.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.evaluation.config import CandidateSpec, ExperimentConfig
from imbalancelab.evaluation.metrics import PRIMARY_METRIC, compute_metrics
from imbalancelab.evaluation.runner import make_candidate_pipeline, positive_scores
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.pipelines.builder import FeatureSpec
from imbalancelab.splitting.splits import Holdout, HoldoutMismatchError, check_holdout
from imbalancelab.tracking import records as rec


class FinalEvaluationError(RuntimeError):
    """Final evaluation cannot proceed (missing threshold, wrong dataset, unknown model...)."""


class FinalEvaluationExistsError(FinalEvaluationError):
    """The run already has a final evaluation and ``force`` was not given."""


@dataclass(frozen=True)
class FinalEvaluationResult:
    record: dict[str, Any]
    pipeline: Any  # chosen model refit on outer-train rows
    features: FeatureSpec
    threshold: float


def _spec_for(name: str, config: ExperimentConfig) -> CandidateSpec:
    for spec in config.all_specs():
        if spec.name == name:
            return spec
    raise FinalEvaluationError(f"model {name!r} is not part of this run")


def _append_log(run_dir: Path, entry: dict[str, Any]) -> None:
    with (run_dir / rec.FINAL_LOG_FILE).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, default=str) + "\n")


def final_evaluate(
    dataset: LoadedDataset,
    run_dir: Path,
    model: str | None = None,
    force: bool = False,
    reason: str | None = None,
) -> FinalEvaluationResult:
    """Refit ``model`` (default: best candidate by OOF AP) and the baselines on outer-train
    rows, score the stored test rows once, and record the results in the run directory."""
    run_dir = Path(run_dir)
    record = rec.RunRecord(run_dir)
    meta = record.run
    if meta.get("status") != "completed":
        raise FinalEvaluationError("run is not completed")
    if dataset.sha256 != meta["dataset"]["sha256"]:
        raise FinalEvaluationError("dataset SHA-256 does not match the run's dataset")
    holdout = Holdout.load(run_dir / rec.HOLDOUT_FILE)
    try:
        check_holdout(dataset, holdout)
    except HoldoutMismatchError as exc:
        raise FinalEvaluationError(str(exc)) from exc
    if holdout.test_sha256 != meta["holdout"]["test_sha256"]:
        raise FinalEvaluationError("stored holdout test hash differs from run.json")

    previous = run_dir / rec.FINAL_FILE
    if previous.exists():
        if not force:
            raise FinalEvaluationExistsError(
                "this run already has a final evaluation; the test set is scored once. "
                "Pass force=True with a reason to re-evaluate (this is logged)."
            )
        if not reason or not reason.strip():
            raise FinalEvaluationError("forced re-evaluation requires a non-empty reason")
        _append_log(
            run_dir,
            {
                "event": "forced_reevaluation",
                "at": rec.utc_now(),
                "reason": reason,
                "previous_sha256": hashlib.sha256(previous.read_bytes()).hexdigest(),
            },
        )

    config = ExperimentConfig.model_validate(record.config)
    summary = record.summary
    model = model or summary.get("best_candidate_by_mean_oof_ap")
    if model is None:
        raise FinalEvaluationError("no model given and the run has no candidate to select")
    _spec_for(model, config)

    thresholds = record.thresholds or {"analyses": {}}
    analysis = thresholds["analyses"].get(model)
    if analysis is None:
        raise FinalEvaluationError(
            f"no threshold analysis for {model!r}; run threshold analysis on OOF predictions "
            "before final evaluation"
        )
    strategy = ThresholdStrategy.model_validate(analysis["strategy"])
    baseline_analyses: dict[str, dict[str, Any]] = {}
    for base in config.baseline_names():
        existing = thresholds["analyses"].get(base)
        if existing is None or existing["strategy"] != analysis["strategy"]:
            existing = run_threshold_analysis(run_dir, base, strategy)
        baseline_analyses[base] = existing

    features = FeatureSpec.model_validate(meta["feature_spec"])
    train_idx = np.asarray(holdout.train_idx)
    test_idx = np.asarray(holdout.test_idx)
    X, y = dataset.frame, dataset.y
    results: dict[str, Any] = {}
    pred_parts: list[pd.DataFrame] = []
    chosen_pipeline: Any = None
    to_score = [model, *[b for b in config.baseline_names() if b != model]]
    for name in to_score:
        spec = _spec_for(name, config)
        a = analysis if name == model else baseline_analyses[name]
        pipeline = make_candidate_pipeline(spec, features, config)
        pipeline.fit(X.iloc[train_idx], y[train_idx])
        scores = positive_scores(pipeline, X.iloc[test_idx])
        ms = compute_metrics(
            y[test_idx], scores, threshold=a["chosen_threshold"], beta=strategy.beta
        )
        results[name] = {
            "threshold": a["chosen_threshold"],
            "threshold_created_at": a["created_at"],
            "metrics": {k: v.model_dump(mode="json") for k, v in ms.metrics.items()},
            "confusion": ms.confusion.model_dump(mode="json"),
        }
        pred_parts.append(
            pd.DataFrame(
                {
                    "model": name,
                    "row_index": test_idx,
                    "y_true": y[test_idx].astype(np.int8),
                    "y_score": scores,
                    "provenance": "test",
                }
            )
        )
        if name == model:
            chosen_pipeline = pipeline

    comparisons = []
    for base in config.baseline_names():
        if base == model:
            continue
        for metric in (PRIMARY_METRIC, "roc_auc"):
            a_val = results[model]["metrics"][metric]["value"]
            b_val = results[base]["metrics"][metric]["value"]
            comparisons.append(
                {
                    "candidate": model,
                    "baseline": base,
                    "metric": metric,
                    "candidate_value": a_val,
                    "baseline_value": b_val,
                    "diff": None if a_val is None or b_val is None else a_val - b_val,
                }
            )

    out = {
        "run_id": record.run_id,
        "model": model,
        "evaluated_at": rec.utc_now(),
        "forced": previous.exists(),
        "dataset_sha256": dataset.sha256,
        "test_sha256": holdout.test_sha256,
        "n_outer_train": int(train_idx.size),
        "n_test": int(test_idx.size),
        "n_test_positive": int(y[test_idx].sum()),
        "refit_on": "outer-train rows only",
        "threshold": analysis["chosen_threshold"],
        "threshold_provenance": {
            "source": "out-of-fold predictions",
            "strategy": analysis["strategy"],
            "selection_rule": analysis["selection_rule"],
            "analysis_created_at": analysis["created_at"],
            "per_repeat_spread": analysis["per_repeat_spread"]["threshold"],
        },
        "results": results,
        "comparisons": comparisons,
        "note": "single test-set evaluation; one number per model, no fold spread",
    }
    pd.concat(pred_parts, ignore_index=True).to_parquet(
        run_dir / rec.FINAL_PREDICTIONS_FILE, index=False
    )
    rec.write_json(previous, out)
    _append_log(
        run_dir,
        {
            "event": "final_evaluation",
            "at": out["evaluated_at"],
            "model": model,
            "forced": out["forced"],
            "reason": reason,
        },
    )
    return FinalEvaluationResult(
        record=out, pipeline=chosen_pipeline, features=features, threshold=out["threshold"]
    )
