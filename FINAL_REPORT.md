# ImbalanceLab: final report

**Prepared by:** Implementation Engineer · **Date:** 2026-10-22 · **For:** supervisor review

All milestones M0–M10 are implemented and committed, and each passed its gate. None is marked
`verified`: that status is reserved for the supervisor. Evidence for each milestone is in
[REVIEW_PACKET.md](REVIEW_PACKET.md), and decisions D1–D26 and known issues are in
[PROJECT_STATUS.md](PROJECT_STATUS.md).

## 1. Milestones and commits

| Milestone | Scope | Status | Commit |
|---|---|---|---|
| M0 | Skeleton, tooling, plan | done (supervisor to verify) | `03ead06` |
| — | Part A: invariant 7, lock, CI, pyarrow | applied | `5fbb139` |
| M1 | Data loading, schema validation, profiling | done (supervisor to verify) | `fdc15f3` |
| M2 | Outer holdout, inner CV, duplicates, pipeline builder | done (supervisor to verify) | `d906960` |
| M3 | Metrics with explicit undefined cases | done (supervisor to verify) | `58c6241` |
| M4 | Runner, baselines, run records | done (supervisor to verify) | `9e207a5` |
| M5 | OOF thresholds + one-shot final evaluation | done (supervisor to verify) | `7ce0891` |
| M6 | Audit report | done (supervisor to verify) | `68a5647` |
| M7 | FastAPI | done (supervisor to verify) | `a9ff54e` |
| M8 | Streamlit frontend | done (supervisor to verify) | `45706fc` |
| M9 | Persistence + inference | done (supervisor to verify) | `b250b9a` |
| M10 | Docs + case study | done (supervisor to verify) | `91c6f54` |

```text
$ git log --oneline
91c6f54 M10: README, case study on mammography from real run records, smoke script
b250b9a M9: model persistence with integrity check; inference endpoint
45706fc M8: Streamlit frontend as a pure API client
a9ff54e M7: FastAPI endpoints over a library workflow layer
68a5647 M6: evidence-based audit report (Markdown + HTML) from run records
7ce0891 M5: OOF threshold analysis with provenance guard; one-shot final evaluation
9e207a5 M4: experiment runner, baselines, file-based run records
58c6241 M3: metrics with explicit undefined cases
d906960 M2: outer holdout, inner CV, cross-boundary duplicates, pipeline builder
fdc15f3 M1: data loading, schema validation, profiling
5fbb139 Plan amendments: invariant 7, lock file, CI, pyarrow
03ead06 T0: project skeleton, tooling, plan
```

This report is committed after the log above, in its own commit.

## 2. Final gate output (verbatim, on commit `91c6f54`)

```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
55 files already formatted
[exit 0]

$ mypy
Success: no issues found in 37 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 53%]
..............................................................           [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  <project-root>\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
src\imbalancelab\__init__.py                    2      0   100%
src\imbalancelab\api\__init__.py                0      0   100%
src\imbalancelab\api\app.py                   114      0   100%
src\imbalancelab\api\schemas.py                45      0   100%
src\imbalancelab\config.py                     15      1    93%   27
src\imbalancelab\data\__init__.py               4      0   100%
src\imbalancelab\data\errors.py                21      0   100%
src\imbalancelab\data\loader.py               143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                37      0   100%
src\imbalancelab\evaluation\__init__.py         2      0   100%
src\imbalancelab\evaluation\config.py          35      0   100%
src\imbalancelab\evaluation\final.py          109      4    96%   74-75, 102, 160
src\imbalancelab\evaluation\metrics.py        115      0   100%
src\imbalancelab\evaluation\runner.py         117      0   100%
src\imbalancelab\evaluation\thresholds.py     138      0   100%
src\imbalancelab\models\__init__.py             2      0   100%
src\imbalancelab\models\persistence.py        100      0   100%
src\imbalancelab\models\registry.py            18      0   100%
src\imbalancelab\pipelines\__init__.py          2      0   100%
src\imbalancelab\pipelines\builder.py          66      0   100%
src\imbalancelab\profiling\__init__.py          3      0   100%
src\imbalancelab\profiling\profile.py         169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py          9      0   100%
src\imbalancelab\reporting\__init__.py          2      0   100%
src\imbalancelab\reporting\figures.py          44      1    98%   28
src\imbalancelab\reporting\render.py           82      0   100%
src\imbalancelab\reporting\report.py          163      7    96%   59, 125, 172, 202, 245, 440, 442
src\imbalancelab\splitting\__init__.py          3      0   100%
src\imbalancelab\splitting\duplicates.py       24      0   100%
src\imbalancelab\splitting\splits.py          195      3    98%   96, 102, 114
src\imbalancelab\tracking\__init__.py           2      0   100%
src\imbalancelab\tracking\records.py          120      3    98%   89-90, 170
src\imbalancelab\workflow.py                  144      6    96%   62-63, 90, 135, 234, 258
-------------------------------------------------------------------------
TOTAL                                        2045     33    98%
134 passed, 1 warning in 130.58s (0:02:10)
[exit 0]
```

