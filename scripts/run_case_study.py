"""Reproduce the ImbalanceLab case study on the `mammography` benchmark dataset end to end.

    python scripts/run_case_study.py

Two runs share everything (candidates, seeds, CV, selection rule, threshold strategy) except
the split:

  (a) ``a_stratified``       - stratified holdout + stratified CV (the original M10 protocol)
  (b) ``b_duplicate_groups`` - ``duplicate_groups=True``: identical feature rows form one group,
                               and holdout/CV use StratifiedGroupKFold, so no duplicate cluster
                               crosses a split boundary.

For each run: register (profile + outer holdout) -> repeated CV -> OOF threshold analysis for the
best candidate by mean OOF AP -> one-shot final test evaluation -> report -> export the run record
to docs/case_study/<label>/ -> generate docs/case_study.md from those records.

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
from imbalancelab.data.loader import load_dataset
from imbalancelab.data.schema import DatasetSchema
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.metrics import average_precision, roc_auc
from imbalancelab.evaluation.thresholds import ThresholdStrategy
from imbalancelab.profiling.profile import feature_row_hashes
from imbalancelab.reporting.report import comparison_verdict, final_test_verdict, fmt, fmt_summary
from imbalancelab.splitting.groups import resolve_groups
from imbalancelab.splitting.splits import HoldoutConfig, pin_oversized_groups
from imbalancelab.tracking.records import RunRecord

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATASET = "mammography"
SOURCE = {
    "collection": "imbalanced-learn benchmark collection (imblearn.datasets.fetch_datasets)",
    "zenodo_record": "https://zenodo.org/records/61452",
    "doi": "10.5281/zenodo.61452",
    "creators": "Lemaitre, Nogueira, Aridas, Oliveira (2016)",
    "license": "ODC-ODbL (Open Database License), as listed on the Zenodo record",
    "original_repository": "UCI (per the imbalanced-learn dataset table; benchmark proposed by "
    "Ding, Z., 'Diversified Ensemble Classifiers for Highly Imbalanced Data Learning and "
    "their Application in Bioinformatics', 2011)",
}
# ---- protocol: identical for both runs except duplicate_groups ----
# These constants are unchanged since the first execution in M10 (see docs/case_study.md,
# "Was the protocol fixed before results were seen?").
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
    return omitted


def _subset_metrics(y: np.ndarray, s: np.ndarray) -> dict[str, Any]:
    return {
        "n_rows": int(y.size),
        "n_positive": int(y.sum()),
        "prevalence": float(y.mean()) if y.size else None,
        "average_precision": average_precision(y, s).value,
        "roc_auc": roc_auc(y, s).value,
    }


def _pinned_hashes(dataset: Any, hashes: np.ndarray, record: RunRecord) -> set[int]:
    """Feature-row hashes of the groups the holdout pinned to training (duplicate groups only:
    a pinned group is one duplicate cluster, i.e. one feature-row hash)."""
    h = record.run["holdout"]
    groups, _, _ = resolve_groups(dataset)
    if groups is None or not h.get("n_pinned_rows"):
        return set()
    cfg = HoldoutConfig.model_validate(h["config"])
    mask = pin_oversized_groups(groups, cfg.test_size * dataset.n_rows, cfg.max_eval_group_fraction)
    return set(hashes[mask].tolist())


def duplicate_sensitivity(record: RunRecord, data_path: Path) -> dict[str, Any]:
    """Post-hoc re-slice of the *stored* test predictions: metrics on all test rows and on test
    rows whose features do not exactly duplicate an outer-train row. No refit, no re-scoring,
    no selection."""
    schema = DatasetSchema.model_validate(record.run["dataset"]["schema"])
    dataset = load_dataset(data_path, schema)
    if dataset.sha256 != record.run["dataset"]["sha256"]:
        raise RuntimeError("dataset file does not match the run's dataset SHA-256")
    hashes = feature_row_hashes(dataset.frame, dataset.feature_columns)
    holdout = record.holdout
    train_hashes = set(hashes[holdout["train_idx"]].tolist())
    test_idx = np.asarray(holdout["test_idx"])
    dup = {int(i): hashes[i] in train_hashes for i in test_idx}
    preds = record.final_predictions()
    assert preds is not None
    models: dict[str, Any] = {}
    for model, g in preds.groupby("model", sort=False):
        keep = ~g["row_index"].map(dup).to_numpy(dtype=bool)
        y, sc = g["y_true"].to_numpy(dtype=int), g["y_score"].to_numpy(dtype=float)
        models[str(model)] = {
            "all_rows": _subset_metrics(y, sc),
            "excluding_duplicates_of_train": _subset_metrics(y[keep], sc[keep]),
        }
    pinned_rows = [
        i
        for i in holdout["train_idx"]
        if record.run["holdout"].get("n_pinned_rows")
        and hashes[i] in _pinned_hashes(dataset, hashes, record)
    ]
    return {
        "description": "post-hoc re-slicing of stored final test predictions; no refit, "
        "no re-scoring, no selection",
        "n_pinned_rows": len(pinned_rows),
        "n_positive_pinned_rows": int(dataset.y[pinned_rows].sum()) if pinned_rows else 0,
        "n_test": int(test_idx.size),
        "n_test_rows_duplicating_outer_train": int(sum(dup.values())),
        "n_positive_test_rows_duplicating_outer_train": int(
            sum(int(dataset.y[i]) for i, d in dup.items() if d)
        ),
        "models": models,
    }


def run_protocol(
    ws: workflow.Workspace, csv: Path, label: str, schema: DatasetSchema
) -> tuple[RunRecord, dict[str, Any], dict[str, Any]]:
    reg = workflow.register_dataset(ws, csv, ".csv", schema, HOLDOUT, source_name=csv.name)
    print(f"[{label}] registered {reg.dataset_id}: {reg.n_rows} rows, sha256={reg.sha256}")
    brief = workflow.start_run(ws, reg.dataset_id, CONFIG)
    run_id, best = brief["run_id"], brief["best_candidate_by_mean_oof_ap"]
    print(f"[{label}] run {run_id} {brief['status']}; best candidate by OOF AP: {best}")
    workflow.analyse_thresholds(ws, run_id, best, THRESHOLD_STRATEGY)
    final = workflow.finalize_run(ws, run_id, model=best)
    print(f"[{label}] final evaluation done; persisted model {final['model_id']}")
    workflow.report_path(ws, run_id, "markdown")
    run_dir = ws.run_dir(run_id)
    export_dir = DOCS / "case_study" / label
    omitted = export_run(run_dir, export_dir)
    record = RunRecord(run_dir)
    sensitivity = duplicate_sensitivity(record, ws.dataset_dir(reg.dataset_id) / "data.csv")
    (export_dir / "duplicate_sensitivity.json").write_text(json.dumps(sensitivity, indent=2) + "\n")
    return record, omitted, sensitivity


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
        "roc_auc": r["metrics"]["roc_auc"]["value"],
        "n_rows": int(y.size),
        "n_positive": int(y.sum()),
        "prevalence": float(y.mean()),
        "result": r,
    }


def _crossing(record: RunRecord) -> dict[str, Any]:
    for w in record.run.get("split_warnings", []):
        if w["code"] == "cross_boundary_duplicates":
            return dict(w["evidence"])
    return {
        "test_rows_duplicating_train": 0,
        "folds_affected": 0,
        "max_val_rows_duplicating_train": 0,
    }


def _gap(oof: float | None, test: float | None) -> str:
    return "undefined" if oof is None or test is None else f"{oof - test:+.4f}"


def build_case_study(
    runs: dict[str, tuple[RunRecord, dict[str, Any], dict[str, Any]]],
    provenance: dict[str, Any],
) -> str:
    rec_a, _, sens_a = runs["a_stratified"]
    rec_b, omitted_b, sens_b = runs["b_duplicate_groups"]
    run_a, run_b = rec_a.run, rec_b.run
    sum_a, sum_b = rec_a.summary, rec_b.summary
    best_a, best_b = sum_a["best_candidate_by_mean_oof_ap"], sum_b["best_candidate_by_mean_oof_ap"]
    t_b = _test_part(rec_b, best_b)
    t_a = _test_part(rec_a, best_a)
    assert t_a is not None and t_b is not None
    profile = rec_b.profile or {}
    cb = profile["class_balance"]
    info_b = run_b["holdout"]["group_info"]
    final_b = rec_b.final_evaluation or {}
    th_b = (rec_b.thresholds or {})["analyses"][best_b]
    sp = th_b["per_repeat_spread"]

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
            "below is read from files in those folders. Nothing was typed in by hand.",
            "",
            "## Headline (run b: duplicate-aware split)",
            "",
            f"The selected model **`{best_b}`** scored **test AP {fmt(t_b['ap'])}** on a single "
            f"evaluation of {t_b['n_rows']} test rows with {t_b['n_positive']} positives "
            f"(prevalence {fmt(t_b['prevalence'])}). On the same test rows, the baselines scored:",
            "",
            "| Model | Test AP (scored once) | Test rows | Positives | Prevalence |",
            "|---|---|---|---|---|",
        ]
    )
    for name in final_b["results"]:
        t = _test_part(rec_b, name)
        assert t is not None
        add(
            [
                f"| `{name}` | {fmt(t['ap'])} | {t['n_rows']} | {t['n_positive']} | "
                f"{fmt(t['prevalence'])} |"
            ]
        )
    add(
        [
            "",
            "Run (b) is the headline because in run (a) exact-duplicate rows cross the train/test "
            "and CV boundaries (see the duplicate-leakage finding below). In run (b) no duplicate "
            "cluster crosses any boundary: the cross-boundary duplicate check reports "
            f"{_crossing(rec_b)['test_rows_duplicating_train']} test rows and "
            f"{_crossing(rec_b)['folds_affected']} affected folds.",
            "",
            f"**Evaluation population (run b):** {run_b['holdout']['n_pinned_groups']} duplicate "
            f"cluster(s) of {sens_b['n_pinned_rows']} identical rows "
            f"({sens_b['n_positive_pinned_rows']} positive) are too large to sit in a test or "
            "validation set without dominating it. They are pinned to the training side of the "
            "holdout and of every CV fold, so **no test or validation metric covers those rows**. "
            "The test set is drawn from the remaining rows.",
            "",
            "## Data source",
            "",
            "| Field | Value |",
            "|---|---|",
            f"| Dataset | `{DATASET}` |",
            f"| Collection | {SOURCE['collection']} |",
            f"| Zenodo record / DOI | {SOURCE['zenodo_record']} / `{SOURCE['doi']}` |",
            f"| Creators | {SOURCE['creators']} |",
            f"| Licence | {SOURCE['license']} |",
            f"| Original repository | {SOURCE['original_repository']} |",
            f"| SHA-256 of extracted `{provenance['npz_file']}` | `{provenance['npz_sha256']}` |",
            f"| SHA-256 of CSV used (both runs) | `{run_b['dataset']['sha256']}` |",
            f"| Rows / features | {cb['n_rows']} / {profile['n_features']} |",
            f"| Positives / negatives | {cb['n_positive']} / {cb['n_negative']} "
            f"(prevalence {fmt(cb['positive_rate'])}, ratio {fmt(cb['imbalance_ratio'], 1)}:1) |",
            "| Exact duplicate rows (profile) | "
            f"{profile['duplicates']['n_exact_duplicate_rows']} |",
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
            "outer-train rows, and the test rows are scored once.",
            "- **(a) `a_stratified`:** a stratified holdout and stratified CV (the original M10 "
            "protocol).",
            "- **(b) `b_duplicate_groups`:** `duplicate_groups=True`. Rows with identical feature "
            "values form one group, and both the holdout and CV use `StratifiedGroupKFold`. "
            f"There are {info_b['n_groups']} split groups, of which "
            f"{info_b['n_duplicate_clusters']} "
            f"are duplicate clusters covering {info_b['n_rows_in_duplicate_clusters']} rows; "
            f"{info_b['n_conflicting_label_clusters']} cluster(s) have conflicting labels "
            f"({info_b['n_rows_in_conflicting_clusters']} rows, kept). Groups larger than "
            f"{HOLDOUT.max_eval_group_fraction:.0%} of the target test or validation size are "
            f"pinned to training: {run_b['holdout']['n_pinned_groups']} group(s) and "
            f"{run_b['holdout']['n_pinned_rows']} rows for the holdout, "
            f"{run_b['cv']['n_pinned_groups']} group(s) and {run_b['cv']['n_pinned_rows']} rows "
            "for CV.",
            "",
            "### Was the protocol fixed before results were seen?",
            "",
            "- The candidate list, seeds, CV settings, selection rule and threshold strategy were "
            "written into `scripts/run_case_study.py` before its first execution in M10. They have "
            "not been changed since; this rewrite keeps the same constants.",
            "- **Git history cannot prove this ordering.** The script's first commit (`91c6f54`, "
            "M10) came after those executions. The evidence is the M10 command log in "
            "`REVIEW_PACKET.md`: the first execution failed before producing results (a file-path "
            "bug), the second was stopped before its output was read, and later executions changed "
            "only report wording.",
            "- **Run (b) was not pre-specified.** It was requested by the supervisor after the "
            "run (a) results were seen. Its candidate set, seeds and selection rule are those of "
            "run (a), unchanged.",
            "",
            "## Results, run (b)",
            "",
            "OOF AP is a **selection estimate (optimistic: used for model selection)**. Test AP "
            "is a single scoring of the held-out rows.",
            "",
            "| Model | Role | OOF AP: selection estimate (optimistic) | OOF ROC AUC | "
            "Test AP (scored once) | Test rows / positives / prevalence |",
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
            f"{fmt(t['ap'])} | {t['n_rows']} / {t['n_positive']} / {fmt(t['prevalence'])}"
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
            f"- {final_test_verdict(c)}"
            for c in final_b["comparisons"]
            if c["metric"] == "average_precision"
        ]
    )

    r = t_b["result"]
    m = r["metrics"]
    c = r["confusion"]
    add(
        [
            "",
            "## Threshold, run (b)",
            "",
            f"- **Model:** `{best_b}`. **Strategy:** `{th_b['strategy']['kind']}` with beta="
            f"{th_b['strategy']['beta']}, selected on OOF predictions for each of "
            f"{sp['threshold']['n']} CV repeats. **Rule:** {th_b['selection_rule']}.",
            f"- **Chosen threshold:** {fmt(th_b['chosen_threshold'])}. Per-repeat thresholds: "
            f"mean {fmt(sp['threshold']['mean'])} ± {fmt(sp['threshold']['std'])} (sample std), "
            f"range [{fmt(sp['threshold']['min'])}, {fmt(sp['threshold']['max'])}]. Individual "
            "values: "
            + ", ".join(f"repeat {p['repeat']}: {fmt(p['threshold'])}" for p in th_b["per_repeat"])
            + ".",
            "- **Test metrics at the chosen threshold** (scored once):",
            "",
            "| Precision | Recall | F-beta (beta=2) | MCC | TP | FP | FN | TN |",
            "|---|---|---|---|---|---|---|---|",
            f"| {fmt(m['precision']['value'])} | {fmt(m['recall']['value'])} | "
            f"{fmt(m['fbeta']['value'])} | {fmt(m['mcc']['value'])} | {c['tp']} | {c['fp']} | "
            f"{c['fn']} | {c['tn']} |",
            "",
            "## Duplicate-leakage finding: run (a) vs run (b)",
            "",
            "The two runs use **different test sets**. Each split strategy draws its own holdout, "
            "so differences between the columns combine the effect of duplicates crossing "
            "boundaries with the effect of a different test sample.",
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
            f"| Selected model (same rule) | `{best_a}` | `{best_b}` |",
            f"| Selected model OOF AP: selection estimate (optimistic) | "
            f"{fmt_summary(sum_a['models'][best_a]['average_precision'])} | "
            f"{fmt_summary(sum_b['models'][best_b]['average_precision'])} |",
            f"| Selected model test AP (scored once) | {fmt(t_a['ap'])} | {fmt(t_b['ap'])} |",
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
        add(
            [
                f"| `{base}` OOF / test AP (gap) | "
                f"{fmt(sum_a['models'][base]['average_precision']['mean'])} / {fmt(ta['ap'])} "
                f"({_gap(sum_a['models'][base]['average_precision']['mean'], ta['ap'])}) | "
                f"{fmt(sum_b['models'][base]['average_precision']['mean'])} / {fmt(tb['ap'])} "
                f"({_gap(sum_b['models'][base]['average_precision']['mean'], tb['ap'])}) |"
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
            "| Model | Subset | Rows | Positives | Prevalence | AP | ROC AUC |",
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
                    f"{fmt(p['prevalence'])} | {fmt(p['average_precision'])} | "
                    f"{fmt(p['roc_auc'])} |"
                ]
            )
    add(
        [
            "",
            "**AP depends on prevalence.** The two subsets have different prevalence, so their AP "
            "values are not directly comparable. Compare each model with `dummy_prior` *within "
            "the same subset* (dummy AP equals that subset's prevalence). This re-slice covers "
            "the test set only and does not show the effect of duplicates on run (a)'s CV "
            "estimates. Run (b) addresses that by construction. In run (b) the re-slice excludes "
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
            "- One dataset. Each run has one outer split, so the test numbers are single draws "
            "with no spread, and runs (a) and (b) use different test rows.",
            f"- Test sets are small in positives ({t_a['n_positive']} in (a), "
            f"{t_b['n_positive']} in (b)).",
            "- Fixed small model configs with no hyperparameter search (MVP scope). Probabilities "
            "are not calibrated.",
            "- The features are anonymised numeric measurements, so the duplicates could not be "
            "reviewed against domain knowledge. Whether they are repeated measurements or "
            "artefacts is unknown.",
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
            "## Run records",
            "",
            "- (a): [`case_study/a_stratified/`](case_study/a_stratified/) (report: "
            "[`report/report.md`](case_study/a_stratified/report/report.md))",
            "- (b): [`case_study/b_duplicate_groups/`](case_study/b_duplicate_groups/) (report: "
            "[`report/report.md`](case_study/b_duplicate_groups/report/report.md))",
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
    args = parser.parse_args()

    try:
        npz, csv = download(args.data_home)
    except (URLError, OSError) as exc:
        print(f"ENVIRONMENT LIMITATION: dataset download failed: {exc}", file=sys.stderr)
        print("No results were produced. Synthetic data is NOT substituted.", file=sys.stderr)
        return 2
    provenance = {"npz_file": npz.name, "npz_sha256": sha256(npz), "csv_sha256": sha256(csv)}
    print(f"downloaded {npz} sha256={provenance['npz_sha256']}")

    for old in (DOCS / "case_study").glob("run-*"):  # pre-T-R1 export layout
        shutil.rmtree(old)
    ws = workflow.Workspace.at(args.workspace)
    runs = {label: run_protocol(ws, csv, label, schema) for label, schema in RUNS.items()}
    for label, (record, _, _) in runs.items():
        (DOCS / "case_study" / label / "PROVENANCE.json").write_text(
            json.dumps(
                {**SOURCE, "dataset": DATASET, **provenance, "run_id": record.run_id},
                indent=2,
            )
            + "\n"
        )
    doc = build_case_study(runs, provenance)
    (DOCS / "case_study.md").write_text(doc, encoding="utf-8", newline="\n")
    print(
        "wrote docs/case_study.md, docs/case_study/a_stratified, docs/case_study/b_duplicate_groups"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
