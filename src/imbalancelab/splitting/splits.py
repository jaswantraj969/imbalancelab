"""Outer holdout and inner CV folds for stratified, group, and temporal strategies.

All indices are absolute row positions into ``LoadedDataset.frame``. The outer holdout is
created once per dataset (see :func:`get_or_create_holdout`). Inner CV folds are built from
outer-train rows only.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pandas.api import types as ptypes
from pydantic import BaseModel, Field
from sklearn.model_selection import RepeatedStratifiedKFold, StratifiedGroupKFold

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.data.schema import SplitStrategy
from imbalancelab.profiling.warnings import ProfileWarning


class SplitError(ValueError):
    """The requested split cannot be built on this data."""


class HoldoutMismatchError(SplitError):
    """A stored holdout does not match the dataset or the requested config."""


class HoldoutConfig(BaseModel):
    test_size: float = Field(default=0.2, gt=0, lt=1)
    gap: int = Field(default=0, ge=0)  # temporal: distinct time values dropped before test
    seed: int = 42


class CVConfig(BaseModel):
    n_splits: int = Field(default=5, ge=2)
    n_repeats: int = Field(default=3, ge=1)
    gap: int = Field(default=0, ge=0)  # temporal: distinct time values dropped before val
    seed: int = 42


class Holdout(BaseModel):
    strategy: SplitStrategy
    config: HoldoutConfig
    dataset_sha256: str
    n_rows: int
    train_idx: list[int]
    test_idx: list[int]
    gap_idx: list[int] = Field(default_factory=list)
    test_sha256: str

    def save(self, path: Path) -> None:
        Path(path).write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Holdout":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


class Fold(BaseModel):
    repeat: int
    fold: int
    train_idx: list[int]
    val_idx: list[int]


class CVPlan(BaseModel):
    strategy: SplitStrategy
    config: CVConfig
    n_repeats_effective: int
    folds: list[Fold]
    fold_indices_sha256: str
    warnings: list[ProfileWarning] = Field(default_factory=list)


def indices_sha256(payload: Any) -> str:
    """SHA-256 of a canonical JSON encoding of an index structure."""
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def folds_sha256(folds: list[Fold]) -> str:
    return indices_sha256([[f.repeat, f.fold, f.train_idx, f.val_idx] for f in folds])


def _sorted_list(idx: np.ndarray) -> list[int]:
    return [int(i) for i in np.sort(idx)]


def _require_both_classes(y: np.ndarray, idx: np.ndarray, what: str) -> None:
    n_pos = int(y[idx].sum())
    if n_pos == 0 or n_pos == len(idx):
        raise SplitError(f"{what} contains a single class ({len(idx)} rows, {n_pos} positive)")


def _time_values(dataset: LoadedDataset) -> np.ndarray:
    col = dataset.schema.time_column
    if col is None:
        raise SplitError("temporal strategy requires schema.time_column")
    series = dataset.frame[col]
    if series.isna().any():
        raise SplitError(f"time column {col!r} has missing values")
    if ptypes.is_datetime64_any_dtype(series):
        return pd.to_datetime(series).to_numpy(dtype="datetime64[ns]").astype(np.int64)
    return series.to_numpy(dtype=float)


def _groups(dataset: LoadedDataset) -> np.ndarray:
    col = dataset.schema.group_column
    if col is None:
        raise SplitError("group strategy requires schema.group_column")
    series = dataset.frame[col]
    if series.isna().any():
        raise SplitError(f"group column {col!r} has missing values")
    return series.astype(str).to_numpy()


# --------------------------------------------------------------------------- holdout


def make_holdout(dataset: LoadedDataset, config: HoldoutConfig | None = None) -> Holdout:
    """Create the outer train/test holdout using the schema's split strategy."""
    config = config or HoldoutConfig()
    strategy = dataset.schema.split_strategy
    n = dataset.n_rows
    y = dataset.y
    all_idx = np.arange(n)
    gap_idx = np.array([], dtype=int)

    if strategy == "stratified":
        n_test = int(np.ceil(config.test_size * n))
        n_pos = int(y.sum())
        if min(n_pos, n - n_pos) < 2 or n_test < 2 or n - n_test < 2:
            raise SplitError("stratified holdout needs at least 2 samples of each class per side")
        rng = np.random.default_rng(config.seed)
        test_parts = []
        for cls in (0, 1):
            members = all_idx[y == cls]
            k = int(round(config.test_size * len(members)))
            k = min(max(k, 1), len(members) - 1)
            test_parts.append(rng.choice(members, size=k, replace=False))
        test_idx = np.concatenate(test_parts)
        train_idx = np.setdiff1d(all_idx, test_idx)
    elif strategy == "group":
        groups = _groups(dataset)
        n_folds = max(2, int(round(1.0 / config.test_size)))
        if len(np.unique(groups)) < n_folds:
            raise SplitError(
                f"group holdout needs at least {n_folds} distinct groups, "
                f"found {len(np.unique(groups))}"
            )
        sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=config.seed)
        train_idx, test_idx = next(iter(sgkf.split(all_idx, y, groups)))
    else:
        t = _time_values(dataset)
        uniq = np.unique(t)
        if len(uniq) < 2 + config.gap:
            raise SplitError("temporal holdout needs more distinct time values than gap + 1")
        counts = np.array([np.sum(t == u) for u in uniq])
        rows_from_end = np.cumsum(counts[::-1])[::-1]  # rows with time >= uniq[k]
        target = config.test_size * n
        candidates = np.arange(1 + config.gap, len(uniq))
        k = int(candidates[np.argmin(np.abs(rows_from_end[candidates] - target))])
        test_idx = all_idx[t >= uniq[k]]
        train_idx = all_idx[t < uniq[k - config.gap]]
        gap_idx = all_idx[(t >= uniq[k - config.gap]) & (t < uniq[k])]

    _require_both_classes(y, np.asarray(train_idx), "outer-train split")
    _require_both_classes(y, np.asarray(test_idx), "test split")
    test_list = _sorted_list(np.asarray(test_idx))
    return Holdout(
        strategy=strategy,
        config=config,
        dataset_sha256=dataset.sha256,
        n_rows=n,
        train_idx=_sorted_list(np.asarray(train_idx)),
        test_idx=test_list,
        gap_idx=_sorted_list(gap_idx),
        test_sha256=indices_sha256(test_list),
    )


