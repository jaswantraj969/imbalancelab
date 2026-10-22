import json

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import CandidateSpec, ExperimentConfig
from imbalancelab.evaluation.runner import RunError, paired_comparison, run_experiment
from imbalancelab.models import make_estimator
from imbalancelab.splitting import CVConfig, HoldoutConfig, folds_sha256, make_holdout
from imbalancelab.splitting.splits import Fold
from imbalancelab.tracking import InvalidIdError, RecordNotFoundError, RunRecord, RunStore


def _dataset(write_csv, name: str = "d.csv", frame: pd.DataFrame | None = None, **kw: object):
    schema = DatasetSchema.model_validate(
        {"target": "label", "positive_label": "yes", "id_column": "row_id", **kw}
    )
    return load_dataset(
        write_csv(make_imbalanced_frame() if frame is None else frame, name), schema
    )


def _config(**kw: object) -> ExperimentConfig:
    base: dict[str, object] = {
        "candidates": [{"model": "hgb"}, {"model": "logreg_balanced", "sampler": "random_over"}],
        "cv": {"n_splits": 3, "n_repeats": 2, "seed": 1},
    }
    base.update(kw)
    return ExperimentConfig.model_validate(base)


@pytest.fixture
def run(write_csv, tmp_path):
    ds = _dataset(write_csv)
    holdout = make_holdout(ds, HoldoutConfig(seed=0))
    result = run_experiment(ds, holdout, _config(), tmp_path / "runs", dataset_id="ds1")
    return ds, holdout, result


def test_run_directory_contents(run) -> None:
    ds, holdout, result = run
    files = {p.name for p in result.run_dir.iterdir()}
    assert files == {
        "run.json",
        "config.json",
        "environment.json",
        "dataset_sha256.txt",
        "holdout.json",
        "fold_indices.json",
        "profile.json",
        "fold_metrics.json",
        "summary.json",
        "oof_predictions.parquet",
    }
    record = RunRecord(result.run_dir)
    meta = record.run
    assert meta["status"] == "completed" and meta["finished_at"]
    assert meta["dataset"]["sha256"] == ds.sha256
    assert (result.run_dir / "dataset_sha256.txt").read_text().strip() == ds.sha256
    assert meta["seed"] == 42 and meta["dataset_id"] == "ds1"
    assert meta["holdout"]["test_sha256"] == holdout.test_sha256
    assert meta["baselines"] == ["dummy_prior", "logreg_balanced"]
    assert meta["models"] == [
        "dummy_prior",
        "logreg_balanced",
        "hgb",
        "logreg_balanced+random_over",
    ]
    env = record.environment
    for pkg in ("numpy", "pandas", "scikit-learn", "imbalanced-learn"):
        assert env["packages"][pkg]
    assert env["python"]
    assert record.config["cv"]["n_splits"] == 3
    folds = [Fold.model_validate(f) for f in record.folds["folds"]]
    assert folds_sha256(folds) == meta["cv"]["fold_indices_sha256"]
    assert record.profile is not None and record.profile["dataset_sha256"] == ds.sha256
    assert record.thresholds is None and record.final_evaluation is None
    assert record.final_predictions() is None and record.final_log() == []


def test_all_models_share_identical_folds_and_never_see_test(run) -> None:
    ds, holdout, result = run
    oof = RunRecord(result.run_dir).oof_predictions()
    assert set(oof["provenance"]) == {"oof"}
    assert not set(oof["row_index"]) & set(holdout.test_idx)
    assert set(oof["row_index"]) == set(holdout.train_idx)
    keyed = {
        m: g.sort_values(["repeat", "fold", "row_index"])[["repeat", "fold", "row_index"]]
        .to_numpy()
        .tolist()
        for m, g in oof.groupby("model")
    }
    reference = keyed["dummy_prior"]
    assert all(v == reference for v in keyed.values())
    np.testing.assert_array_equal(oof["y_true"].to_numpy(), ds.y[oof["row_index"].to_numpy()])
    assert len(oof) == 4 * 2 * len(holdout.train_idx)  # 4 models x 2 repeats