The one warning is Starlette's deprecation notice for `httpx` in its TestClient (it recommends
`httpx2`); the dev dependency is `httpx` as specified. Wall time varies between runs on this
machine (62–173 s observed for similar suites).

## 3. Case-study headline results (copied from run records)

- **Run ID:** `run-20261022T083838Z-b12a4417` · **dataset ID:** `ds-20261022T083837Z-2d9c08c1` · **persisted model:**
  `model-20261022T083913Z-86d46690`
- **Dataset:** `mammography`, imbalanced-learn benchmark (Zenodo DOI 10.5281/zenodo.61452;
  licence ODC-ODbL as listed on the record). 11183 rows. Dataset SHA-256
  `eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed`.
- **Holdout:** test indices SHA-256 `ee4a3c8a3d3efbbfac7e1c20ba4c7fae2c3d9cec55bdd2101aed8a75a2a271c7`
  (8946 outer-train / 2237 test rows).
  Folds: SHA-256 `273eb075663b91f47cad5b3600106b2b8617408cc133e221ca2f251fcb6da372` (15 folds,
  stratified).
- **Sources:** `docs/case_study/run-20261022T083838Z-b12a4417/summary.json` (OOF) and `final_evaluation.json`
  (test, scored once).

| Model | Role | OOF AP (mean ± std) | OOF ROC AUC | Test AP | Test ROC AUC | Test recall @thr | Test precision @thr |
|---|---|---|---|---|---|---|---|
| `dummy_prior` | baseline | 0.0233 ± 0.0003 (n=15) | 0.5000 ± 0.0000 (n=15) | 0.0232 | 0.5000 | 1.0000 | 0.0232 |
| `logreg_balanced` | baseline | 0.5427 ± 0.0783 (n=15) | 0.9268 ± 0.0240 (n=15) | 0.4669 | 0.9167 | 0.6923 | 0.3830 |
| `hgb` | candidate | 0.7175 ± 0.0541 (n=15) | 0.9144 ± 0.0209 (n=15) | not scored | not scored | — | — |
| `hgb+random_under` | candidate | 0.6075 ± 0.0986 (n=15) | 0.9459 ± 0.0167 (n=15) | not scored | not scored | — | — |
| `hgb+smote` | candidate, **selected** | 0.7449 ± 0.0362 (n=15) | 0.9230 ± 0.0231 (n=15) | 0.6670 | 0.8917 | 0.7308 | 0.5672 |
| `random_forest` | candidate | 0.7094 ± 0.0707 (n=15) | 0.9310 ± 0.0156 (n=15) | not scored | not scored | — | — |

- **Threshold:** for `hgb+smote`, `max_fbeta` (beta=2) on OOF, median of 3 repeats =
  **0.4292** (per-repeat mean 0.4664 ± 0.0790).
- **Baseline thresholds:** each baseline is scored at its own OOF-selected threshold, using the
  same strategy.
- **Caveat found by the tool:** 632 of
  2237 test rows duplicate outer-train feature rows. In a post-hoc re-slice of the
  stored test predictions (no refit, no re-scoring, no selection), `hgb+smote`'s test AP is
  0.6670 on all rows and 0.7060 on the
  1605 non-duplicate rows. Prevalence differs between these subsets, and the check does
  not cover CV. See [docs/case_study.md](docs/case_study.md).
- **Reproducibility:** the case study was executed 3 times successfully, and the metrics and all
  three SHA-256s (dataset, folds, test) were identical each time.

