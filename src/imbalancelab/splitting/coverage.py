"""Evaluation coverage: which rows no test or validation metric ever describes.

Computed from the stored holdout and CV folds only. A row is *evaluated* if it is in the test set
or in at least one validation fold. Rows that are never evaluated fall into:

* **forced to train**: the row's split group exceeded the large-group cut-off
  (``max_eval_group_fraction``) and was pinned to the training side;
* **gap**: temporal gap rows, excluded from both sides;
* **other**: e.g. the initial training window of an expanding-window temporal CV.
"""

from typing import Any

import numpy as np
import pandas as pd

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.splitting.groups import GroupingError, resolve_groups
from imbalancelab.splitting.splits import CVPlan, Holdout, SplitError, pin_oversized_groups

COVERAGE_WARNING_PCT = 10.0  # forced-to-train rows above this % of the dataset trigger a warning


def evaluation_coverage(dataset: LoadedDataset, holdout: Holdout, plan: CVPlan) -> dict[str, Any]:
    n, y = dataset.n_rows, dataset.y
    evaluated = set(holdout.test_idx)
    for fold in plan.folds:
        evaluated.update(fold.val_idx)
    gap = set(holdout.gap_idx)
    never = np.array(sorted(set(range(n)) - evaluated - gap), dtype=int)

    try:
        groups, _, _ = resolve_groups(dataset)
    except GroupingError as exc:
        raise SplitError(str(exc)) from exc
    forced_mask = np.zeros(n, dtype=bool)
    holdout_limit = cv_limit = None
    if groups is not None:
        holdout_limit = holdout.config.max_eval_group_fraction * holdout.config.test_size * n
        forced_mask |= pin_oversized_groups(
            groups, holdout.config.test_size * n, holdout.config.max_eval_group_fraction
        )
        outer = np.asarray(holdout.train_idx)
        fold_size = len(outer) / plan.config.n_splits
        cv_limit = plan.config.max_eval_group_fraction * fold_size
        cv_mask = pin_oversized_groups(
            groups[outer], fold_size, plan.config.max_eval_group_fraction
        )
        forced_mask[outer[cv_mask]] = True
    forced = np.array([i for i in never if forced_mask[i]], dtype=int)
    other = np.array([i for i in never if not forced_mask[i]], dtype=int)

    group_sizes: list[int] = []
    group_positives: list[int] = []
    if groups is not None and forced.size:
        frame = pd.DataFrame({"g": groups[forced], "y": y[forced]})
        stats = frame.groupby("g")["y"].agg(["size", "sum"]).sort_values("size", ascending=False)
        group_sizes = [int(v) for v in stats["size"]]
        group_positives = [int(v) for v in stats["sum"]]

    n_pos_total = int(y.sum())
    pct_rows = 100.0 * forced.size / n
    return {
        "n_rows": n,
        "n_positive": n_pos_total,
        "n_rows_evaluated": len(evaluated),
        "forced_to_train": {
            "n_rows": int(forced.size),
            "n_positive": int(y[forced].sum()) if forced.size else 0,
            "pct_of_rows": pct_rows,
            "pct_of_positives": 100.0
            * (int(y[forced].sum()) if forced.size else 0)
            / max(n_pos_total, 1),
            "n_groups": len(group_sizes),
            "group_sizes": group_sizes,
            "group_positive_counts": group_positives,
        },
        "gap_rows": len(gap),
        "other_never_evaluated": {
            "n_rows": int(other.size),
            "n_positive": int(y[other].sum()) if other.size else 0,
            "reason": "temporal initial training window"
            if dataset.schema.split_strategy == "temporal"
            else "not in any test or validation fold",
        },
        "cutoff": {
            "holdout_max_eval_group_fraction": holdout.config.max_eval_group_fraction,
            "holdout_row_limit": holdout_limit,
            "cv_max_eval_group_fraction": plan.config.max_eval_group_fraction,
            "cv_row_limit": cv_limit,
            "applies": groups is not None,
        },
        "warning_threshold_pct": COVERAGE_WARNING_PCT,
        "warning": pct_rows > COVERAGE_WARNING_PCT,
    }