def test_fold_metrics_and_summary(run) -> None:
    _, _, result = run
    record = RunRecord(result.run_dir)
    rows = record.fold_metrics
    assert len(rows) == 4 * 6
    summary = record.summary
    ap = summary["models"]["hgb"]["average_precision"]
    values = [r["metrics"]["average_precision"]["value"] for r in rows if r["model"] == "hgb"]
    assert ap["n"] == 6 and ap["mean"] == pytest.approx(np.mean(values))
    assert ap["std"] == pytest.approx(np.std(values, ddof=1))
    dummy_ap = summary["models"]["dummy_prior"]["average_precision"]["mean"]
    assert dummy_ap == pytest.approx(0.15, abs=0.05)  # chance level = prevalence
    comps = summary["comparisons"]
    assert {(c["candidate"], c["baseline"], c["metric"]) for c in comps} >= {
        ("hgb", "dummy_prior", "average_precision"),
        ("hgb", "logreg_balanced", "average_precision"),
        ("logreg_balanced", "dummy_prior", "average_precision"),
    }
    assert summary["best_candidate_by_mean_oof_ap"] in {"hgb", "logreg_balanced+random_over"}
    assert "p_value" not in json.dumps(summary)


def test_same_seed_and_config_give_identical_metrics(write_csv, tmp_path) -> None:
    ds = _dataset(write_csv)
    holdout = make_holdout(ds)
    a = run_experiment(ds, holdout, _config(), tmp_path / "runs")
    b = run_experiment(ds, holdout, _config(), tmp_path / "runs")
    assert a.run_id != b.run_id

    def strip(rows):
        return [{k: v for k, v in r.items() if k != "fit_predict_seconds"} for r in rows]

    assert strip(RunRecord(a.run_dir).fold_metrics) == strip(RunRecord(b.run_dir).fold_metrics)
    pd.testing.assert_frame_equal(
        RunRecord(a.run_dir).oof_predictions(), RunRecord(b.run_dir).oof_predictions()
    )
    assert a.summary == b.summary
    c = run_experiment(
        ds, holdout, _config(cv={"n_splits": 3, "n_repeats": 2, "seed": 2}), tmp_path / "runs"
    )
    assert (
        RunRecord(c.run_dir).run["cv"]["fold_indices_sha256"]
        != RunRecord(a.run_dir).run["cv"]["fold_indices_sha256"]
    )


@pytest.mark.parametrize("strategy", ["group", "temporal"])
def test_runner_uses_schema_split_strategy(write_csv, tmp_path, strategy: str) -> None:
    kw = {"group_column": "group"} if strategy == "group" else {"time_column": "ts"}
    ds = _dataset(write_csv, split_strategy=strategy, **kw)
    holdout = make_holdout(ds)
    result = run_experiment(ds, holdout, _config(candidates=[]), tmp_path / "runs")
    record = RunRecord(result.run_dir)
    assert record.run["cv"]["strategy"] == strategy
    folds = [Fold.model_validate(f) for f in record.folds["folds"]]
    if strategy == "group":
        g = ds.frame["group"].to_numpy()
        assert all(not set(g[f.train_idx]) & set(g[f.val_idx]) for f in folds)
    else:
        t = ds.frame["ts"].to_numpy()
        assert all(t[f.train_idx].max() < t[f.val_idx].min() for f in folds)
        assert record.run["cv"]["n_repeats_effective"] == 1
    assert record.run["candidates"] == []
    assert record.summary["best_candidate_by_mean_oof_ap"] is None


def test_failed_model_marks_run_failed(write_csv, tmp_path) -> None:
    frame = make_imbalanced_frame(n=120, positive_rate=0.0)
    frame.loc[:9, "label"] = "yes"  # 10 positives; SMOTE with k=50 must fail
    ds = _dataset(write_csv, frame=frame)
    holdout = make_holdout(ds)
    cfg = _config(candidates=[{"model": "hgb", "sampler": "smote"}], smote_k_neighbors=50)
    with pytest.raises(RunError, match="hgb\\+smote"):
        run_experiment(ds, holdout, cfg, tmp_path / "runs")
    (run_dir,) = (tmp_path / "runs").iterdir()
    meta = json.loads((run_dir / "run.json").read_text())
    assert meta["status"] == "failed" and "hgb+smote" in meta["error"]


def test_cross_boundary_duplicates_recorded(write_csv, tmp_path) -> None:
    frame = make_imbalanced_frame(n=200)
    dup = frame.iloc[:50].copy()
    dup["row_id"] = np.arange(200, 250)
    ds = _dataset(write_csv, frame=pd.concat([frame, dup], ignore_index=True))
    result = run_experiment(ds, make_holdout(ds), _config(candidates=[]), tmp_path / "runs")
    codes = {w["code"] for w in RunRecord(result.run_dir).run["split_warnings"]}
    assert "cross_boundary_duplicates" in codes


