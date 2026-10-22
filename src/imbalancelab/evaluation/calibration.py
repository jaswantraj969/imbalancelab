"""Calibration *disclosure* (not a calibration stage): reliability curve and score caveats.

The reliability curve uses quantile bins of the scores. Bin edges are score quantiles, so bins
hold roughly equal numbers of rows. Tied scores can merge edges, so fewer bins than requested are
possible, and the number of rows in each bin is always reported.
"""

from typing import Any

import numpy as np

from imbalancelab.evaluation.metrics import validate_inputs

RESAMPLER_NOTE = (
    "Scores from models trained with a resampler ({models}) are ranking scores, NOT calibrated "
    "probabilities. Resampling changes the class balance seen during training, so these scores "
    "do not estimate the probability of the positive class. Do not interpret them as risk."
)
NO_RESAMPLER_NOTE = (
    "No resampler was used in this run. Calibration was not assessed beyond the Brier score and "
    "the reliability curve; no calibration stage was applied."
)
CLASS_WEIGHT_NOTE = (
    "Class-weighted models ({models}) also shift scores away from the training prevalence."
)
CLASS_WEIGHTED_MODELS = ("logreg_balanced", "random_forest")


def reliability_curve(y_true: object, y_score: object, n_bins: int = 10) -> dict[str, Any]:
    """Quantile-binned reliability curve: per bin, rows, positives, mean score, observed rate."""
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")
    y, s = validate_inputs(y_true, y_score)
    if y.size == 0:
        return {"n_bins_requested": n_bins, "binning": "quantile", "bins": []}
    edges = np.unique(np.quantile(s, np.linspace(0.0, 1.0, n_bins + 1)))
    if edges.size == 1:  # all scores equal: one bin
        assign = np.zeros(s.size, dtype=int)
        edges = np.array([edges[0], edges[0]])
    else:
        # interior edges: a score equal to an edge goes to the upper bin; the max goes to the last
        assign = np.clip(np.searchsorted(edges[1:-1], s, side="right"), 0, edges.size - 2)
    bins = []
    for b in range(edges.size - 1):
        mask = assign == b
        n = int(mask.sum())
        if n == 0:
            continue
        bins.append(
            {
                "lower": float(edges[b]),
                "upper": float(edges[b + 1]),
                "n": n,
                "n_positive": int(y[mask].sum()),
                "mean_score": float(s[mask].mean()),
                "observed_rate": float(y[mask].mean()),
            }
        )
    return {"n_bins_requested": n_bins, "binning": "quantile", "bins": bins}


def calibration_disclosure(model_specs: list[dict[str, Any]]) -> list[str]:
    """Plain-language statements about how to read the scores of a run's models."""
    resampled = [m["name"] for m in model_specs if m.get("sampler", "none") != "none"]
    weighted = [m["name"] for m in model_specs if m.get("model") in CLASS_WEIGHTED_MODELS]
    notes = [
        RESAMPLER_NOTE.format(models=", ".join(f"`{m}`" for m in resampled))
        if resampled
        else NO_RESAMPLER_NOTE
    ]
    if weighted:
        notes.append(CLASS_WEIGHT_NOTE.format(models=", ".join(f"`{m}`" for m in weighted)))
    return notes
