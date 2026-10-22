"""Metrics for imbalanced binary classification with explicit undefined cases.

A metric that is mathematically undefined for the given input (for example a ranking metric on
a single-class ``y_true``, or precision with no positive predictions) returns
``MetricResult(value=None, defined=False, reason=...)``. It never returns a silent 0, an
unexplained NaN, or a crash. Threshold metrics are computed from confusion counts, using the
convention ``score >= threshold`` means "predict positive".

Edge-case contract (tested in ``tests/test_metrics.py``):

* **Single-class ``y_true``** (all negative or all positive): average precision, ROC AUC,
  balanced accuracy and MCC are **undefined** (``value=None, defined=False`` with a reason).
  Recall is undefined when there are no positives.
* **Constant scores** with both classes present: average precision is **defined and equals the
  prevalence**, and ROC AUC is **defined and equals 0.5** (chance level, all ties). Both carry
  ``note="constant scores: value equals the chance level (all ties)"``. This is what the prior
  ``DummyClassifier`` baseline produces. MCC is undefined because predictions are constant.
* **No positive predictions** at the threshold: precision is undefined, and recall and F-beta
  are 0 (defined) when positives exist.
"""

import math

import numpy as np
from pydantic import BaseModel
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

PRIMARY_METRIC = "average_precision"
RANKING_METRICS = ("average_precision", "roc_auc", "brier")
THRESHOLD_METRICS = ("precision", "recall", "f1", "fbeta", "balanced_accuracy", "mcc")
METRIC_NAMES = RANKING_METRICS + THRESHOLD_METRICS
HIGHER_IS_BETTER = {name: name != "brier" for name in METRIC_NAMES}


class MetricResult(BaseModel):
    name: str
    value: float | None
    defined: bool
    reason: str | None = None  # why undefined
    note: str | None = None  # caveat on a defined value


class ConfusionCounts(BaseModel):
    threshold: float
    tn: int
    fp: int
    fn: int
    tp: int


class MetricSet(BaseModel):
    threshold: float
    beta: float
    n: int
    n_positive: int
    confusion: ConfusionCounts
    metrics: dict[str, MetricResult]

    def value(self, name: str) -> float | None:
        return self.metrics[name].value


def _undefined(name: str, reason: str) -> MetricResult:
    return MetricResult(name=name, value=None, defined=False, reason=reason)


def _defined(name: str, value: float, note: str | None = None) -> MetricResult:
    return MetricResult(name=name, value=float(value), defined=True, note=note)