def test_paired_comparison_arithmetic() -> None:
    def row(model: str, fold: int, value: float | None) -> dict:
        return {
            "model": model,
            "repeat": 0,
            "fold": fold,
            "metrics": {"average_precision": {"value": value}, "brier": {"value": value}},
        }

    rows = [
        row("a", 0, 0.5),
        row("b", 0, 0.4),
        row("a", 1, 0.3),
        row("b", 1, 0.4),
        row("a", 2, 0.6),
        row("b", 2, 0.6),
        row("a", 3, None),
        row("b", 3, 0.2),
    ]
    c = paired_comparison(rows, "a", "b", "average_precision")
    assert c["n_pairs"] == 3 and c["n_pairs_skipped_undefined"] == 1
    assert (c["wins"], c["losses"], c["ties"]) == (1, 1, 1)
    assert c["mean_diff"] == pytest.approx(0.0) and c["win_fraction"] == pytest.approx(1 / 3)
    brier = paired_comparison(rows, "a", "b", "brier")  # lower is better
    assert (brier["wins"], brier["losses"]) == (1, 1)
    empty = paired_comparison([], "a", "b", "average_precision")
    assert empty["n_pairs"] == 0 and empty["win_fraction"] is None


def test_config_validation_and_registry() -> None:
    with pytest.raises(ValidationError):
        ExperimentConfig(candidates=[CandidateSpec(model="hgb"), CandidateSpec(model="hgb")])
    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate({"candidates": [{"model": "xgboost"}]})
    cfg = ExperimentConfig(candidates=[CandidateSpec(model="logreg_balanced")])
    assert [s.name for s in cfg.all_specs()] == ["dummy_prior", "logreg_balanced"]
    assert cfg.candidate_names() == []
    rf = make_estimator("random_forest", 3)
    assert rf.random_state == 3
    with pytest.raises(ValueError):
        make_estimator("nope", 0)


def test_run_store(tmp_path) -> None:
    store = RunStore(tmp_path / "runs")
    assert store.list() == []
    with pytest.raises(InvalidIdError):
        store.create("../evil")
    with pytest.raises(InvalidIdError):
        store.path("a/b")
    with pytest.raises(RecordNotFoundError):
        store.path("missing")
    run_id, path = store.create("run-x")
    assert run_id == "run-x" and path.is_dir()
    assert store.list() == []  # no run.json yet
    (path / "run.json").write_text("{}")
    assert store.list() == ["run-x"] and store.path("run-x") == path
    with pytest.raises(RecordNotFoundError):
        RunRecord(tmp_path)


def test_random_forest_candidate_runs(write_csv, tmp_path) -> None:
    ds = _dataset(write_csv)
    cfg = _config(
        candidates=[{"model": "random_forest"}], cv=CVConfig(n_splits=2, n_repeats=1).model_dump()
    )
    result = run_experiment(ds, make_holdout(ds), cfg, tmp_path / "runs")
    assert "random_forest" in result.summary["models"]


def test_random_forest_oof_predictions_are_bitwise_reproducible(write_csv, tmp_path) -> None:
    """Regression (T-R1 L2): with n_jobs=-1 RF probabilities differed in the last bit between
    runs, so the stored OOF parquet could not be regenerated byte for byte."""
    import hashlib

    ds = _dataset(write_csv)
    holdout = make_holdout(ds)
    cfg = _config(
        candidates=[{"model": "random_forest"}], cv=CVConfig(n_splits=3, n_repeats=1).model_dump()
    )
    a = run_experiment(ds, holdout, cfg, tmp_path / "r1")
    b = run_experiment(ds, holdout, cfg, tmp_path / "r2")
    oof_a, oof_b = RunRecord(a.run_dir).oof_predictions(), RunRecord(b.run_dir).oof_predictions()
    np.testing.assert_array_equal(oof_a["y_score"].to_numpy(), oof_b["y_score"].to_numpy())
    digest = [
        hashlib.sha256((r.run_dir / "oof_predictions.parquet").read_bytes()).hexdigest()
        for r in (a, b)
    ]
    assert digest[0] == digest[1]
    assert make_estimator("random_forest", 0).n_jobs == 1
