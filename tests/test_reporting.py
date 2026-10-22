import os
import re
from pathlib import Path

import pytest

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import final_evaluate
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.reporting import comparison_verdict, final_test_verdict, generate_report
from imbalancelab.reporting.render import Document, Paragraph, Table, to_html, to_markdown
from imbalancelab.reporting.report import fmt, fmt_ci, fmt_summary
from imbalancelab.splitting import make_holdout
from imbalancelab.tracking import RunRecord

SNAPSHOT = Path(__file__).parent / "snapshots" / "report_structure.md"


def _run(write_csv, tmp_path, final: bool = True) -> Path:
    schema = DatasetSchema(target="label", positive_label="yes", id_column="row_id")
    ds = load_dataset(write_csv(make_imbalanced_frame(n=260, seed=21), "synthetic.csv"), schema)
    holdout = make_holdout(ds)
    cfg = ExperimentConfig.model_validate(
        {"candidates": [{"model": "hgb"}], "cv": {"n_splits": 3, "n_repeats": 2}}
    )
    run_dir = run_experiment(ds, holdout, cfg, tmp_path / "runs").run_dir
    if final:
        run_threshold_analysis(run_dir, "hgb", ThresholdStrategy(kind="max_fbeta", beta=2.0))
        final_evaluate(ds, run_dir, "hgb")
    return run_dir


def mask(text: str) -> str:
    """Remove values that legitimately vary (ids, hashes, times, numbers, platform)."""
    text = re.sub(r"\| Python / platform \|.*\|", "| Python / platform | <platform> |", text)
    text = re.sub(r"run-\d{8}T\d{6}Z-[0-9a-f]{8}", "<run_id>", text)
    text = re.sub(r"[0-9a-f]{64}", "<sha256>", text)
    text = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", "<time>", text)
    # verdict wording depends on the numbers; its logic is tested separately
    text = re.sub(r"\b(beats|does NOT beat)\b", "<verdict>", text)
    return re.sub(r"[-+]?\d+(\.\d+)?(e[-+]?\d+)?", "<n>", text)


def test_report_structure_snapshot(write_csv, tmp_path) -> None:
    paths = generate_report(_run(write_csv, tmp_path))
    masked = mask(paths.markdown.read_text(encoding="utf-8"))
    if os.environ.get("UPDATE_SNAPSHOTS") == "1":
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(masked, encoding="utf-8", newline="\n")
    assert SNAPSHOT.exists(), "snapshot missing; run with UPDATE_SNAPSHOTS=1 once and review it"
    assert masked == SNAPSHOT.read_text(encoding="utf-8")


def test_report_numbers_trace_to_run_records(write_csv, tmp_path) -> None:
    run_dir = _run(write_csv, tmp_path)
    paths = generate_report(run_dir)
    md = paths.markdown.read_text(encoding="utf-8")
    record = RunRecord(run_dir)
    summary, final = record.summary, record.final_evaluation
    for model in record.run["models"]:
        ap = fmt_summary(summary["models"][model]["average_precision"])
        assert f"| {model} | {ap} |" in md
    for model, r in final["results"].items():
        ap = fmt_ci(r, "average_precision")  # point estimate + bootstrap CI from the record
        ci = r["ci"]["average_precision"]
        assert (
            ap == f"{fmt(r['metrics']['average_precision']['value'])} "
            f"[{ci['lower']:.4f}, {ci['upper']:.4f}]"
        )
        assert f"| {model} | {fmt(r['threshold'])} | {ap} |" in md
    chosen = record.thresholds["analyses"]["hgb"]["chosen_threshold"]
    assert f"| hgb | max_fbeta (beta 2.0) | {fmt(chosen)} |" in md
    assert record.run["dataset"]["sha256"] in md and record.run["cv"]["fold_indices_sha256"] in md
    for p in paths.figures:
        assert p.is_file() and p.stat().st_size > 1000
        assert f"figures/{p.name}" in md
    assert {p.name for p in paths.figures} == {
        "oof_pr.png",
        "oof_roc.png",
        "test_pr.png",
        "test_roc.png",
        "test_reliability.png",
    }
    html = paths.html.read_text(encoding="utf-8")
    assert html.count("data:image/png;base64,") == 5
    assert "<table>" in html and "<script" not in html


def test_report_before_final_evaluation_says_so(write_csv, tmp_path) -> None:
    run_dir = _run(write_csv, tmp_path, final=False)
    md = generate_report(run_dir).markdown.read_text(encoding="utf-8")
    assert "Final test evaluation has **not** been performed" in md
    assert "No threshold analysis recorded" in md
    assert "Not yet performed. No test-set numbers exist" in md
    assert "test_pr.png" not in md


def test_report_refuses_incomplete_run(write_csv, tmp_path) -> None:
    run_dir = _run(write_csv, tmp_path, final=False)
    meta = (run_dir / "run.json").read_text().replace('"completed"', '"failed"')
    (run_dir / "run.json").write_text(meta)
    with pytest.raises(ValueError, match="not completed"):
        generate_report(run_dir)


def _comp(mean_diff, wins, n, metric="average_precision"):
    return {
        "candidate": "hgb",
        "baseline": "logreg_balanced",
        "metric": metric,
        "n_pairs": n,
        "mean_diff": mean_diff,
        "wins": wins,
        "win_fraction": wins / n if n else None,
    }


def test_verdict_states_plainly_when_not_beating_baseline() -> None:
    assert "**hgb** beats **logreg_balanced**" in comparison_verdict(_comp(0.03, 8, 10))
    assert "does NOT beat" in comparison_verdict(_comp(-0.01, 2, 10))
    assert "does NOT beat" in comparison_verdict(_comp(0.01, 4, 10))  # mean up, mostly losses
    assert "does NOT beat" in comparison_verdict(_comp(0.0, 5, 10))
    assert "cannot be compared" in comparison_verdict(_comp(None, 0, 0))
    test_c = {
        "candidate": "hgb",
        "baseline": "dummy_prior",
        "metric": "average_precision",
        "candidate_value": 0.2,
        "baseline_value": 0.3,
        "diff": -0.1,
    }
    assert "does NOT beat" in final_test_verdict(test_c)
    assert "beats" in final_test_verdict({**test_c, "diff": 0.1})
    assert "undefined" in final_test_verdict({**test_c, "diff": None})


def test_render_escaping() -> None:
    doc = Document("T <x>")
    doc.add(Paragraph("a **b** `c` <script>"), Table(["h|1"], [["v|2"]]))
    md, html = to_markdown(doc), to_html(doc)
    assert "h\\|1" in md and "v\\|2" in md
    assert "<strong>b</strong>" in html and "<code>c</code>" in html
    assert "&lt;script&gt;" in html and "<script>" not in html
    assert fmt(None) == "undefined" and fmt(True) == "True" and fmt(3) == "3"
