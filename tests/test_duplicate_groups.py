"""H1: duplicate-aware splitting. No duplicate cluster may cross any split boundary."""

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.splitting import (
    CVConfig,
    HoldoutConfig,
    HoldoutMismatchError,
    SplitError,
    cross_boundary_duplicates,
    get_or_create_holdout,
    make_cv_folds,
    make_holdout,
)
from imbalancelab.splitting.groups import resolve_groups
from imbalancelab.tracking import RunRecord


def duplicated_frame(n: int = 400, dup_fraction: float = 0.5, seed: int = 0) -> pd.DataFrame:
    """Synthetic frame where ~dup_fraction of rows are copied 1-3 times (new row ids)."""
    base = make_imbalanced_frame(n=n, positive_rate=0.15, seed=seed)
    base = base.drop(columns=["ts"])
    rng = np.random.default_rng(seed)
    src = rng.choice(n, size=int(n * dup_fraction), replace=False)
    copies = base.iloc[np.repeat(src, rng.integers(1, 4, size=len(src)))].copy()
    # a few copies get the opposite label -> conflicting-label clusters
    flip = copies.index[:5]
    copies.loc[flip, "label"] = np.where(copies.loc[flip, "label"] == "yes", "no", "yes")
    frame = pd.concat([base, copies], ignore_index=True)
    frame["row_id"] = np.arange(len(frame))
    return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _ds(write_csv, frame=None, name="dup.csv", **kw):
    schema = DatasetSchema.model_validate(
        {
            "target": "label",
            "positive_label": "yes",
            "id_column": "row_id",
            "duplicate_groups": True,
            **kw,
        }
    )
    return load_dataset(write_csv(duplicated_frame() if frame is None else frame, name), schema)


def independent_clusters(ds) -> np.ndarray:
    """Cluster key computed independently of the library (repr of the feature tuple)."""
    return np.array([repr(tuple(r)) for r in ds.frame[ds.feature_columns].itertuples(index=False)])


def _crossing(keys: np.ndarray, a: list[int], b: list[int]) -> int:
    return len(set(keys[a]) & set(keys[b]))


def test_no_duplicate_cluster_crosses_outer_or_inner_boundaries(write_csv) -> None:
    ds = _ds(write_csv)
    keys = independent_clusters(ds)
    assert len(np.unique(keys)) < ds.n_rows  # the fixture really has duplicates
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=1))
    assert holdout.duplicate_groups is True
    assert _crossing(keys, holdout.train_idx, holdout.test_idx) == 0
    assert sorted(holdout.train_idx + holdout.test_idx) == list(range(ds.n_rows))
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=3, seed=2))
    assert plan.duplicate_groups is True and len(plan.folds) == 12
    for fold in plan.folds:
        assert _crossing(keys, fold.train_idx, fold.val_idx) == 0
        assert not set(fold.val_idx) & set(holdout.test_idx)
    # the existing cross-boundary duplicate check must report zero
    assert cross_boundary_duplicates(ds, holdout, plan) == []


def test_without_duplicate_groups_the_same_data_crosses_boundaries(write_csv) -> None:
    ds = _ds(write_csv, duplicate_groups=False)
    holdout = make_holdout(ds, HoldoutConfig(seed=1))
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=1))
    warnings = cross_boundary_duplicates(ds, holdout, plan)
    assert warnings and warnings[0].evidence["test_rows_duplicating_train"] > 0


def test_reproducible_by_seed(write_csv) -> None:
    ds = _ds(write_csv)
    a = make_holdout(ds, HoldoutConfig(seed=5))
    b = make_holdout(ds, HoldoutConfig(seed=5))
    c = make_holdout(ds, HoldoutConfig(seed=6))
    assert a == b and a.test_idx != c.test_idx
    cv = CVConfig(n_splits=4, n_repeats=2, seed=3)
    assert (
        make_cv_folds(ds, a, cv).fold_indices_sha256 == make_cv_folds(ds, a, cv).fold_indices_sha256
    )
    other = CVConfig(n_splits=4, n_repeats=2, seed=4)
    assert (
        make_cv_folds(ds, a, other).fold_indices_sha256
        != make_cv_folds(ds, a, cv).fold_indices_sha256
    )


def test_stratification_within_tolerance(write_csv) -> None:
    ds = _ds(write_csv)
    rate = ds.y.mean()
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=1))
    assert abs(ds.y[holdout.test_idx].mean() - rate) < 0.03
    assert len(holdout.test_idx) == pytest.approx(0.2 * ds.n_rows, rel=0.15)
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2))
    outer_rate = ds.y[holdout.train_idx].mean()
    for fold in plan.folds:
        assert abs(ds.y[fold.val_idx].mean() - outer_rate) < 0.05


