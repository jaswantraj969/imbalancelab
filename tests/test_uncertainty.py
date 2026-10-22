import numpy as np
import pytest

from imbalancelab.evaluation.metrics import compute_metrics
from imbalancelab.evaluation.uncertainty import (
    CI_METRICS,
    BootstrapConfig,
    bootstrap_cis,
    stratified_resample_indices,
)


@pytest.fixture
def well_behaved() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    y = (rng.random(600) < 0.15).astype(int)
    s = np.clip(0.35 * y + rng.random(600) * 0.65, 0, 1)
    return y, s


def test_deterministic_by_seed(well_behaved) -> None:
    y, s = well_behaved
    cfg = BootstrapConfig(n_resamples=300, seed=7)
    a = bootstrap_cis(y, s, threshold=0.5, beta=2.0, config=cfg)
    b = bootstrap_cis(y, s, threshold=0.5, beta=2.0, config=cfg)
    c = bootstrap_cis(
        y, s, threshold=0.5, beta=2.0, config=BootstrapConfig(n_resamples=300, seed=8)
    )
    assert a == b
    assert a["average_precision"].lower != c["average_precision"].lower


def test_ci_contains_point_and_matches_metrics(well_behaved) -> None:
    y, s = well_behaved
    cis = bootstrap_cis(y, s, threshold=0.5, beta=2.0, config=BootstrapConfig(n_resamples=500))
    assert set(cis) == set(CI_METRICS)
    reference = compute_metrics(y, s, threshold=0.5, beta=2.0)
    for name, ci in cis.items():
        assert ci.point == pytest.approx(reference.value(name)), name
        assert ci.lower is not None and ci.upper is not None
        assert ci.lower <= ci.point <= ci.upper, name
        assert ci.lower < ci.upper, name
        assert ci.n_defined == 500 and ci.n_undefined == 0
        assert ci.confidence == 0.95 and ci.n_resamples == 500


def test_stratification_preserves_class_counts(well_behaved) -> None:
    y, _ = well_behaved
    idx = stratified_resample_indices(y, n_resamples=200, seed=1)
    assert idx.shape == (200, y.size)
    n_pos = int(y.sum())
    assert (y[idx].sum(axis=1) == n_pos).all()
    # with replacement: some rows repeat within a resample
    assert any(len(np.unique(row)) < y.size for row in idx[:10])


def test_undefined_resamples_are_counted_not_dropped() -> None:
    # one positive with a score above the threshold; resamples that miss it entirely are
    # impossible (stratified), but a high threshold makes precision undefined whenever no
    # selected row scores above it
    y = np.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    s = np.array([0.40, 0.95, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    cis = bootstrap_cis(y, s, threshold=0.9, config=BootstrapConfig(n_resamples=400, seed=3))
    p = cis["precision"]
    # precision is defined only in resamples that contain the 0.95-scored negative
    assert 0 < p.n_undefined < 400 and p.n_defined + p.n_undefined == 400
    expected_undefined = 400 * (8 / 9) ** 9  # P(negative at index 1 never drawn in 9 draws)
    assert p.n_undefined == pytest.approx(expected_undefined, rel=0.35)
    all_undefined = bootstrap_cis(y, s, threshold=0.99, config=BootstrapConfig(n_resamples=100))
    assert all_undefined["precision"].n_undefined == 100
    assert all_undefined["precision"].lower is None and all_undefined["precision"].upper is None
    assert all_undefined["precision"].point is None


def test_vectorised_resample_metrics_match_scikit_learn_with_ties() -> None:
    from sklearn import metrics as skm

    from imbalancelab.evaluation.uncertainty import resample_metric_values

    rng = np.random.default_rng(5)
    y = (rng.random(300) < 0.2).astype(int)
    s = np.round(0.3 * y + rng.random(300) * 0.7, 1)  # heavy ties
    idx = stratified_resample_indices(y, n_resamples=40, seed=2)
    values = resample_metric_values(y, s, idx, threshold=0.5, beta=2.0)
    for i, row in enumerate(idx):
        yy, ss = y[row], s[row]
        pred = (ss >= 0.5).astype(int)
        assert values["average_precision"][i] == pytest.approx(skm.average_precision_score(yy, ss))
        assert values["roc_auc"][i] == pytest.approx(skm.roc_auc_score(yy, ss))
        assert values["precision"][i] == pytest.approx(skm.precision_score(yy, pred))
        assert values["recall"][i] == pytest.approx(skm.recall_score(yy, pred))
        assert values["fbeta"][i] == pytest.approx(skm.fbeta_score(yy, pred, beta=2.0))
        assert values["mcc"][i] == pytest.approx(skm.matthews_corrcoef(yy, pred))
