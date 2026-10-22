"""Detect identical feature rows that sit on both sides of a split boundary."""

import numpy as np

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.profiling.profile import feature_row_hashes
from imbalancelab.profiling.warnings import ProfileWarning
from imbalancelab.splitting.splits import CVPlan, Holdout


def _n_crossing(hashes: np.ndarray, train_idx: list[int], eval_idx: list[int]) -> int:
    train_set = set(hashes[train_idx].tolist())
    return int(sum(h in train_set for h in hashes[eval_idx].tolist()))


def cross_boundary_duplicates(
    dataset: LoadedDataset, holdout: Holdout, plan: CVPlan | None = None
) -> list[ProfileWarning]:
    """Count evaluation rows whose feature values exactly duplicate a training row.

    Checked across the outer train/test boundary and, if ``plan`` is given, across every inner
    train/validation boundary. Returns at most one WARNING, carrying the counts as evidence.
    """
    features = dataset.feature_columns
    if not features:
        return []
    hashes = feature_row_hashes(dataset.frame, features)
    test_crossing = _n_crossing(hashes, holdout.train_idx, holdout.test_idx)
    per_fold: list[dict[str, int]] = []
    if plan is not None:
        for fold in plan.folds:
            k = _n_crossing(hashes, fold.train_idx, fold.val_idx)
            if k:
                per_fold.append({"repeat": fold.repeat, "fold": fold.fold, "n_rows": k})
    if not test_crossing and not per_fold:
        return []
    max_fold = max((d["n_rows"] for d in per_fold), default=0)
    return [
        ProfileWarning(
            code="cross_boundary_duplicates",
            message=(
                f"{test_crossing} test row(s) exactly duplicate outer-train feature rows, and "
                f"{len(per_fold)} CV fold(s) have validation rows duplicating their training "
                f"rows (max {max_fold}). Scores on duplicated rows may be optimistic."
            ),
            evidence={
                "test_rows_duplicating_train": test_crossing,
                "n_test_rows": len(holdout.test_idx),
                "folds_affected": len(per_fold),
                "max_val_rows_duplicating_train": max_fold,
                "per_fold": per_fold,
            },
        )
    ]
