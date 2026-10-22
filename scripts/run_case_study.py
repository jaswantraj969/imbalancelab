"""Reproduce the ImbalanceLab case study on the `mammography` benchmark dataset.

    python scripts/run_case_study.py                   # full fresh run (scores the test sets)
    python scripts/run_case_study.py --amend-existing  # T-R2: amend the committed runs in place

Two runs share everything (candidates, seeds, CV, selection rule, threshold strategy) except
the split:

  (a) ``a_stratified``       - stratified holdout + stratified CV (the original M10 protocol)
  (b) ``b_duplicate_groups`` - ``duplicate_groups=True``: identical feature rows form one group,
                               and holdout/CV use StratifiedGroupKFold, so no duplicate cluster
                               crosses a split boundary; oversized groups are pinned to training.

Full mode: register -> repeated CV -> OOF threshold analysis for the best candidate by mean OOF
AP -> one-shot final test evaluation (with bootstrap CIs) -> report -> export to
docs/case_study/<label>/ -> generate docs/case_study.md from those records.

``--amend-existing`` does NOT score any test set again. For the workspace runs whose IDs match
the committed exports it adds evaluation coverage (folds rebuilt from the stored holdout, fold
SHA-256 verified) and bootstrap CIs (from the stored test predictions), regenerates the reports,
re-exports, and regenerates docs/case_study.md. Every amendment is logged in the run record.

If the download fails the script stops with exit code 2; it never substitutes synthetic data.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.error import URLError

import numpy as np
import pandas as pd

import imbalancelab.workflow as workflow
from imbalancelab.data.loader import LoadedDataset, load_dataset
from imbalancelab.data.schema import DatasetSchema
from imbalancelab.evaluation.calibration import calibration_disclosure
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import amend_bootstrap_cis
from imbalancelab.evaluation.metrics import average_precision, roc_auc
from imbalancelab.evaluation.runner import amend_evaluation_coverage
from imbalancelab.evaluation.thresholds import ThresholdStrategy
from imbalancelab.evaluation.uncertainty import BootstrapConfig, bootstrap_cis
from imbalancelab.models.persistence import load_model, predict
from imbalancelab.profiling.profile import feature_row_hashes
from imbalancelab.reporting.render import Document, to_markdown
from imbalancelab.reporting.report import (
    comparison_verdict,
    coverage_blocks,
    final_test_verdict,
    fmt,
    fmt_ci,
    fmt_summary,
    generate_report,
)
from imbalancelab.splitting.splits import HoldoutConfig
from imbalancelab.tracking.records import RunRecord

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATASET = "mammography"
SOURCE = {
    "collection": "imbalanced-learn benchmark collection (imblearn.datasets.fetch_datasets)",
    "title": "Imbalanced dataset for benchmarking",
    "zenodo_record": "https://zenodo.org/records/61452",
    "doi": "10.5281/zenodo.61452",
    "creators": "Lemaitre, Nogueira, Aridas, Oliveira (2016)",
    "license": "Open Database License (ODbL), licence id `odc-odbl` on the Zenodo record",
    "license_url": "https://opendatacommons.org/licenses/odbl/",
    "original_repository": "UCI (per the imbalanced-learn dataset table; benchmark proposed by "
    "Ding, Z., 'Diversified Ensemble Classifiers for Highly Imbalanced Data Learning and "
    "their Application in Bioinformatics', 2011)",
}
NOTICE = f"""# Notice: data source and licence

