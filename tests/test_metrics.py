import numpy as np
import pytest
from sklearn import metrics as skm

from imbalancelab.evaluation.metrics import (
    METRIC_NAMES,
    average_precision,
    brier,
    compute_metrics,
    confusion_at_threshold,
    fbeta,
    roc_auc,
    validate_inputs,
)


@pytest.fixture
def normal_inputs() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    y = (rng.random(400) < 0.1).astype(int)
    score = np.clip(0.2 * y + rng.random(400) * 0.8, 0, 1)
    return y, score


@pytest.mark.parametrize("threshold", [0.3, 0.5, 0.7])
@pytest.mark.parametrize("beta", [0.5, 1.0, 2.0])
def test_matches_scikit_learn(normal_inputs, threshold: float, beta: float) -> None:
    y, s = normal_inputs
    pred = (s >= threshold).astype(int)
    m = compute_metrics(y, s, threshold=threshold, beta=beta)
    expected = {
        "average_precision": skm.average_precision_score(y, s),
        "roc_auc": skm.roc_auc_score(y, s),
        "brier": skm.brier_score_loss(y, s),
        "precision": skm.precision_score(y, pred),
        "recall": skm.recall_score(y, pred),
        "f1": skm.f1_score(y, pred),
        "fbeta": skm.fbeta_score(y, pred, beta=beta),
        "balanced_accuracy": skm.balanced_accuracy_score(y, pred),
        "mcc": skm.matthews_corrcoef(y, pred),
    }
    assert set(m.metrics) == set(METRIC_NAMES)
    for name, value in expected.items():
        assert m.metrics[name].defined, name
        assert m.value(name) == pytest.approx(value, rel=1e-12, abs=1e-12), name
    tn, fp, fn, tp = skm.confusion_matrix(y, pred).ravel()
    assert (m.confusion.tn, m.confusion.fp, m.confusion.fn, m.confusion.tp) == (tn, fp, fn, tp)
    assert m.n == 400 and m.n_positive == int(y.sum())


@pytest.mark.parametrize("cls", [0, 1])
def test_single_class_y_true(cls: int) -> None:
    y = np.full(20, cls)
    s = np.linspace(0, 1, 20)
    m = compute_metrics(y, s)
    for name in ("average_precision", "roc_auc", "balanced_accuracy", "mcc"):
        r = m.metrics[name]
        assert r.defined is False and r.value is None and r.reason, name
    assert m.metrics["brier"].defined
    if cls == 0:
        assert not m.metrics["recall"].defined
        assert "no positive samples" in (m.metrics["recall"].reason or "")
        assert m.metrics["f1"].defined and m.value("f1") == 0.0  # fp>0 -> F = 0
    else:
        assert m.metrics["recall"].defined


def test_no_positive_predictions() -> None:
    y = np.array([0, 0, 0, 1, 1])
    s = np.array([0.1, 0.2, 0.3, 0.2, 0.4])
    m = compute_metrics(y, s, threshold=0.9)
    p = m.metrics["precision"]
    assert not p.defined and p.value is None and "no positive predictions" in (p.reason or "")
    assert m.value("recall") == 0.0
    assert m.value("f1") == 0.0  # 0 / (beta^2 * fn) is defined
    assert m.metrics["mcc"].reason == "predictions are constant at this threshold"
    assert m.value("balanced_accuracy") == 0.5
    assert m.metrics["average_precision"].defined  # ranking metrics do not use the threshold


def test_constant_scores_give_chance_level_with_note() -> None:
    y = np.array([0, 0, 0, 0, 1, 1, 0, 0, 0, 0])
    s = np.full(10, 0.3)
    m = compute_metrics(y, s, threshold=0.5)
    ap, auc = m.metrics["average_precision"], m.metrics["roc_auc"]
    assert ap.defined and ap.value == pytest.approx(0.2) and ap.note
    assert auc.defined and auc.value == pytest.approx(0.5) and auc.note
    assert not m.metrics["mcc"].defined and not m.metrics["precision"].defined
    m_low = compute_metrics(y, s, threshold=0.1)  # constant "all positive" predictions
    assert m_low.value("precision") == pytest.approx(0.2) and m_low.value("recall") == 1.0
    assert not m_low.metrics["mcc"].defined


def test_perfect_predictions() -> None:
    y = np.array([0, 0, 1, 1, 0, 1])
    s = y.astype(float)
    m = compute_metrics(y, s)
    for name in (
        "average_precision",
        "roc_auc",
        "precision",
        "recall",
        "f1",
        "fbeta",
        "balanced_accuracy",
        "mcc",
    ):
        assert m.value(name) == pytest.approx(1.0), name
    assert m.value("brier") == 0.0
    assert m.metrics["roc_auc"].note is None


def test_empty_input_and_degenerate_fbeta() -> None:
    m = compute_metrics([], [])
    assert all(not r.defined for r in m.metrics.values())
    c = confusion_at_threshold([0, 0], [0.1, 0.2], 0.5)
    assert not fbeta(c).defined
    with pytest.raises(ValueError):
        fbeta(c, beta=0)


def test_brier_requires_probabilities() -> None:
    assert not brier([0, 1], [-1.0, 2.0]).defined
    assert brier([0, 1], [0.0, 1.0]).value == 0.0


def test_input_validation() -> None:
    with pytest.raises(ValueError, match="lengths"):
        validate_inputs([0, 1], [0.1])
    with pytest.raises(ValueError, match="NaN"):
        average_precision([0, 1], [0.1, np.nan])
    with pytest.raises(ValueError, match="binary"):
        roc_auc([0, 2], [0.1, 0.2])


@pytest.mark.parametrize("cls", [0, 1])
def test_documented_contract_single_class_undefined_constant_scores_defined(cls: int) -> None:
    """The edge-case table in README.md and the metrics docstring."""
    single = compute_metrics(np.full(10, cls), np.linspace(0.1, 0.9, 10))
    for name in ("average_precision", "roc_auc"):
        r = single.metrics[name]
        assert (r.defined, r.value) == (False, None) and r.reason
    y = np.array([0, 0, 0, 1, 0, 0, 1, 0, 0, 0])
    constant = compute_metrics(y, np.full(10, 0.42))
    assert constant.metrics["average_precision"].value == pytest.approx(y.mean())
    assert constant.metrics["roc_auc"].value == pytest.approx(0.5)
    assert constant.metrics["average_precision"].defined and constant.metrics["roc_auc"].defined
