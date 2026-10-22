"""Reproduce the ImbalanceLab case study on the `mammography` benchmark dataset end to end.

    python scripts/run_case_study.py

Steps: download (imbalanced-learn benchmark collection, Zenodo DOI 10.5281/zenodo.61452) ->
CSV -> register (profile + outer holdout) -> repeated CV -> OOF threshold analysis ->
one-shot final test evaluation -> report -> export run records to docs/case_study/ ->
generate docs/case_study.md from those records.

The protocol below is fixed in code before any result is seen. If the download fails, the
script stops with exit code 2; it never substitutes synthetic data.
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
from imbalancelab.splitting.splits import HoldoutConfig
from imbalancelab.tracking.records import RunRecord

ROOT = Path(__file__).resolve().parents[1]
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
# ---- pre-specified protocol (do not tune after seeing results) ----
SCHEMA = DatasetSchema(target="target", positive_label=1, split_strategy="stratified")
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
EXPORT_SKIP_LARGER_THAN = 1_000_000  # bytes; larger files are listed with their SHA-256 only


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def download(data_home: Path) -> tuple[Path, Path]:
    """Fetch the dataset; return (extracted .npz path, CSV path)."""
    from imblearn.datasets import fetch_datasets

    bunch = fetch_datasets(
        data_home=str(data_home), filter_data=(DATASET,), download_if_missing=True, verbose=True
    )[DATASET]
    from imblearn.datasets._zenodo import MAP_NAME_ID, POST_FILENAME, PRE_FILENAME

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


def duplicate_sensitivity(record: RunRecord, data_path: Path) -> dict[str, Any]:
    """Post-hoc check on the *stored* test predictions: recompute test AP / ROC AUC after
    excluding test rows whose features exactly duplicate an outer-train row.

    Nothing is refit or re-scored and nothing is selected from this; it only re-slices the
    predictions written by the single final evaluation.
    """
    dataset = load_dataset(data_path, SCHEMA)
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
        y, sc = g["y_true"].to_numpy(), g["y_score"].to_numpy()
        models[str(model)] = {
            "all_rows": {
                "n": int(len(g)),
                "n_positive": int(y.sum()),
                "average_precision": average_precision(y, sc).value,
                "roc_auc": roc_auc(y, sc).value,
            },
            "excluding_duplicates_of_train": {
                "n": int(keep.sum()),
                "n_positive": int(y[keep].sum()),
                "average_precision": average_precision(y[keep], sc[keep]).value,
                "roc_auc": roc_auc(y[keep], sc[keep]).value,
            },
        }
    n_dup = int(sum(dup.values()))
    return {
        "description": "post-hoc re-slicing of stored final test predictions; no refit, "
        "no re-scoring, no selection",
        "n_test": int(test_idx.size),
        "n_test_rows_duplicating_outer_train": n_dup,
        "n_positive_test_rows_duplicating_outer_train": int(
            sum(dataset.y[i] for i, d in dup.items() if d)
        ),
        "models": models,
    }


def build_case_study(
    record: RunRecord,
    provenance: dict[str, Any],
    export_dir: Path,
    omitted: dict[str, Any],
    sensitivity: dict[str, Any],
) -> str:
    run, summary, profile = record.run, record.summary, record.profile or {}
    final, th = record.final_evaluation or {}, record.thresholds or {}
    cb = profile["class_balance"]
    rel = export_dir.relative_to(ROOT / "docs").as_posix()
    best = summary["best_candidate_by_mean_oof_ap"]
    lines = [
        "# Case study: `mammography` (imbalanced-learn benchmark)",
        "",
        "> Generated by `scripts/run_case_study.py` from the run record "
        f"`{run['run_id']}`. Every number below is read from files in "
        f"[`{rel}/`]({rel}/). Nothing was typed in by hand.",
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
        f"| SHA-256 of CSV used (run dataset hash) | `{run['dataset']['sha256']}` |",
        f"| Rows / features | {cb['n_rows']} / {profile['n_features']} |",
        f"| Positives / negatives | {cb['n_positive']} / {cb['n_negative']} "
        f"(rate {fmt(cb['positive_rate'])}, ratio {fmt(cb['imbalance_ratio'], 1)}:1) |",
        "",
        "## Protocol (fixed in code before running)",
        "",
        f"- Outer holdout: stratified, test_size {HOLDOUT.test_size}, seed {HOLDOUT.seed} "
        f"({run['holdout']['n_outer_train']} outer-train rows, {run['holdout']['n_test']} test "
        f"rows; test-index SHA-256 `{run['holdout']['test_sha256']}`).",
        f"- Inner CV on outer-train rows only: stratified {CONFIG.cv.n_splits}-fold × "
        f"{CONFIG.cv.n_repeats} repeats (seed {CONFIG.cv.seed}); fold-index SHA-256 "
        f"`{run['cv']['fold_indices_sha256']}`. All models share these folds.",
        "- Baselines: `dummy_prior`, `logreg_balanced`. Candidates: "
        + ", ".join(f"`{c}`" for c in run["candidates"])
        + ". Samplers sit inside the imblearn pipeline and run only during fit.",
        "- Primary metric: average precision (AP). The candidate is selected by mean OOF AP.",
        f"- Threshold: `{THRESHOLD_STRATEGY.kind}` with beta={THRESHOLD_STRATEGY.beta} "
        "(recall-weighted), selected per CV repeat on OOF predictions, median taken.",
        "- Final evaluation: the selected candidate and both baselines are refit on outer-train "
        "rows and the test rows are scored once.",
        "",
        "## Headline results",
        "",
        "Out-of-fold values are mean ± sample std over "
        f"{run['cv']['n_folds_total']} folds. Test values are single evaluations (no spread).",
        "",
        "| Model | Role | OOF AP | OOF ROC AUC | OOF Brier | Test AP | Test ROC AUC |",
        "|---|---|---|---|---|---|---|",
    ]
    results = final.get("results", {})
    for name in run["models"]:
        s = summary["models"][name]
        role = "baseline" if name in run["baselines"] else "candidate"
        if name == best:
            role += " (selected)"
        t = results.get(name, {}).get("metrics", {})
        test_ap = fmt(t["average_precision"]["value"]) if t else "not scored"
        test_auc = fmt(t["roc_auc"]["value"]) if t else "not scored"
        lines.append(
            f"| `{name}` | {role} | {fmt_summary(s['average_precision'])} | "
            f"{fmt_summary(s['roc_auc'])} | {fmt_summary(s['brier'])} | {test_ap} | {test_auc} |"
        )
    dups = profile.get("duplicates", {})
    sv = sensitivity
    sel = sv["models"].get(best, {})
    lines += [
        "",
        "### Key caveat: duplicated rows",
        "",
        f"The profile found **{dups.get('n_exact_duplicate_rows', 'n/a')} rows that exactly "
        f"duplicate an earlier row** (out of {cb['n_rows']}). After the split, "
        f"**{sv['n_test_rows_duplicating_outer_train']} of {sv['n_test']} test rows** "
        f"({sv['n_positive_test_rows_duplicating_outer_train']} of them positive) have feature "
        "values identical to an outer-train row, and every CV fold has the same issue (see the "
        "split warnings below). The tool reports this as a warning, not proof of leakage: "
        "repeated measurements may be genuine in this data. But a model can score such rows "
        "partly by memorisation, which could make scores optimistic. The check below tests "
        "whether that happened here.",
    ]
    if sel:
        a, b = sel["all_rows"], sel["excluding_duplicates_of_train"]
        lines += [
            "",
            "Sensitivity check (post hoc, re-slicing the *stored* test predictions only, with no "
            "refit and no re-scoring; nothing was selected from it):",
            "",
            "| Model | Test rows | Positives | Test AP | Test ROC AUC |",
            "|---|---|---|---|---|",
        ]
        for name, m in sv["models"].items():
            parts = (
                ("all", m["all_rows"]),
                ("excluding duplicates of train", m["excluding_duplicates_of_train"]),
            )
            for label, part in parts:
                lines.append(
                    f"| `{name}` ({label}) | {part['n']} | {part['n_positive']} | "
                    f"{fmt(part['average_precision'])} | {fmt(part['roc_auc'])} |"
                )
        ap_all, ap_unique = a["average_precision"], b["average_precision"]
        direction = (
            "is lower"
            if ap_unique is not None and ap_all is not None and ap_unique < ap_all
            else "is not lower"
        )
        rate_all = a["n_positive"] / a["n"]
        rate_unique = b["n_positive"] / b["n"] if b["n"] else float("nan")
        lines += [
            "",
            f"For the selected `{best}`, test AP is {fmt(ap_all)} on all test rows and "
            f"{fmt(ap_unique)} on the {b['n']} test rows that do not duplicate outer-train rows, "
            f"so AP {direction} once the duplicated rows are removed. The subsets differ in "
            f"positive rate ({fmt(rate_all)} vs {fmt(rate_unique)}), and AP depends on prevalence. "
            "Compare each model with `dummy_prior` *within the same subset*, not across "
            "subsets. This check covers the test set only. It does not establish whether the "
            "duplicates inflated the CV estimates. Values come from "
            f"[`{rel}/duplicate_sensitivity.json`]({rel}/duplicate_sensitivity.json).",
        ]
    lines += ["", "## Comparisons against baselines (paired over identical folds)", ""]
    lines += [
        f"- {comparison_verdict(c)}"
        for c in summary["comparisons"]
        if c["metric"] == "average_precision"
    ]
    lines += [
        "",
        "These are descriptive. CV folds are correlated, so no significance test is reported.",
        "",
        "## Threshold (selected on out-of-fold predictions)",
        "",
    ]
    a = th.get("analyses", {}).get(best)
    if a:
        sp = a["per_repeat_spread"]
        lines += [
            f"- Model `{best}`: chosen threshold **{fmt(a['chosen_threshold'])}** (median of "
            f"{sp['threshold']['n']} per-repeat selections; mean {fmt(sp['threshold']['mean'])} "
            f"± {fmt(sp['threshold']['std'])}, range [{fmt(sp['threshold']['min'])}, "
            f"{fmt(sp['threshold']['max'])}]).",
            f"- At each repeat's own threshold (optimistic, same OOF data): precision "
            f"{fmt(sp['precision']['mean'])}, recall {fmt(sp['recall']['mean'])}, "
            f"F2 {fmt(sp['fbeta']['mean'])} (means over repeats).",
        ]
    lines += ["", "## Final test evaluation (scored once)", ""]
    if final:
        lines += [
            f"Evaluated at {final['evaluated_at']} on {final['n_test']} test rows "
            f"({final['n_test_positive']} positive); forced: {final['forced']}.",
            "",
            "| Model | Threshold | AP | ROC AUC | Precision | Recall | F2 | MCC | TP/FP/FN/TN |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for name, r in results.items():
            m = r["metrics"]
            lines.append(
                f"| `{name}` | {fmt(r['threshold'])} | {fmt(m['average_precision']['value'])} | "
                f"{fmt(m['roc_auc']['value'])} | {fmt(m['precision']['value'])} | "
                f"{fmt(m['recall']['value'])} | {fmt(m['fbeta']['value'])} | "
                f"{fmt(m['mcc']['value'])} | "
                + "{tp}/{fp}/{fn}/{tn}".format(**r["confusion"])
                + " |"
            )
        lines += [""] + [
            f"- {final_test_verdict(c)}"
            for c in final["comparisons"]
            if c["metric"] == "average_precision"
        ]
        if final.get("persisted_model_id"):
            lines.append(
                f"- Persisted model (refit on outer-train rows only): "
                f"`{final['persisted_model_id']}` (artifact not committed: `*.joblib` is "
                "gitignored)."
            )
    lines += ["", "## Data profile warnings (heuristic, not proof)", ""]
    warnings = profile.get("warnings", [])
    lines += [
        f"- `{w['code']}`" + (f" on `{w['column']}`" if w["column"] else "") + f": {w['message']}"
        for w in warnings
    ] or ["- None fired."]
    split_w = run.get("split_warnings", [])
    lines += [f"- Split check `{w['code']}`: {w['message']}" for w in split_w]
    lines += [
        "",
        "## Limitations",
        "",
        "- One dataset and one outer split. The test numbers are a single draw with no spread.",
        "- Exact duplicate rows cross the train/test and CV boundaries (see the key caveat). "
        "Duplicate-aware (grouped) splitting was not used in this pre-specified protocol.",
        f"- The test set has {final.get('n_test_positive', 'n/a')} positives, so test metrics "
        "are noisy.",
        "- Fixed small model configs with no hyperparameter search (by design in the MVP).",
        "- The features are anonymised numeric measurements, so no domain review of leakage "
        "was possible beyond the automated heuristics.",
        "- Probabilities are not calibrated.",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python -m venv .venv && source .venv/bin/activate   # Windows: .venv\\Scripts\\activate",
        "pip install -r requirements-lock.txt && pip install -e . --no-deps",
        "python scripts/run_case_study.py",
        "```",
        "",
        "Run IDs and timestamps differ between executions. Metrics should match up to "
        "library-version differences, because seeds, folds (SHA-256 above) and the test indices "
        "are fixed.",
        "",
        "## Run record",
        "",
        f"- Exported copy: [`{rel}/`]({rel}/) (full audit report: "
        f"[`{rel}/report/report.md`]({rel}/report/report.md)).",
        "- Files omitted from the export because of size, listed with SHA-256 in "
        f"`OMITTED_FILES.json`: {', '.join(f'`{k}`' for k in omitted) or 'none'}.",
        f"- Environment: Python {record.environment['python']}, scikit-learn "
        f"{record.environment['packages']['scikit-learn']}, imbalanced-learn "
        f"{record.environment['packages']['imbalanced-learn']}, numpy "
        f"{record.environment['packages']['numpy']}, pandas "
        f"{record.environment['packages']['pandas']}.",
        "",
    ]
    return "\n".join(lines)


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

    ws = workflow.Workspace.at(args.workspace)
    reg = workflow.register_dataset(ws, csv, ".csv", SCHEMA, HOLDOUT, source_name=csv.name)
    print(f"registered {reg.dataset_id}: {reg.n_rows} rows, sha256={reg.sha256}")
    brief = workflow.start_run(ws, reg.dataset_id, CONFIG)
    run_id = brief["run_id"]
    best = brief["best_candidate_by_mean_oof_ap"]
    print(f"run {run_id} {brief['status']}; best candidate by OOF AP: {best}")
    workflow.analyse_thresholds(ws, run_id, best, THRESHOLD_STRATEGY)
    final = workflow.finalize_run(ws, run_id, model=best)
    print(f"final evaluation done; persisted model {final['model_id']}")
    workflow.report_path(ws, run_id, "markdown")

    run_dir = ws.run_dir(run_id)
    export_dir = ROOT / "docs" / "case_study" / run_id
    for old in (ROOT / "docs" / "case_study").glob("run-*"):
        if old != export_dir:
            shutil.rmtree(old)
    omitted = export_run(run_dir, export_dir)
    (export_dir / "PROVENANCE.json").write_text(
        json.dumps(
            {**SOURCE, "dataset": DATASET, **provenance, "dataset_id": reg.dataset_id}, indent=2
        )
        + "\n"
    )
    record = RunRecord(run_dir)
    data_path = ws.dataset_dir(reg.dataset_id) / "data.csv"
    sensitivity = duplicate_sensitivity(record, data_path)
    sensitivity_json = json.dumps(sensitivity, indent=2) + "\n"
    (export_dir / "duplicate_sensitivity.json").write_text(sensitivity_json)
    doc = build_case_study(record, provenance, export_dir, omitted, sensitivity)
    (ROOT / "docs" / "case_study.md").write_text(doc, encoding="utf-8", newline="\n")
    print(f"wrote docs/case_study.md and {export_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