def test_conflicting_labels_kept_in_one_cluster_and_counted(write_csv) -> None:
    ds = _ds(write_csv)
    groups, info, warnings = resolve_groups(ds)
    assert groups is not None and info is not None
    keys = independent_clusters(ds)
    frame = pd.DataFrame({"k": keys, "y": ds.y})
    expected_conflicts = int((frame.groupby("k")["y"].nunique() > 1).sum())
    sizes = frame.groupby("k").size()
    assert expected_conflicts > 0
    assert info.n_conflicting_label_clusters == expected_conflicts
    assert info.n_duplicate_clusters == int((sizes > 1).sum())
    assert info.n_rows_in_duplicate_clusters == int(sizes[sizes > 1].sum())
    assert info.n_groups == len(np.unique(keys)) and info.source == "duplicates"
    assert "conflicting_label_clusters" in {w.code for w in warnings}
    # same key <=> same group id
    for key in np.unique(keys)[:50]:
        assert len(np.unique(groups[keys == key])) == 1


def test_combined_with_declared_groups(write_csv, caplog) -> None:
    frame = duplicated_frame()
    frame["group"] = np.arange(len(frame)) % 40  # duplicates land in different declared groups
    ds = _ds(write_csv, frame, "g.csv", group_column="group", split_strategy="group")
    with caplog.at_level("WARNING", logger="imbalancelab.splitting.groups"):
        groups, info, warnings = resolve_groups(ds)
    assert info is not None and info.source == "declared+duplicates"
    logged = [r.getMessage() for r in caplog.records if "merged" in r.getMessage()]
    assert len(logged) == 1
    assert logged[0].startswith(f"duplicate_groups: {info.n_declared_groups_merged} declared")
    merged_w = next(w for w in warnings if w.code == "duplicate_clusters_span_declared_groups")
    assert merged_w.evidence["n_declared_groups_merged"] == info.n_declared_groups_merged
    assert info.n_clusters_spanning_declared_groups > 0
    assert info.n_groups <= 40 and info.n_declared_groups_merged == 40 - info.n_groups
    assert "duplicate_clusters_span_declared_groups" in {w.code for w in warnings}
    declared = ds.frame["group"].to_numpy()
    for g in np.unique(declared):  # a declared group is never split across merged groups
        assert len(np.unique(groups[declared == g])) == 1

    sparse = duplicated_frame(n=600, dup_fraction=0.05, seed=3)
    sparse["group"] = np.arange(len(sparse)) % 60
    ds2 = _ds(write_csv, sparse, "g2.csv", group_column="group", split_strategy="group")
    holdout = make_holdout(ds2, HoldoutConfig(test_size=0.25, seed=0))
    keys = independent_clusters(ds2)
    assert _crossing(keys, holdout.train_idx, holdout.test_idx) == 0
    assert not set(declared_of(ds2, holdout.train_idx)) & set(declared_of(ds2, holdout.test_idx))
    plan = make_cv_folds(ds2, holdout, CVConfig(n_splits=3, n_repeats=1))
    for fold in plan.folds:
        assert _crossing(keys, fold.train_idx, fold.val_idx) == 0


def declared_of(ds, idx):
    return ds.frame["group"].to_numpy()[idx]


def test_declared_groups_without_duplicate_flag_unchanged(write_csv) -> None:
    frame = make_imbalanced_frame()
    ds = _ds(
        write_csv,
        frame,
        "plain.csv",
        group_column="group",
        split_strategy="group",
        duplicate_groups=False,
    )
    _, info, warnings = resolve_groups(ds)
    assert info is not None and info.source == "declared" and warnings == []
    assert make_holdout(ds).group_info == info


def test_run_record_contains_duplicate_groups(write_csv, tmp_path) -> None:
    ds = _ds(write_csv)
    holdout = make_holdout(ds)
    cfg = ExperimentConfig.model_validate({"candidates": [], "cv": {"n_splits": 3, "n_repeats": 1}})
    result = run_experiment(ds, holdout, cfg, tmp_path / "runs")
    run = RunRecord(result.run_dir).run
    assert run["holdout"]["duplicate_groups"] is True
    assert run["cv"]["duplicate_groups"] is True
    info = run["holdout"]["group_info"]
    assert info["n_duplicate_clusters"] > 0 and info["n_groups"] < ds.n_rows
    assert run["cv"]["n_groups_outer_train"] > 0
    codes = {w["code"] for w in run["split_warnings"]}
    assert "cross_boundary_duplicates" not in codes
    assert "conflicting_label_clusters" in codes


