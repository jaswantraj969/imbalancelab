"""Stratified bootstrap confidence intervals for single test-set evaluations.

Positives and negatives are resampled separately, with replacement, so every resample has
exactly the observed number of positives and negatives (the test-set prevalence is kept fixed).
The interval is the percentile interval of the metric over resamples. A resample in which a
metric is undefined (for example precision when nothing is predicted positive) is **counted** in
``n_undefined``, not silently dropped, and the percentiles are taken over the defined values.

Point estimates come from :mod:`imbalancelab.evaluation.metrics`. Resample values use vectorised
implementations of the same definitions (tested against scikit-learn, including ties).

This is applied to final test predictions only. Out-of-fold metrics already report their fold
spread.
"""

import numpy as np
from pydantic import BaseModel, Field
from scipy.stats import rankdata

from imbalancelab.evaluation.metrics import compute_metrics, validate_inputs

CI_METRICS = ("average_precision", "roc_auc", "precision", "recall", "fbeta", "mcc")


class BootstrapConfig(BaseModel):
    n_resamples: int = Field(default=2000, ge=100)
    seed: int = 42
    confidence: float = Field(default=0.95, gt=0, lt=1)


class MetricCI(BaseModel):
    name: str
    point: float | None
    lower: float | None
    upper: float | None
    confidence: float
    n_resamples: int
    n_defined: int
    n_undefined: int  # resamples where the metric was undefined (counted, not dropped)


def stratified_resample_indices(y_true: np.ndarray, n_resamples: int, seed: int) -> np.ndarray:
    """``(n_resamples, n)`` index matrix. In every row the first ``n_pos`` columns are positives
    and the rest negatives, so class counts are preserved exactly."""
    y = np.asarray(y_true).astype(int)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    rng = np.random.default_rng(seed)
    pos_draw = rng.integers(0, max(pos.size, 1), size=(n_resamples, pos.size))
    neg_draw = rng.integers(0, max(neg.size, 1), size=(n_resamples, neg.size))
    return np.hstack([pos[pos_draw], neg[neg_draw]]).astype(np.int64)


def _average_precision_rows(y: np.ndarray, s: np.ndarray) -> np.ndarray:
    """AP per row (sklearn definition: sum over distinct thresholds of ΔR · P)."""
    out = np.full(s.shape[0], np.nan)
    n_pos_all = y.sum(axis=1)
    for i in range(s.shape[0]):
        n_pos = n_pos_all[i]
        if n_pos == 0 or n_pos == y.shape[1]:
            continue
        order = np.argsort(-s[i], kind="mergesort")
        ss, yy = s[i][order], y[i][order]
        ends = np.r_[np.flatnonzero(np.diff(ss) != 0), ss.size - 1]
        tp = np.cumsum(yy)[ends]
        precision = tp / (ends + 1)
        recall_steps = np.diff(np.r_[0, tp]) / n_pos
        out[i] = float(np.sum(recall_steps * precision))
    return out


def _roc_auc_rows(y: np.ndarray, s: np.ndarray) -> np.ndarray:
    """ROC AUC per row via average ranks (Mann-Whitney U; ties count one half)."""
    n_pos = y.sum(axis=1).astype(float)
    n_neg = y.shape[1] - n_pos
    ranks = rankdata(s, axis=1)
    rank_sum_pos = np.where(y == 1, ranks, 0.0).sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return np.where((n_pos > 0) & (n_neg > 0), auc, np.nan)


def _threshold_rows(
    y: np.ndarray, s: np.ndarray, threshold: float, beta: float
) -> dict[str, np.ndarray]:
    pred = s >= threshold
    pos = y == 1
    tp = (pred & pos).sum(axis=1).astype(float)
    fp = (pred & ~pos).sum(axis=1).astype(float)
    fn = (~pred & pos).sum(axis=1).astype(float)
    tn = (~pred & ~pos).sum(axis=1).astype(float)
    b2 = beta * beta
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(tp + fp > 0, tp / (tp + fp), np.nan)
        recall = np.where(tp + fn > 0, tp / (tp + fn), np.nan)
        denom = (1 + b2) * tp + b2 * fn + fp
        fb = np.where(denom > 0, (1 + b2) * tp / denom, np.nan)
        margins = (tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)
        mcc = np.where(margins > 0, (tp * tn - fp * fn) / np.sqrt(margins), np.nan)
    return {"precision": precision, "recall": recall, "fbeta": fb, "mcc": mcc}


def resample_metric_values(
    y_true: np.ndarray, y_score: np.ndarray, idx: np.ndarray, threshold: float, beta: float
) -> dict[str, np.ndarray]:
    """Metric value per resample (NaN where undefined) for each metric in ``CI_METRICS``."""
    y, s = y_true[idx], y_score[idx]
    return {
        "average_precision": _average_precision_rows(y, s),
        "roc_auc": _roc_auc_rows(y, s),
        **_threshold_rows(y, s, threshold, beta),
    }


def bootstrap_cis(
    y_true: object,
    y_score: object,
    threshold: float,
    beta: float = 1.0,
    config: BootstrapConfig | None = None,
) -> dict[str, MetricCI]:
    """Point estimate and stratified-bootstrap percentile CI for each metric in ``CI_METRICS``.

    The same resample indices are used for every metric (and, given the same seed and test
    rows, for every model), so intervals of different models are computed on identical resamples.
    """
    config = config or BootstrapConfig()
    yt, ys = validate_inputs(y_true, y_score)
    idx = stratified_resample_indices(yt, config.n_resamples, config.seed)
    values = resample_metric_values(yt, ys, idx, threshold, beta)
    point = compute_metrics(yt, ys, threshold=threshold, beta=beta)
    alpha = (1.0 - config.confidence) / 2.0
    out: dict[str, MetricCI] = {}
    for name in CI_METRICS:
        defined = values[name][~np.isnan(values[name])]
        out[name] = MetricCI(
            name=name,
            point=point.value(name),
            lower=float(np.quantile(defined, alpha)) if defined.size else None,
            upper=float(np.quantile(defined, 1.0 - alpha)) if defined.size else None,
            confidence=config.confidence,
            n_resamples=config.n_resamples,
            n_defined=int(defined.size),
            n_undefined=int(config.n_resamples - defined.size),
        )
    return out
