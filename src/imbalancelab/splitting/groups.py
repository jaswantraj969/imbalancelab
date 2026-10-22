"""Group IDs for group-aware splitting: declared groups and/or exact-duplicate clusters.

With ``schema.duplicate_groups=True`` every set of rows with identical feature values (the
target, id, group and time columns are excluded) forms one *duplicate cluster*. Rows with
identical features but different labels are kept and stay in the same cluster. Splitting on
these clusters guarantees that no duplicate cluster crosses any train/validation/test boundary.

If the schema also declares a ``group_column``, declared groups are combined with duplicate
clusters by connected components: declared groups linked by a shared duplicate cluster are
merged into one split group. A declared group is therefore never split, no duplicate cluster
crosses a boundary, and a warning reports how many clusters spanned declared groups.
"""

import logging
from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.profiling.profile import feature_row_hashes
from imbalancelab.profiling.warnings import ProfileWarning

logger = logging.getLogger(__name__)

GroupSource = Literal["declared", "duplicates", "declared+duplicates"]


class GroupInfo(BaseModel):
    """How split groups were formed; recorded in holdouts and run records."""

    source: GroupSource
    duplicate_groups: bool
    n_rows: int
    n_groups: int
    n_duplicate_clusters: int  # clusters of identical feature rows with more than one row
    n_rows_in_duplicate_clusters: int
    n_conflicting_label_clusters: int  # duplicate clusters whose rows have different labels
    n_rows_in_conflicting_clusters: int
    n_clusters_spanning_declared_groups: int = 0
    n_declared_groups: int | None = None
    n_declared_groups_merged: int = 0  # declared groups absorbed into a merged split group


class GroupingError(ValueError):
    """Groups cannot be formed (e.g. missing values in the declared group column)."""


def duplicate_cluster_ids(dataset: LoadedDataset) -> np.ndarray:
    """Integer cluster ID per row; rows with identical feature values share an ID."""
    if not dataset.feature_columns:
        raise GroupingError("duplicate_groups needs at least one feature column")
    hashes = feature_row_hashes(dataset.frame, dataset.feature_columns)
    codes, _ = pd.factorize(pd.Series(hashes), sort=False)
    return np.asarray(codes, dtype=np.int64)


def _declared(dataset: LoadedDataset) -> np.ndarray:
    col = dataset.schema.group_column
    if col is None:
        raise GroupingError("group strategy requires schema.group_column")
    series = dataset.frame[col]
    if series.isna().any():
        raise GroupingError(f"group column {col!r} has missing values")
    codes, _ = pd.factorize(series.astype(str), sort=True)
    return np.asarray(codes, dtype=np.int64)


def _cluster_stats(clusters: np.ndarray, y: np.ndarray) -> dict[str, int]:
    frame = pd.DataFrame({"c": clusters, "y": y})
    grouped = frame.groupby("c")["y"]
    sizes = grouped.size()
    multi = sizes[sizes > 1]
    conflicting = grouped.nunique()
    conflicting = conflicting[conflicting > 1]
    return {
        "n_duplicate_clusters": len(multi),
        "n_rows_in_duplicate_clusters": int(multi.sum()),
        "n_conflicting_label_clusters": len(conflicting),
        "n_rows_in_conflicting_clusters": int(sizes.loc[conflicting.index].sum()),
    }


def resolve_groups(
    dataset: LoadedDataset,
) -> tuple[np.ndarray | None, GroupInfo | None, list[ProfileWarning]]:
    """Split groups for ``dataset``: ``(None, None, [])`` when splitting is not group-aware."""
    schema = dataset.schema
    if schema.split_strategy == "temporal":
        return None, None, []
    declared = _declared(dataset) if schema.split_strategy == "group" else None
    if not schema.duplicate_groups:
        if declared is None:
            return None, None, []
        info = GroupInfo(
            source="declared",
            duplicate_groups=False,
            n_rows=dataset.n_rows,
            n_groups=int(len(np.unique(declared))),
            n_duplicate_clusters=0,
            n_rows_in_duplicate_clusters=0,
            n_conflicting_label_clusters=0,
            n_rows_in_conflicting_clusters=0,
            n_declared_groups=int(len(np.unique(declared))),
        )
        return declared, info, []

    clusters = duplicate_cluster_ids(dataset)
    stats = _cluster_stats(clusters, dataset.y)
    warnings: list[ProfileWarning] = []
    if stats["n_conflicting_label_clusters"]:
        warnings.append(
            ProfileWarning(
                code="conflicting_label_clusters",
                severity="info",
                message=(
                    f"{stats['n_conflicting_label_clusters']} duplicate cluster(s) "
                    f"({stats['n_rows_in_conflicting_clusters']} rows) have identical features "
                    "but different labels; they are kept and split together."
                ),
                evidence={
                    "n_clusters": stats["n_conflicting_label_clusters"],
                    "n_rows": stats["n_rows_in_conflicting_clusters"],
                },
            )
        )
    if declared is None:
        info = GroupInfo(
            source="duplicates",
            duplicate_groups=True,
            n_rows=dataset.n_rows,
            n_groups=int(len(np.unique(clusters))),
            **stats,
        )
        return clusters, info, warnings

    # connected components over a bipartite graph: declared-group nodes + cluster nodes
    n_declared = int(declared.max()) + 1
    n_nodes = n_declared + int(clusters.max()) + 1
    graph = coo_matrix(
        (np.ones(len(declared)), (declared, n_declared + clusters)), shape=(n_nodes, n_nodes)
    )
    _, component = connected_components(graph, directed=False)
    groups = np.asarray(component[declared], dtype=np.int64)
    spans = pd.DataFrame({"c": clusters, "d": declared}).groupby("c")["d"].nunique()
    n_spanning = int((spans > 1).sum())
    n_merged_groups = int(len(np.unique(groups)))
    info = GroupInfo(
        source="declared+duplicates",
        duplicate_groups=True,
        n_rows=dataset.n_rows,
        n_groups=n_merged_groups,
        n_clusters_spanning_declared_groups=n_spanning,
        n_declared_groups=n_declared,
        n_declared_groups_merged=n_declared - n_merged_groups,
        **stats,
    )
    if n_spanning:
        logger.warning(
            "duplicate_groups: %d declared group(s) merged into larger split groups (D27): "
            "%d duplicate cluster(s) span declared groups; %d declared groups -> %d split groups",
            n_declared - n_merged_groups,
            n_spanning,
            n_declared,
            n_merged_groups,
        )
        warnings.append(
            ProfileWarning(
                code="duplicate_clusters_span_declared_groups",
                message=(
                    f"{n_spanning} duplicate cluster(s) contain rows from more than one declared "
                    f"group; {n_declared} declared groups were merged into {n_merged_groups} "
                    "split groups so that no duplicate cluster crosses a split boundary."
                ),
                evidence={
                    "n_clusters_spanning": n_spanning,
                    "n_declared_groups": n_declared,
                    "n_split_groups": n_merged_groups,
                    "n_declared_groups_merged": n_declared - n_merged_groups,
                },
            )
        )
    return groups, info, warnings