def test_flag_change_is_a_holdout_mismatch_and_temporal_is_rejected(write_csv, tmp_path) -> None:
    ds = _ds(write_csv)
    path = tmp_path / "holdout.json"
    get_or_create_holdout(ds, HoldoutConfig(), path)
    plain = _ds(write_csv, duplicate_groups=False)
    assert plain.sha256 == ds.sha256
    with pytest.raises(HoldoutMismatchError, match="duplicate_groups"):
        get_or_create_holdout(plain, None, path)
    with pytest.raises(ValidationError, match="temporal"):
        DatasetSchema(
            target="label",
            positive_label="yes",
            time_column="ts",
            split_strategy="temporal",
            duplicate_groups=True,
        )


def test_no_features_is_a_split_error(write_csv) -> None:
    frame = pd.DataFrame({"row_id": range(40), "label": ["yes", "no", "no", "no"] * 10})
    ds = _ds(write_csv, frame, "nofeat.csv")
    with pytest.raises(SplitError, match="feature"):
        make_holdout(ds)


def giant_cluster_frame(n: int = 1000, giant: int = 300, seed: int = 0) -> pd.DataFrame:
    """Mirror of the mammography failure mode: one cluster of `giant` identical rows with only a
    few positives, plus ordinary unique rows."""
    frame = make_imbalanced_frame(n=n, positive_rate=0.08, seed=seed).drop(columns=["ts", "group"])
    frame.loc[: giant - 1, ["x_signal", "x_noise", "color"]] = [-1.0, 0.0, "a"]
    frame.loc[: giant - 1, "label"] = "no"
    frame.loc[[0, 1], "label"] = "yes"  # 2 conflicting positives inside the giant cluster
    return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def test_giant_cluster_is_pinned_to_train_and_test_stays_representative(write_csv) -> None:
    ds = _ds(write_csv, giant_cluster_frame(), "giant.csv")
    keys = independent_clusters(ds)
    giant_key = pd.Series(keys).value_counts().index[0]
    in_giant = keys == giant_key
    assert in_giant.sum() == 300
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=0))
    assert not in_giant[holdout.test_idx].any()  # giant cluster entirely on the training side
    assert holdout.n_pinned_groups == 1 and holdout.n_pinned_rows == 300
    codes = {w.code for w in holdout.warnings}
    assert "oversized_groups_pinned_to_train" in codes
    assert "holdout_size_deviation" not in codes and "holdout_prevalence_deviation" not in codes
    eligible = ~in_giant
    assert abs(ds.y[holdout.test_idx].mean() - ds.y[eligible].mean()) < 0.03
    assert abs(len(holdout.test_idx) / ds.n_rows - 0.2) < 0.05
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2))
    assert plan.n_pinned_groups == 1 and plan.n_pinned_rows == 300
    outer_eligible = np.asarray(holdout.train_idx)[~in_giant[holdout.train_idx]]
    for fold in plan.folds:
        assert in_giant[fold.train_idx].sum() == 300 and not in_giant[fold.val_idx].any()
        assert _crossing(keys, fold.train_idx, fold.val_idx) == 0
        assert abs(ds.y[fold.val_idx].mean() - ds.y[outer_eligible].mean()) < 0.05
    assert cross_boundary_duplicates(ds, holdout, plan) == []


def test_without_pinning_a_dominated_test_set_is_flagged(write_csv) -> None:
    """max_eval_group_fraction=1.0 lets a cluster just below the test size into the test set;
    the balance check must then report that one group dominates it (the T-R1 mammography
    failure mode)."""
    ds = _ds(write_csv, giant_cluster_frame(giant=180), "giant2.csv")
    keys = independent_clusters(ds)
    giant_key = pd.Series(keys).value_counts().index[0]
    for seed in range(20):
        holdout = make_holdout(ds, HoldoutConfig(seed=seed, max_eval_group_fraction=1.0))
        assert holdout.n_pinned_rows == 0
        if (keys[holdout.test_idx] == giant_key).any():
            codes = {w.code for w in holdout.warnings}
            assert "holdout_dominated_by_group" in codes
            return
    pytest.fail("no seed placed the giant cluster in the test set")


