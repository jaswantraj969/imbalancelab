"""Dataset profiling: class balance, data-quality checks, and leakage suspicions."""

import re
from typing import Literal

import numpy as np
import pandas as pd
from pandas.api import types as ptypes
from pydantic import BaseModel, Field
from sklearn.metrics import roc_auc_score

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.profiling.warnings import ProfileWarning

ColumnRole = Literal["feature", "target", "id", "group", "time"]


class ProfileThresholds(BaseModel):
    """Tunable cut-offs for the profiling heuristics."""

    near_constant_ratio: float = Field(default=0.99, gt=0, le=1)
    id_unique_ratio: float = Field(default=0.95, gt=0, le=1)
    id_min_rows: int = Field(default=20, ge=1)
    high_missing_ratio: float = Field(default=0.5, gt=0, le=1)
    leak_auc: float = Field(default=0.95, gt=0.5, le=1)
    pure_category_min_support: int = Field(default=20, ge=1)
    pure_category_max_chance: float = Field(default=1e-4, gt=0, lt=1)


class ClassBalance(BaseModel):
    n_rows: int
    n_positive: int
    n_negative: int
    positive_rate: float
    imbalance_ratio: float | None  # negatives per positive; None if no positives


class ColumnProfile(BaseModel):
    name: str
    role: ColumnRole
    dtype: str
    n_missing: int
    missing_ratio: float
    n_unique: int


class DuplicateSummary(BaseModel):
    n_exact_duplicate_rows: int  # rows identical to an earlier row (all non-ID columns)
    n_conflicting_groups: int  # identical features, different labels
    n_conflicting_rows: int


class DatasetProfile(BaseModel):
    """JSON-serialisable dataset profile."""

    dataset_sha256: str
    n_rows: int
    n_columns: int
    n_features: int
    target: str
    positive_label: str
    class_balance: ClassBalance
    columns: list[ColumnProfile]
    duplicates: DuplicateSummary
    warnings: list[ProfileWarning]
    notes: list[str]
    thresholds: ProfileThresholds


def profile_dataset(
    dataset: LoadedDataset, thresholds: ProfileThresholds | None = None
) -> DatasetProfile:
    """Profile ``dataset``. Every heuristic finding is returned as a :class:`ProfileWarning`."""
    th = thresholds or ProfileThresholds()
    frame, y, schema = dataset.frame, dataset.y, dataset.schema
    features = dataset.feature_columns
    warnings: list[ProfileWarning] = []

    roles: dict[str, ColumnRole] = {schema.target: "target"}
    if schema.id_column:
        roles[schema.id_column] = "id"
    if schema.group_column:
        roles[schema.group_column] = "group"
    if schema.time_column:
        roles[schema.time_column] = "time"

    columns = [
        ColumnProfile(
            name=str(c),
            role=roles.get(c, "feature"),
            dtype=str(frame[c].dtype),
            n_missing=int(frame[c].isna().sum()),
            missing_ratio=float(frame[c].isna().mean()),
            n_unique=int(frame[c].nunique(dropna=True)),
        )
        for c in frame.columns
    ]

    if not features:
        warnings.append(
            ProfileWarning(
                code="no_features",
                message="Dataset has no feature columns besides target/id/group/time.",
                evidence={"n_columns": len(frame.columns)},
            )
        )

    for col in features:
        warnings.extend(_column_quality_warnings(frame[col], col, th))
        warnings.extend(_id_like_warnings(frame[col], col, th))
        warnings.extend(_leak_warnings(frame[col], col, y, th))
    warnings.extend(_name_match_warnings(features, schema.target))

    duplicates = _duplicate_summary(frame, y, features, schema.id_column)
    if duplicates.n_exact_duplicate_rows:
        warnings.append(
            ProfileWarning(
                code="exact_duplicates",
                message=(
                    f"{duplicates.n_exact_duplicate_rows} row(s) duplicate an earlier row; "
                    "duplicates crossing split boundaries can inflate scores."
                ),
                evidence={"n_rows": duplicates.n_exact_duplicate_rows},
            )
        )
    if duplicates.n_conflicting_groups:
        warnings.append(
            ProfileWarning(
                code="conflicting_duplicates",
                message=(
                    f"{duplicates.n_conflicting_groups} group(s) of rows have identical "
                    "features but different labels (possible label noise)."
                ),
                evidence={
                    "n_groups": duplicates.n_conflicting_groups,
                    "n_rows": duplicates.n_conflicting_rows,
                },
            )
        )

    n_pos = int(y.sum())
    n_neg = int(len(y) - n_pos)
    balance = ClassBalance(
        n_rows=len(y),
        n_positive=n_pos,
        n_negative=n_neg,
        positive_rate=n_pos / len(y),
        imbalance_ratio=(n_neg / n_pos) if n_pos else None,
    )
    return DatasetProfile(
        dataset_sha256=dataset.sha256,
        n_rows=len(frame),
        n_columns=len(frame.columns),
        n_features=len(features),
        target=schema.target,
        positive_label=str(schema.positive_label),
        class_balance=balance,
        columns=columns,
        duplicates=duplicates,
        warnings=warnings,
        notes=list(dataset.notes),
        thresholds=th,
    )


