import json

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError
from sklearn.metrics import precision_recall_curve

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import (
    FinalEvaluationError,
    FinalEvaluationExistsError,
    final_evaluate,
)
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import (
    PredictionSet,
    ProvenanceError,
    ThresholdSelectionError,
    ThresholdStrategy,
    analyse_thresholds,
    evaluate_threshold,
    run_threshold_analysis,
    select_threshold,
    threshold_curve,
    threshold_curve_for_model,
)
from imbalancelab.splitting import make_holdout
from imbalancelab.tracking import RunRecord


@pytest.fixture
def preds() -> PredictionSet:
    rng = np.random.default_rng(3)
    y = (rng.random(300) < 0.2).astype(int)
    s = np.round(np.clip(0.35 * y + rng.random(300) * 0.65, 0, 1), 2)  # rounded -> ties
    return PredictionSet(y_true=y, y_score=s, provenance="oof")


def _brute(preds: PredictionSet, strategy: ThresholdStrategy) -> float:
    """Exhaustive reference implementation over distinct scores (+ 'predict none')."""
    cands = sorted(
        {*preds.y_score.tolist(), float(np.nextafter(preds.y_score.max(), np.inf))}, reverse=True
    )
    best_t, best_key = None, None
    for t in cands:
        c = evaluate_threshold(preds, t, strategy)
        if strategy.kind == "max_fbeta":
            key = (c.fbeta,)
        elif strategy.kind == "min_cost":
            key = (-c.expected_cost,)
        elif strategy.kind == "target_recall":
            if c.recall < strategy.target:
                continue
            key = (c.precision if c.precision is not None else -1,)
        else:
            if c.precision is None or c.precision < strategy.target:
                continue
            key = (c.recall,)
        if best_key is None or key > best_key:  # strict: ties keep the higher threshold
            best_t, best_key = t, key
    assert best_t is not None
    return best_t


def test_curve_matches_scikit_learn(preds) -> None:
    curve = threshold_curve(preds)
    assert np.isnan(curve["precision"].iloc[0]) and curve["tp"].iloc[0] == 0
    p, r, t = precision_recall_curve(preds.y_true, preds.y_score)
    ours = curve.iloc[1:].set_index("threshold")
    for prec, rec_, thr in zip(p[:-1], r[:-1], t, strict=True):
        assert ours.loc[thr, "precision"] == pytest.approx(prec)
        assert ours.loc[thr, "recall"] == pytest.approx(rec_)
    assert (curve["tp"] + curve["fn"] == preds.y_true.sum()).all()
    assert curve["threshold"].is_monotonic_decreasing


@pytest.mark.parametrize(
    "strategy",
    [
        ThresholdStrategy(kind="max_fbeta", beta=1.0),
        ThresholdStrategy(kind="max_fbeta", beta=2.0),
        ThresholdStrategy(kind="target_recall", target=0.8),
        ThresholdStrategy(kind="target_precision", target=0.5),
        ThresholdStrategy(kind="min_cost", cost_fp=1.0, cost_fn=5.0),
        ThresholdStrategy(kind="min_cost", cost_fp=1.0, cost_fn=0.0),
    ],
)
def test_selection_matches_brute_force(preds, strategy) -> None:
    choice = select_threshold(preds, strategy)
    assert choice.threshold == pytest.approx(_brute(preds, strategy))
    again = evaluate_threshold(preds, choice.threshold, strategy)
    assert again.tp == choice.tp and again.fp == choice.fp
    if strategy.kind == "target_recall":
        assert choice.recall >= 0.8
    if strategy.kind == "target_precision":
        assert choice.precision is not None and choice.precision >= 0.5


def test_min_cost_can_choose_predict_nothing(preds) -> None:
    choice = select_threshold(preds, ThresholdStrategy(kind="min_cost", cost_fp=1, cost_fn=0))
    assert choice.tp == 0 and choice.fp == 0 and choice.precision is None
    assert choice.threshold > preds.y_score.max()