def test_evaluation_coverage_recorded_and_reported_with_warning(write_csv, tmp_path) -> None:
    from imbalancelab.reporting import generate_report

    ds = _ds(write_csv, giant_cluster_frame(n=1000, giant=300), "cov.csv")
    holdout = make_holdout(ds, HoldoutConfig(seed=0))
    cfg = ExperimentConfig.model_validate(
        {"candidates": [], "cv": {"n_splits": 3, "n_repeats": 2, "max_eval_group_fraction": 0.3}}
    )
    result = run_experiment(ds, holdout, cfg, tmp_path / "runs")
    run = RunRecord(result.run_dir).run
    cov = run["evaluation_coverage"]
    # independent count: rows in neither the test set nor any validation fold
    folds = RunRecord(result.run_dir).folds["folds"]
    evaluated = set(holdout.test_idx).union(*[set(f["val_idx"]) for f in folds])
    never = sorted(set(range(ds.n_rows)) - evaluated)
    assert cov["forced_to_train"]["n_rows"] == len(never) == 300
    assert cov["forced_to_train"]["n_positive"] == int(ds.y[never].sum()) == 2
    assert cov["forced_to_train"]["pct_of_rows"] == pytest.approx(30.0)
    assert cov["forced_to_train"]["group_sizes"] == [300]
    assert cov["forced_to_train"]["group_positive_counts"] == [2]
    assert cov["cutoff"]["holdout_max_eval_group_fraction"] == 0.25
    assert cov["cutoff"]["cv_max_eval_group_fraction"] == 0.3  # config parameter is recorded
    assert cov["warning"] is True
    assert "evaluation_coverage_gap" in {w["code"] for w in run["split_warnings"]}
    md = generate_report(result.run_dir).markdown.read_text(encoding="utf-8")
    section = md.split("## 5. Evaluation coverage")[1].split("## 6.")[0]
    assert "**WARNING:** 300 rows (30.0% of the dataset, 2 positives)" in section
    assert "do not describe these rows" in section
    assert "| Forced to train, never evaluated: rows / positives | 300 / 2 |" in section
    assert "1: 300 rows (2 positive)" in section


def test_evaluation_coverage_without_pinning_has_no_warning(write_csv, tmp_path) -> None:
    from imbalancelab.reporting import generate_report

    ds = _ds(write_csv, duplicate_groups=False)
    cfg = ExperimentConfig.model_validate({"candidates": [], "cv": {"n_splits": 3, "n_repeats": 1}})
    result = run_experiment(ds, make_holdout(ds), cfg, tmp_path / "runs")
    cov = RunRecord(result.run_dir).run["evaluation_coverage"]
    assert cov["forced_to_train"]["n_rows"] == 0 and cov["warning"] is False
    assert cov["n_rows_evaluated"] == ds.n_rows and cov["cutoff"]["applies"] is False
    md = generate_report(result.run_dir).markdown.read_text(encoding="utf-8")
    section = md.split("## 5. Evaluation coverage")[1].split("## 6.")[0]
    assert "WARNING" not in section and "not applicable" in section


def test_amend_evaluation_coverage_reproduces_and_verifies_fold_hash(write_csv, tmp_path) -> None:
    import json

    from imbalancelab.evaluation.runner import amend_evaluation_coverage

    ds = _ds(write_csv, giant_cluster_frame(n=1000, giant=300), "amend.csv")
    cfg = ExperimentConfig.model_validate({"candidates": [], "cv": {"n_splits": 3, "n_repeats": 1}})
    result = run_experiment(ds, make_holdout(ds), cfg, tmp_path / "runs")
    path = result.run_dir / "run.json"
    original = json.loads(path.read_text())
    stripped = {k: v for k, v in original.items() if k != "evaluation_coverage"}
    stripped["split_warnings"] = [
        w for w in original["split_warnings"] if w["code"] != "evaluation_coverage_gap"
    ]
    path.write_text(json.dumps(stripped))
    coverage = amend_evaluation_coverage(ds, result.run_dir)
    amended = json.loads(path.read_text())
    assert coverage == original["evaluation_coverage"] == amended["evaluation_coverage"]
    assert "evaluation_coverage_gap" in {w["code"] for w in amended["split_warnings"]}
    assert "fold-index SHA-256 verified" in amended["amendments"][-1]["what"]
    amended["cv"]["fold_indices_sha256"] = "0" * 64
    path.write_text(json.dumps(amended))
    with pytest.raises(ValueError, match="fold-index"):
        amend_evaluation_coverage(ds, result.run_dir)
    other = _ds(write_csv, giant_cluster_frame(n=1000, giant=300, seed=1), "other.csv")
    with pytest.raises(ValueError, match="SHA-256"):
        amend_evaluation_coverage(other, result.run_dir)
