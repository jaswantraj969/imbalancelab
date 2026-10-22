"""Repeated-CV experiment runner writing a file-based run record.

All models in a run (baselines and candidates) are fit and scored on identical, stored fold
indices drawn from outer-train rows only. Test rows are never touched here.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.evaluation.config import CandidateSpec, ExperimentConfig
from imbalancelab.evaluation.metrics import (
    HIGHER_IS_BETTER,
    METRIC_NAMES,
    PRIMARY_METRIC,
    compute_metrics,
)
from imbalancelab.models.registry import MODEL_DESCRIPTIONS, make_estimator
from imbalancelab.pipelines.builder import FeatureSpec, build_pipeline, infer_feature_spec
from imbalancelab.profiling.profile import DatasetProfile, profile_dataset
from imbalancelab.splitting.duplicates import cross_boundary_duplicates
from imbalancelab.splitting.splits import CVPlan, Holdout, check_holdout, make_cv_folds
from imbalancelab.tracking import records as rec

COMPARISON_METRICS = (PRIMARY_METRIC, "roc_auc")


class RunError(RuntimeError):
    """A model failed to fit or predict during the experiment."""


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_dir: Path
    summary: dict[str, Any]


def make_candidate_pipeline(
    spec: CandidateSpec, features: FeatureSpec, config: ExperimentConfig
) -> Any:
    """The unfitted pipeline for ``spec``; used identically by CV and final evaluation."""
    return build_pipeline(
        features,
        make_estimator(spec.model, config.seed),
        sampler=spec.sampler,
        seed=config.seed,
        smote_k_neighbors=config.smote_k_neighbors,
    )


def positive_scores(pipeline: Any, X: pd.DataFrame) -> np.ndarray:
    proba = pipeline.predict_proba(X)
    classes = list(pipeline.classes_)
    return np.asarray(proba[:, classes.index(1)], dtype=float)


def summarise(values: list[float | None]) -> dict[str, Any]:
    defined = np.array([v for v in values if v is not None], dtype=float)
    n = int(defined.size)
    return {
        "mean": float(defined.mean()) if n else None,
        "std": float(defined.std(ddof=1)) if n > 1 else None,
        "min": float(defined.min()) if n else None,
        "max": float(defined.max()) if n else None,
        "n": n,
        "n_undefined": len(values) - n,
    }


def paired_comparison(
    fold_rows: list[dict[str, Any]], candidate: str, baseline: str, metric: str
) -> dict[str, Any]:
    """Per-fold paired differences (candidate - baseline) and the win fraction.

    Folds share indices, so differences are paired. No significance test is run: CV folds are
    correlated, so naive tests overstate confidence.
    """
    by_key: dict[tuple[int, int], dict[str, float | None]] = {}
    for row in fold_rows:
        if row["model"] in (candidate, baseline):
            key = (row["repeat"], row["fold"])
            by_key.setdefault(key, {})[row["model"]] = row["metrics"][metric]["value"]
    diffs: list[float] = []
    n_skipped = 0
    for key in sorted(by_key):
        pair = by_key[key]
        a, b = pair.get(candidate), pair.get(baseline)
        if a is None or b is None:
            n_skipped += 1
            continue
        diffs.append(a - b)
    arr = np.array(diffs, dtype=float)
    sign = 1.0 if HIGHER_IS_BETTER[metric] else -1.0
    wins = int(np.sum(sign * arr > 0))
    losses = int(np.sum(sign * arr < 0))
    n = int(arr.size)
    return {
        "candidate": candidate,
        "baseline": baseline,
        "metric": metric,
        "n_pairs": n,
        "n_pairs_skipped_undefined": n_skipped,
        "mean_diff": float(arr.mean()) if n else None,
        "std_diff": float(arr.std(ddof=1)) if n > 1 else None,
        "min_diff": float(arr.min()) if n else None,
        "max_diff": float(arr.max()) if n else None,
        "wins": wins,
        "losses": losses,
        "ties": n - wins - losses,
        "win_fraction": wins / n if n else None,
    }


def run_experiment(
    dataset: LoadedDataset,
    holdout: Holdout,
    config: ExperimentConfig,
    runs_dir: Path,
    profile: DatasetProfile | None = None,
    run_id: str | None = None,
    dataset_id: str | None = None,
) -> RunResult:
    """Run repeated CV for baselines + candidates on outer-train rows and record everything."""
    created_at = rec.utc_now()
    check_holdout(dataset, holdout)
    plan: CVPlan = make_cv_folds(dataset, holdout, config.cv)
    features = infer_feature_spec(dataset.frame, dataset.feature_columns)
    profile = profile or profile_dataset(dataset)
    split_warnings = [*plan.warnings, *cross_boundary_duplicates(dataset, holdout, plan)]
    specs = config.all_specs()

    store = rec.RunStore(runs_dir)
    run_id, run_dir = store.create(run_id)
    run_meta: dict[str, Any] = {
        "run_id": run_id,
        "status": "running",
        "created_at": created_at,
        "finished_at": None,
        "dataset_id": dataset_id,
        "dataset": {
            "sha256": dataset.sha256,
            "source_name": dataset.source_path.name,
            "n_rows": dataset.n_rows,
            "schema": dataset.schema.model_dump(mode="json"),
            "positive_label_coerced": dataset.positive_label_coerced,
            "notes": list(dataset.notes),
        },
        "holdout": {
            "strategy": holdout.strategy,
            "config": holdout.config.model_dump(mode="json"),
            "n_outer_train": len(holdout.train_idx),
            "n_test": len(holdout.test_idx),
            "n_gap": len(holdout.gap_idx),
            "test_sha256": holdout.test_sha256,
        },
        "cv": {
            "strategy": plan.strategy,
            "config": plan.config.model_dump(mode="json"),
            "n_repeats_effective": plan.n_repeats_effective,
            "n_folds_total": len(plan.folds),
            "fold_indices_sha256": plan.fold_indices_sha256,
        },
        "seed": config.seed,
        "primary_metric": PRIMARY_METRIC,
        "baselines": config.baseline_names(),
        "candidates": config.candidate_names(),
        "models": [s.name for s in specs],
        "model_specs": [
            {
                "name": s.name,
                "model": s.model,
                "sampler": s.sampler,
                "description": MODEL_DESCRIPTIONS[s.model],
            }
            for s in specs
        ],
        "feature_spec": features.model_dump(mode="json"),
        "split_warnings": [w.model_dump(mode="json") for w in split_warnings],
        "error": None,
    }
    rec.write_json(run_dir / rec.CONFIG_FILE, config.model_dump(mode="json"))
    rec.write_json(run_dir / rec.ENVIRONMENT_FILE, rec.environment_info())
    (run_dir / rec.DATASET_SHA_FILE).write_text(dataset.sha256 + "\n", encoding="utf-8")
    holdout.save(run_dir / rec.HOLDOUT_FILE)
    rec.write_json(run_dir / rec.FOLDS_FILE, plan.model_dump(mode="json"))
    rec.write_json(run_dir / rec.PROFILE_FILE, profile.model_dump(mode="json"))
    rec.write_json(run_dir / rec.RUN_FILE, run_meta)

    X = dataset.frame
    y = dataset.y
    fold_rows: list[dict[str, Any]] = []
    oof_parts: list[pd.DataFrame] = []
    try:
        for spec in specs:
            for fold in plan.folds:
                tr, va = np.asarray(fold.train_idx), np.asarray(fold.val_idx)
                pipeline = make_candidate_pipeline(spec, features, config)
                start = time.perf_counter()
                try:
                    pipeline.fit(X.iloc[tr], y[tr])
                    scores = positive_scores(pipeline, X.iloc[va])
                except Exception as exc:  # recorded, then re-raised as RunError
                    raise RunError(
                        f"model {spec.name!r} failed on repeat {fold.repeat} fold {fold.fold}: "
                        f"{type(exc).__name__}: {exc}"
                    ) from exc
                elapsed = time.perf_counter() - start
                ms = compute_metrics(y[va], scores, threshold=config.threshold, beta=config.beta)
                fold_rows.append(
                    {
                        "model": spec.name,
                        "repeat": fold.repeat,
                        "fold": fold.fold,
                        "n_train": len(tr),
                        "n_val": len(va),
                        "n_val_positive": int(y[va].sum()),
                        "fit_predict_seconds": round(elapsed, 4),
                        "threshold": config.threshold,
                        "beta": config.beta,
                        "metrics": {k: v.model_dump(mode="json") for k, v in ms.metrics.items()},
                        "confusion": ms.confusion.model_dump(mode="json"),
                    }
                )
                oof_parts.append(
                    pd.DataFrame(
                        {
                            "model": spec.name,
                            "repeat": fold.repeat,
                            "fold": fold.fold,
                            "row_index": va,
                            "y_true": y[va].astype(np.int8),
                            "y_score": scores,
                            "provenance": "oof",
                        }
                    )
                )
    except RunError as exc:
        run_meta.update(status="failed", finished_at=rec.utc_now(), error=str(exc))
        rec.write_json(run_dir / rec.RUN_FILE, run_meta)
        raise

    summary = build_summary(fold_rows, config)
    rec.write_json(run_dir / rec.FOLD_METRICS_FILE, fold_rows)
    rec.write_json(run_dir / rec.SUMMARY_FILE, summary)
    pd.concat(oof_parts, ignore_index=True).to_parquet(run_dir / rec.OOF_FILE, index=False)
    run_meta.update(status="completed", finished_at=rec.utc_now())
    rec.write_json(run_dir / rec.RUN_FILE, run_meta)
    return RunResult(run_id=run_id, run_dir=run_dir, summary=summary)


def build_summary(fold_rows: list[dict[str, Any]], config: ExperimentConfig) -> dict[str, Any]:
    models = [s.name for s in config.all_specs()]
    per_model: dict[str, dict[str, Any]] = {}
    for name in models:
        rows = [r for r in fold_rows if r["model"] == name]
        per_model[name] = {
            metric: summarise([r["metrics"][metric]["value"] for r in rows])
            for metric in METRIC_NAMES
        }
    comparisons = []
    baselines = config.baseline_names()
    pairs = [(c, b) for c in config.candidate_names() for b in baselines]
    pairs.append((baselines[1], baselines[0]))  # logreg vs dummy: is there any signal?
    for cand, base in pairs:
        for metric in COMPARISON_METRICS:
            comparisons.append(paired_comparison(fold_rows, cand, base, metric))

    candidates = config.candidate_names()
    ranked = sorted(
        (c for c in candidates if per_model[c][PRIMARY_METRIC]["mean"] is not None),
        key=lambda c: per_model[c][PRIMARY_METRIC]["mean"],
        reverse=True,
    )
    return {
        "primary_metric": PRIMARY_METRIC,
        "reference_threshold": config.threshold,
        "beta": config.beta,
        "models": per_model,
        "comparisons": comparisons,
        "best_candidate_by_mean_oof_ap": ranked[0] if ranked else None,
        "selection_rule": (
            "candidate with the highest mean out-of-fold average precision; test data is not used"
        ),
    }