## 4. End-to-end smoke test (real responses)

`python scripts/smoke_api.py` started `uvicorn imbalancelab.api.app:app` as a subprocess with a
temporary workspace. It then called `/health`, uploaded a **synthetic** CSV (used only for this
smoke test), launched a run, ran threshold analysis and final evaluation, checked that a second
final evaluation is refused (409), and fetched the report over HTTP. The output is verbatim;
long bodies are truncated by the script, and those cuts are marked `... [truncated]`.

```text
INFO:     Started server process [16628]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
INFO:     127.0.0.1:56124 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:56125 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:56126 - "POST /datasets HTTP/1.1" 201 Created
INFO:     127.0.0.1:56127 - "POST /runs HTTP/1.1" 201 Created
INFO:     127.0.0.1:56128 - "POST /runs/run-20261022T084415Z-7f7c97c5/thresholds HTTP/1.1" 200 OK
INFO:     127.0.0.1:56129 - "POST /runs/run-20261022T084415Z-7f7c97c5/final-evaluation HTTP/1.1" 200 OK
INFO:     127.0.0.1:56130 - "POST /runs/run-20261022T084415Z-7f7c97c5/final-evaluation HTTP/1.1" 409 Conflict
INFO:     127.0.0.1:56131 - "GET /runs/run-20261022T084415Z-7f7c97c5/report?format=markdown HTTP/1.1" 200 OK
INFO:     127.0.0.1:53074 - "GET /runs/run-20261022T084415Z-7f7c97c5/report HTTP/1.1" 200 OK
$ <project-root>\.venv\Scripts\python.exe -m uvicorn imbalancelab.api.app:app --host 127.0.0.1 --port 8765

### health
GET http://127.0.0.1:8765/health -> HTTP 200
content-type: application/json
{
  "status": "ok",
  "version": "0.1.0"
}

### upload synthetic CSV (SYNTHETIC DATA, smoke test only)
POST http://127.0.0.1:8765/datasets -> HTTP 201
content-type: application/json
{
  "dataset_id": "ds-20261022T084415Z-eb2f2f8a",
  "created_at": "2026-10-22T08:44:15.821142Z",
  "source_name": "synthetic_smoke.csv",
  "sha256": "482b5496836933f69aaa9deae4a16db973741aea962334ba2ce32d4d04a6ed8c",
  "n_rows": 400,
  "n_features": 3,
  "positive_rate": 0.105,
  "dataset_schema": {
    "target": "label",
    "positive_label": 1,
    "id_column": null,
    "group_column": null,
    "time_column": null,
    "expected_dtypes": {},
    "split_strategy": "stratified"
  },
  "holdout_config": {
    "test_size": 0.2,
    "gap": 0,
    "seed": 42
  },
  "n_outer_train": 320,
  "n_test": 80,
  "test_sha256": "08c01ddd4bfae01cd7b9d6d18f52e993fb4275785bd6bc53d69434aad35c81fa",
  "n_warnings": 0,
  "notes": []
}

### launch run
POST http://127.0.0.1:8765/runs -> HTTP 201
content-type: application/json
{
  "run_id": "run-20261022T084415Z-7f7c97c5",
  "status": "completed",
  "dataset_id": "ds-20261022T084415Z-eb2f2f8a",
  "created_at": "2026-10-22T08:44:15.879062Z",
  "finished_at": "2026-10-22T08:44:17.965909Z",
  "models": [
    "dummy_prior",
    "logreg_balanced",
    "hgb"
  ],
  "best_candidate_by_mean_oof_ap": "hgb",
  "has_final_evaluation": false,
  "error": null
}

### threshold analysis (OOF)
POST http://127.0.0.1:8765/runs/run-20261022T084415Z-7f7c97c5/thresholds -> HTTP 200
content-type: application/json
{
  "model": "hgb",
  "strategy": {
    "kind": "max_fbeta",
    "beta": 2.0,
    "target": null,
    "cost_fp": 1.0,
    "cost_fn": 1.0
  },
  "provenance": "oof",
  "selection_rule": "median of per-repeat thresholds selected on out-of-fold predictions",
  "chosen_threshold": 0.006795252458039416,
  "per_repeat": [
    {
      "repeat": 0,
      "n": 320,
      "threshold": 0.0024881613737451607,
      "precision": 0.17763157894736842,
      "recall": 0.7941176470588235,
      "fbeta": 0.46875,
      "expected_cost": 0.4125,
      "tp": 27,
      "fp": 125,
      "fn": 7,
      "tn": 161
    },
    {
      "repeat": 1,
      "n": 320,
      "threshold": 0.011102343542333672,
      "precision": 0.21138211382113822,
      "recall": 0.7647058823529411,
      "fbeta": 0.5019305019305019,
    
... [truncated]

### final evaluation
POST http://127.0.0.1:8765/runs/run-20261022T084415Z-7f7c97c5/final-evaluation -> HTTP 200
content-type: application/json
{
  "run_id": "run-20261022T084415Z-7f7c97c5",
  "model": "hgb",
  "evaluated_at": "2026-10-22T08:44:18.479672Z",
  "forced": false,
  "dataset_sha256": "482b5496836933f69aaa9deae4a16db973741aea962334ba2ce32d4d04a6ed8c",
  "test_sha256": "08c01ddd4bfae01cd7b9d6d18f52e993fb4275785bd6bc53d69434aad35c81fa",
  "n_outer_train": 320,
  "n_test": 80,
  "n_test_positive": 8,
  "refit_on": "outer-train rows only",
  "threshold": 0.006795252458039416,
  "threshold_provenance": {
    "source": "out-of-fold predictions",
    "strategy": {
      "kind": "max_fbeta",
      "beta": 2.0,
      "target": null,
      "cost_fp": 1.0,
      "cost_fn": 1.0
    },
    "selection_rule": "median of per-repeat thresholds selected on out-of-fold predictions",
    "analysis_created_at": "2026-10-22T08:44:18.074947Z"
... [truncated]

### second final evaluation (must be refused)
POST http://127.0.0.1:8765/runs/run-20261022T084415Z-7f7c97c5/final-evaluation -> HTTP 409
content-type: application/json
{
  "error": "final_evaluation_exists",
  "detail": "this run already has a final evaluation; the test set is scored once. Pass force=True with a reason to re-evaluate (this is logged)."
}

### report (markdown)
GET http://127.0.0.1:8765/runs/run-20261022T084415Z-7f7c97c5/report?format=markdown -> HTTP 200
content-type: text/markdown; charset=utf-8
# ImbalanceLab audit report: run run-20261022T084415Z-7f7c97c5

## 1. Verdict

- Best candidate by mean out-of-fold AP: **hgb** (selected on OOF predictions only; the test set was not used for selection).
- **hgb** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.1659, better in 6 of 6 folds (win fraction 1.00).
- **hgb** does NOT beat **logreg_balanced** on out-of-fold average precision: mean paired difference -0.1729, better in 0 of 6 folds (win fraction 0.00).
- **logreg_balanced** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.3388, better in 6 of 6 folds (win fraction 1.00).
- **hgb** beats **dummy_prior** on the test set (average_precision: 0.2124 vs 0.1000, difference +0.1124; single evaluation, no spread).
- **hgb** does NOT beat **logreg_balanced** on the test set (average_precision: 0.2124 vs 0.4605, difference -0.2482; single evaluation, no spread).

Comparisons use paired differences on identical stored folds. CV folds are correlated, so no significance test is reported; win fractions and spreads are descriptive.

## 2. Dataset

| Field | Value |
|---|---|
| Source file | synthetic_smoke.csv |
| SHA-256 | `482b5496836933f69aaa9deae4a16db973741aea962334ba2ce32d4d04a6ed8c` |
| Rows | 400 |
| Target / positive label | `label` / `1` |
| Positives / negatives | 42 / 358 |
| Positive rate | 0.1050 |
| Imbalance ratio (neg:pos) | 8.52 |
| Feature columns | 3 |
| Split strategy (schema) | stratified |

Features used: 2 numeric, 1 categorical.

## 3. Data profile warnings

No profiling heuristics fired.

Duplicates: 0 exact duplicate rows; 0 conflicting-label groups (0 rows).

## 4. Split strategy

| Field | Value |
|---|---|
| Outer holdout strategy | stratified |
| Test size (config) | 0.20 |
| Outer-train rows / test rows / gap rows | 320 / 80 / 0 |
| Test indices SHA-256 | `08c01ddd4bfae01cd7b9d6d18f52e993fb4275785bd6bc53d69434aad35c81fa` |
| Inner CV strategy | stratified |
| Folds × repeats | 3 × 2 (6 folds) |
| Fold indices SHA-256 | `36ff0a126c599f7735258dd2d38d8d48d72d672f3bbe245b4a14db1fc808ab7a` |

CV, model selection and threshold selection use outer-train rows only. All models were fit on identical stored folds.

## 5. Models

| Name | Role | Sampler | Estimator |
|---|---|---|---|
| dummy_prior | baseline | none | DummyClassifier(strategy='prior'): predicts the training prevalence |
| logreg_balanced | baseline | none | LogisticRegression(class_weight='balanced', max_iter=
... [truncated]

GET report html -> HTTP 200, 167622 chars, content-type text/html; charset=utf-8
```

