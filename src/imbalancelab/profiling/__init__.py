"""Dataset profiling: class balance, missingness, duplicates, constant/ID-like columns,
and target-leak suspects reported as warnings (M1).
"""

from imbalancelab.profiling.profile import (
    ClassBalance,
    ColumnProfile,
    DatasetProfile,
    DuplicateSummary,
    ProfileThresholds,
    feature_row_hashes,
    profile_dataset,
)
from imbalancelab.profiling.warnings import ProfileWarning

__all__ = [
    "ClassBalance",
    "ColumnProfile",
    "DatasetProfile",
    "DuplicateSummary",
    "ProfileThresholds",
    "ProfileWarning",
    "feature_row_hashes",
    "profile_dataset",
]
