from typing import Any

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression

from conftest import make_imbalanced_frame
from imbalancelab.pipelines import (
    FeatureSpec,
    build_pipeline,
    build_preprocessor,
    infer_feature_spec,
    make_sampler,
)


class RecordingClassifier(ClassifierMixin, BaseEstimator):
    """Records exactly what reaches the estimator at fit and predict time."""

    def fit(self, X: Any, y: Any) -> "RecordingClassifier":
        self.fit_X_ = np.asarray(X).copy()
        self.fit_y_ = np.asarray(y).copy()
        self.classes_ = np.unique(y)
        self.predict_X_: list[np.ndarray] = []
        return self

    def predict_proba(self, X: Any) -> np.ndarray:
        X = np.asarray(X)
        self.predict_X_.append(X.copy())
        p = 1 / (1 + np.exp(-X[:, 0]))
        return np.column_stack([1 - p, p])

    def predict(self, X: Any) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


@pytest.fixture
def frame() -> pd.DataFrame:
    f = make_imbalanced_frame(n=240, seed=4)
    f["flag"] = f["x_signal"] > 0
    f.loc[f.index[:10], "color"] = np.nan
    return f


@pytest.fixture
def spec(frame: pd.DataFrame) -> FeatureSpec:
    return infer_feature_spec(frame, ["x_signal", "x_noise", "color", "flag"])


def test_infer_feature_spec(frame: pd.DataFrame) -> None:
    frame = frame.copy()
    frame["when"] = pd.to_datetime(frame["ts"])
    frame["empty"] = np.nan
    spec = infer_feature_spec(frame, ["x_signal", "color", "flag", "when", "empty"])
    assert spec.numeric == ["x_signal", "flag"]
    assert spec.categorical == ["color"]
    assert set(spec.dropped) == {"when", "empty"}
    assert spec.used == ["x_signal", "flag", "color"]
    with pytest.raises(ValueError):
        infer_feature_spec(frame, ["empty"])


def test_scaler_parameters_come_from_training_rows_only(frame, spec) -> None:
    y = (frame["label"] == "yes").to_numpy(dtype=int)
    train = np.arange(0, 160)
    pipe = build_pipeline(spec, LogisticRegression(), sampler="none")
    pipe.fit(frame.iloc[train], y[train])
    scaler = pipe.named_steps["preprocess"].named_transformers_["num"].named_steps["scale"]

    train_num = frame.iloc[train][spec.numeric].astype(float)
    imputed = train_num.fillna(train_num.median())
    np.testing.assert_allclose(scaler.mean_, imputed.mean().to_numpy())
    np.testing.assert_allclose(scaler.scale_, imputed.std(ddof=0).to_numpy())
    full = frame[spec.numeric].astype(float)
    full_mean = full.fillna(full.median()).mean().to_numpy()
    assert not np.allclose(scaler.mean_, full_mean)  # would match if all rows leaked in


def test_categories_learned_from_training_rows_only(frame, spec) -> None:
    y = (frame["label"] == "yes").to_numpy(dtype=int)
    train = frame.index[frame["color"] != "c"]
    pipe = build_pipeline(spec, LogisticRegression())
    pipe.fit(frame.loc[train], y[train])
    enc = pipe.named_steps["preprocess"].named_transformers_["cat"].named_steps["onehot"]
    assert "c" not in set(enc.categories_[0])
    # unseen category at predict time is ignored, not an error
    assert pipe.predict_proba(frame[frame["color"] == "c"]).shape[1] == 2


@pytest.mark.parametrize("sampler", ["random_over", "random_under", "smote"])
def test_sampler_changes_fit_data_but_not_predict_data(frame, spec, sampler) -> None:
    y = (frame["label"] == "yes").to_numpy(dtype=int)
    train, val = np.arange(0, 180), np.arange(180, 240)
    pipe = build_pipeline(spec, RecordingClassifier(), sampler=sampler, seed=0)
    pipe.fit(frame.iloc[train], y[train])
    model = pipe.named_steps["model"]
    n_pos = int(y[train].sum())
    counts = np.bincount(model.fit_y_)
    assert counts[0] == counts[1]  # the sampler balanced the training fold
    assert len(model.fit_y_) != len(train)
    assert (len(model.fit_y_) > len(train)) == (sampler != "random_under")
    assert n_pos < len(train) - n_pos

    proba = pipe.predict_proba(frame.iloc[val])
    seen = model.predict_X_[-1]
    expected_X = pipe.named_steps["preprocess"].transform(frame.iloc[val])
    assert seen.shape[0] == len(val)  # no resampling at predict time
    np.testing.assert_allclose(seen, expected_X)
    np.testing.assert_allclose(proba[:, 1], 1 / (1 + np.exp(-expected_X[:, 0])))


def test_pipeline_without_sampler_has_no_sampler_step(spec) -> None:
    pipe = build_pipeline(spec, LogisticRegression())
    assert [name for name, _ in pipe.steps] == ["preprocess", "model"]
    pipe2 = build_pipeline(spec, LogisticRegression(), sampler="smote")
    assert [name for name, _ in pipe2.steps] == ["preprocess", "sampler", "model"]


def test_make_sampler_unknown() -> None:
    with pytest.raises(ValueError):
        make_sampler("bogus", 0)  # type: ignore[arg-type]
    assert make_sampler("none", 0) is None


def test_preprocessor_numeric_only_and_categorical_only(frame) -> None:
    num = build_preprocessor(FeatureSpec(numeric=["x_signal"]))
    assert num.fit_transform(frame).shape == (len(frame), 1)
    cat = build_preprocessor(FeatureSpec(categorical=["color"]))
    out = cat.fit_transform(frame)
    assert out.shape == (len(frame), 4)  # a, b, c, __missing__
    np.testing.assert_allclose(out.sum(axis=1), 1.0)