The files in this directory are derived from the `mammography` dataset of the
**"{SOURCE["title"]}"** collection by {SOURCE["creators"]},
DOI [{SOURCE["doi"]}](https://doi.org/{SOURCE["doi"]}), {SOURCE["zenodo_record"]}.

That database is made available under the **Open Database License (ODbL)**
({SOURCE["license_url"]}), as listed on the Zenodo record (licence id `odc-odbl`). The predictions,
indices and other records here are derived from that database. Any redistribution of a derived
database must follow the ODbL terms (attribution and share-alike).

The original data originates from the UCI repository via the imbalanced-learn benchmark
(benchmark proposed by Ding, Z., 2011).
"""
# ---- protocol: identical for both runs except duplicate_groups ----
# These constants are unchanged since the first execution in M10 (see docs/case_study.md,
# "Protocol history").
HOLDOUT = HoldoutConfig(test_size=0.2, seed=42)
CONFIG = ExperimentConfig.model_validate(
    {
        "candidates": [
            {"model": "hgb"},
            {"model": "hgb", "sampler": "random_under"},
            {"model": "hgb", "sampler": "smote"},
            {"model": "random_forest"},
        ],
        "cv": {"n_splits": 5, "n_repeats": 3, "seed": 42},
        "seed": 42,
    }
)
THRESHOLD_STRATEGY = ThresholdStrategy(kind="max_fbeta", beta=2.0)
BOOTSTRAP = BootstrapConfig(n_resamples=2000, seed=42)
SELECTION_RULE = (
    "the non-baseline candidate with the highest mean out-of-fold average precision "
    "(summary.best_candidate_by_mean_oof_ap); test data is not used"
)
RUNS = {
    "a_stratified": DatasetSchema(
        target="target", positive_label=1, split_strategy="stratified", duplicate_groups=False
    ),
    "b_duplicate_groups": DatasetSchema(
        target="target", positive_label=1, split_strategy="stratified", duplicate_groups=True
    ),
}
EXPORT_SKIP_LARGER_THAN = 1_000_000  # bytes; larger files are listed with their SHA-256 only

# Execution history of this case study, from the command logs in
# docs/process/REVIEW_PACKET.md (M10, T-R1).
# Facts only; used verbatim in docs/case_study.md "Protocol history".
PROTOCOL_HISTORY_ROWS = [
    (
        "1",
        "M10",
        "(none: failed before CV)",
        "—",
        "no",
        "`FileNotFoundError` on the extracted file name",
    ),
    (
        "2",
        "M10",
        "(stopped by me)",
        "—",
        "unknown",
        "stopped to fix `source_name`; its log was overwritten, so whether it reached final "
        "evaluation is unknown",
    ),
    ("3", "M10", "`run-20261022T083455Z-ef809093`", "—", "yes", "superseded (report wording)"),
    ("4", "M10", "`run-20261022T083728Z-db0f0d23`", "—", "yes", "superseded (report wording)"),
    (
        "5",
        "M10",
        "`run-20261022T083838Z-b12a4417`",
        "—",
        "yes",
        "committed in M10, superseded in T-R1",
    ),
    (
        "6",
        "T-R1",
        "`run-20261022T090059Z-c27d4eb9`",
        "`run-20261022T090141Z-9165d0cb` (**split v1**, no large-group rule)",
        "yes",
        "run (b) found **degenerate** and discarded (see below)",
    ),
    (
        "7",
        "T-R1",
        "`run-20261022T090930Z-8ca49f38`",
        "`run-20261022T091037Z-8d492e51` (**split v2**)",
        "yes",
        "superseded: the hash check exposed random-forest non-determinism (D29)",
    ),
    (
        "8",
        "T-R1",
        "`run-20261022T091904Z-596af186`",
        "`run-20261022T092013Z-2056207e` (split v2)",
        "yes",
        "**reported runs**",
    ),
    (
        "9",
        "T-R2",
        "same as #8",
        "same as #8",
        "**no**",
        "bootstrap CIs and evaluation coverage added from stored predictions and indices",
    ),
]
PROTOCOL_HISTORY = "\n".join(
    [
        "| # | When | Run (a) stratified | Run (b) duplicate groups | Test set scored? | Outcome |",
        "|---|---|---|---|---|---|",
        *("| " + " | ".join(row) + " |" for row in PROTOCOL_HISTORY_ROWS),
    ]
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(data_home: Path) -> tuple[Path, Path]:
    """Fetch the dataset; return (extracted .npz path, CSV path)."""
    from imblearn.datasets import fetch_datasets
    from imblearn.datasets._zenodo import MAP_NAME_ID, POST_FILENAME, PRE_FILENAME

    bunch = fetch_datasets(
        data_home=str(data_home), filter_data=(DATASET,), download_if_missing=True, verbose=True
    )[DATASET]
    npz = data_home / "zenodo" / f"{PRE_FILENAME}{MAP_NAME_ID[DATASET]}{POST_FILENAME}"
    if not npz.is_file():
        raise FileNotFoundError(f"expected extracted file {npz} not found")
    frame = pd.DataFrame(bunch.data, columns=[f"feature_{i}" for i in range(bunch.data.shape[1])])
    frame["target"] = bunch.target.astype(int)
    csv = data_home.parent / f"{DATASET}.csv"
    frame.to_csv(csv, index=False)
    return npz, csv


def export_run(run_dir: Path, dest: Path) -> dict[str, Any]:
    """Copy the run record to ``dest``; files over the size limit are listed, not copied."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    omitted = {}
    for path in sorted(run_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(run_dir)
        if path.stat().st_size > EXPORT_SKIP_LARGER_THAN:
            omitted[str(rel).replace("\\", "/")] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    (dest / "OMITTED_FILES.json").write_text(json.dumps(omitted, indent=2) + "\n")
    (dest / "NOTICE.md").write_text(NOTICE, encoding="utf-8", newline="\n")
    return omitted


def _load(record: RunRecord, data_path: Path) -> LoadedDataset:
    schema = DatasetSchema.model_validate(record.run["dataset"]["schema"])
    dataset = load_dataset(data_path, schema)
    if dataset.sha256 != record.run["dataset"]["sha256"]:
        raise RuntimeError("dataset file does not match the run's dataset SHA-256")
    return dataset


def _subset_metrics(y: np.ndarray, s: np.ndarray, threshold: float) -> dict[str, Any]:
    cis = bootstrap_cis(y, s, threshold=threshold, beta=THRESHOLD_STRATEGY.beta, config=BOOTSTRAP)
    return {
        "n_rows": int(y.size),
        "n_positive": int(y.sum()),
        "prevalence": float(y.mean()) if y.size else None,
        "average_precision": average_precision(y, s).value,
        "roc_auc": roc_auc(y, s).value,
        "ci": {k: cis[k].model_dump(mode="json") for k in ("average_precision", "roc_auc")},
    }


def duplicate_sensitivity(record: RunRecord, dataset: LoadedDataset) -> dict[str, Any]:
    """Post-hoc re-slice of the *stored* test predictions: metrics (with bootstrap CIs) on all
    test rows and on test rows whose features do not exactly duplicate an outer-train row.
    No refit, no re-scoring, no selection."""
    hashes = feature_row_hashes(dataset.frame, dataset.feature_columns)
    holdout = record.holdout
    train_hashes = set(hashes[holdout["train_idx"]].tolist())
    test_idx = np.asarray(holdout["test_idx"])
    dup = {int(i): hashes[i] in train_hashes for i in test_idx}
    preds = record.final_predictions()
    final = record.final_evaluation
    assert preds is not None and final is not None
    models: dict[str, Any] = {}
    for model, g in preds.groupby("model", sort=False):
        threshold = final["results"][str(model)]["threshold"]
        keep = ~g["row_index"].map(dup).to_numpy(dtype=bool)
        y, sc = g["y_true"].to_numpy(dtype=int), g["y_score"].to_numpy(dtype=float)
        models[str(model)] = {
            "all_rows": _subset_metrics(y, sc, threshold),
            "excluding_duplicates_of_train": _subset_metrics(y[keep], sc[keep], threshold),
        }
    return {
        "description": "post-hoc re-slicing of stored final test predictions; no refit, "
        "no re-scoring, no selection; CIs: stratified bootstrap "
        f"({BOOTSTRAP.n_resamples} resamples, seed {BOOTSTRAP.seed})",
        "n_test": int(test_idx.size),
        "n_test_rows_duplicating_outer_train": int(sum(dup.values())),
        "n_positive_test_rows_duplicating_outer_train": int(
            sum(int(dataset.y[i]) for i, d in dup.items() if d)
        ),
        "models": models,
    }


def cluster_analysis(
    record: RunRecord, dataset: LoadedDataset, models_dir: Path
) -> tuple[str, dict[str, Any]]:
    """Facts about the largest duplicate cluster and the selected model's prediction for it."""
    feats = dataset.feature_columns
    hashes = feature_row_hashes(dataset.frame, feats)
    counts = pd.Series(hashes).value_counts()
    rows = np.flatnonzero(hashes == counts.index[0])
    X = dataset.frame[feats]
    vector = X.iloc[rows[0]]
    n_pos = int(dataset.y[rows].sum())
    lines = [
        f"Largest duplicate cluster (run {record.run_id}, duplicate_groups=True)",
        f"rows: {rows.size} of {dataset.n_rows} ({100 * rows.size / dataset.n_rows:.2f}% of "
        f"the dataset)   positives: {n_pos}   negatives: {rows.size - n_pos}",
        f"rows in the cluster that are in the test set: "
        f"{len(set(rows.tolist()) & set(record.holdout['test_idx']))}",
        f"identical feature vector of all {rows.size} rows "
        f"(all rows equal: {bool((X.iloc[rows] == vector).all(axis=None))}):",
    ]
    n_min = n_zero = 0
    for col in feats:
        column = X[col].to_numpy(dtype=float)
        v = float(vector[col])
        is_min, is_max = v == column.min(), v == column.max()
        n_min += int(is_min)
        n_zero += int(v == 0.0)
        same = int(np.sum(column == v))
        lines.append(
            f"  {col} = {v:.8f}   column min {column.min():.8f}, median {np.median(column):.8f}, "
            f"max {column.max():.8f}   is column min: {'yes' if is_min else 'no'}   "
            f"is column max: {'yes' if is_max else 'no'}   rows with exactly this value: "
            f"{same} ({100 * same / column.size:.2f}%)   rows below it: "
            f"{int(np.sum(column < v))}"
        )
    lines += [
        f"features equal to their column minimum: {n_min} of {len(feats)}"
        + (" (consistent with a floor or zero-measurement value)" if n_min == len(feats) else ""),
        f"features equal to 0: {n_zero} of {len(feats)}",
        f"distinct values within the vector: {len(set(np.round(vector.to_numpy(dtype=float), 8)))}",
    ]
    facts: dict[str, Any] = {
        "n_rows": int(rows.size),
        "n_positive": n_pos,
        "prevalence": n_pos / rows.size,
        "in_test": len(set(rows.tolist()) & set(record.holdout["test_idx"])),
    }
    final = record.final_evaluation or {}
    model_id = final.get("persisted_model_id")
    if model_id:
        loaded = load_model(models_dir, model_id)
        preds = predict(loaded, X.iloc[rows])
        p = preds["probability"].to_numpy()
        lines += [
            f"selected model: {loaded.metadata.model_name} (persisted model {model_id}, refit on "
            f"outer-train rows only, artifact SHA-256 verified on load)",
            f"predicted probability for the cluster's feature vector: {p[0]:.8f}   "
            f"distinct predicted values over the {rows.size} rows: {len(np.unique(p))}",
            f"stored threshold: {loaded.metadata.threshold:.8f}   predicted label: "
            f"{int(preds['label'].iloc[0])}   "
            f"(training prevalence of the cluster: {n_pos / rows.size:.6f})",
        ]
        facts.update(
            model=loaded.metadata.model_name,
            probability=float(p[0]),
            threshold=float(loaded.metadata.threshold),
            label=int(preds["label"].iloc[0]),
        )
    return "\n".join(lines), facts


def run_protocol(ws: workflow.Workspace, csv: Path, label: str, schema: DatasetSchema) -> RunRecord:
    reg = workflow.register_dataset(ws, csv, ".csv", schema, HOLDOUT, source_name=csv.name)
    print(f"[{label}] registered {reg.dataset_id}: {reg.n_rows} rows, sha256={reg.sha256}")
    brief = workflow.start_run(ws, reg.dataset_id, CONFIG)
    run_id, best = brief["run_id"], brief["best_candidate_by_mean_oof_ap"]
    print(f"[{label}] run {run_id} {brief['status']}; best candidate by OOF AP: {best}")
    workflow.analyse_thresholds(ws, run_id, best, THRESHOLD_STRATEGY)
    final = workflow.finalize_run(ws, run_id, model=best, bootstrap=BOOTSTRAP)
    print(f"[{label}] final evaluation done; persisted model {final['model_id']}")
    return RunRecord(ws.run_dir(run_id))


def amend_protocol(ws: workflow.Workspace, label: str) -> RunRecord:
    """Amend the workspace run behind the committed export ``label`` (no test scoring)."""
    committed = json.loads((DOCS / "case_study" / label / "run.json").read_text())
    run_dir = ws.run_dir(committed["run_id"])
    record = RunRecord(run_dir)
    dataset = _load(record, ws.dataset_dir(committed["dataset_id"]) / "data.csv")
    preds_sha = sha256(run_dir / "final_predictions.parquet")
    coverage = amend_evaluation_coverage(dataset, run_dir)
    amend_bootstrap_cis(run_dir, BOOTSTRAP)
    assert sha256(run_dir / "final_predictions.parquet") == preds_sha  # test predictions untouched
    f = coverage["forced_to_train"]
    print(
        f"[{label}] amended {committed['run_id']}: coverage forced_to_train={f['n_rows']} rows "
        f"({f['n_positive']} positive); bootstrap CIs added from stored predictions"
    )
    return record


def finish(
    ws: workflow.Workspace, label: str, record: RunRecord
) -> tuple[dict, dict, LoadedDataset]:
    generate_report(record.path)
    export_dir = DOCS / "case_study" / label
    omitted = export_run(record.path, export_dir)
    dataset = _load(record, ws.dataset_dir(record.run["dataset_id"]) / "data.csv")
    sensitivity = duplicate_sensitivity(record, dataset)
    (export_dir / "duplicate_sensitivity.json").write_text(json.dumps(sensitivity, indent=2) + "\n")
    return omitted, sensitivity, dataset


# ------------------------------------------------------------------ document generation


def _test_part(record: RunRecord, model: str) -> dict[str, Any] | None:
    final = record.final_evaluation or {}
    r = final.get("results", {}).get(model)
    if r is None:
        return None
    preds = record.final_predictions()
    assert preds is not None
    g = preds[preds["model"] == model]
    y = g["y_true"].to_numpy(dtype=int)
    return {
        "ap": r["metrics"]["average_precision"]["value"],
        "n_rows": int(y.size),
        "n_positive": int(y.sum()),
        "prevalence": float(y.mean()),
        "result": r,
    }


def _crossing(record: RunRecord) -> dict[str, Any]:
    for w in record.run.get("split_warnings", []):
        if w["code"] == "cross_boundary_duplicates":
            return dict(w["evidence"])
    return {"test_rows_duplicating_train": 0, "folds_affected": 0}


def _gap(oof: float | None, test: float | None) -> str:
    return "undefined" if oof is None or test is None else f"{oof - test:+.4f}"


def _ci_text(part: dict[str, Any], metric: str) -> str:
    ci = part["ci"][metric]
    value = fmt(part[metric])
    if ci["lower"] is None:
        return f"{value} [CI undefined]"
    return f"{value} [{ci['lower']:.4f}, {ci['upper']:.4f}]"


def _coverage_markdown(record: RunRecord) -> str:
    doc = Document(title="x")
    doc.add(*coverage_blocks(record.run))
    return to_markdown(doc).split("\n", 2)[2].rstrip()


def build_case_study(
    rec_a: RunRecord,
    rec_b: RunRecord,
    sens_a: dict[str, Any],
    sens_b: dict[str, Any],
    omitted_b: dict[str, Any],
    provenance: dict[str, Any],
    cluster_text: str,
    cluster: dict[str, Any],
) -> str:
    run_a, run_b = rec_a.run, rec_b.run
    sum_a, sum_b = rec_a.summary, rec_b.summary
    best_a, best_b = sum_a["best_candidate_by_mean_oof_ap"], sum_b["best_candidate_by_mean_oof_ap"]
    t_a, t_b = _test_part(rec_a, best_a), _test_part(rec_b, best_b)
    assert t_a is not None and t_b is not None
    profile = rec_b.profile or {}
    cb = profile["class_balance"]
    info_b = run_b["holdout"]["group_info"]
    final_b = rec_b.final_evaluation or {}
    bs = final_b["bootstrap"]
    th_b = (rec_b.thresholds or {})["analyses"][best_b]
    sp = th_b["per_repeat_spread"]
    cov_b = run_b["evaluation_coverage"]["forced_to_train"]
    ci_note = (
        f"Brackets are {bs['confidence']:.0%} CIs from a stratified bootstrap of the test rows "
        f"({bs['n_resamples']} resamples, seed {bs['seed']}; positives and negatives resampled "
        "separately). They reflect test-sample variation only."
    )

    L: list[str] = []
    add = L.extend
    add(
        [
            "# Case study: `mammography` (imbalanced-learn benchmark)",
            "",
            "> Generated by `scripts/run_case_study.py` from two run records: "
            f"(a) `{run_a['run_id']}` in [`case_study/a_stratified/`](case_study/a_stratified/) "
            f"and (b) `{run_b['run_id']}` in "
            "[`case_study/b_duplicate_groups/`](case_study/b_duplicate_groups/). Every number "
            "below is read from files in those folders or computed from them by the script. "
            "Nothing was typed in by hand.",
            "",
            "> **Data licence:** derived from the "
            f'"{SOURCE["title"]}" collection ({SOURCE["creators"]}, DOI '
            f"[{SOURCE['doi']}](https://doi.org/{SOURCE['doi']})), available under the "
            f"[Open Database License (ODbL)]({SOURCE['license_url']}). See "
            "[Data source and licence](#data-source-and-licence).",
            "",
            "## Headline (run b: duplicate-aware split)",
            "",
            f"The selected model **`{best_b}`** scored **test AP "
            f"{fmt_ci(t_b['result'], 'average_precision')}** on a single evaluation of "
            f"{t_b['n_rows']} test rows with {t_b['n_positive']} positives (prevalence "
            f"{fmt(t_b['prevalence'])}). On the same test rows:",
            "",
            "| Model | Test AP [95% CI] | Test ROC AUC [95% CI] | Test Brier [95% CI] (lower "
            "is better) | Test rows | Positives | Prevalence |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for name in final_b["results"]:
        t = _test_part(rec_b, name)
        assert t is not None
        add(
            [
                f"| `{name}` | {fmt_ci(t['result'], 'average_precision')} | "
                f"{fmt_ci(t['result'], 'roc_auc')} | {fmt_ci(t['result'], 'brier')} | "
                f"{t['n_rows']} | {t['n_positive']} | {fmt(t['prevalence'])} |"
            ]
        )
    add(
        [
            "",
            f"Paired bootstrap of the test difference (`{best_b}` − baseline; same resampled rows "
            "for both models):",
            "",
            "| Baseline | Metric | Difference [95% CI] | Win fraction |",
            "|---|---|---|---|",
        ]
    )
    for d in final_b.get("paired_bootstrap", []):
        add(
            [
                f"| `{d['baseline']}` | {d['metric']} | {d['point']:+.4f} "
                f"[{d['lower']:+.4f}, {d['upper']:+.4f}] | {d['win_fraction']:.3f} |"
            ]
        )
    oof_sel = sum_b["models"][best_b]["average_precision"]["mean"]
    ap_ci = t_b["result"]["ci"]["average_precision"]
    inside = ap_ci["lower"] <= oof_sel <= ap_ci["upper"]
    add(
        [
            "",
            f"The OOF selection estimate for `{best_b}` (mean AP {fmt(oof_sel)}, optimistic "
            "because it was used for selection) "
            + (
                f"**lies inside** the test AP 95% CI [{ap_ci['lower']:.4f}, "
                f"{ap_ci['upper']:.4f}]. The two are consistent. This does **not** show that test "
                "performance exceeds CV performance."
                if inside
                else f"**lies outside** the test AP 95% CI [{ap_ci['lower']:.4f}, "
                f"{ap_ci['upper']:.4f}]."
            ),
        ]
    )
    add(
        [
            "",
            ci_note,
            "",
            f"**Evaluation coverage (run b): {cov_b['n_rows']} rows ({cov_b['pct_of_rows']:.1f}% "
            f"of the dataset, {cov_b['n_positive']} positives) are never in any test or "
            "validation set.** They form one oversized duplicate cluster that is forced to "
            "training, so the results above do not describe those rows. See "
            "[Evaluation coverage](#evaluation-coverage-run-b) and the "
            "[data-quality finding](#data-quality-finding-the-3329-row-cluster).",
            "",
            "Run (b) is the headline because in run (a) exact-duplicate rows cross the train/test "
            "and CV boundaries. In run (b) the cross-boundary duplicate check reports "
            f"{_crossing(rec_b)['test_rows_duplicating_train']} test rows and "
            f"{_crossing(rec_b)['folds_affected']} affected folds.",
            "",
            "## Data source and licence",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Dataset | `{DATASET}` |",
            f'| Collection | "{SOURCE["title"]}", {SOURCE["collection"]} |',
            f"| Zenodo record / DOI | {SOURCE['zenodo_record']} / `{SOURCE['doi']}` |",
            f"| Creators | {SOURCE['creators']} |",
            f"| Licence | {SOURCE['license']}: {SOURCE['license_url']} |",
            f"| Original repository | {SOURCE['original_repository']} |",
            f"| SHA-256 of extracted `{provenance['npz_file']}` | `{provenance['npz_sha256']}` |",
            f"| SHA-256 of CSV used (both runs) | `{run_b['dataset']['sha256']}` |",
            f"| Rows / features | {cb['n_rows']} / {profile['n_features']} |",
            f"| Positives / negatives | {cb['n_positive']} / {cb['n_negative']} "
            f"(prevalence {fmt(cb['positive_rate'])}, ratio {fmt(cb['imbalance_ratio'], 1)}:1) |",
            "| Exact duplicate rows (profile) | "
            f"{profile['duplicates']['n_exact_duplicate_rows']} |",
            "",
            "Attribution: this case study and the run records under `docs/case_study/` are derived "
            "from the database above, which is licensed under the ODbL. A `NOTICE.md` in each "
            "run-record directory repeats the source, DOI and licence.",
            "",
            "## Protocol",
            "",
            "Both runs use the same protocol. The only difference is the split.",
            "",
            f"- **Candidates (full list):** {', '.join(f'`{c}`' for c in run_b['candidates'])}. "
            f"**Baselines:** {', '.join(f'`{c}`' for c in run_b['baselines'])}. Small fixed "
            "configs (see `run.json` `model_specs`). Samplers run inside the imblearn pipeline "
            "during fit only.",
            f"- **Selection rule:** {SELECTION_RULE}.",
            f"- **Threshold rule:** `{THRESHOLD_STRATEGY.kind}` with beta={THRESHOLD_STRATEGY.beta}"
            ", selected on each CV repeat's OOF predictions for the selected model; the median "
            "of the per-repeat thresholds is used.",
            f"- **Seeds and CV:** holdout test_size {HOLDOUT.test_size} with seed {HOLDOUT.seed}; "
            f"{CONFIG.cv.n_splits}-fold × {CONFIG.cv.n_repeats} repeats with seed "
            f"{CONFIG.cv.seed}; estimator seed {CONFIG.seed}.",
            "- **Final evaluation:** the selected model and both baselines are refit on "
            "outer-train rows, and the test rows are scored once per execution (see "
            "Protocol history). Bootstrap CIs come from the stored test predictions.",
            "- **(a) `a_stratified`:** a stratified holdout and stratified CV (the original M10 "
            "protocol).",
            "- **(b) `b_duplicate_groups`:** `duplicate_groups=True`. Rows with identical feature "
            "values form one group, and both the holdout and CV use `StratifiedGroupKFold`. "
            f"There are {info_b['n_groups']} split groups, of which "
            f"{info_b['n_duplicate_clusters']} are duplicate clusters covering "
            f"{info_b['n_rows_in_duplicate_clusters']} rows. "
            f"{info_b['n_conflicting_label_clusters']} cluster(s) have conflicting labels "
            f"({info_b['n_rows_in_conflicting_clusters']} rows, kept). **Large-group rule:** a "
            "group larger than `max_eval_group_fraction` "
            f"({run_b['evaluation_coverage']['cutoff']['holdout_max_eval_group_fraction']:.0%}) "
            "of the target test or validation size is forced to train.",
            "",
            "### Protocol history",
            "",
            "Every execution of this case study, from the command logs in "
            "[`docs/process/REVIEW_PACKET.md`](process/REVIEW_PACKET.md):",
            "",
            PROTOCOL_HISTORY.rstrip(),
            "",
            "- **Run (b) was added after run (a) results had been seen.** The supervisor requested "
            "it in review T-R1, after the M10 case study (run a protocol) was reported.",
            "- **The first run (b) split (split v1, execution 6) was produced, scored, found "
            "degenerate, and discarded.** Its test set was one 3329-row duplicate cluster plus 45 "
            "other rows that were all positive. `StratifiedGroupKFold` had rebalanced the class "
            "ratio around the unsplittable cluster, and two different models scored the same "
            "test AP. The degeneracy was found by inspecting that run's test predictions.",
            "- **The large-group rule was then added.** Groups above 25% of the target test or "
            "validation size are forced to train, and holdout size, prevalence and "
            "dominant-group warnings were added (PROJECT_STATUS D28). Only this one cut-off value "
            "was tried. The reported run (b) uses **the second split (split v2)**.",
            "- **Test-set reuse:** the run (a) test set (test-index SHA-256 "
            f"`{run_a['holdout']['test_sha256'][:16]}…`) was scored in executions 3–8, six times "
            "with the same protocol, plus possibly execution 2. The split v2 test set (SHA-256 "
            f"`{run_b['holdout']['test_sha256'][:16]}…`) was scored in executions 7 and 8. The "
            "change between 7 and 8 (random-forest threads, D29) came from the out-of-fold hash "
            "check, not from test results, and did not change any reported metric. Execution 9 "
            "scored nothing.",
            "- **Fixed before any case-study test scoring:** the candidate list, seeds, CV "
            "settings and selection rule were written into this script before execution 1. "
            "Git cannot prove that ordering, because the script was first committed in M10 "
            "(`91c6f54`) after those executions.",
            "- **Threshold aggregation rule (median across repeats):** decided in M5 as "
            "PROJECT_STATUS decision **D15** and implemented in commit **`7ce0891`** "
            "(2026-10-22 13:05:52 +05:00). This **precedes** the first case-study execution "
            "(execution 3, run `run-20261022T083455Z-ef809093` = 08:34:55Z = 13:34:55 +05:00) "
            "and so all test scoring.",
            "",
            "## Results, run (b)",
            "",
            "OOF AP is a **selection estimate (optimistic: used for model selection)**. Test "
            "values are single scorings of the held-out rows, with 95% bootstrap CIs.",
            "",
            "| Model | Role | OOF AP: selection estimate (optimistic) | OOF ROC AUC | "
            "Test AP [95% CI] | Test rows / positives / prevalence |",
            "|---|---|---|---|---|---|",
        ]
    )
    for name in run_b["models"]:
        s = sum_b["models"][name]
        role = "baseline" if name in run_b["baselines"] else "candidate"
        if name == best_b:
            role += " (selected)"
        t = _test_part(rec_b, name)
        test_cells = (
            f"{fmt_ci(t['result'], 'average_precision')} | {t['n_rows']} / {t['n_positive']} / "
            f"{fmt(t['prevalence'])}"
            if t
            else "not scored | —"
        )
        add(
            [
                f"| `{name}` | {role} | {fmt_summary(s['average_precision'])} | "
                f"{fmt_summary(s['roc_auc'])} | {test_cells} |"
            ]
        )
    add(["", "Paired comparisons on identical folds (run b, OOF AP, descriptive):", ""])
    add(
        [
            f"- {comparison_verdict(c)}"
            for c in sum_b["comparisons"]
            if c["metric"] == "average_precision"
        ]
    )
    add(
        [
            f"- {final_test_verdict(c, final_b['results'])}"
            for c in final_b["comparisons"]
            if c["metric"] == "average_precision"
        ]
    )
    r = t_b["result"]
    c = r["confusion"]
    add(
        [
            "",
            "## Threshold, run (b)",
            "",
            f"- **Model:** `{best_b}`. **Strategy:** `{th_b['strategy']['kind']}` with beta="
            f"{th_b['strategy']['beta']}, selected on OOF predictions for each of "
            f"{sp['threshold']['n']} CV repeats. **Rule:** {th_b['selection_rule']} (decided in "
            "M5, D15 / `7ce0891`).",
            f"- **Chosen threshold:** {fmt(th_b['chosen_threshold'])}. Per-repeat thresholds: "
            f"mean {fmt(sp['threshold']['mean'])} ± {fmt(sp['threshold']['std'])} (sample std), "
            f"range [{fmt(sp['threshold']['min'])}, {fmt(sp['threshold']['max'])}]. Individual "
            "values: "
            + ", ".join(f"repeat {p['repeat']}: {fmt(p['threshold'])}" for p in th_b["per_repeat"])
            + ".",
            "- **Test metrics at the chosen threshold** (scored once; [95% CI]):",
            "",
            "| Precision | Recall | F-beta (beta=2) | MCC | TP | FP | FN | TN |",
            "|---|---|---|---|---|---|---|---|",
            f"| {fmt_ci(r, 'precision')} | {fmt_ci(r, 'recall')} | {fmt_ci(r, 'fbeta')} | "
            f"{fmt_ci(r, 'mcc')} | {c['tp']} | {c['fp']} | {c['fn']} | {c['tn']} |",
            "",
            f"**Recall scope:** the {cluster['n_rows']} forced-to-train rows all have the same "
            f"score, {cluster.get('probability', float('nan')):.4f}, which is below the stored "
            f"threshold {cluster.get('threshold', float('nan')):.4f}, so all of them are "
            f"classified **negative** (label {cluster.get('label')}). Their "
            f"{cluster['n_positive']} positives would therefore be missed. The test recall above "
            "describes only the evaluated rows.",
            "",
            ci_note,
            "",
            "## Calibration (disclosure only; no calibration stage)",
            "",
            *[f"- **{n}**" for n in calibration_disclosure(run_b.get("model_specs") or [])],
            f"- Test Brier score of `{best_b}`: {fmt_ci(r, 'brier')}. The reliability curve "
            "(quantile bins, n per bin) is in the run (b) audit report, section 9.",
            f"- **Evidence from the cluster:** for the {cluster['n_rows']}-row cluster, "
            f"`{cluster.get('model')}` outputs {cluster.get('probability', float('nan')):.4f}, "
            f"while the cluster's observed positive rate is {cluster['prevalence']:.4f} "
            f"({cluster['n_positive']}/{cluster['n_rows']}, in training rows). That is "
            f"{cluster.get('probability', float('nan')) / cluster['prevalence']:.0f}× higher, so "
            "this score does not estimate the probability of the positive class.",
            "",
            "## Evaluation coverage (run b)",
            "",
            "As generated in the run's audit report (section 5):",
            "",
            _coverage_markdown(rec_b),
            "",
            "## Data-quality finding: the 3329-row cluster",
            "",
            "Output of `cluster_analysis()` in `scripts/run_case_study.py`. The data and the "
            "persisted run (b) model (refit on outer-train rows, as in the final evaluation) are "
            "used. This describes values only and makes no claim about their cause.",
            "",
            "```text",
            cluster_text,
            "```",
            "",
            "## Duplicate-leakage finding: run (a) vs run (b)",
            "",
            "The two runs use **different test sets**. Differences between the columns combine "
            "the effect of duplicates crossing boundaries with the effect of a different test "
            "sample, and in run (b) with the exclusion of the forced-to-train cluster.",
            "",
            "| | (a) stratified | (b) duplicate groups |",
            "|---|---|---|",
            f"| Run ID | `{run_a['run_id']}` | `{run_b['run_id']}` |",
            f"| Test rows duplicating outer-train rows | "
            f"{_crossing(rec_a)['test_rows_duplicating_train']} | "
            f"{_crossing(rec_b)['test_rows_duplicating_train']} |",
            f"| CV folds with validation rows duplicating training rows | "
            f"{_crossing(rec_a)['folds_affected']} of {run_a['cv']['n_folds_total']} | "
            f"{_crossing(rec_b)['folds_affected']} of {run_b['cv']['n_folds_total']} |",
            f"| Rows never evaluated (forced to train) | "
            f"{run_a['evaluation_coverage']['forced_to_train']['n_rows']} | {cov_b['n_rows']} |",
            f"| Selected model (same rule) | `{best_a}` | `{best_b}` |",
            f"| Selected model OOF AP: selection estimate (optimistic) | "
            f"{fmt_summary(sum_a['models'][best_a]['average_precision'])} | "
            f"{fmt_summary(sum_b['models'][best_b]['average_precision'])} |",
            f"| Selected model test AP [95% CI] | {fmt_ci(t_a['result'], 'average_precision')} | "
            f"{fmt_ci(t_b['result'], 'average_precision')} |",
            f"| Test rows / positives / prevalence | {t_a['n_rows']} / {t_a['n_positive']} / "
            f"{fmt(t_a['prevalence'])} | {t_b['n_rows']} / {t_b['n_positive']} / "
            f"{fmt(t_b['prevalence'])} |",
            f"| **OOF-minus-test AP gap (selected model)** | "
            f"{_gap(sum_a['models'][best_a]['average_precision']['mean'], t_a['ap'])} | "
            f"{_gap(sum_b['models'][best_b]['average_precision']['mean'], t_b['ap'])} |",
        ]
    )
    for base in run_b["baselines"]:
        ta, tb = _test_part(rec_a, base), _test_part(rec_b, base)
        assert ta is not None and tb is not None
        oa = sum_a["models"][base]["average_precision"]["mean"]
        ob = sum_b["models"][base]["average_precision"]["mean"]
        add(
            [
                f"| `{base}` OOF AP / test AP [95% CI] (gap) | {fmt(oa)} / "
                f"{fmt_ci(ta['result'], 'average_precision')} ({_gap(oa, ta['ap'])}) | "
                f"{fmt(ob)} / {fmt_ci(tb['result'], 'average_precision')} ({_gap(ob, tb['ap'])}) |"
            ]
        )
    add(
        [
            "",
            "OOF values are means over folds. The gap is OOF mean minus the single test value. "
            "A positive gap means the selection estimate was higher than the test result.",
            "",
            "### Duplicate-removed re-slice of run (a)'s test predictions",
            "",
            "This is a post-hoc re-slice of run (a)'s *stored* test predictions: no refit, no "
            "re-scoring, nothing selected. It excludes test rows whose features exactly "
            "duplicate an outer-train row "
            f"({sens_a['n_test_rows_duplicating_outer_train']} rows, of which "
            f"{sens_a['n_positive_test_rows_duplicating_outer_train']} positive).",
            "",
            "| Model | Subset | Rows | Positives | Prevalence | AP [95% CI] | ROC AUC [95% CI] |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for name, parts in sens_a["models"].items():
        for label, key in (
            ("all test rows", "all_rows"),
            ("excluding duplicates of train", "excluding_duplicates_of_train"),
        ):
            p = parts[key]
            add(
                [
                    f"| `{name}` | {label} | {p['n_rows']} | {p['n_positive']} | "
                    f"{fmt(p['prevalence'])} | {_ci_text(p, 'average_precision')} | "
                    f"{_ci_text(p, 'roc_auc')} |"
                ]
            )
    add(
        [
            "",
            "**AP depends on prevalence.** The two subsets have different prevalence, so their AP "
            "values are not directly comparable. Compare each model with `dummy_prior` *within "
            "the same subset* (dummy AP equals that subset's prevalence). This re-slice covers "
            "the test set only and does not show the effect of duplicates on run (a)'s CV "
            "estimates. In run (b) the same re-slice excludes "
            f"{sens_b['n_test_rows_duplicating_outer_train']} rows.",
            "",
            "## Data profile and split warnings (heuristic, not proof)",
            "",
        ]
    )
    for w in profile.get("warnings", []):
        col = f" on `{w['column']}`" if w["column"] else ""
        add([f"- `{w['code']}`{col}: {w['message']}"])
    for lbl, rec in (("(a)", rec_a), ("(b)", rec_b)):
        for w in rec.run.get("split_warnings", []):
            add([f"- {lbl} split check `{w['code']}`: {w['message']}"])
    env = rec_b.environment
    add(
        [
            "",
            "## Limitations",
            "",
            "- One dataset. Each run has one outer split, so the test numbers are single draws; "
            "the bootstrap CIs cover test-sample variation, not variation from re-splitting or "
            "re-training. Runs (a) and (b) use different test rows.",
            f"- Test sets are small in positives ({t_a['n_positive']} in (a), "
            f"{t_b['n_positive']} in (b)), so the CIs are wide.",
            f"- Run (b) results do not describe the {cov_b['n_rows']} forced-to-train rows.",
            "- Fixed small model configs with no hyperparameter search (MVP scope). Probabilities "
            "are not calibrated.",
            "- The features are anonymised numeric measurements, so the cluster could not be "
            "reviewed against domain knowledge.",
            "",
            "## Reproduce",
            "",
            "```bash",
            "python -m venv .venv",
            "source .venv/bin/activate        # Windows: .venv\\Scripts\\activate",
            "pip install -r requirements-lock.txt && pip install -e . --no-deps",
            "python scripts/run_case_study.py            # both runs + this document",
            "python scripts/verify_case_study_hashes.py  # regenerate large files, check SHA-256",
            "```",
            "",
            "A fresh `run_case_study.py` scores new test sets with the same seeds. The committed "
            "records were amended in T-R2 with `--amend-existing`, which scores nothing.",
            "",
            "## Run records",
            "",
            "- (a): [`case_study/a_stratified/`](case_study/a_stratified/) (report: "
            "[`report/report.md`](case_study/a_stratified/report/report.md))",
            "- (b): [`case_study/b_duplicate_groups/`](case_study/b_duplicate_groups/) (report: "
            "[`report/report.md`](case_study/b_duplicate_groups/report/report.md))",
            "- Amendments (T-R2) are listed in each `run.json` (`amendments`) and "
            "`final_evaluation.json` (`amendments`), and in `final_evaluation_log.jsonl`.",
            "- Files over 1 MB are not committed and are listed with SHA-256 in each "
            f"`OMITTED_FILES.json` (run b: {', '.join(f'`{k}`' for k in omitted_b) or 'none'}). "
            "`scripts/verify_case_study_hashes.py` regenerates them and checks the hashes.",
            f"- Environment: Python {env['python']}, scikit-learn "
            f"{env['packages']['scikit-learn']}, imbalanced-learn "
            f"{env['packages']['imbalanced-learn']}, numpy {env['packages']['numpy']}, pandas "
            f"{env['packages']['pandas']}.",
            "",
        ]
    )
    return "\n".join(L)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--workspace", type=Path, default=ROOT / "runs" / "case_study")
    parser.add_argument("--data-home", type=Path, default=ROOT / "data" / "raw" / "imblearn")
    parser.add_argument(
        "--amend-existing",
        action="store_true",
        help="amend the committed runs (coverage + bootstrap CIs) without scoring test sets",
    )
    args = parser.parse_args()

    try:
        npz, csv = download(args.data_home)
    except (URLError, OSError) as exc:
        print(f"ENVIRONMENT LIMITATION: dataset download failed: {exc}", file=sys.stderr)
        print("No results were produced. Synthetic data is NOT substituted.", file=sys.stderr)
        return 2
    provenance = {"npz_file": npz.name, "npz_sha256": sha256(npz), "csv_sha256": sha256(csv)}
    print(f"downloaded {npz} sha256={provenance['npz_sha256']}")

    ws = workflow.Workspace.at(args.workspace)
    records: dict[str, RunRecord] = {}
    for label, schema in RUNS.items():
        if args.amend_existing:
            records[label] = amend_protocol(ws, label)
        else:
            records[label] = run_protocol(ws, csv, label, schema)
    finished = {label: finish(ws, label, rec) for label, rec in records.items()}
    for label, record in records.items():
        (DOCS / "case_study" / label / "PROVENANCE.json").write_text(
            json.dumps(
                {**SOURCE, "dataset": DATASET, **provenance, "run_id": record.run_id},
                indent=2,
            )
            + "\n"
        )
    rec_b = records["b_duplicate_groups"]
    cluster_text, cluster = cluster_analysis(
        rec_b, finished["b_duplicate_groups"][2], ws.models_dir
    )
    print(cluster_text)
    doc = build_case_study(
        records["a_stratified"],
        rec_b,
        finished["a_stratified"][1],
        finished["b_duplicate_groups"][1],
        finished["b_duplicate_groups"][0],
        provenance,
        cluster_text,
        cluster,
    )
    (DOCS / "case_study.md").write_text(doc, encoding="utf-8", newline="\n")
    print(
        "wrote docs/case_study.md, docs/case_study/a_stratified, docs/case_study/b_duplicate_groups"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
