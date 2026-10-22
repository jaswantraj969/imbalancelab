"""Outer holdout and inner CV for stratified, group, and temporal strategies (M2)."""

from imbalancelab.splitting.duplicates import cross_boundary_duplicates
from imbalancelab.splitting.splits import (
    CVConfig,
    CVPlan,
    Fold,
    Holdout,
    HoldoutConfig,
    HoldoutMismatchError,
    SplitError,
    check_holdout,
    folds_sha256,
    get_or_create_holdout,
    indices_sha256,
    make_cv_folds,
    make_holdout,
)

__all__ = [
    "CVConfig",
    "CVPlan",
    "Fold",
    "Holdout",
    "HoldoutConfig",
    "HoldoutMismatchError",
    "SplitError",
    "check_holdout",
    "cross_boundary_duplicates",
    "folds_sha256",
    "get_or_create_holdout",
    "indices_sha256",
    "make_cv_folds",
    "make_holdout",
]
