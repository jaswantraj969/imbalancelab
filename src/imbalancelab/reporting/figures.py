"""Precision-recall and ROC figures drawn from stored predictions only."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import precision_recall_curve, roc_curve  # noqa: E402


def _usable(group: pd.DataFrame) -> bool:
    return 0 < int(group["y_true"].sum()) < len(group)


def plot_curves(predictions: pd.DataFrame, title: str, out_dir: Path, stem: str) -> list[Path]:
    """Write ``<stem>_pr.png`` and ``<stem>_roc.png``; one line per model.

    ``predictions`` needs columns model, y_true, y_score. Models whose predictions contain a
    single class are skipped, because their curves are undefined.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = [(m, g) for m, g in predictions.groupby("model", sort=False) if _usable(g)]
    if not groups:
        return []
    paths = []
    prevalence = float(predictions["y_true"].mean())

    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=110)
    for model, g in groups:
        p, r, _ = precision_recall_curve(g["y_true"], g["y_score"])
        ax.step(r, p, where="post", label=str(model), linewidth=1.4)
    ax.axhline(prevalence, color="grey", linestyle=":", linewidth=1, label="prevalence")
    ax.set(
        xlabel="Recall",
        ylabel="Precision",
        title=f"Precision-recall: {title}",
        xlim=(0, 1),
        ylim=(0, 1.02),
    )
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    pr_path = out_dir / f"{stem}_pr.png"
    fig.savefig(pr_path)
    plt.close(fig)
    paths.append(pr_path)

    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=110)
    for model, g in groups:
        fpr, tpr, _ = roc_curve(g["y_true"], g["y_score"])
        ax.plot(fpr, tpr, label=str(model), linewidth=1.4)
    ax.plot([0, 1], [0, 1], color="grey", linestyle=":", linewidth=1, label="chance")
    ax.set(
        xlabel="False positive rate",
        ylabel="True positive rate",
        title=f"ROC: {title}",
        xlim=(0, 1),
        ylim=(0, 1.02),
    )
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    roc_path = out_dir / f"{stem}_roc.png"
    fig.savefig(roc_path)
    plt.close(fig)
    paths.append(roc_path)
    return paths


def first_repeat(oof: pd.DataFrame) -> pd.DataFrame:
    """OOF predictions of the first CV repeat (one prediction per outer-train row)."""
    first = int(np.min(oof["repeat"]))
    return oof[oof["repeat"] == first]


def plot_reliability(calibration: dict[str, dict], out_dir: Path, stem: str) -> Path | None:
    """Reliability (calibration) curve per model from stored quantile bins; marker size ~ n."""
    curves = {
        m: c["reliability"]["bins"] for m, c in calibration.items() if c["reliability"]["bins"]
    }
    if not curves:
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=110)
    top = 0.0
    for model, bins in curves.items():
        x = [b["mean_score"] for b in bins]
        y = [b["observed_rate"] for b in bins]
        top = max(top, *x, *y)
        ax.plot(x, y, marker="o", linewidth=1.2, label=str(model))
    top = min(1.0, top * 1.05 + 1e-3)
    ax.plot(
        [0, top], [0, top], color="grey", linestyle=":", linewidth=1, label="perfect calibration"
    )
    ax.set(
        xlabel="Mean score in bin",
        ylabel="Observed positive rate in bin",
        title="Reliability (test set, quantile bins)",
        xlim=(0, top),
        ylim=(0, top),
    )
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    path = out_dir / f"{stem}_reliability.png"
    fig.savefig(path)
    plt.close(fig)
    return path
