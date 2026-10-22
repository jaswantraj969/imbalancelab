"""ImbalanceLab Streamlit frontend: a pure client of the HTTP API.

Run with:  streamlit run frontend/app.py
API base URL: environment variable IMBALANCELAB_API_URL (default http://localhost:8000).
"""

from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from api_client import ApiClient, ApiError, api_url_from_env

PAGES = ("Upload & profile", "Run experiment", "Results & thresholds", "Final evaluation", "Report")
CANDIDATES = {
    "hgb": {"model": "hgb"},
    "hgb + random undersampling": {"model": "hgb", "sampler": "random_under"},
    "hgb + SMOTE": {"model": "hgb", "sampler": "smote"},
    "random_forest": {"model": "random_forest"},
    "logreg_balanced + random oversampling": {"model": "logreg_balanced", "sampler": "random_over"},
}


def fmt(value: Any) -> str:
    return "undefined" if value is None else f"{value:.4f}"


def show_error(exc: Exception) -> None:
    if isinstance(exc, ApiError):
        st.error(f"API error {exc.status} ({exc.error}): {exc.detail}")
    else:
        st.error(f"Could not reach the API: {exc}")


def dataset_picker(client: ApiClient, key: str) -> str | None:
    datasets = client.list_datasets()
    if not datasets:
        st.info("No datasets registered yet. Upload one first.")
        return None
    labels = {f"{d['dataset_id']} ({d['source_name']}, {d['n_rows']} rows)": d for d in datasets}
    choice = st.selectbox("Dataset", list(labels), key=key)
    return str(labels[choice]["dataset_id"]) if choice else None


def run_picker(client: ApiClient, key: str) -> dict[str, Any] | None:
    runs = [r for r in client.list_runs() if r["status"] == "completed"]
    if not runs:
        st.info("No completed runs yet.")
        return None
    labels = {f"{r['run_id']} (dataset {r['dataset_id']})": r for r in runs}
    choice = st.selectbox("Run", list(labels), key=key)
    return labels[choice] if choice else None