def test_test_provenance_is_rejected(preds) -> None:
    test = PredictionSet(y_true=preds.y_true, y_score=preds.y_score, provenance="test")
    with pytest.raises(ProvenanceError):
        select_threshold(test, ThresholdStrategy())
    with pytest.raises(ProvenanceError):
        threshold_curve(test)
    frame = pd.DataFrame(
        {
            "model": "m",
            "repeat": 0,
            "y_true": preds.y_true,
            "y_score": preds.y_score,
            "provenance": "test",
        }
    )
    with pytest.raises(ProvenanceError):
        analyse_thresholds(frame, "m", ThresholdStrategy())
    mixed = frame.assign(provenance=["oof", "test"] * 150)
    with pytest.raises(ProvenanceError, match="mixed"):
        PredictionSet.from_frame(mixed)
    validation = PredictionSet(preds.y_true, preds.y_score, "validation")
    assert select_threshold(validation, ThresholdStrategy()).threshold > 0
    with pytest.raises(ValueError):
        PredictionSet(preds.y_true, preds.y_score, "bogus")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        PredictionSet(preds.y_true, preds.y_score[:3], "oof")


def test_selection_errors(preds) -> None:
    with pytest.raises(ThresholdSelectionError):
        select_threshold(
            PredictionSet(np.zeros(5, int), np.linspace(0, 1, 5), "oof"), ThresholdStrategy()
        )
    weak = PredictionSet(np.array([0, 1, 0, 1]), np.array([0.9, 0.1, 0.8, 0.2]), "oof")
    with pytest.raises(ThresholdSelectionError, match="precision"):
        select_threshold(weak, ThresholdStrategy(kind="target_precision", target=0.9))
    with pytest.raises(ValidationError):
        ThresholdStrategy(kind="target_recall")
    with pytest.raises(ValidationError):
        ThresholdStrategy(kind="min_cost", cost_fp=0, cost_fn=0)
    with pytest.raises(ThresholdSelectionError):
        analyse_thresholds(pd.DataFrame(columns=["model"]), "m", ThresholdStrategy())


# ------------------------------------------------------------------ run-level


@pytest.fixture
def completed_run(write_csv, tmp_path):
    schema = DatasetSchema(target="label", positive_label="yes", id_column="row_id")
    ds = load_dataset(write_csv(make_imbalanced_frame(n=320, seed=11)), schema)
    holdout = make_holdout(ds)
    cfg = ExperimentConfig.model_validate(
        {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 3}}
    )
    result = run_experiment(ds, holdout, cfg, tmp_path / "runs")
    return ds, holdout, result.run_dir


def test_per_repeat_threshold_analysis_is_stored(completed_run) -> None:
    _, _, run_dir = completed_run
    strategy = ThresholdStrategy(kind="max_fbeta", beta=2.0)
    analysis = run_threshold_analysis(run_dir, "hgb", strategy)
    assert len(analysis["per_repeat"]) == 3
    thresholds = [r["threshold"] for r in analysis["per_repeat"]]
    assert analysis["chosen_threshold"] == pytest.approx(np.median(thresholds))
    spread = analysis["per_repeat_spread"]["threshold"]
    assert spread["n"] == 3 and spread["mean"] == pytest.approx(np.mean(thresholds))
    assert spread["std"] == pytest.approx(np.std(thresholds, ddof=1))
    # each per-repeat threshold equals an independent selection on that repeat's OOF rows
    oof = RunRecord(run_dir).oof_predictions()
    for r in analysis["per_repeat"]:
        g = oof[(oof["model"] == "hgb") & (oof["repeat"] == r["repeat"])]
        assert select_threshold(PredictionSet.from_frame(g), strategy).threshold == r["threshold"]
    stored = RunRecord(run_dir).thresholds
    assert stored["analyses"]["hgb"]["chosen_threshold"] == analysis["chosen_threshold"]
    run_threshold_analysis(run_dir, "hgb", ThresholdStrategy(kind="target_recall", target=0.7))
    assert len(RunRecord(run_dir).thresholds["history"]) == 2
    with pytest.raises(ThresholdSelectionError):
        run_threshold_analysis(run_dir, "not_a_model", strategy)
    curve = threshold_curve_for_model(run_dir, "hgb", repeat=1)
    assert len(curve) > 2
    with pytest.raises(ThresholdSelectionError):
        threshold_curve_for_model(run_dir, "hgb", repeat=9)


