"""Model registry: two fixed baselines plus a few candidate estimators with small fixed configs."""

from typing import Any, Literal

from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

ModelName = Literal["dummy_prior", "logreg_balanced", "hgb", "random_forest"]
BASELINE_MODELS: tuple[ModelName, ...] = ("dummy_prior", "logreg_balanced")
MODEL_NAMES: tuple[ModelName, ...] = ("dummy_prior", "logreg_balanced", "hgb", "random_forest")

MODEL_DESCRIPTIONS: dict[str, str] = {
    "dummy_prior": "DummyClassifier(strategy='prior'): predicts the training prevalence",
    "logreg_balanced": "LogisticRegression(class_weight='balanced', max_iter=2000)",
    "hgb": "HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, early_stopping=False)",
    "random_forest": (
        "RandomForestClassifier(n_estimators=300, min_samples_leaf=2, "
        "class_weight='balanced_subsample')"
    ),
}


def make_estimator(name: str, seed: int) -> Any:
    """A fresh, unfitted estimator for ``name``, seeded with ``seed`` where applicable."""
    if name == "dummy_prior":
        return DummyClassifier(strategy="prior")
    if name == "logreg_balanced":
        return LogisticRegression(class_weight="balanced", max_iter=2000)
    if name == "hgb":
        return HistGradientBoostingClassifier(
            max_iter=200, learning_rate=0.1, early_stopping=False, random_state=seed
        )
    if name == "random_forest":
        return RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            n_jobs=1,  # multi-threaded tree averaging is not bit-reproducible
            random_state=seed,
        )
    raise ValueError(f"unknown model {name!r}; expected one of {MODEL_NAMES}")
