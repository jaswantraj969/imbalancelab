import numpy as np
import pandas as pd
import pytest

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.splitting import (
    CVConfig,
    HoldoutConfig,
    HoldoutMismatchError,
    SplitError,
    check_holdout,
    cross_boundary_duplicates,
    get_or_create_holdout,
    indices_sha256,
    make_cv_folds,
    make_holdout,
)


def _ds(write_csv, frame: pd.DataFrame | None = None, name: str = "d.csv", **kw: object):
    frame = make_imbalanced_frame() if frame is None else frame
    schema = DatasetSchema.model_validate(
        {"target": "label", "positive_label": "yes", "id_column": "row_id", **kw}
    )
    return load_dataset(write_csv(frame, name), schema)


def _assert_partition(holdout, n: int) -> None:
    train, test, gap = set(holdout.train_idx), set(holdout.test_idx), set(holdout.gap_idx)
    assert not (train & test) and not (train & gap) and not (test & gap)
    assert train | test | gap == set(range(n))


# ----------------------------------------------------------------- stratified


def test_stratified_holdout_is_reproducible_and_stratified(write_csv) -> None:
    ds = _ds(write_csv)
    h1 = make_holdout(ds, HoldoutConfig(test_size=0.25, seed=7))
    h2 = make_holdout(ds, HoldoutConfig(test_size=0.25, seed=7))
    h3 = make_holdout(ds, HoldoutConfig(test_size=0.25, seed=8))
    assert h1 == h2 and h1.test_idx != h3.test_idx
    _assert_partition(h1, ds.n_rows)
    assert h1.test_sha256 == indices_sha256(h1.test_idx)
    rate = ds.y.mean()
    assert abs(ds.y[h1.test_idx].mean() - rate) < 0.02
    assert len(h1.test_idx) == pytest.approx(0.25 * ds.n_rows, abs=2)


def test_stratified_cv_folds_within_outer_train(write_csv) -> None:
    ds = _ds(write_csv)
    holdout = make_holdout(ds)
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2, seed=3))
    assert len(plan.folds) == 8 and plan.n_repeats_effective == 2
    outer = set(holdout.train_idx)
    rate = ds.y[holdout.train_idx].mean()
    for repeat in range(2):
        folds = [f for f in plan.folds if f.repeat == repeat]
        vals = [i for f in folds for i in f.val_idx]
        assert sorted(vals) == sorted(outer)  # each repeat partitions outer-train
        for f in folds:
            assert set(f.train_idx) <= outer and set(f.val_idx) <= outer
            assert not set(f.train_idx) & set(f.val_idx)
            assert not set(f.val_idx) & set(holdout.test_idx)
            assert abs(ds.y[f.val_idx].mean() - rate) < 0.05
    again = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2, seed=3))
    assert again.fold_indices_sha256 == plan.fold_indices_sha256
    other = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2, seed=4))
    assert other.fold_indices_sha256 != plan.fold_indices_sha256


def test_too_few_minority_samples_for_folds(write_csv) -> None:
    frame = make_imbalanced_frame(n=60, positive_rate=0.0)
    frame.loc[:5, "label"] = "yes"  # 6 positives -> ~4-5 in outer-train
    ds = _ds(write_csv, frame)
    holdout = make_holdout(ds)
    with pytest.raises(SplitError, match="minority"):
        make_cv_folds(ds, holdout, CVConfig(n_splits=10))


def test_holdout_requires_two_per_class(write_csv) -> None:
    frame = make_imbalanced_frame(n=40, positive_rate=0.0)
    frame["label"] = "no"
    frame.loc[0, "label"] = "yes"
    with pytest.raises(SplitError):
        make_holdout(_ds(write_csv, frame))


# ----------------------------------------------------------------- group


