"""Outer holdout and inner CV folds for stratified, group, and temporal strategies.

Splitting is group-aware (``StratifiedGroupKFold``) whenever groups resolve: a declared
``group_column`` (group strategy) and/or exact-duplicate clusters
(``schema.duplicate_groups=True``, see :mod:`imbalancelab.splitting.groups`).

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
from imbalancelab.splitting.groups import GroupInfo, GroupingError, resolve_groups

# a test set in which one group exceeds this share is flagged, whatever the pinning setting
DOMINANT_GROUP_SHARE = 0.5


class SplitError(ValueError):
    """The requested split cannot be built on this data."""


class HoldoutMismatchError(SplitError):
    """A stored holdout does not match the dataset or the requested config."""


class HoldoutConfig(BaseModel):
    test_size: float = Field(default=0.2, gt=0, lt=1)
    gap: int = Field(default=0, ge=0)  # temporal: distinct time values dropped before test
    seed: int = 42
    # group-aware splits: a group larger than this fraction of the target test-set size is
    # pinned to the training side (see ``pin_oversized_groups``)
    max_eval_group_fraction: float = Field(default=0.25, gt=0, le=1)


class CVConfig(BaseModel):
    n_splits: int = Field(default=5, ge=2)
    n_repeats: int = Field(default=3, ge=1)
    gap: int = Field(default=0, ge=0)  # temporal: distinct time values dropped before val
    seed: int = 42
    max_eval_group_fraction: float = Field(default=0.25, gt=0, le=1)


class Holdout(BaseModel):
    strategy: SplitStrategy
    config: HoldoutConfig
    dataset_sha256: str
    n_rows: int
    train_idx: list[int]
    test_idx: list[int]
    gap_idx: list[int] = Field(default_factory=list)
    test_sha256: str
    duplicate_groups: bool = False
    group_info: GroupInfo | None = None
    n_pinned_groups: int = 0  # oversized groups forced into outer-train
    n_pinned_rows: int = 0
    warnings: list[ProfileWarning] = Field(default_factory=list)

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
    duplicate_groups: bool = False
    n_groups: int | None = None  # split groups in outer-train (group-aware CV only)
    n_pinned_groups: int = 0  # oversized groups kept on the training side of every fold
    n_pinned_rows: int = 0


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


def pin_oversized_groups(groups: np.ndarray, eval_size: float, fraction: float) -> np.ndarray:
    """Boolean mask of rows whose group is too large to sit in an evaluation set.

    A group larger than ``fraction * eval_size`` rows cannot be placed in a test or validation
    set without dominating it: ``StratifiedGroupKFold`` then fills the rest of that set with
    whatever rebalances the class ratio, and the evaluation set stops being representative.
    Such groups are pinned to the training side instead. The evaluation population then excludes
    their rows, and callers record and report this.
    """
    sizes = pd.Series(groups).value_counts()
    oversized = sizes.index[sizes > fraction * eval_size]
    return np.isin(groups, np.asarray(oversized))


def _pinned_warning(
    where: str, mask: np.ndarray, groups: np.ndarray, limit: float
) -> ProfileWarning:
    n_groups = int(len(np.unique(groups[mask])))
    return ProfileWarning(
        code="oversized_groups_pinned_to_train",
        message=(
            f"{n_groups} group(s) covering {int(mask.sum())} rows exceed {limit:.0f} rows "
            f"(max_eval_group_fraction of the {where} size) and are always on the training "
            f"side; {where} metrics do not cover these rows."
        ),
        evidence={
            "where": where,
            "n_groups": n_groups,
            "n_rows": int(mask.sum()),
            "row_limit": float(limit),
        },
    )


def _balance_warnings(
    y: np.ndarray,
    test_idx: np.ndarray,
    eligible: np.ndarray,
    config: HoldoutConfig,
    n: int,
    groups: np.ndarray,
) -> list[ProfileWarning]:
    """Warn when the test set's size, prevalence or group composition is far from requested."""
    out: list[ProfileWarning] = []
    largest = float(pd.Series(groups[test_idx]).value_counts().iloc[0]) / max(len(test_idx), 1)
    if largest > DOMINANT_GROUP_SHARE:
        out.append(
            ProfileWarning(
                code="holdout_dominated_by_group",
                message=(
                    f"One split group makes up {largest:.1%} of the test set (more than "
                    f"{DOMINANT_GROUP_SHARE:.0%}); the test set may not be representative."
                ),
                evidence={"largest_group_share": largest},
            )
        )
    frac = len(test_idx) / n
    if abs(frac - config.test_size) > 0.25 * config.test_size:
        out.append(
            ProfileWarning(
                code="holdout_size_deviation",
                message=f"Test set is {frac:.1%} of rows; requested {config.test_size:.1%}.",
                evidence={"test_fraction": frac, "requested": config.test_size},
            )
        )
    ref = float(y[eligible].mean())
    prev = float(y[test_idx].mean())
    if ref > 0 and abs(prev - ref) > 0.25 * ref:
        out.append(
            ProfileWarning(
                code="holdout_prevalence_deviation",
                message=(
                    f"Test prevalence {prev:.4f} differs from {ref:.4f} (rows eligible for test) "
                    "by more than 25%."
                ),
                evidence={"test_prevalence": prev, "eligible_prevalence": ref},
            )
        )
    return out


