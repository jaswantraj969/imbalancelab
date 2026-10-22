# Project Status

Status values: `not started` · `in progress` · `done` (engineer's acceptance criteria pass) ·
`verified` (only the supervisor sets this, after review).

| Milestone | Description | Status | Evidence |
|---|---|---|---|
| M0 | Skeleton, tooling, plan | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (T0) |
| M1 | Data loading, schema validation, profiling | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M1) |
| M2 | Splitting + leakage-safe pipeline builder | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M2) |
| M3 | Metrics module incl. edge cases | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M3) |
| M4 | Experiment runner, baselines, run records | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M4) |
| M5 | Threshold analysis (OOF/validation only) | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M5) |
| M6 | Evidence-based audit report | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M6) |
| M7 | FastAPI endpoints | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M7) |
| M8 | Streamlit frontend (via API only) | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M8) |
| M9 | Model persistence + inference endpoint | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M9) |
| M10 | Docs + case study from real results | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M10) |

## Known issues

- Plan step "tree -L 3" substituted with `find` (no `tree` binary in Git Bash on this machine); see REVIEW_PACKET.md T0 deviations.
- CI workflow (`.github/workflows/ci.yml`) is defined but has never run: the repository has no
  remote (environment limitation).
- Starlette emits a deprecation warning for `httpx` in its TestClient (prefers `httpx2`); the dev
  dependency is `httpx` as specified.
- Case-study data (`mammography`) contains 3334 exact-duplicate rows that cross split boundaries;
  documented with a post-hoc sensitivity check; a duplicate-grouped re-run was not done.

## Decisions

- **D1 (plan amendment):** added invariant 7 (outer holdout once per dataset; test scored once)
  and the M2/M4/M5/tooling amendments to IMPLEMENTATION_PLAN.md.
- **D2:** `python-multipart` added as a runtime dependency. FastAPI requires it for the
  multipart upload in `POST /datasets` (M7).
- **D3:** `requirements-lock.txt` is a *universal* lock (`uv pip compile --universal
  --python-version 3.11`), so one file serves both CI versions. numpy is resolved to 2.4.x on
  3.11 and 2.5.x on 3.12+ via environment markers.
- **D4:** removed `python_version = "3.11"` from the mypy config. numpy 2.5 type stubs use PEP 695
  `type` statements, which mypy rejects when targeting 3.11. mypy now targets the running
  interpreter, so CI's 3.11 job checks against numpy 2.4 (from the lock) and its 3.13 job against
  numpy 2.5.
- **D5:** profiling runs on the full dataset, before the outer holdout. It is descriptive, is
  never used for fitting or selection, and covers the data a reviewer must judge as a whole (for
  example duplicates). This is not a leakage path, because no model, threshold, or feature choice
  reads it automatically.
- **D6:** "exact duplicate rows" compares every column except `id_column`, since a unique ID
  would otherwise hide true duplicates. "Conflicting duplicates" compares feature columns only.
- **D7:** a pure category is flagged only when support ≥ `pure_category_min_support` and the
  probability of that purity under the base rate (p^n or (1-p)^n) is ≤
  `pure_category_max_chance` (default 1e-4). Without this, every small all-negative category in
  a 1%-positive dataset would be flagged.
- **D8:** the temporal `gap` is counted in *distinct time values*, not rows, so tied timestamps
  never straddle a boundary. Temporal CV forces `n_repeats=1` (it is deterministic) and records
  an info warning instead of failing.
- **D9:** the group holdout takes the first fold of `StratifiedGroupKFold` with
  `n_splits = round(1/test_size)`, so the test set is roughly stratified and group-disjoint. The
  test fraction is therefore approximate.
- **D10:** the sampler runs after preprocessing, because SMOTE needs complete numeric input.
  One-hot uses `max_categories=50` to keep dense output bounded, with `handle_unknown="ignore"`
  as specified.