def test_group_splits_never_share_groups(write_csv) -> None:
    ds = _ds(write_csv, group_column="group", split_strategy="group")
    groups = ds.frame["group"].to_numpy()
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=1))
    _assert_partition(holdout, ds.n_rows)
    assert not set(groups[holdout.train_idx]) & set(groups[holdout.test_idx])
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2))
    assert len(plan.folds) == 8
    for f in plan.folds:
        assert not set(groups[f.train_idx]) & set(groups[f.val_idx])
        assert set(f.train_idx) | set(f.val_idx) <= set(holdout.train_idx)
    assert (
        make_holdout(ds, HoldoutConfig(seed=1)).test_idx
        == make_holdout(ds, HoldoutConfig(seed=1)).test_idx
    )


def test_group_errors(write_csv) -> None:
    ds = _ds(
        write_csv, make_imbalanced_frame(n_groups=3), group_column="group", split_strategy="group"
    )
    with pytest.raises(SplitError, match="groups"):
        make_holdout(ds, HoldoutConfig(test_size=0.2))
    ds2 = _ds(
        write_csv,
        make_imbalanced_frame(n_groups=8),
        "g.csv",
        group_column="group",
        split_strategy="group",
    )
    holdout = make_holdout(ds2, HoldoutConfig(test_size=0.5))
    with pytest.raises(SplitError, match="groups"):
        make_cv_folds(ds2, holdout, CVConfig(n_splits=6))
    frame = make_imbalanced_frame()
    frame["group"] = frame["group"].astype(float)
    frame.loc[3, "group"] = np.nan
    ds3 = _ds(write_csv, frame, "g3.csv", group_column="group", split_strategy="group")
    with pytest.raises(SplitError, match="missing"):
        make_holdout(ds3)


# ----------------------------------------------------------------- temporal


@pytest.mark.parametrize("gap", [0, 3])
def test_temporal_ordering_holds(write_csv, gap: int) -> None:
    ds = _ds(write_csv, time_column="ts", split_strategy="temporal")
    t = ds.frame["ts"].to_numpy()
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, gap=gap))
    _assert_partition(holdout, ds.n_rows)
    assert t[holdout.train_idx].max() < t[holdout.test_idx].min()
    assert len(np.unique(t[holdout.gap_idx])) == gap
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=3, n_repeats=2, gap=gap))
    assert plan.n_repeats_effective == 1 and len(plan.folds) == 3
    assert "temporal_repeats_ignored" in {w.code for w in plan.warnings}
    for f in plan.folds:
        assert t[f.train_idx].max() < t[f.val_idx].min()
        between = np.unique(t[(t > t[f.train_idx].max()) & (t < t[f.val_idx].min())])
        assert len(between) == gap
        assert set(f.val_idx) <= set(holdout.train_idx)
    sizes = [len(f.train_idx) for f in plan.folds]
    assert sizes == sorted(sizes)  # expanding window


def test_temporal_ties_never_straddle_boundary(write_csv) -> None:
    frame = make_imbalanced_frame(n=200)
    frame["ts"] = np.repeat(np.arange(40), 5)  # 5 rows per time value
    ds = _ds(write_csv, frame, time_column="ts", split_strategy="temporal")
    t = ds.frame["ts"].to_numpy()
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.23))
    assert t[holdout.train_idx].max() < t[holdout.test_idx].min()
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=3, n_repeats=1))
    for f in plan.folds:
        assert t[f.train_idx].max() < t[f.val_idx].min()


def test_temporal_errors(write_csv) -> None:
    frame = make_imbalanced_frame(n=200)
    frame["ts"] = np.repeat([1, 2], 100)
    ds = _ds(write_csv, frame, time_column="ts", split_strategy="temporal")
    with pytest.raises(SplitError):
        make_holdout(ds, HoldoutConfig(gap=1))
    ds2 = _ds(write_csv, None, "t2.csv", time_column="ts", split_strategy="temporal")
    holdout = make_holdout(ds2)
    with pytest.raises(SplitError, match="too few"):
        make_cv_folds(ds2, holdout, CVConfig(n_splits=5, gap=60))
    frame3 = make_imbalanced_frame()
    frame3["ts"] = frame3["ts"].astype(object)
    frame3.loc[4, "ts"] = None
    ds3 = _ds(write_csv, frame3, "t3.csv", time_column="ts", split_strategy="temporal")
    with pytest.raises(SplitError, match="missing"):
        make_holdout(ds3)