## 5. `git ls-files` (at commit `91c6f54`)

```text
.gitattributes
.github/workflows/ci.yml
.gitignore
IMPLEMENTATION_PLAN.md
PROJECT_STATUS.md
README.md
REVIEW_PACKET.md
data/raw/.gitkeep
docs/case_study.md
docs/case_study/run-20261022T083838Z-b12a4417/OMITTED_FILES.json
docs/case_study/run-20261022T083838Z-b12a4417/PROVENANCE.json
docs/case_study/run-20261022T083838Z-b12a4417/config.json
docs/case_study/run-20261022T083838Z-b12a4417/dataset_sha256.txt
docs/case_study/run-20261022T083838Z-b12a4417/duplicate_sensitivity.json
docs/case_study/run-20261022T083838Z-b12a4417/environment.json
docs/case_study/run-20261022T083838Z-b12a4417/final_evaluation.json
docs/case_study/run-20261022T083838Z-b12a4417/final_evaluation_log.jsonl
docs/case_study/run-20261022T083838Z-b12a4417/final_predictions.parquet
docs/case_study/run-20261022T083838Z-b12a4417/fold_metrics.json
docs/case_study/run-20261022T083838Z-b12a4417/holdout.json
docs/case_study/run-20261022T083838Z-b12a4417/profile.json
docs/case_study/run-20261022T083838Z-b12a4417/report/figures/oof_pr.png
docs/case_study/run-20261022T083838Z-b12a4417/report/figures/oof_roc.png
docs/case_study/run-20261022T083838Z-b12a4417/report/figures/test_pr.png
docs/case_study/run-20261022T083838Z-b12a4417/report/figures/test_roc.png
docs/case_study/run-20261022T083838Z-b12a4417/report/report.html
docs/case_study/run-20261022T083838Z-b12a4417/report/report.md
docs/case_study/run-20261022T083838Z-b12a4417/run.json
docs/case_study/run-20261022T083838Z-b12a4417/summary.json
docs/case_study/run-20261022T083838Z-b12a4417/thresholds.json
frontend/README.md
frontend/api_client.py
frontend/app.py
pyproject.toml
requirements-lock.txt
runs/.gitkeep
scripts/gate.sh
scripts/run_case_study.py
scripts/smoke_api.py
src/imbalancelab/__init__.py
src/imbalancelab/api/__init__.py
src/imbalancelab/api/app.py
src/imbalancelab/api/schemas.py
src/imbalancelab/config.py
src/imbalancelab/data/__init__.py
src/imbalancelab/data/errors.py
src/imbalancelab/data/loader.py
src/imbalancelab/data/schema.py
src/imbalancelab/evaluation/__init__.py
src/imbalancelab/evaluation/config.py
src/imbalancelab/evaluation/final.py
src/imbalancelab/evaluation/metrics.py
src/imbalancelab/evaluation/runner.py
src/imbalancelab/evaluation/thresholds.py
src/imbalancelab/models/__init__.py
src/imbalancelab/models/persistence.py
src/imbalancelab/models/registry.py
src/imbalancelab/pipelines/__init__.py
src/imbalancelab/pipelines/builder.py
src/imbalancelab/profiling/__init__.py
src/imbalancelab/profiling/profile.py
src/imbalancelab/profiling/warnings.py
src/imbalancelab/reporting/__init__.py
src/imbalancelab/reporting/figures.py
src/imbalancelab/reporting/render.py
src/imbalancelab/reporting/report.py
src/imbalancelab/splitting/__init__.py
src/imbalancelab/splitting/duplicates.py
src/imbalancelab/splitting/splits.py
src/imbalancelab/tracking/__init__.py
src/imbalancelab/tracking/records.py
src/imbalancelab/workflow.py
tests/conftest.py
tests/snapshots/report_structure.md
tests/test_api.py
tests/test_data_loader.py
tests/test_frontend.py
tests/test_metrics.py
tests/test_persistence.py
tests/test_pipelines.py
tests/test_profiling.py
tests/test_readme.py
tests/test_reporting.py
tests/test_runner.py
tests/test_smoke.py
tests/test_splitting.py
tests/test_thresholds_final.py
```