def validate_inputs(y_true: object, y_score: object) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(y_true, y_score)`` as arrays; raise ValueError on malformed input."""
    yt = np.asarray(y_true).ravel()
    ys = np.asarray(y_score, dtype=float).ravel()
    if yt.shape != ys.shape:
        raise ValueError(f"y_true and y_score lengths differ: {yt.shape[0]} vs {ys.shape[0]}")
    if ys.size and not np.all(np.isfinite(ys)):
        raise ValueError("y_score contains NaN or infinite values")
    if yt.size and not set(np.unique(yt).tolist()) <= {0, 1}:
        raise ValueError("y_true must be binary 0/1")
    return yt.astype(int), ys


def _single_class_reason(yt: np.ndarray) -> str | None:
    if yt.size == 0:
        return "empty input"
    n_pos = int(yt.sum())
    if n_pos == 0:
        return "y_true has no positive samples"
    if n_pos == yt.size:
        return "y_true has no negative samples"
    return None


def _constant_note(ys: np.ndarray) -> str | None:
    if ys.size and np.all(ys == ys[0]):
        return "constant scores: value equals the chance level (all ties)"
    return None


def average_precision(y_true: object, y_score: object) -> MetricResult:
    yt, ys = validate_inputs(y_true, y_score)
    reason = _single_class_reason(yt)
    if reason:
        return _undefined("average_precision", reason)
    return _defined("average_precision", average_precision_score(yt, ys), _constant_note(ys))


def roc_auc(y_true: object, y_score: object) -> MetricResult:
    yt, ys = validate_inputs(y_true, y_score)
    reason = _single_class_reason(yt)
    if reason:
        return _undefined("roc_auc", reason)
    return _defined("roc_auc", roc_auc_score(yt, ys), _constant_note(ys))


def brier(y_true: object, y_score: object) -> MetricResult:
    yt, ys = validate_inputs(y_true, y_score)
    if yt.size == 0:
        return _undefined("brier", "empty input")
    if ys.min() < 0 or ys.max() > 1:
        return _undefined("brier", "scores are not probabilities in [0, 1]")
    return _defined("brier", brier_score_loss(yt, ys))


def confusion_at_threshold(y_true: object, y_score: object, threshold: float) -> ConfusionCounts:
    yt, ys = validate_inputs(y_true, y_score)
    pred = ys >= threshold
    pos = yt == 1
    return ConfusionCounts(
        threshold=float(threshold),
        tp=int(np.sum(pred & pos)),
        fp=int(np.sum(pred & ~pos)),
        fn=int(np.sum(~pred & pos)),
        tn=int(np.sum(~pred & ~pos)),
    )


def precision(c: ConfusionCounts) -> MetricResult:
    if c.tp + c.fp == 0:
        return _undefined("precision", "no positive predictions at this threshold")
    return _defined("precision", c.tp / (c.tp + c.fp))


def recall(c: ConfusionCounts) -> MetricResult:
    if c.tp + c.fn == 0:
        return _undefined("recall", "y_true has no positive samples")
    return _defined("recall", c.tp / (c.tp + c.fn))


def fbeta(c: ConfusionCounts, beta: float = 1.0, name: str = "fbeta") -> MetricResult:
    if beta <= 0:
        raise ValueError("beta must be positive")
    b2 = beta * beta
    denom = (1 + b2) * c.tp + b2 * c.fn + c.fp
    if denom == 0:
        return _undefined(name, "no positive samples and no positive predictions")
    return _defined(name, (1 + b2) * c.tp / denom)


def balanced_accuracy(c: ConfusionCounts) -> MetricResult:
    if c.tp + c.fn == 0 or c.tn + c.fp == 0:
        return _undefined("balanced_accuracy", "y_true contains a single class")
    return _defined("balanced_accuracy", 0.5 * (c.tp / (c.tp + c.fn) + c.tn / (c.tn + c.fp)))


def mcc(c: ConfusionCounts) -> MetricResult:
    margins = [c.tp + c.fp, c.tp + c.fn, c.tn + c.fp, c.tn + c.fn]
    if any(m == 0 for m in margins):
        if c.tp + c.fn == 0 or c.tn + c.fp == 0:
            reason = "y_true contains a single class"
        else:
            reason = "predictions are constant at this threshold"
        return _undefined("mcc", reason)
    num = c.tp * c.tn - c.fp * c.fn
    return _defined("mcc", num / math.sqrt(math.prod(float(m) for m in margins)))


def compute_metrics(
    y_true: object, y_score: object, threshold: float = 0.5, beta: float = 1.0
) -> MetricSet:
    """All metrics for one set of predictions."""
    yt, ys = validate_inputs(y_true, y_score)
    c = confusion_at_threshold(yt, ys, threshold)
    results = [
        average_precision(yt, ys),
        roc_auc(yt, ys),
        brier(yt, ys),
        precision(c),
        recall(c),
        fbeta(c, 1.0, name="f1"),
        fbeta(c, beta, name="fbeta"),
        balanced_accuracy(c),
        mcc(c),
    ]
    return MetricSet(
        threshold=float(threshold),
        beta=float(beta),
        n=int(yt.size),
        n_positive=int(yt.sum()),
        confusion=c,
        metrics={r.name: r for r in results},
    )
