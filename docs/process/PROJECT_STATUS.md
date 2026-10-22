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
| M10 | Docs + case study from real results | done (not verified by supervisor; T-R1 fixes applied) | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M10, T-R1) |
| T-R1 | Supervisor review fixes (H1, H2, M1–M5, L1, L2) | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (T-R1) |
| T-R2 | Bootstrap CIs, evaluation coverage, cluster analysis, disclosures, CI | done (M4 completed in T-R3) | [REVIEW_PACKET.md](REVIEW_PACKET.md) (T-R2) |
| T-R3 | GitHub CI, calibration disclosure, paired bootstrap, repo tidy | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (T-R3) |

## Known issues

- Plan step "tree -L 3" substituted with `find` (no `tree` binary in Git Bash on this machine); see REVIEW_PACKET.md T0 deviations.
- **GitHub CI (resolved in T-R3):** the private repository `jaswantraj969/imbalancelab` was
  created as authorised, and GitHub Actions runs the gate on Python 3.11 and 3.13. Run URLs and
  results are in REVIEW_PACKET T-R3 and FINAL_REPORT.
- (Resolved in T-R3, D34) Starlette's TestClient warned that plain `httpx` is deprecated; `httpx2`
  is now a dev dependency, and the suite runs with zero warnings.
- Case-study data (`mammography`) has one cluster of 3329 identical feature rows (7 positive).
  In run (b) it is pinned to training, so the case-study test metrics do not cover it (stated in
  `docs/case_study.md`).
- Playwright (used by `scripts/ui_screenshots.py`) is an optional dev tool and is not in the
  project dependencies or the lock file.

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
- **D27 (T-R1 H1):** `duplicate_groups` is a `DatasetSchema` flag, since the holdout is per
  dataset. A cluster is all rows with identical feature values (target, id, group and time
  excluded), and conflicting labels stay in one cluster. With a declared `group_column`, groups
  are combined by **connected components** (declared groups linked by a shared duplicate cluster
  are merged), so a declared group is never split and no cluster crosses a boundary. A warning
  reports the spanning clusters. I read the instruction "combine: group = declared group" as
  this merge, because keeping declared groups unchanged would let clusters cross boundaries.
  Temporal + `duplicate_groups` is rejected.
- **D28 (T-R1 H1, found on real data):** with mammography's single 3329-row cluster,
  `StratifiedGroupKFold` produced a degenerate holdout (the cluster plus 45 all-positive rows;
  logreg and hgb+smote had identical test AP). Fix: groups larger than `max_eval_group_fraction`
  (default 0.25) of the target test/validation size are pinned to training in the holdout and in
  every CV fold, and test-fold counts are sized for the eligible rows. Added holdout warnings
  `holdout_size_deviation`, `holdout_prevalence_deviation`, and `holdout_dominated_by_group`
  (> 50% of the test set from one group). The degenerate run was not committed; it is
  documented in REVIEW_PACKET T-R1.
- **D29 (T-R1 L2, found by the hash check):** `random_forest` now uses `n_jobs=1`.
  Multi-threaded tree averaging gave last-bit (≤ 2.2e-16) differences between runs, so stored
  OOF predictions could not be regenerated byte for byte. Metrics were unaffected at reported
  precision (`summary.json` identical).
- **D30 (T-R2):** bootstrap CIs and evaluation coverage were added to the committed case-study
  runs by **amending** them (`scripts/run_case_study.py --amend-existing`), not by re-running.
  CIs come from the stored `final_predictions.parquet`, and coverage from the stored holdout plus
  folds rebuilt and checked against the recorded fold-index SHA-256. This avoids scoring the test
  sets again. Amendments are logged in `run.json` / `final_evaluation.json` (`amendments`) and
  in `final_evaluation_log.jsonl`. The stored test predictions are byte-identical before and
  after.
- **D31 (T-R2):** "evaluation coverage": a row counts as evaluated if it is in the test set or in
  at least one validation fold. Never-evaluated rows are split into forced-to-train (oversized
  groups), temporal gap, and other. The report WARNING triggers when forced-to-train rows exceed
  10% of the dataset. Bootstrap: stratified (class counts fixed), percentile interval, 2000
  resamples, seed 42, the same resample indices for all models of a run. It is applied to test
  metrics only.
- **D32 (T-R3 H1):** calibration is **disclosed, not fixed**, since there is no calibration stage
  (MVP scope). The final evaluation stores, per model, the test Brier score with a bootstrap CI
  and a reliability curve with 10 quantile bins (ties can merge bins; n per bin is recorded). The
  report, README and the API `Prediction.probability` description state that resampler-trained
  scores are ranking scores, NOT calibrated probabilities, and must not be read as risk. Runs
  without a resampler state that calibration was not assessed beyond Brier and the curve.
  Class-weighted models are noted as shifting scores too.
- **D33 (T-R3 M2):** paired stratified bootstrap of AP and ROC AUC differences (selected model −
  each baseline). It uses the same resample indices as the per-model CIs (seed 42, 2000
  resamples) and reports the point, 95% CI, win fraction (strictly better) and tie fraction. It
  is descriptive, not a significance test.
- **D34 (T-R3 L1):** the only pytest warning was `StarletteDeprecationWarning: Using httpx with
  starlette.testclient is deprecated; install httpx2 instead`. Starlette 1.9's TestClient imports
  `httpx2` first, so `httpx2>=2.16,<3` was added to the dev extras and lock. `httpx` stays as T0
  specified. Result: 0 warnings.
- **D35 (T-R3 L2):** IMPLEMENTATION_PLAN, PROJECT_STATUS, REVIEW_PACKET and FINAL_REPORT moved to
  `docs/process/`. `scripts/check_links.py` verifies every relative Markdown link. Historical
  entries in REVIEW_PACKET still mention the old root-level paths; they are verbatim logs.

## Last updated

2026-10-23 — T-R3 (Implementation Engineer). Awaiting supervisor verification. Nothing to resume.
