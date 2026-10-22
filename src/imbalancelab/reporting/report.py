"""Evidence-based audit report generated only from a run directory's records."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from imbalancelab.reporting.figures import first_repeat, plot_curves
from imbalancelab.reporting.render import (
    BulletList,
    Code,
    Document,
    Heading,
    Image,
    Paragraph,
    Table,
    to_html,
    to_markdown,
)
from imbalancelab.tracking.records import RunRecord

REPORT_DIR = "report"
CV_TABLE_METRICS = (
    ("average_precision", "AP (primary)"),
    ("roc_auc", "ROC AUC"),
    ("brier", "Brier ↓"),
    ("precision", "Precision@ref"),
    ("recall", "Recall@ref"),
    ("f1", "F1@ref"),
)
TEST_TABLE_METRICS = (
    ("average_precision", "AP"),
    ("roc_auc", "ROC AUC"),
    ("brier", "Brier ↓"),
    ("precision", "Precision"),
    ("recall", "Recall"),
    ("fbeta", "F-beta"),
    ("mcc", "MCC"),
)
FEW_TEST_POSITIVES = 30


@dataclass(frozen=True)
class ReportPaths:
    markdown: Path
    html: Path
    figures: list[Path]


def fmt(value: Any, digits: int = 4) -> str:
    if value is None:
        return "undefined"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def fmt_signed(value: float | None, digits: int = 4) -> str:
    return "undefined" if value is None else f"{value:+.{digits}f}"


def fmt_summary(s: dict[str, Any]) -> str:
    if s["mean"] is None:
        return f"undefined (0/{s['n_undefined']} folds defined)"
    spread = f" ± {s['std']:.4f}" if s["std"] is not None else ""
    undefined = f", {s['n_undefined']} undefined" if s["n_undefined"] else ""
    return f"{s['mean']:.4f}{spread} (n={s['n']}{undefined})"


def comparison_verdict(c: dict[str, Any]) -> str:
    """Plain-language statement of whether ``candidate`` beats ``baseline`` across CV folds."""
    cand, base = f"**{c['candidate']}**", f"**{c['baseline']}**"
    metric = "average precision" if c["metric"] == "average_precision" else c["metric"]
    if not c["n_pairs"]:
        return f"{cand} vs {base}: cannot be compared on {metric} (no folds with defined values)."
    beats = c["mean_diff"] > 0 and c["win_fraction"] > 0.5
    word = "beats" if beats else "does NOT beat"
    return (
        f"{cand} {word} {base} on out-of-fold {metric}: mean paired difference "
        f"{fmt_signed(c['mean_diff'])}, better in {c['wins']} of {c['n_pairs']} folds "
        f"(win fraction {c['win_fraction']:.2f})."
    )


def fmt_ci(result: dict[str, Any], metric: str) -> str:
    """Point estimate with its bootstrap 95% CI, e.g. ``0.8228 [0.7612, 0.8790]``."""
    value = fmt(result["metrics"][metric]["value"])
    ci = (result.get("ci") or {}).get(metric)
    if not ci:
        return value
    if ci["lower"] is None:
        return f"{value} [CI undefined]"
    undefined = f", {ci['n_undefined']} undefined" if ci["n_undefined"] else ""
    return f"{value} [{ci['lower']:.4f}, {ci['upper']:.4f}{undefined}]"


def final_test_verdict(c: dict[str, Any], results: dict[str, Any] | None = None) -> str:
    cand, base = f"**{c['candidate']}**", f"**{c['baseline']}**"
    if c["diff"] is None:
        return f"{cand} vs {base}: test {c['metric']} undefined for at least one model."
    word = "beats" if c["diff"] > 0 else "does NOT beat"
    if results and c["candidate"] in results and c["baseline"] in results:
        values = (
            f"{fmt_ci(results[c['candidate']], c['metric'])} vs "
            f"{fmt_ci(results[c['baseline']], c['metric'])} (95% CIs)"
        )
    else:
        values = f"{fmt(c['candidate_value'])} vs {fmt(c['baseline_value'])}"
    return (
        f"{cand} {word} {base} on the test set ({c['metric']}: {values}, point difference "
        f"{fmt_signed(c['diff'])}; single evaluation)."
    )


def coverage_blocks(run: dict[str, Any]) -> list[Any]:
    """The 'Evaluation coverage' section body (also used by docs)."""
    cov = run.get("evaluation_coverage")
    if cov is None:
        return [Paragraph("Evaluation coverage was not recorded for this run.")]
    f = cov["forced_to_train"]
    cut = cov["cutoff"]
    blocks: list[Any] = []
    if cov["warning"]:
        blocks.append(
            Paragraph(
                f"**WARNING:** {f['n_rows']} rows ({f['pct_of_rows']:.1f}% of the dataset, "
                f"{f['n_positive']} positives) were never in any test or validation set. "
                "**The reported results do not describe these rows.**"
            )
        )
    cutoff = (
        f"groups larger than {cut['holdout_max_eval_group_fraction']:.0%} of the target test "
        f"size ({cut['holdout_row_limit']:.0f} rows) or "
        f"{cut['cv_max_eval_group_fraction']:.0%} of the target validation-fold size "
        f"({cut['cv_row_limit']:.0f} rows) are forced to train"
        if cut["applies"]
        else "not applicable (splitting is not group-aware)"
    )
    sizes = ", ".join(
        f"{n} rows ({p} positive)"
        for n, p in zip(f["group_sizes"], f["group_positive_counts"], strict=True)
    )
    blocks.append(
        Table(
            ["Field", "Value"],
            [
                ["Rows / positives in dataset", f"{cov['n_rows']} / {cov['n_positive']}"],
                ["Rows evaluated (test or any validation fold)", fmt(cov["n_rows_evaluated"])],
                [
                    "Forced to train, never evaluated: rows / positives",
                    f"{f['n_rows']} / {f['n_positive']}",
                ],
                [
                    "Forced to train: % of rows / % of positives",
                    f"{f['pct_of_rows']:.2f}% / {f['pct_of_positives']:.2f}%",
                ],
                ["Large-group cut-off", cutoff],
                ["Forced-to-train groups", f"{f['n_groups']}" + (f": {sizes}" if sizes else "")],
                ["Temporal gap rows", fmt(cov["gap_rows"])],
                [
                    "Other never-evaluated rows",
                    f"{cov['other_never_evaluated']['n_rows']} "
                    f"({cov['other_never_evaluated']['reason']})",
                ],
                ["Warning threshold", f"{cov['warning_threshold_pct']:.0f}% of rows"],
            ],
        )
    )
    return blocks


def _group_summary(h: dict[str, Any]) -> str:
    info = h.get("group_info")
    if not h.get("duplicate_groups"):
        if info:
            return f"off (declared groups: {info['n_groups']})"
        return "off"
    if info is None:
        return "on (no group info recorded)"
    return (
        f"on: {info['n_groups']} split groups ({info['source']}); "
        f"{info['n_duplicate_clusters']} duplicate clusters covering "
        f"{info['n_rows_in_duplicate_clusters']} rows; "
        f"{info['n_conflicting_label_clusters']} with conflicting labels"
    )


def build_document(record: RunRecord, figure_dir: Path) -> tuple[Document, list[Path]]:
    run = record.run
    summary = record.summary
    profile = record.profile or {}
    thresholds = record.thresholds
    final = record.final_evaluation
    env = record.environment
    config = record.config
    figures: list[Path] = []
    doc = Document(title=f"ImbalanceLab audit report: run {run['run_id']}")
    rel = f"{figure_dir.name}/"

    # --- 1. verdict
    ap_comps = [c for c in summary["comparisons"] if c["metric"] == "average_precision"]
    doc.add(Heading(2, "1. Verdict"))
    best = summary.get("best_candidate_by_mean_oof_ap")
    lines = [comparison_verdict(c) for c in ap_comps]
    if best:
        lines.insert(
            0,
            f"Best candidate by mean out-of-fold AP: **{best}** (selected on OOF "
            "predictions only; the test set was not used for selection).",
        )
    else:
        lines.insert(0, "No candidate models besides the baselines were run.")
    if final:
        lines += [
            final_test_verdict(c, final["results"])
            for c in final["comparisons"]
            if c["metric"] == "average_precision"
        ]
    else:
        lines.append(
            "Final test evaluation has **not** been performed; no test-set results are reported."
        )
    doc.add(BulletList(lines))
    doc.add(
        Paragraph(
            "Comparisons use paired differences on identical stored folds. CV folds "
            "are correlated, so no significance test is reported; win fractions and "
            "spreads are descriptive."
        )
    )

    # --- 2. dataset
    ds = run["dataset"]
    cb = profile.get("class_balance", {})
    doc.add(Heading(2, "2. Dataset"))
    doc.add(
        Table(
            ["Field", "Value"],
            [
                ["Source file", ds["source_name"]],
                ["SHA-256", f"`{ds['sha256']}`"],
                ["Rows", fmt(ds["n_rows"])],
                [
                    "Target / positive label",
                    f"`{ds['schema']['target']}` / `{ds['schema']['positive_label']}`",
                ],
                [
                    "Positives / negatives",
                    f"{fmt(cb.get('n_positive'))} / {fmt(cb.get('n_negative'))}",
                ],
                ["Positive rate", fmt(cb.get("positive_rate"))],
                ["Imbalance ratio (neg:pos)", fmt(cb.get("imbalance_ratio"), 2)],
                ["Feature columns", fmt(profile.get("n_features"))],
                ["Split strategy (schema)", ds["schema"]["split_strategy"]],
            ],
        )
    )
    if ds.get("notes"):
        doc.add(Paragraph("Loader notes:"), BulletList(list(ds["notes"])))
    fs = run["feature_spec"]
    doc.add(
        Paragraph(
            f"Features used: {len(fs['numeric'])} numeric, {len(fs['categorical'])} categorical."
            + (
                f" Dropped: {', '.join(f'`{k}` ({v})' for k, v in fs['dropped'].items())}."
                if fs["dropped"]
                else ""
            )
        )
    )

    # --- 3. profile warnings
    doc.add(Heading(2, "3. Data profile warnings"))
    warnings = profile.get("warnings", [])
    if warnings:
        doc.add(
            Paragraph(
                "These are **heuristic suspicions with the triggering statistic**, not "
                "proof of a problem. Each needs domain review."
            )
        )
        doc.add(
            Table(
                ["Code", "Column", "Severity", "Message"],
                [[w["code"], w["column"] or "—", w["severity"], w["message"]] for w in warnings],
            )
        )
    else:
        doc.add(Paragraph("No profiling heuristics fired."))
    dup = profile.get("duplicates")
    if dup:
        doc.add(
            Paragraph(
                f"Duplicates: {dup['n_exact_duplicate_rows']} exact duplicate rows; "
                f"{dup['n_conflicting_groups']} conflicting-label groups "
                f"({dup['n_conflicting_rows']} rows)."
            )
        )

    # --- 4. splits
    h, cv = run["holdout"], run["cv"]
    doc.add(Heading(2, "4. Split strategy"))
    doc.add(
        Table(
            ["Field", "Value"],
            [
                ["Outer holdout strategy", h["strategy"]],
                ["Test size (config)", fmt(h["config"]["test_size"], 2)],
                [
                    "Outer-train rows / test rows / gap rows",
                    f"{h['n_outer_train']} / {h['n_test']} / {h['n_gap']}",
                ],
                ["Test indices SHA-256", f"`{h['test_sha256']}`"],
                ["Inner CV strategy", cv["strategy"]],
                [
                    "Folds × repeats",
                    f"{cv['config']['n_splits']} × {cv['n_repeats_effective']}"
                    f" ({cv['n_folds_total']} folds)",
                ],
                ["Fold indices SHA-256", f"`{cv['fold_indices_sha256']}`"],
                ["Duplicate-aware groups", _group_summary(h)],
                [
                    "Oversized groups pinned to training (test / CV)",
                    f"{h.get('n_pinned_groups', 0)} groups, {h.get('n_pinned_rows', 0)} rows / "
                    f"{cv.get('n_pinned_groups', 0)} groups, {cv.get('n_pinned_rows', 0)} rows",
                ],
            ],
        )
    )
    doc.add(
        Paragraph(
            "CV, model selection and threshold selection use outer-train rows only. "
            "All models were fit on identical stored folds."
        )
    )
    split_w = run.get("split_warnings", [])
    if split_w:
        doc.add(BulletList([f"`{w['code']}` ({w['severity']}): {w['message']}" for w in split_w]))

    # --- 5. evaluation coverage
    doc.add(Heading(2, "5. Evaluation coverage"))
    doc.add(*coverage_blocks(run))

    # --- 6. models
    doc.add(Heading(2, "6. Models"))
    specs = run.get("model_specs") or [
        {"name": m, "sampler": "—", "description": ""} for m in run["models"]
    ]
    baselines = set(run["baselines"])
    doc.add(
        Table(
            ["Name", "Role", "Sampler", "Estimator"],
            [
                [
                    s["name"],
                    "baseline" if s["name"] in baselines else "candidate",
                    s["sampler"],
                    s["description"],
                ]
                for s in specs
            ],
        )
    )

    # --- 6. CV results
    doc.add(Heading(2, "7. Cross-validation results (out-of-fold)"))
    doc.add(
        Paragraph(
            f"Mean ± sample std across folds. `@ref` metrics use the fixed reference threshold "
            f"{fmt(summary['reference_threshold'], 2)}, not a tuned threshold."
        )
    )
    doc.add(
        Table(
            ["Model", *[label for _, label in CV_TABLE_METRICS]],
            [
                [name, *[fmt_summary(summary["models"][name][m]) for m, _ in CV_TABLE_METRICS]]
                for name in run["models"]
            ],
        )
    )
    doc.add(Heading(3, "Paired comparisons against baselines"))
    doc.add(
        Table(
            [
                "Candidate",
                "Baseline",
                "Metric",
                "Pairs",
                "Mean diff",
                "Std diff",
                "W/L/T",
                "Win fraction",
            ],
            [
                [
                    c["candidate"],
                    c["baseline"],
                    c["metric"],
                    fmt(c["n_pairs"]),
                    fmt_signed(c["mean_diff"]),
                    fmt(c["std_diff"]),
                    f"{c['wins']}/{c['losses']}/{c['ties']}",
                    fmt(c["win_fraction"], 2),
                ]
                for c in summary["comparisons"]
            ],
        )
    )
    oof = record.oof_predictions()
    figs = plot_curves(first_repeat(oof), "out-of-fold (repeat 0)", figure_dir, "oof")
    figures += figs
    doc.add(*[Image(p, rel + p.name, f"OOF curve {p.stem}") for p in figs])

    # --- 7. thresholds
    doc.add(Heading(2, "8. Threshold analysis (out-of-fold predictions only)"))
    if thresholds and thresholds.get("analyses"):
        rows = []
        for model, a in thresholds["analyses"].items():
            sp = a["per_repeat_spread"]
            st = a["strategy"]
            strat = (
                st["kind"]
                + (f" (target {st['target']})" if st.get("target") else "")
                + (f" (beta {st['beta']})" if st["kind"] == "max_fbeta" else "")
            )
            rows.append(
                [
                    model,
                    strat,
                    fmt(a["chosen_threshold"]),
                    f"{fmt(sp['threshold']['mean'])} ± {fmt(sp['threshold']['std'])} "
                    f"[{fmt(sp['threshold']['min'])}, {fmt(sp['threshold']['max'])}]",
                    fmt(sp["precision"]["mean"]),
                    fmt(sp["recall"]["mean"]),
                    fmt(sp["fbeta"]["mean"]),
                    fmt(sp["threshold"]["n"]),
                ]
            )
        doc.add(
            Table(
                [
                    "Model",
                    "Strategy",
                    "Chosen (median)",
                    "Per-repeat threshold mean ± std [min, max]",
                    "Precision",
                    "Recall",
                    "F-beta",
                    "Repeats",
                ],
                rows,
            )
        )
        doc.add(
            Paragraph(
                "Precision, recall and F-beta are per-repeat means at each repeat's "
                "own selected threshold, which is optimistic because selection and "
                "measurement use the same OOF predictions."
            )
        )
    else:
        doc.add(Paragraph("No threshold analysis recorded for this run."))

    # --- 8. final
    doc.add(Heading(2, "9. Final test evaluation"))
    if final:
        prov = final["threshold_provenance"]
        doc.add(
            Paragraph(
                f"Model **{final['model']}** refit on {final['n_outer_train']} outer-train rows "
                f"and scored once on {final['n_test']} test rows "
                f"({final['n_test_positive']} positive) at threshold "
                f"{fmt(final['threshold'])} (selected on {prov['source']}, strategy "
                f"`{prov['strategy']['kind']}`). Evaluated at {final['evaluated_at']}."
            )
        )
        if final.get("forced"):
            doc.add(
                Paragraph(
                    "**This final evaluation was forced (a repeat test-set scoring).** "
                    "See the evaluation log below."
                )
            )
        doc.add(
            Table(
                ["Model", "Threshold", *[label for _, label in TEST_TABLE_METRICS], "TP/FP/FN/TN"],
                [
                    [
                        name,
                        fmt(r["threshold"]),
                        *[fmt_ci(r, m) for m, _ in TEST_TABLE_METRICS],
                        "{tp}/{fp}/{fn}/{tn}".format(**r["confusion"]),
                    ]
                    for name, r in final["results"].items()
                ],
            )
        )
        bs = final.get("bootstrap")
        if bs:
            doc.add(
                Paragraph(
                    f"Brackets: {bs['confidence']:.0%} CI from a {bs['method']}, "
                    f"{bs['n_resamples']} resamples, seed {bs['seed']}, computed from the stored "
                    "test predictions. Undefined resamples are counted in the bracket; Brier has "
                    "no CI."
                )
            )
        else:
            doc.add(Paragraph("No bootstrap CIs recorded for this final evaluation."))
        test_preds = record.final_predictions()
        if test_preds is not None:
            figs = plot_curves(test_preds, "test set", figure_dir, "test")
            figures += figs
            doc.add(*[Image(p, rel + p.name, f"Test curve {p.stem}") for p in figs])
        log = record.final_log()
        doc.add(
            Paragraph(f"Final-evaluation log: {len(log)} entr{'y' if len(log) == 1 else 'ies'}.")
        )
        doc.add(
            BulletList(
                [
                    f"{e['at']}: {e['event']}"
                    + (f" (reason: {e['reason']})" if e.get("reason") else "")
                    for e in log
                ]
            )
        )
    else:
        doc.add(Paragraph("Not yet performed. No test-set numbers exist for this run."))

    # --- 9. limitations
    doc.add(Heading(2, "10. Limitations"))
    lim = [
        "CV folds share training data, so fold scores are correlated; spreads understate "
        "uncertainty and no significance claims are made.",
        "Profile warnings are heuristics; a flagged column is not proven leakage, and an "
        "unflagged column is not proven safe.",
        "Thresholds are selected on out-of-fold predictions; their OOF metrics are optimistic.",
    ]
    if final:
        lim.append(
            "Test results are a single evaluation per model; bootstrap CIs reflect test-sample "
            "variation only, not model-training variation."
        )
        if final["n_test_positive"] < FEW_TEST_POSITIVES:
            lim.append(
                f"Only {final['n_test_positive']} positive test rows: test metrics have "
                "high variance."
            )
    if cv["strategy"] == "temporal":
        lim.append("Temporal CV uses a single expanding-window repeat.")
    if split_w:
        lim.append("Split warnings were raised (section 4); affected scores may be optimistic.")
    cov = run.get("evaluation_coverage")
    if cov and cov["forced_to_train"]["n_rows"]:
        lim.append(
            f"{cov['forced_to_train']['n_rows']} rows in oversized groups were never evaluated "
            "(section 5)."
        )
    doc.add(BulletList(lim))

    # --- 10. reproducibility
    doc.add(Heading(2, "11. Reproducibility"))
    pk = env["packages"]
    doc.add(
        Table(
            ["Field", "Value"],
            [
                ["Run ID", run["run_id"]],
                ["Created / finished", f"{run['created_at']} / {run['finished_at']}"],
                ["Seed", fmt(run["seed"])],
                ["Dataset SHA-256", f"`{ds['sha256']}`"],
                ["Fold indices SHA-256", f"`{cv['fold_indices_sha256']}`"],
                ["Test indices SHA-256", f"`{h['test_sha256']}`"],
                ["Python / platform", f"{env['python']} / {env['platform']}"],
                *[[name, str(version)] for name, version in pk.items()],
            ],
        )
    )
    doc.add(
        Paragraph("Experiment config (`config.json`):"), Code(json.dumps(config, indent=2), "json")
    )
    return doc, figures


def generate_report(run_dir: Path) -> ReportPaths:
    """Write ``report/report.md`` and ``report/report.html`` (+ figures) inside ``run_dir``."""
    record = RunRecord(run_dir)
    if record.run.get("status") != "completed":
        raise ValueError("cannot report on a run that is not completed")
    out_dir = Path(run_dir) / REPORT_DIR
    figure_dir = out_dir / "figures"
    out_dir.mkdir(exist_ok=True)
    doc, figures = build_document(record, figure_dir)
    md_path, html_path = out_dir / "report.md", out_dir / "report.html"
    md_path.write_text(to_markdown(doc), encoding="utf-8", newline="\n")
    html_path.write_text(to_html(doc), encoding="utf-8", newline="\n")
    return ReportPaths(markdown=md_path, html=html_path, figures=figures)