def get_or_create_holdout(
    dataset: LoadedDataset, config: HoldoutConfig | None, path: Path
) -> Holdout:
    """Load the stored holdout at ``path`` or create and store it (once per dataset).

    A stored holdout is reused only if it belongs to the same dataset (SHA-256) and was made
    with the same strategy and config; otherwise :class:`HoldoutMismatchError` is raised so
    that a new test set is never silently drawn.
    """
    path = Path(path)
    if path.exists():
        holdout = Holdout.load(path)
        if holdout.dataset_sha256 != dataset.sha256:
            raise HoldoutMismatchError("stored holdout belongs to a different dataset (SHA-256)")
        if holdout.strategy != dataset.schema.split_strategy:
            raise HoldoutMismatchError("stored holdout used a different split strategy")
        if config is not None and holdout.config != config:
            raise HoldoutMismatchError("stored holdout was created with a different config")
        if holdout.test_sha256 != indices_sha256(holdout.test_idx):
            raise HoldoutMismatchError("stored holdout test indices fail their SHA-256 check")
        return holdout
    holdout = make_holdout(dataset, config)
    path.parent.mkdir(parents=True, exist_ok=True)
    holdout.save(path)
    return holdout


def check_holdout(dataset: LoadedDataset, holdout: Holdout) -> None:
    """Raise if ``holdout`` does not belong to ``dataset`` or has been tampered with."""
    if holdout.dataset_sha256 != dataset.sha256 or holdout.n_rows != dataset.n_rows:
        raise HoldoutMismatchError("holdout does not belong to this dataset")
    if holdout.test_sha256 != indices_sha256(holdout.test_idx):
        raise HoldoutMismatchError("holdout test indices fail their SHA-256 check")
    if set(holdout.train_idx) & set(holdout.test_idx):
        raise HoldoutMismatchError("holdout train and test indices overlap")


