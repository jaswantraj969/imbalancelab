# Project Status

Status values: `not started` · `in progress` · `done` (engineer's acceptance criteria pass) ·
`verified` (only the supervisor sets this, after review).

| Milestone | Description | Status | Evidence |
|---|---|---|---|
| M0 | Skeleton, tooling, plan | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (T0) |
| M1 | Data loading, schema validation, profiling | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M1) |
| M2 | Splitting + leakage-safe pipeline builder | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M2) |
| M3 | Metrics module incl. edge cases | done | [REVIEW_PACKET.md](REVIEW_PACKET.md) (M3) |
| M4 | Experiment runner, baselines, run records | not started | — |
| M5 | Threshold analysis (OOF/validation only) | not started | — |
| M6 | Evidence-based audit report | not started | — |
| M7 | FastAPI endpoints | not started | — |
| M8 | Streamlit frontend (via API only) | not started | — |
| M9 | Model persistence + inference endpoint | not started | — |
| M10 | Docs + case study from real results | not started | — |

## Known issues

- Plan step "tree -L 3" substituted with `find` (no `tree` binary in Git Bash on this machine); see REVIEW_PACKET.md T0 deviations.

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

## Last updated

2026-10-22 — M3 (Implementation Engineer)