def test_single_class_validation_fold_is_warned(write_csv) -> None:
    frame = make_imbalanced_frame(n=200, positive_rate=0.0)
    frame["label"] = "no"
    # positives only early and late: some temporal validation folds have none
    frame.loc[[0, 1, 2, 3, 4, 5, 190, 191, 192, 193, 194, 195], "label"] = "yes"
    ds = _ds(write_csv, frame, time_column="ts", split_strategy="temporal")
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.1))
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=3, n_repeats=1))
    assert "single_class_validation_fold" in {w.code for w in plan.warnings}


# ----------------------------------------------------------------- holdout storage


def test_get_or_create_holdout_once(write_csv, tmp_path) -> None:
    ds = _ds(write_csv)
    path = tmp_path / "store" / "holdout.json"
    h1 = get_or_create_holdout(ds, HoldoutConfig(seed=5), path)
    assert path.exists()
    h2 = get_or_create_holdout(ds, None, path)  # reuse without config
    assert h1 == h2
    with pytest.raises(HoldoutMismatchError, match="config"):
        get_or_create_holdout(ds, HoldoutConfig(seed=6), path)
    other = _ds(write_csv, make_imbalanced_frame(seed=9), "other.csv")
    with pytest.raises(HoldoutMismatchError, match="dataset"):
        get_or_create_holdout(other, None, path)
    tampered = h1.model_copy(update={"test_idx": h1.test_idx[1:]})
    tampered.save(path)
    with pytest.raises(HoldoutMismatchError, match="SHA-256"):
        get_or_create_holdout(ds, None, path)
    with pytest.raises(HoldoutMismatchError):
        check_holdout(ds, tampered)
    grouped = _ds(write_csv, None, "g.csv", group_column="group", split_strategy="group")
    h1.model_copy(update={"dataset_sha256": grouped.sha256}).save(path)
    with pytest.raises(HoldoutMismatchError, match="strategy"):
        get_or_create_holdout(grouped, None, path)


def test_check_holdout_overlap(write_csv) -> None:
    ds = _ds(write_csv)
    h = make_holdout(ds)
    bad = h.model_copy(update={"train_idx": [*h.train_idx, h.test_idx[0]]})
    with pytest.raises(HoldoutMismatchError, match="overlap"):
        check_holdout(ds, bad)
    with pytest.raises(HoldoutMismatchError):
        make_cv_folds(ds, h.model_copy(update={"n_rows": 3}))


# ----------------------------------------------------------------- duplicates


def test_cross_boundary_duplicates_detected(write_csv) -> None:
    frame = make_imbalanced_frame(n=200)
    dup = frame.iloc[:40].copy()
    dup["row_id"] = np.arange(200, 240)
    ds = _ds(write_csv, pd.concat([frame, dup], ignore_index=True))
    holdout = make_holdout(ds, HoldoutConfig(seed=0))
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=3, n_repeats=1))
    warnings = cross_boundary_duplicates(ds, holdout, plan)
    assert len(warnings) == 1
    w = warnings[0]
    assert w.code == "cross_boundary_duplicates" and w.severity == "warning"
    ev = w.evidence
    # count independently
    feats = ds.feature_columns
    keys = np.array([repr(tuple(r)) for r in ds.frame[feats].itertuples(index=False)])
    train_keys = set(keys[holdout.train_idx])
    expected = sum(k in train_keys for k in keys[holdout.test_idx])
    assert ev["test_rows_duplicating_train"] == expected > 0
    assert ev["folds_affected"] >= 1


def test_no_duplicates_no_warning(write_csv) -> None:
    ds = _ds(write_csv)
    holdout = make_holdout(ds)
    assert cross_boundary_duplicates(ds, holdout, make_cv_folds(ds, holdout)) == []
    target_only = _ds(
        write_csv, pd.DataFrame({"row_id": range(20), "label": ["yes", "no"] * 10}), "t.csv"
    )
    assert cross_boundary_duplicates(target_only, make_holdout(target_only)) == []