## 6. Deviations, limitations, and environment-blocked steps

### Deviations from instructions
- **T0:** `tree` is not installed, so `find` was used for the directory listing. The commit
  messages carry a `Co-Authored-By` trailer.
- **D4:** mypy no longer pins `python_version = "3.11"`, because numpy 2.5 stubs use 3.12
  syntax. CI's 3.11 job checks against numpy 2.4.
- **D11:** constant scores keep AP and ROC AUC *defined* (chance level, with a `note`), because
  the prior Dummy baseline's AP must equal the prevalence. MCC and precision become undefined as
  appropriate.
- **D8:** temporal CV forces `n_repeats=1` (recorded as an info warning). The temporal gap is
  counted in distinct time values.
- **D19:** `POST /models/{id}/predict` existed from M7 but returned 404 until M9 implemented
  persistence.
- **D25:** a post-hoc duplicate sensitivity check was added to the case study, beyond the spec.
  It re-slices stored test predictions only.
- **D26:** two case-study run-record files over 1 MB (`fold_indices.json`,
  `oof_predictions.parquet`) are not committed. Their SHA-256s are in `OMITTED_FILES.json`.
- **Line endings:** exported case-study JSON files were written with CRLF on Windows and
  committed with LF (`.gitattributes` `eol=lf`). The recorded dataset, fold and test SHA-256s
  are computed on the dataset file and the index lists, not on these exported copies, so they
  are unaffected.

