import numpy as np
import pytest

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.calibration import (
    NO_RESAMPLER_NOTE,
    calibration_disclosure,
    reliability_curve,
)
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import final_evaluate
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.evaluation.uncertainty import BootstrapConfig, paired_bootstrap_difference
from imbalancelab.reporting import generate_report
from imbalancelab.splitting import make_holdout

# ------------------------------------------------------------------ reliability curve


def test_reliability_bins_computed_correctly() -> None:
    s = np.arange(100) / 100.0  # 0.00 ... 0.99, distinct
    y = (np.arange(100) % 4 == 0).astype(int)  # every 4th row positive
    curve = reliability_curve(y, s, n_bins=10)
    bins = curve["bins"]
    assert curve["binning"] == "quantile" and len(bins) == 10
    assert [b["n"] for b in bins] == [10] * 10
    for k, b in enumerate(bins):  # bin k holds rows 10k .. 10k+9
        rows = np.arange(10 * k, 10 * k + 10)
        assert b["mean_score"] == pytest.approx(s[rows].mean())
        assert b["observed_rate"] == pytest.approx(y[rows].mean())
        assert b["n_positive"] == int(y[rows].sum())
        assert b["lower"] <= s[rows].min() and s[rows].max() <= b["upper"]
    assert sum(b["n"] for b in bins) == 100


def test_reliability_ties_and_constant_scores() -> None:
    y = np.array([0, 1, 0, 1, 0, 0, 0, 1])
    s = np.array([0.1, 0.1, 0.1, 0.1, 0.9, 0.9, 0.9, 0.9])
    curve = reliability_curve(y, s, n_bins=10)  # tied edges collapse to 2 bins
    assert [b["n"] for b in curve["bins"]] == [4, 4]
    assert [b["observed_rate"] for b in curve["bins"]] == [0.5, 0.25]
    const = reliability_curve(y, np.full(8, 0.3), n_bins=5)
    assert len(const["bins"]) == 1 and const["bins"][0]["n"] == 8
    assert reliability_curve([], [], 5)["bins"] == []
    with pytest.raises(ValueError):
        reliability_curve(y, s, n_bins=0)


def test_disclosure_texts() -> None:
    with_sampler = calibration_disclosure(
        [
            {"name": "hgb+smote", "model": "hgb", "sampler": "smote"},
            {"name": "dummy_prior", "model": "dummy_prior", "sampler": "none"},
        ]
    )
    assert "NOT calibrated probabilities" in with_sampler[0] and "`hgb+smote`" in with_sampler[0]
    assert "Do not interpret them as risk" in with_sampler[0]
    without = calibration_disclosure([{"name": "hgb", "model": "hgb", "sampler": "none"}])
    assert without == [NO_RESAMPLER_NOTE]


# ------------------------------------------------------------------ paired bootstrap


def _scores(seed: int = 0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    y = (rng.random(500) < 0.15).astype(int)
    good = np.clip(0.4 * y + rng.random(500) * 0.6, 0, 1)
    weak = np.clip(0.1 * y + rng.random(500) * 0.9, 0, 1)
    return y, good, weak


def test_paired_identical_models_give_zero() -> None:
    y, good, _ = _scores()
    d = paired_bootstrap_difference(
        y, good, good, "average_precision", config=BootstrapConfig(n_resamples=300)
    )
    assert d.point == 0.0 and d.lower == 0.0 and d.upper == 0.0
    assert d.win_fraction == 0.0 and d.tie_fraction == 1.0 and d.n_undefined == 0


def test_paired_deterministic_by_seed_and_detects_better_model() -> None:
    y, good, weak = _scores()
    cfg = BootstrapConfig(n_resamples=400, seed=11)
    a = paired_bootstrap_difference(y, good, weak, "average_precision", "good", "weak", cfg)
    b = paired_bootstrap_difference(y, good, weak, "average_precision", "good", "weak", cfg)
    c = paired_bootstrap_difference(
        y,
        good,
        weak,
        "average_precision",
        "good",
        "weak",
        BootstrapConfig(n_resamples=400, seed=12),
    )
    assert a == b and a.lower != c.lower
    assert a.point is not None and a.point > 0 and a.lower is not None and a.lower > 0
    assert a.lower <= a.point <= a.upper and a.win_fraction == 1.0
    auc = paired_bootstrap_difference(y, good, weak, "roc_auc", config=cfg)
    assert auc.point is not None and auc.point > 0
    with pytest.raises(ValueError):
        paired_bootstrap_difference(y, good, weak, "precision")


# ------------------------------------------------------------------ run-level + report


@pytest.mark.parametrize("sampler", ["smote", "none"])
def test_final_record_and_report_carry_calibration_and_paired(write_csv, tmp_path, sampler) -> None:
    schema = DatasetSchema(target="label", positive_label="yes", id_column="row_id")
    ds = load_dataset(write_csv(make_imbalanced_frame(n=320, seed=11)), schema)
    cfg = ExperimentConfig.model_validate(
        {
            "candidates": [{"model": "hgb", "sampler": sampler}],
            "cv": {"n_splits": 3, "n_repeats": 1},
        }
    )
    run_dir = run_experiment(ds, make_holdout(ds), cfg, tmp_path / "runs").run_dir
    name = "hgb" if sampler == "none" else "hgb+smote"
    run_threshold_analysis(run_dir, name, ThresholdStrategy())
    rec = final_evaluate(ds, run_dir, name, bootstrap=BootstrapConfig(n_resamples=200)).record
    sel = rec["results"][name]
    assert sel["calibration"]["brier_ci"]["point"] == sel["metrics"]["brier"]["value"]
    assert sum(b["n"] for b in sel["calibration"]["reliability"]["bins"]) == rec["n_test"]
    pairs = {(d["baseline"], d["metric"]) for d in rec["paired_bootstrap"]}
    assert pairs == {
        (b, m) for b in ("dummy_prior", "logreg_balanced") for m in ("average_precision", "roc_auc")
    }
    md = generate_report(run_dir).markdown.read_text(encoding="utf-8")
    assert "### Calibration (disclosure only; no calibration stage)" in md
    assert "### Paired bootstrap of test differences" in md
    assert "test_reliability.png" in md
    if sampler == "smote":
        assert "are ranking scores, NOT calibrated probabilities" in md
        assert "Do not interpret them as risk" in md
    else:
        assert "Calibration was not assessed beyond the Brier score" in md
    assert "Class-weighted models (`logreg_balanced`)" in md


def test_api_schema_states_scores_are_not_calibrated() -> None:
    from imbalancelab.api.schemas import Prediction, PredictResponse
    from imbalancelab.workflow import score_note

    desc = Prediction.model_json_schema()["properties"]["probability"]["description"]
    assert "NOT a calibrated probability" in desc and "must not be interpreted as risk" in desc
    assert "score_note" in PredictResponse.model_json_schema()["required"]
    assert "NOT calibrated probabilities" in score_note("hgb+smote")
    assert "Calibration was not assessed" in score_note("hgb")
