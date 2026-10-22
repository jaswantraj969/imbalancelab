import json

import numpy as np
import pandas as pd
import pytest

from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.profiling import ProfileThresholds, profile_dataset


def _load(write_csv, frame: pd.DataFrame, **kw: object):
    schema = DatasetSchema.model_validate({"target": "label", "positive_label": 1, **kw})
    return load_dataset(write_csv(frame), schema)


def _codes(profile, column: str | None = None) -> set[str]:
    return {w.code for w in profile.warnings if column is None or w.column == column}


@pytest.fixture
def base() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    n = 200
    y = np.zeros(n, dtype=int)
    y[:20] = 1
    rng.shuffle(y)
    return pd.DataFrame({"x": rng.normal(size=n), "label": y})


def test_class_balance_and_json_serialisable(write_csv, base) -> None:
    profile = profile_dataset(_load(write_csv, base))
    cb = profile.class_balance
    assert (cb.n_rows, cb.n_positive, cb.n_negative) == (200, 20, 180)
    assert cb.positive_rate == pytest.approx(0.1)
    assert cb.imbalance_ratio == pytest.approx(9.0)
    json.dumps(profile.model_dump(mode="json"))
    assert profile.n_features == 1
    assert {c.role for c in profile.columns} == {"feature", "target"}


def test_missingness_constant_near_constant_all_nan(write_csv, base) -> None:
    frame = base.copy()
    frame["const"] = 7
    frame["near"] = 0
    frame.loc[0, "near"] = 1
    frame["all_nan"] = np.nan
    frame["mostly_nan"] = np.where(np.arange(200) < 150, np.nan, 1.0)
    profile = profile_dataset(_load(write_csv, frame))
    assert "constant_column" in _codes(profile, "const")
    assert "near_constant_column" in _codes(profile, "near")
    assert _codes(profile, "all_nan") == {"all_missing"}
    assert "high_missingness" in _codes(profile, "mostly_nan")
    col = next(c for c in profile.columns if c.name == "mostly_nan")
    assert col.n_missing == 150 and col.missing_ratio == pytest.approx(0.75)


def test_duplicates_and_conflicting_labels(write_csv) -> None:
    frame = pd.DataFrame(
        {
            "id": range(6),
            "x": [1, 1, 2, 3, 3, 4],
            "label": [0, 0, 1, 0, 1, 1],
        }
    )
    profile = profile_dataset(_load(write_csv, frame, id_column="id"))
    # rows 0/1 identical (ignoring id); rows 3/4 same features but different labels
    assert profile.duplicates.n_exact_duplicate_rows == 1
    assert profile.duplicates.n_conflicting_groups == 1
    assert profile.duplicates.n_conflicting_rows == 2
    assert {"exact_duplicates", "conflicting_duplicates"} <= _codes(profile)


def test_id_like_columns(write_csv, base) -> None:
    frame = base.copy()
    frame["seq"] = np.arange(200)
    frame["uuid"] = [f"u{i}" for i in np.random.default_rng(0).permutation(200)]
    profile = profile_dataset(_load(write_csv, frame))
    assert "id_like_column" in _codes(profile, "seq")
    assert "id_like_column" in _codes(profile, "uuid")
    assert "id_like_column" not in _codes(profile, "x")  # continuous floats are not IDs
    seq = next(w for w in profile.warnings if w.column == "seq" and w.code == "id_like_column")
    assert seq.evidence["monotonic"] is True


def test_target_leak_suspects_are_warnings_with_evidence(write_csv, base) -> None:
    frame = base.copy()
    frame["leaky"] = frame["label"] * 10 + np.random.default_rng(2).normal(size=200) * 0.01
    frame.loc[:4, "leaky"] = np.nan  # NaNs are dropped before computing AUC
    frame["label_copy_name"] = np.random.default_rng(3).normal(size=200)
    frame["cat"] = np.where(frame["label"] == 1, "P", np.where(np.arange(200) % 2, "A", "B"))
    profile = profile_dataset(_load(write_csv, frame))

    leak = [w for w in profile.warnings if w.code == "suspected_target_leak"]
    numeric = next(w for w in leak if w.column == "leaky")
    assert numeric.evidence["univariate_auc"] >= 0.95
    assert numeric.evidence["n_dropped_missing"] == 5
    assert "suspected" in numeric.message.lower()
    assert numeric.severity == "warning"
    pure_by_cat = {w.evidence["category"]: w for w in leak if w.column == "cat"}
    pure = pure_by_cat["P"]
    assert pure.evidence["positive_rate"] == 1.0 and pure.evidence["support"] == 20
    # ~90 all-negative rows at a 10% base rate: chance 0.9**90 < 1e-4, so also flagged
    assert pure_by_cat["A"].evidence["positive_rate"] == 0.0
    assert pure_by_cat["A"].evidence["chance_probability"] < 1e-4
    assert "possible" in pure.message.lower()
    assert "target_name_match" in _codes(profile, "label_copy_name")
    assert "suspected_target_leak" not in _codes(profile, "x")


def test_pure_negative_category_needs_low_chance(write_csv, base) -> None:
    frame = base.copy()
    # an all-negative category of 25 rows is unremarkable at a 10% base rate
    frame["cat"] = "other"
    neg_rows = frame.index[frame["label"] == 0][:25]
    frame.loc[neg_rows, "cat"] = "N"
    profile = profile_dataset(_load(write_csv, frame))
    assert "suspected_target_leak" not in _codes(profile, "cat")
    strict = ProfileThresholds(pure_category_max_chance=0.5)
    profile2 = profile_dataset(_load(write_csv, frame), strict)
    assert "suspected_target_leak" in _codes(profile2, "cat")


def test_configurable_thresholds(write_csv, base) -> None:
    frame = base.copy()
    frame["weak"] = frame["label"] + np.random.default_rng(5).normal(size=200) * 0.6
    default = profile_dataset(_load(write_csv, frame))
    assert "suspected_target_leak" not in _codes(default, "weak")
    loose = profile_dataset(_load(write_csv, frame), ProfileThresholds(leak_auc=0.6))
    assert "suspected_target_leak" in _codes(loose, "weak")


def test_target_only_dataset(write_csv) -> None:
    profile = profile_dataset(_load(write_csv, pd.DataFrame({"label": [0, 1, 0, 1]})))
    assert profile.n_features == 0
    assert "no_features" in _codes(profile)
    assert profile.duplicates.n_conflicting_groups == 0


def test_bool_and_datetime_features(write_csv, base) -> None:
    frame = base.copy()
    frame["flag"] = frame["label"].astype(bool)
    frame["when"] = pd.date_range("2024-01-01", periods=200, freq="h")
    schema = DatasetSchema(target="label", positive_label=1, expected_dtypes={"when": "datetime"})
    ds = load_dataset(write_csv(frame), schema)
    profile = profile_dataset(ds)
    assert "suspected_target_leak" in _codes(profile, "flag")
    assert "suspected_target_leak" not in _codes(profile, "when")