- **D11:** constant scores do not make AP or ROC AUC undefined. With all ties, AP equals the
  prevalence and AUC equals 0.5: well-defined chance-level values, not 0/0. The prior
  `DummyClassifier` baseline produces exactly such scores, and its AP (= prevalence) is the
  reference every model must beat, so making it undefined would remove the baseline. These
  values carry `note="constant scores: value equals the chance level (all ties)"`. Constant
  scores do make MCC undefined (constant predictions), and precision undefined when nothing is
  predicted positive.
- **D12:** F-beta is computed as (1+β²)TP / ((1+β²)TP + β²FN + FP), which is undefined only when
  the denominator is 0. Hence "no positive predictions but positives exist" gives F = 0
  (defined), even though precision is undefined. This matches the counts-based definition and
  scikit-learn's value.
- **D13:** "best candidate" = the highest mean OOF average precision among non-baseline
  candidates (`summary.best_candidate_by_mean_oof_ap`). It is a selection made on OOF data
  only; final evaluation may use it or an explicitly named model.
- **D14:** paired comparisons are reported for AP (primary) and ROC AUC, for each candidate
  against each baseline, plus logreg against dummy (is there any signal at all?). Folds where
  either side is undefined are skipped and counted.
- **D15:** the chosen threshold is the **median** of the per-repeat thresholds (robust to one
  odd repeat). Mean, std, min and max are reported alongside it.
- **D16:** final evaluation also refits and scores both baselines on the test set, each at its
  own OOF-selected threshold (same strategy), so test results are reported against the
  baselines (invariant 4). This is still one scoring per model, and the baselines involve no
  selection.
- **D17:** a candidate "beats" a baseline in the report only if the mean paired difference is
  > 0 **and** the win fraction is > 0.5. Anything else is reported as "does NOT beat". This is
  conservative and descriptive, not a significance claim.
- **D18:** no Markdown library was added. A small internal document model renders to both
  Markdown and HTML, which keeps the dependency list as specified.
- **D19:** `POST /models/{id}/predict` was added in M7 with its request and response models,
  but persistence is M9, so until then it returns 404. M9 wires `final-evaluation` to persist
  the refit pipeline and implements prediction.
- **D20:** a library `workflow` module is the API's only dependency on ML code, so the "no ML
  logic in routes" requirement is checked by an AST test on `api/app.py` imports.
- **D21:** the holdout is created at dataset registration (`POST /datasets`, optional
  `holdout` JSON) and stored with the dataset. All runs on that dataset share it.
- **D22:** frontend tests run a real uvicorn server in a background thread and drive the
  Streamlit app with `streamlit.testing.v1.AppTest`. This tests the frontend against the real
  API rather than against mocks.
- **D23:** a model is persisted at final evaluation (default `persist_model=True`). The artifact
  is the pipeline refit on outer-train rows that produced the reported test numbers, so served
  predictions match the audited model exactly.
- **D24:** the case-study protocol is fixed in code (`scripts/run_case_study.py`) before the run:
  stratified 80/20 holdout (seed 42), 5×3 CV, candidates hgb, hgb+random_under, hgb+smote and
  random_forest, selection by mean OOF AP, `max_fbeta` with beta=2 (recall-weighted, which suits
  screening). It was not tuned after seeing results. The three successful executions used the
  same protocol and produced identical metrics.
- **D25:** the duplicate sensitivity analysis is explicitly *post hoc* and re-slices stored test
  predictions only. It cannot influence the model or threshold, and the text states its
  prevalence caveat and that it does not cover CV.
- **D26:** run-record files over 1 MB are not committed to `docs/`. Their SHA-256s are listed in
  `OMITTED_FILES.json`, and `scripts/run_case_study.py` regenerates them.

## Last updated

2026-10-22 — M10 + FINAL_REPORT.md (Implementation Engineer). All milestones done; awaiting supervisor verification. Nothing to resume.