def _column_quality_warnings(
    series: pd.Series, col: str, th: ProfileThresholds
) -> list[ProfileWarning]:
    out: list[ProfileWarning] = []
    n = len(series)
    n_missing = int(series.isna().sum())
    if n_missing == n:
        out.append(
            ProfileWarning(
                code="all_missing",
                column=col,
                message=f"Column {col!r} is entirely missing.",
                evidence={"missing_ratio": 1.0},
            )
        )
        return out
    if n_missing / n >= th.high_missing_ratio:
        out.append(
            ProfileWarning(
                code="high_missingness",
                column=col,
                severity="info",
                message=f"Column {col!r} is {n_missing / n:.1%} missing.",
                evidence={"missing_ratio": n_missing / n, "threshold": th.high_missing_ratio},
            )
        )
    n_unique = int(series.nunique(dropna=False))
    if n_unique <= 1:
        out.append(
            ProfileWarning(
                code="constant_column",
                column=col,
                message=f"Column {col!r} has a single value and carries no information.",
                evidence={"n_unique": n_unique},
            )
        )
        return out
    top_ratio = float(series.value_counts(dropna=False, normalize=True).iloc[0])
    if top_ratio >= th.near_constant_ratio:
        out.append(
            ProfileWarning(
                code="near_constant_column",
                column=col,
                severity="info",
                message=f"Column {col!r} is near-constant: top value covers {top_ratio:.2%}.",
                evidence={"top_value_ratio": top_ratio, "threshold": th.near_constant_ratio},
            )
        )
    return out


def _id_like_warnings(series: pd.Series, col: str, th: ProfileThresholds) -> list[ProfileWarning]:
    non_null = series.dropna()
    n = len(non_null)
    if n < th.id_min_rows:
        return []
    unique_ratio = float(non_null.nunique() / n)
    is_float = ptypes.is_float_dtype(series)
    integer_valued = ptypes.is_integer_dtype(series) or (
        is_float and bool(np.all(np.mod(non_null.to_numpy(dtype=float), 1) == 0))
    )
    monotonic = (
        integer_valued
        and unique_ratio == 1.0
        and (non_null.is_monotonic_increasing or non_null.is_monotonic_decreasing)
    )
    high_card = (not is_float or integer_valued) and unique_ratio >= th.id_unique_ratio
    if not (monotonic or high_card):
        return []
    reason = "monotonic unique integers" if monotonic else "near-unique values"
    return [
        ProfileWarning(
            code="id_like_column",
            column=col,
            message=(
                f"Column {col!r} looks like a possible identifier ({reason}); identifiers "
                "rarely generalise and may encode row order."
            ),
            evidence={
                "unique_ratio": unique_ratio,
                "monotonic": bool(monotonic),
                "threshold": th.id_unique_ratio,
            },
        )
    ]


def _leak_warnings(
    series: pd.Series, col: str, y: np.ndarray, th: ProfileThresholds
) -> list[ProfileWarning]:
    if ptypes.is_bool_dtype(series):
        series = series.astype(float)
    if ptypes.is_numeric_dtype(series):
        return _numeric_leak_warning(series, col, y, th)
    if ptypes.is_datetime64_any_dtype(series):
        return []
    return _pure_category_warnings(series, col, y, th)