def _resolve(dataset: LoadedDataset) -> tuple[np.ndarray | None, GroupInfo | None, list]:
    try:
        return resolve_groups(dataset)
    except GroupingError as exc:
        raise SplitError(str(exc)) from exc


# --------------------------------------------------------------------------- holdout


def make_holdout(dataset: LoadedDataset, config: HoldoutConfig | None = None) -> Holdout:
    """Create the outer train/test holdout using the schema's split strategy."""
    config = config or HoldoutConfig()
    strategy = dataset.schema.split_strategy
    n = dataset.n_rows
    y = dataset.y
    all_idx = np.arange(n)
    gap_idx = np.array([], dtype=int)
    groups, group_info, group_warnings = _resolve(dataset)
    n_pinned_groups = n_pinned_rows = 0

    if strategy != "temporal" and groups is None:
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
    elif groups is not None:
        target = config.test_size * n
        pinned = pin_oversized_groups(groups, target, config.max_eval_group_fraction)
        eligible = all_idx[~pinned]
        n_folds = max(2, int(round(len(eligible) / target)))
        n_eligible_groups = len(np.unique(groups[eligible]))
        if n_eligible_groups < n_folds:
            raise SplitError(
                f"group holdout needs at least {n_folds} distinct groups, found {n_eligible_groups}"
            )
        sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=config.seed)
        tr, te = next(iter(sgkf.split(eligible, y[eligible], groups[eligible])))
        test_idx = eligible[te]
        train_idx = np.concatenate([eligible[tr], all_idx[pinned]])
        n_pinned_groups, n_pinned_rows = int(len(np.unique(groups[pinned]))), int(pinned.sum())
        if n_pinned_rows:
            limit = config.max_eval_group_fraction * target
            group_warnings = [*group_warnings, _pinned_warning("test set", pinned, groups, limit)]
        group_warnings = [
            *group_warnings,
            *_balance_warnings(y, np.asarray(test_idx), eligible, config, n, groups),
        ]
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
        duplicate_groups=dataset.schema.duplicate_groups,
        group_info=group_info,
        n_pinned_groups=n_pinned_groups,
        n_pinned_rows=n_pinned_rows,
        warnings=group_warnings,
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
        if holdout.duplicate_groups != dataset.schema.duplicate_groups:
            raise HoldoutMismatchError("stored holdout used a different duplicate_groups setting")
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
    all_groups, _, _ = _resolve(dataset)
    n_groups: int | None = None
    n_pinned_groups = n_pinned_rows = 0

    if strategy != "temporal" and all_groups is None:
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
    elif all_groups is not None:
        groups = all_groups[outer]
        n_groups = len(np.unique(groups))
        fold_size = len(outer) / config.n_splits
        pinned = pin_oversized_groups(groups, fold_size, config.max_eval_group_fraction)
        eligible, always_train = outer[~pinned], outer[pinned]
        n_eligible_groups = len(np.unique(groups[~pinned]))
        if n_eligible_groups < config.n_splits:
            raise SplitError(
                f"only {n_eligible_groups} groups in outer-train; cannot build "
                f"{config.n_splits} folds"
            )
        if pinned.any():
            n_pinned_groups = int(len(np.unique(groups[pinned])))
            n_pinned_rows = int(pinned.sum())
            limit = config.max_eval_group_fraction * fold_size
            warnings.append(_pinned_warning("validation fold", pinned, groups, limit))
        for r in range(config.n_repeats):
            sgkf = StratifiedGroupKFold(
                n_splits=config.n_splits, shuffle=True, random_state=config.seed + r
            )
            for f, (tr, va) in enumerate(sgkf.split(eligible, y[eligible], groups[~pinned])):
                folds.append(
                    _fold(r, f, np.concatenate([eligible[tr], always_train]), eligible[va])
                )
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
        duplicate_groups=dataset.schema.duplicate_groups,
        n_groups=n_groups,
        n_pinned_groups=n_pinned_groups,
        n_pinned_rows=n_pinned_rows,
    )


def _fold(repeat: int, fold: int, train: np.ndarray, val: np.ndarray) -> Fold:
    return Fold(repeat=repeat, fold=fold, train_idx=_sorted_list(train), val_idx=_sorted_list(val))