def test_final_evaluation_once_and_forced_logging(completed_run) -> None:
    ds, holdout, run_dir = completed_run
    with pytest.raises(FinalEvaluationError, match="threshold analysis"):
        final_evaluate(ds, run_dir, "hgb")
    analysis = run_threshold_analysis(run_dir, "hgb", ThresholdStrategy(kind="max_fbeta"))

    result = final_evaluate(ds, run_dir)  # defaults to best candidate = hgb
    out = result.record
    assert out["model"] == "hgb" and out["threshold"] == analysis["chosen_threshold"]
    assert out["test_sha256"] == holdout.test_sha256 and not out["forced"]
    assert set(out["results"]) == {"hgb", "dummy_prior", "logreg_balanced"}
    preds = RunRecord(run_dir).final_predictions()
    assert preds is not None and set(preds["provenance"]) == {"test"}
    for _, g in preds.groupby("model"):
        assert sorted(g["row_index"]) == holdout.test_idx  # each model scored once on test
    stored = RunRecord(run_dir).final_evaluation
    assert stored == json.loads(json.dumps(out, default=str))
    # baseline thresholds were selected on OOF with the same strategy
    th = RunRecord(run_dir).thresholds["analyses"]
    assert th["logreg_balanced"]["strategy"] == analysis["strategy"]

    # test predictions can never feed threshold selection
    test_hgb = preds[preds["model"] == "hgb"].assign(repeat=0)
    with pytest.raises(ProvenanceError):
        analyse_thresholds(test_hgb, "hgb", ThresholdStrategy())

    with pytest.raises(FinalEvaluationExistsError):
        final_evaluate(ds, run_dir, "hgb")
    with pytest.raises(FinalEvaluationError, match="reason"):
        final_evaluate(ds, run_dir, "hgb", force=True)
    forced = final_evaluate(ds, run_dir, "hgb", force=True, reason="re-run after audit")
    assert forced.record["forced"] is True
    log = RunRecord(run_dir).final_log()
    assert [e["event"] for e in log] == [
        "final_evaluation",
        "forced_reevaluation",
        "final_evaluation",
    ]
    assert log[1]["reason"] == "re-run after audit" and len(log[1]["previous_sha256"]) == 64


def test_final_pipeline_refit_on_outer_train_only(completed_run) -> None:
    ds, holdout, run_dir = completed_run
    run_threshold_analysis(run_dir, "hgb", ThresholdStrategy())
    result = final_evaluate(ds, run_dir, "hgb")
    scaler = (
        result.pipeline.named_steps["preprocess"].named_transformers_["num"].named_steps["scale"]
    )
    cols = result.features.numeric
    train = ds.frame.iloc[holdout.train_idx][cols].astype(float)
    np.testing.assert_allclose(scaler.mean_, train.fillna(train.median()).mean().to_numpy())


def test_final_evaluation_guards(completed_run, write_csv) -> None:
    ds, _, run_dir = completed_run
    run_threshold_analysis(run_dir, "hgb", ThresholdStrategy())
    other = load_dataset(
        write_csv(make_imbalanced_frame(n=320, seed=12), "other.csv"),
        DatasetSchema(target="label", positive_label="yes", id_column="row_id"),
    )
    with pytest.raises(FinalEvaluationError, match="SHA-256"):
        final_evaluate(other, run_dir, "hgb")
    with pytest.raises(FinalEvaluationError, match="not part"):
        final_evaluate(ds, run_dir, "random_forest")
    meta = json.loads((run_dir / "run.json").read_text())
    meta["holdout"]["test_sha256"] = "0" * 64
    (run_dir / "run.json").write_text(json.dumps(meta))
    with pytest.raises(FinalEvaluationError, match="hash"):
        final_evaluate(ds, run_dir, "hgb")
    meta["status"] = "failed"
    (run_dir / "run.json").write_text(json.dumps(meta))
    with pytest.raises(FinalEvaluationError, match="not completed"):
        final_evaluate(ds, run_dir, "hgb")
    with pytest.raises(ThresholdSelectionError, match="not completed"):
        run_threshold_analysis(run_dir, "hgb", ThresholdStrategy())