def page_upload(client: ApiClient) -> None:
    st.header("Upload a dataset and view its profile")
    with st.form("upload"):
        upload = st.file_uploader("CSV or Parquet file", type=["csv", "parquet"])
        c1, c2 = st.columns(2)
        target = c1.text_input("Target column", "label")
        positive = c2.text_input("Positive label", "1")
        strategy = st.selectbox("Split strategy", ["stratified", "group", "temporal"])
        c3, c4, c5 = st.columns(3)
        id_col = c3.text_input("ID column (optional)")
        group_col = c4.text_input("Group column (required for group)")
        time_col = c5.text_input("Time column (required for temporal)")
        c6, c7, c8 = st.columns(3)
        test_size = c6.number_input("Test size", 0.05, 0.5, 0.2, 0.05)
        gap = c7.number_input("Temporal gap (distinct time values)", 0, 1000, 0)
        seed = c8.number_input("Holdout seed", 0, 2**31 - 1, 42)
        duplicate_groups = st.checkbox(
            "Duplicate-aware groups (identical feature rows never cross a split boundary)"
        )
        submitted = st.form_submit_button("Register dataset")
    if submitted:
        if upload is None:
            st.warning("Choose a file first.")
        else:
            schema: dict[str, Any] = {
                "target": target,
                "positive_label": positive,
                "split_strategy": strategy,
                "duplicate_groups": duplicate_groups,
            }
            for field, value in (
                ("id_column", id_col),
                ("group_column", group_col),
                ("time_column", time_col),
            ):
                if value.strip():
                    schema[field] = value.strip()
            holdout = {"test_size": test_size, "gap": int(gap), "seed": int(seed)}
            try:
                reg = client.upload_dataset(upload.name, upload.getvalue(), schema, holdout)
                st.success(f"Registered {reg['dataset_id']} (SHA-256 {reg['sha256'][:12]}…)")
            except Exception as exc:  # noqa: BLE001 - shown to the user
                show_error(exc)

    st.subheader("Profile")
    dataset_id = dataset_picker(client, "profile_ds")
    if dataset_id:
        profile = client.profile(dataset_id)
        cb = profile["class_balance"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows", cb["n_rows"])
        m2.metric("Positives", cb["n_positive"])
        m3.metric("Positive rate", f"{cb['positive_rate']:.4f}")
        ratio = cb["imbalance_ratio"]
        m4.metric("Neg:pos", "n/a" if ratio is None else f"{ratio:.1f}")
        st.caption("Warnings are heuristic suspicions with evidence, not proof.")
        if profile["warnings"]:
            st.dataframe(
                pd.DataFrame(profile["warnings"])[["code", "column", "severity", "message"]],
            )
        else:
            st.write("No profiling heuristics fired.")
        st.dataframe(pd.DataFrame(profile["columns"]))


def page_run(client: ApiClient) -> None:
    st.header("Configure and launch a run")
    dataset_id = dataset_picker(client, "run_ds")
    if not dataset_id:
        return
    picked = st.multiselect("Candidates (baselines are always added)", list(CANDIDATES), ["hgb"])
    c1, c2, c3 = st.columns(3)
    n_splits = c1.number_input("Folds", 2, 10, 5)
    n_repeats = c2.number_input("Repeats", 1, 10, 3)
    seed = c3.number_input("Seed", 0, 2**31 - 1, 42)
    if st.button("Launch run (synchronous; may take a while)"):
        config = {
            "candidates": [CANDIDATES[p] for p in picked],
            "cv": {"n_splits": int(n_splits), "n_repeats": int(n_repeats), "seed": int(seed)},
            "seed": int(seed),
        }
        with st.spinner("Running cross-validation…"):
            try:
                brief = client.create_run(dataset_id, config)
                st.success(f"Run {brief['run_id']} {brief['status']}.")
                st.json(brief)
            except Exception as exc:  # noqa: BLE001
                show_error(exc)


def page_results(client: ApiClient) -> None:
    st.header("Cross-validation results and threshold analysis")
    run = run_picker(client, "res_run")
    if not run:
        return
    detail = client.get_run(run["run_id"])
    summary = detail["summary"]
    rows = []
    for name, metrics in summary["models"].items():
        ap, auc = metrics["average_precision"], metrics["roc_auc"]
        rows.append(
            {
                "model": name,
                "AP mean": fmt(ap["mean"]),
                "AP std": fmt(ap["std"]),
                "ROC AUC mean": fmt(auc["mean"]),
                "folds": ap["n"],
            }
        )
    st.dataframe(pd.DataFrame(rows))
    st.caption(f"Best candidate by mean OOF AP: {summary['best_candidate_by_mean_oof_ap']}")
    comps = [c for c in summary["comparisons"] if c["metric"] == "average_precision"]
    st.dataframe(
        pd.DataFrame(comps)[
            ["candidate", "baseline", "n_pairs", "mean_diff", "win_fraction", "wins", "losses"]
        ],
    )

    st.subheader("Threshold analysis (out-of-fold predictions only)")
    with st.form("thresholds"):
        model = st.selectbox("Model", detail["run"]["models"])
        kind = st.selectbox(
            "Strategy", ["max_fbeta", "target_recall", "target_precision", "min_cost"]
        )
        c1, c2, c3, c4 = st.columns(4)
        beta = c1.number_input("beta", 0.1, 10.0, 1.0)
        target = c2.number_input("target (recall/precision)", 0.01, 1.0, 0.8)
        cost_fp = c3.number_input("cost FP", 0.0, 1000.0, 1.0)
        cost_fn = c4.number_input("cost FN", 0.0, 1000.0, 1.0)
        go = st.form_submit_button("Select threshold")
    if go:
        strategy: dict[str, Any] = {
            "kind": kind,
            "beta": beta,
            "cost_fp": cost_fp,
            "cost_fn": cost_fn,
        }
        if kind in ("target_recall", "target_precision"):
            strategy["target"] = target
        try:
            analysis = client.thresholds(run["run_id"], model, strategy)
            spread = analysis["per_repeat_spread"]["threshold"]
            st.success(
                f"Chosen threshold {analysis['chosen_threshold']:.4f} (median of "
                f"{spread['n']} repeats; mean {fmt(spread['mean'])} ± {fmt(spread['std'])})"
            )
            st.dataframe(pd.DataFrame(analysis["per_repeat"]))
        except Exception as exc:  # noqa: BLE001
            show_error(exc)


def page_final(client: ApiClient) -> None:
    st.header("Final evaluation (scores the test set once)")
    run = run_picker(client, "final_run")
    if not run:
        return
    detail = client.get_run(run["run_id"])
    if detail["final_evaluation"]:
        st.warning(
            "This run already has a final evaluation. Re-evaluating requires force + "
            "a reason, and is logged."
        )
        st.json(detail["final_evaluation"]["results"])
    analysed = list((detail["thresholds"] or {}).get("analyses", {}))
    if not analysed:
        st.info("Run a threshold analysis first (Results & thresholds page).")
        return
    model = st.selectbox("Model (must have a threshold analysis)", analysed)
    force = st.checkbox("Force re-evaluation")
    reason = st.text_input("Reason (required when forcing)") if force else None
    if st.button("Run final evaluation"):
        try:
            out = client.final_evaluation(run["run_id"], model, force, reason)
            st.success(f"Test set scored once with threshold {out['threshold']:.4f}.")
            rows = [
                {"model": name, **{k: fmt(v["value"]) for k, v in r["metrics"].items()}}
                for name, r in out["results"].items()
            ]
            st.dataframe(pd.DataFrame(rows))
            if out.get("model_id"):
                st.caption(f"Persisted model: {out['model_id']}")
        except Exception as exc:  # noqa: BLE001
            show_error(exc)


def page_report(client: ApiClient) -> None:
    st.header("Audit report")
    run = run_picker(client, "report_run")
    if not run:
        return
    html = client.report(run["run_id"], "html")
    st.download_button("Download HTML report", html, file_name=f"{run['run_id']}.html")
    components.html(html, height=1200, scrolling=True)


def main() -> None:
    st.set_page_config(page_title="ImbalanceLab", layout="wide")
    st.sidebar.title("ImbalanceLab")
    base_url = st.sidebar.text_input("API base URL", api_url_from_env())
    client = ApiClient(base_url)
    try:
        health = client.health()
        st.sidebar.success(f"API ok (v{health['version']})")
    except Exception as exc:  # noqa: BLE001
        st.sidebar.error("API unreachable")
        show_error(exc)
        st.stop()
    page = st.sidebar.radio("Page", PAGES)
    try:
        {
            PAGES[0]: page_upload,
            PAGES[1]: page_run,
            PAGES[2]: page_results,
            PAGES[3]: page_final,
            PAGES[4]: page_report,
        }[page](client)
    except ApiError as exc:
        show_error(exc)


main()
