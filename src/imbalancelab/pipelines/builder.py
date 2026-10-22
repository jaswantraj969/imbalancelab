"""Leakage-safe imblearn pipelines: preprocessing -> optional sampler -> estimator.

Every learned step lives inside one :class:`imblearn.pipeline.Pipeline`. Fitting the pipeline
on a training fold therefore fits imputers, scalers, encoders and samplers on that fold alone.
imblearn runs samplers only during ``fit``, so ``predict``/``predict_proba`` and scoring always
see the original, unresampled rows.
"""

from typing import Any, Literal

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, RandomOverSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.under_sampling import RandomUnderSampler
from pandas.api import types as ptypes
from pydantic import BaseModel, Field
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

SamplerName = Literal["none", "random_under", "random_over", "smote"]
MISSING_CATEGORY = "__missing__"


class FeatureSpec(BaseModel):
    """Which feature columns are encoded how, and which are dropped (with a reason)."""

    numeric: list[str] = Field(default_factory=list)
    categorical: list[str] = Field(default_factory=list)
    dropped: dict[str, str] = Field(default_factory=dict)

    @property
    def used(self) -> list[str]:
        return [*self.numeric, *self.categorical]


def infer_feature_spec(frame: pd.DataFrame, feature_columns: list[str]) -> FeatureSpec:
    """Assign feature columns to numeric or categorical encoders from their dtypes."""
    spec = FeatureSpec()
    for col in feature_columns:
        series = frame[col]
        if series.isna().all():
            spec.dropped[col] = "all values missing"
        elif ptypes.is_datetime64_any_dtype(series):
            spec.dropped[col] = "datetime features are not encoded in the MVP"
        elif ptypes.is_bool_dtype(series) or ptypes.is_numeric_dtype(series):
            spec.numeric.append(col)
        else:
            spec.categorical.append(col)
    if not spec.used:
        raise ValueError("no usable feature columns after dtype inference")
    return spec


def _as_float(x: Any) -> np.ndarray:
    return np.asarray(pd.DataFrame(x).astype(float))


def _as_category_strings(x: Any) -> np.ndarray:
    df = pd.DataFrame(x).astype(object)
    return np.asarray(df.where(df.notna(), MISSING_CATEGORY).astype(str), dtype=object)


def build_preprocessor(spec: FeatureSpec, max_categories: int = 50) -> ColumnTransformer:
    """Median-impute + scale numerics; constant-impute + one-hot categoricals."""
    transformers: list[tuple[str, Any, list[str]]] = []
    if spec.numeric:
        numeric = Pipeline(
            [
                ("to_float", FunctionTransformer(_as_float, feature_names_out="one-to-one")),
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]
        )
        transformers.append(("num", numeric, spec.numeric))
    if spec.categorical:
        categorical = Pipeline(
            [
                (
                    "to_str",
                    FunctionTransformer(_as_category_strings, feature_names_out="one-to-one"),
                ),
                (
                    "onehot",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False,
                        max_categories=max_categories,
                    ),
                ),
            ]
        )
        transformers.append(("cat", categorical, spec.categorical))
    return ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)


def make_sampler(name: SamplerName, seed: int, smote_k_neighbors: int = 5) -> Any | None:
    if name == "none":
        return None
    if name == "random_under":
        return RandomUnderSampler(random_state=seed)
    if name == "random_over":
        return RandomOverSampler(random_state=seed)
    if name == "smote":
        return SMOTE(random_state=seed, k_neighbors=smote_k_neighbors)
    raise ValueError(f"unknown sampler {name!r}")


def build_pipeline(
    spec: FeatureSpec,
    estimator: Any,
    sampler: SamplerName = "none",
    seed: int = 42,
    smote_k_neighbors: int = 5,
) -> ImbPipeline:
    """Compose preprocessing, an optional sampler, and ``estimator`` into one imblearn Pipeline.

    The sampler runs after preprocessing, because SMOTE needs complete numeric input.
    """
    steps: list[tuple[str, Any]] = [("preprocess", build_preprocessor(spec))]
    sampler_obj = make_sampler(sampler, seed, smote_k_neighbors)
    if sampler_obj is not None:
        steps.append(("sampler", sampler_obj))
    steps.append(("model", estimator))
    return ImbPipeline(steps)
