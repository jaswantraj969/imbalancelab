"""T-R5 M1: test-scoring history in the run record, report, and API."""

import pytest

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import amend_bootstrap_cis, final_evaluate, scoring_history
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.evaluation.uncertainty import BootstrapConfig
from imbalancelab.reporting import generate_report
from imbalancelab.tracking import RunRecord

BS = BootstrapConfig(n_resamples=200)


@pytest.fixture
def evaluated(write_csv, tmp_path):
    schema = DatasetSchema(target="label", positive_label="yes", id_column="row_id")
    ds = load_dataset(write_csv(make_imbalanced_frame(n=300, seed=4)), schema)
    from imbalancelab.splitting import make_holdout

    cfg = ExperimentConfig.model_validate(
        {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 1}}
    )
    run_dir = run_experiment(ds, make_holdout(ds), cfg, tmp_path / "runs").run_dir
    run_threshold_analysis(run_dir, "hgb", ThresholdStrategy())
    final_evaluate(ds, run_dir, "hgb", bootstrap=BS)
    return ds, run_dir


def _history_section(md: str) -> str:
    return md.split("### Test-scoring history")[1].split("\n## ")[0]


def test_single_final_evaluation_count_one_no_warning(evaluated) -> None:
    _, run_dir = evaluated
    h = scoring_history(RunRecord(run_dir))
    assert h["n_test_scorings"] == 1 and not h["repeated_test_use"]
    assert h["forced_reevaluations"] == []
    section = _history_section(generate_report(run_dir).markdown.read_text(encoding="utf-8"))
    assert "Test set scored **1 time** for this run" in section
    assert "WARNING" not in section and "Forced re-evaluations: none." in section


def test_amendments_are_not_scorings(evaluated) -> None:
    _, run_dir = evaluated
    amend_bootstrap_cis(run_dir, BS)
    h = scoring_history(RunRecord(run_dir))
    assert h["n_test_scorings"] == 1
    whats = [a["what"] for a in h["amendments_no_test_scoring"]]
    assert any(w.startswith("added bootstrap CIs") for w in whats)
    section = _history_section(generate_report(run_dir).markdown.read_text(encoding="utf-8"))
    assert "Amendments (**no test scoring**):" in section and "added bootstrap CIs" in section
    assert "WARNING" not in section


def test_forced_reevaluation_warns_with_count_and_reason(evaluated) -> None:
    ds, run_dir = evaluated
    final_evaluate(
        ds, run_dir, "hgb", force=True, reason="supervisor-requested rerun", bootstrap=BS
    )
    h = scoring_history(RunRecord(run_dir))
    assert h["n_test_scorings"] == 2 and h["repeated_test_use"]
    assert h["forced_reevaluations"] == [
        {"at": h["scorings"][1]["at"], "model": "hgb", "reason": "supervisor-requested rerun"}
    ]
    md = generate_report(run_dir).markdown.read_text(encoding="utf-8")
    section = _history_section(md)
    assert (
        "**WARNING:** the test set of this run was scored **2 times**. The reported test metrics "
        "may be optimistically biased by repeated test-set use." in section
    )
    assert "Test set scored **2 times** for this run" in section
    assert "| hgb | supervisor-requested rerun |" in section
    assert "The test set of this run was scored 2 times" in md  # limitations line