### Test fixes during development (no assertion weakened)
- **M1:** a test expected only one pure category. The code correctly also flagged two
  all-negative categories, so the test now asserts all three (stricter).
- **M2:** a test helper used `astype(str)`, which keeps NaN under pandas 3. The helper key was
  fixed, and the assertions are unchanged.
- **M6:** the snapshot test masks numbers and the verdict words. Numeric correctness is covered
  by a separate traceability test.

### Bugs found and fixed by self-review
- **M7 → M8:** the unanchored `.gitignore` pattern `models/` would have ignored
  `src/imbalancelab/models/`. It was anchored (`/models/`) and verified with `git check-ignore`
  before any file was lost.
- **M10:** `run.json` recorded the workspace file name instead of the uploaded name. It was
  fixed and covered by a test.

### Limitations
- Binary targets only. Small fixed model configs, with no hyperparameter search. Probabilities
  are not calibrated.
- The API is synchronous, with no job queue, auth or database. It is meant for local,
  single-user use.
- Datetime features are dropped rather than encoded. SMOTE interpolates one-hot columns
  (SMOTENC not used).
- Test results are single evaluations with no spread. CV comparisons are descriptive (no
  significance tests, by design).
- joblib artifacts are pickles. Their SHA-256 is checked before loading, which protects only
  against replaced files.
- The case study uses one dataset and one split. Its pre-specified stratified protocol is not
  duplicate-aware, and a duplicate-grouped re-run was not done.

### Environment-blocked or unverified
- **CI never executed.** `.github/workflows/ci.yml` is defined, but the repository has no
  remote, so it has not run. Python 3.11 compatibility is therefore **untested**: every local
  run used Python 3.13.5.
- **Network:** available. The case-study download (Zenodo archive, 42.5 MB) succeeded, so no
  step was blocked.

## 7. Ready for review

All milestone gates passed. The final gate in section 2 was run on the last milestone commit.
Nothing is marked `verified`; the work is ready for supervisor review.