def _numeric_leak_warning(
    series: pd.Series, col: str, y: np.ndarray, th: ProfileThresholds
) -> list[ProfileWarning]:
    values = series.to_numpy(dtype=float)
    mask = ~np.isnan(values)
    y_used = y[mask]
    if len(np.unique(y_used)) < 2 or len(np.unique(values[mask])) < 2:
        return []
    auc = float(roc_auc_score(y_used, values[mask]))
    strength = max(auc, 1.0 - auc)
    if strength < th.leak_auc:
        return []
    return [
        ProfileWarning(
            code="suspected_target_leak",
            column=col,
            message=(
                f"Column {col!r} alone separates the classes with univariate ROC AUC "
                f"{auc:.3f}; suspected target leakage. Check whether it is known at "
                "prediction time."
            ),
            evidence={
                "univariate_auc": auc,
                "threshold": th.leak_auc,
                "n_used": int(mask.sum()),
                "n_dropped_missing": int((~mask).sum()),
            },
        )
    ]


def _pure_category_warnings(
    series: pd.Series, col: str, y: np.ndarray, th: ProfileThresholds
) -> list[ProfileWarning]:
    base_rate = float(y.mean())
    if base_rate in (0.0, 1.0):
        return []
    keys = series.astype(object).where(series.notna(), "<missing>")
    stats = pd.DataFrame({"k": keys.to_numpy(), "y": y}).groupby("k")["y"].agg(["size", "mean"])
    out: list[ProfileWarning] = []
    for category, row in stats.iterrows():
        support, rate = int(row["size"]), float(row["mean"])
        if support < th.pure_category_min_support or rate not in (0.0, 1.0):
            continue
        chance = base_rate**support if rate == 1.0 else (1.0 - base_rate) ** support
        if chance > th.pure_category_max_chance:
            continue
        out.append(
            ProfileWarning(
                code="suspected_target_leak",
                column=col,
                message=(
                    f"Category {category!r} of {col!r} ({support} rows) is entirely "
                    f"{'positive' if rate == 1.0 else 'negative'}; probability of this under "
                    f"the base rate is {chance:.2e}. Possible target leakage."
                ),
                evidence={
                    "category": str(category),
                    "support": support,
                    "positive_rate": rate,
                    "base_rate": base_rate,
                    "chance_probability": chance,
                    "max_chance": th.pure_category_max_chance,
                },
            )
        )
    return out


def _normalise_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _name_match_warnings(features: list[str], target: str) -> list[ProfileWarning]:
    norm_target = _normalise_name(target)
    if not norm_target:
        return []
    out: list[ProfileWarning] = []
    for col in features:
        norm = _normalise_name(str(col))
        if norm and (norm_target in norm or norm in norm_target):
            out.append(
                ProfileWarning(
                    code="target_name_match",
                    column=col,
                    message=(
                        f"Column {col!r} has a name similar to the target {target!r}; "
                        "possible derived or leaked target."
                    ),
                    evidence={"target": target},
                )
            )
    return out


def feature_row_hashes(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    """Stable per-row hash of ``columns`` (missing values hash consistently)."""
    if not columns:
        return np.zeros(len(frame), dtype=np.uint64)
    return pd.util.hash_pandas_object(frame[columns], index=False).to_numpy()


def _duplicate_summary(
    frame: pd.DataFrame, y: np.ndarray, features: list[str], id_column: str | None
) -> DuplicateSummary:
    non_id = [c for c in frame.columns if c != id_column]
    exact = int(pd.Series(feature_row_hashes(frame, non_id)).duplicated().sum())
    if not features:
        return DuplicateSummary(
            n_exact_duplicate_rows=exact, n_conflicting_groups=0, n_conflicting_rows=0
        )
    grouped = pd.DataFrame({"h": feature_row_hashes(frame, features), "y": y}).groupby("h")["y"]
    nunique = grouped.nunique()
    conflicting = nunique[nunique > 1]
    sizes = grouped.size()
    return DuplicateSummary(
        n_exact_duplicate_rows=exact,
        n_conflicting_groups=len(conflicting),
        n_conflicting_rows=int(sizes.loc[conflicting.index].sum()),
    )