# --------------------------------------------------------------------------- inner CV


def make_cv_folds(
    dataset: LoadedDataset, holdout: Holdout, config: CVConfig | None = None
) -> CVPlan:
    """Inner CV folds over outer-train rows, using the schema's split strategy."""
    config = config or CVConfig()
    check_holdout(dataset, holdout)
    strategy = dataset.schema.split_strategy
    outer = np.asarray(holdout.train_idx)
    y = dataset.y
    y_outer = y[outer]
    warnings: list[ProfileWarning] = []
    folds: list[Fold] = []
    n_repeats = config.n_repeats

    if strategy == "stratified":
        n_min = int(min(y_outer.sum(), len(y_outer) - y_outer.sum()))
        if n_min < config.n_splits:
            raise SplitError(
                f"only {n_min} minority samples in outer-train; cannot build "
                f"{config.n_splits} stratified folds"
            )
        rskf = RepeatedStratifiedKFold(
            n_splits=config.n_splits, n_repeats=config.n_repeats, random_state=config.seed
        )
        for i, (tr, va) in enumerate(rskf.split(outer, y_outer)):
            folds.append(_fold(i // config.n_splits, i % config.n_splits, outer[tr], outer[va]))
    elif strategy == "group":
        groups = _groups(dataset)[outer]
        n_groups = len(np.unique(groups))
        if n_groups < config.n_splits:
            raise SplitError(
                f"only {n_groups} groups in outer-train; cannot build {config.n_splits} folds"
            )
        for r in range(config.n_repeats):
            sgkf = StratifiedGroupKFold(
                n_splits=config.n_splits, shuffle=True, random_state=config.seed + r
            )
            for f, (tr, va) in enumerate(sgkf.split(outer, y_outer, groups)):
                folds.append(_fold(r, f, outer[tr], outer[va]))
    else:
        if config.n_repeats != 1:
            warnings.append(
                ProfileWarning(
                    code="temporal_repeats_ignored",
                    severity="info",
                    message="Temporal CV is deterministic; n_repeats was set to 1.",
                    evidence={"requested_n_repeats": config.n_repeats},
                )
            )
        n_repeats = 1
        t = _time_values(dataset)[outer]
        uniq = np.unique(t)
        chunks = np.array_split(np.arange(len(uniq)), config.n_splits + 1)
        if any(len(c) <= config.gap for c in chunks[1:]):
            raise SplitError(
                f"{len(uniq)} distinct time values are too few for {config.n_splits} temporal "
                f"folds with gap {config.gap}"
            )
        for f in range(config.n_splits):
            train_end = uniq[chunks[f][-1]]
            val_chunk = chunks[f + 1][config.gap :]
            val_start, val_end = uniq[val_chunk[0]], uniq[val_chunk[-1]]
            tr = outer[t <= train_end]
            va = outer[(t >= val_start) & (t <= val_end)]
            folds.append(_fold(0, f, tr, va))

    for fold in folds:
        _require_both_classes(y, np.asarray(fold.train_idx), f"training fold {fold.fold}")
        n_pos = int(y[fold.val_idx].sum())
        if n_pos == 0 or n_pos == len(fold.val_idx):
            warnings.append(
                ProfileWarning(
                    code="single_class_validation_fold",
                    message=(
                        f"Validation fold (repeat {fold.repeat}, fold {fold.fold}) has a single "
                        "class; ranking metrics are undefined for it."
                    ),
                    evidence={"repeat": fold.repeat, "fold": fold.fold, "n_positive": n_pos},
                )
            )
    return CVPlan(
        strategy=strategy,
        config=config,
        n_repeats_effective=n_repeats,
        folds=folds,
        fold_indices_sha256=folds_sha256(folds),
        warnings=warnings,
    )


def _fold(repeat: int, fold: int, train: np.ndarray, val: np.ndarray) -> Fold:
    return Fold(repeat=repeat, fold=fold, train_idx=_sorted_list(train), val_idx=_sorted_list(val))
