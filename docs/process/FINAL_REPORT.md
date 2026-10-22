# ImbalanceLab: final report (revised after supervisor reviews T-R1, T-R2 and T-R3)

**Prepared by:** Implementation Engineer · **Date:** 2026-10-23 · **For:** supervisor review

Milestones M0–M10 and review tasks T-R1–T-R3 are implemented and committed. **Nothing is marked
`verified`**: that is for the supervisor. Per-task evidence is in
[REVIEW_PACKET.md](REVIEW_PACKET.md), and decisions D1–D35 and known issues are in
[PROJECT_STATUS.md](PROJECT_STATUS.md). The process records now live in `docs/process/` (D35).

## 1. Milestones and commits

| Milestone | Scope | Status | Commit |
|---|---|---|---|
| M0 | Skeleton, tooling, plan | done | `03ead06` |
| — | Part A: invariant 7, lock, CI, pyarrow | applied | `5fbb139` |
| M1 | Data loading, schema validation, profiling | done | `fdc15f3` |
| M2 | Outer holdout, inner CV, duplicates, pipeline builder | done | `d906960` |
| M3 | Metrics with explicit undefined cases | done | `58c6241` |
| M4 | Runner, baselines, run records | done | `9e207a5` |
| M5 | OOF thresholds + one-shot final evaluation | done | `7ce0891` |
| M6 | Audit report | done | `68a5647` |
| M7 | FastAPI | done | `a9ff54e` |
| M8 | Streamlit frontend | done | `45706fc` |
| M9 | Persistence + inference | done | `b250b9a` |
| M10 | Docs + case study | done (not verified; revised in T-R1–T-R3) | `91c6f54` |
| T-R1 | Supervisor review fixes | done | `e727ca4` |
| T-R2 | CIs, coverage, cluster analysis, disclosures | done | `01a9d51` |
| T-R3 | GitHub CI, calibration disclosure, paired bootstrap, tidy | done | `f96c85a` |

```text
$ git log --oneline
f96c85a T-R3: calibration disclosure, paired bootstrap, recall scope, httpx2, process docs moved
573b2ba T-R2: review packet entry and regenerated final report
01a9d51 T-R2: bootstrap CIs, evaluation coverage, cluster analysis, protocol history, ODbL notices
924b401 T-R1: review packet entry and revised final report
e727ca4 T-R1: duplicate-aware splitting, honest two-run case study, RF determinism, UI evidence
855c023 Final report for supervisor review
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

This report and the T-R3 REVIEW_PACKET entry are committed after the log above.

## 2. CI and gates on commit `f96c85a`

### GitHub Actions (private repository `jaswantraj969/imbalancelab`)

Run: https://github.com/jaswantraj969/imbalancelab/actions/runs/39841242556 on commit `f96c85a`. Overall conclusion: **success**.

| Job | Result |
|---|---|
| checks (3.13) | **success** |
| checks (3.11) | **success** |

### Local gate, Python 3.13.5 (`.venv`, verbatim)

```text
$ python --version
Python 3.13.5

$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
70 files already formatted
[exit 0]

$ mypy
Success: no issues found in 45 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
src\imbalancelab\__init__.py                     2      0   100%
src\imbalancelab\api\__init__.py                 0      0   100%
src\imbalancelab\api\app.py                    115      0   100%
src\imbalancelab\api\schemas.py                 49      0   100%
src\imbalancelab\config.py                      15      1    93%   27
src\imbalancelab\data\__init__.py                4      0   100%
src\imbalancelab\data\errors.py                 21      0   100%
src\imbalancelab\data\loader.py                143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                 40      0   100%
src\imbalancelab\evaluation\__init__.py          2      0   100%
src\imbalancelab\evaluation\calibration.py      33      1    97%   48
src\imbalancelab\evaluation\config.py           35      0   100%
src\imbalancelab\evaluation\final.py           146      6    96%   85-86, 113, 171, 274, 312
src\imbalancelab\evaluation\metrics.py         115      0   100%
src\imbalancelab\evaluation\runner.py          143      0   100%
src\imbalancelab\evaluation\thresholds.py      138      0   100%
src\imbalancelab\evaluation\uncertainty.py     111      1    99%   61
src\imbalancelab\models\__init__.py              2      0   100%
src\imbalancelab\models\persistence.py         100      0   100%
src\imbalancelab\models\registry.py             18      0   100%
src\imbalancelab\pipelines\__init__.py           2      0   100%
src\imbalancelab\pipelines\builder.py           66      0   100%
src\imbalancelab\profiling\__init__.py           3      0   100%
src\imbalancelab\profiling\profile.py          169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py           9      0   100%
src\imbalancelab\reporting\__init__.py           2      0   100%
src\imbalancelab\reporting\figures.py           65      2    97%   28, 84
src\imbalancelab\reporting\render.py            82      0   100%
src\imbalancelab\reporting\report.py           226     10    96%   60, 95, 124, 181, 184, 264, 294, 515, 593, 639
src\imbalancelab\splitting\__init__.py           3      0   100%
src\imbalancelab\splitting\coverage.py          40      2    95%   34-35
src\imbalancelab\splitting\duplicates.py        24      0   100%
src\imbalancelab\splitting\groups.py            79      1    99%   64
src\imbalancelab\splitting\splits.py           251      2    99%   117, 123
src\imbalancelab\tracking\__init__.py            2      0   100%
src\imbalancelab\tracking\records.py           120      3    98%   89-90, 170
src\imbalancelab\workflow.py                   149      6    96%   63-64, 91, 136, 236, 262
--------------------------------------------------------------------------
TOTAL                                         2524     43    98%
166 passed in 201.78s (0:03:21)
[exit 0]
```

### Local gate, Python 3.11.15 (`.venv311`, verbatim)

```text
$ python --version
Python 3.11.15

$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
70 files already formatted
[exit 0]

$ mypy
Success: no issues found in 45 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.11.15-final-0 _______________

Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
src\imbalancelab\__init__.py                     2      0   100%
src\imbalancelab\api\__init__.py                 0      0   100%
src\imbalancelab\api\app.py                    115      0   100%
src\imbalancelab\api\schemas.py                 49      0   100%
src\imbalancelab\config.py                      15      1    93%   27
src\imbalancelab\data\__init__.py                4      0   100%
src\imbalancelab\data\errors.py                 21      0   100%
src\imbalancelab\data\loader.py                143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                 40      0   100%
src\imbalancelab\evaluation\__init__.py          2      0   100%
src\imbalancelab\evaluation\calibration.py      33      1    97%   48
src\imbalancelab\evaluation\config.py           35      0   100%
src\imbalancelab\evaluation\final.py           146      6    96%   85-86, 113, 171, 274, 312
src\imbalancelab\evaluation\metrics.py         115      0   100%
src\imbalancelab\evaluation\runner.py          143      0   100%
src\imbalancelab\evaluation\thresholds.py      138      0   100%
src\imbalancelab\evaluation\uncertainty.py     111      1    99%   61
src\imbalancelab\models\__init__.py              2      0   100%
src\imbalancelab\models\persistence.py         100      0   100%
src\imbalancelab\models\registry.py             18      0   100%
src\imbalancelab\pipelines\__init__.py           2      0   100%
src\imbalancelab\pipelines\builder.py           66      0   100%
src\imbalancelab\profiling\__init__.py           3      0   100%
src\imbalancelab\profiling\profile.py          169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py           9      0   100%
src\imbalancelab\reporting\__init__.py           2      0   100%
src\imbalancelab\reporting\figures.py           65      2    97%   28, 84
src\imbalancelab\reporting\render.py            82      0   100%
src\imbalancelab\reporting\report.py           226     10    96%   60, 95, 124, 181, 184, 264, 294, 515, 593, 639
src\imbalancelab\splitting\__init__.py           3      0   100%
src\imbalancelab\splitting\coverage.py          40      2    95%   34-35
src\imbalancelab\splitting\duplicates.py        24      0   100%
src\imbalancelab\splitting\groups.py            79      1    99%   64
src\imbalancelab\splitting\splits.py           251      2    99%   117, 123
src\imbalancelab\tracking\__init__.py            2      0   100%
src\imbalancelab\tracking\records.py           120      3    98%   89-90, 170
src\imbalancelab\workflow.py                   149      6    96%   63-64, 91, 136, 236, 262
--------------------------------------------------------------------------
TOTAL                                         2524     43    98%
166 passed in 208.23s (0:03:28)
[exit 0]
```

## 3. Case-study headline (run b: duplicate-aware split)

- **Run (b):** `run-20261022T092013Z-2056207e` in `docs/case_study/b_duplicate_groups/`.
- **Dataset:** `mammography` (Zenodo DOI 10.5281/zenodo.61452, ODbL). Dataset SHA-256
  `eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed`.
- **Split:** no duplicate cluster crosses any boundary (cross-boundary duplicates: 0 test rows,
  0 folds).
- **Evaluation coverage WARNING:** 3329 rows (29.8%,
  7 positives) are forced to train and never evaluated.

**Selected `hgb+smote`: test AP 0.8228 [0.7383, 0.8977]** (scored once) on 1964 test rows,
63 positives. The 95% CIs come from a stratified bootstrap (2000
resamples, seed 42).

| Model | Role | OOF AP: selection estimate (optimistic) | Test AP [95% CI] | Test Brier [95% CI] |
|---|---|---|---|---|
| `dummy_prior` | baseline | 0.0323 ± 0.0000 (n=15) | 0.0321 [0.0321, 0.0321] | 0.0312 [0.0312, 0.0312] |
| `logreg_balanced` | baseline | 0.5681 ± 0.0932 (n=15) | 0.5023 [0.3926, 0.6442] | 0.1182 [0.1101, 0.1267] |
| `hgb` | candidate | 0.7295 ± 0.0589 (n=15) | not scored | not scored |
| `hgb+random_under` | candidate | 0.5465 ± 0.0694 (n=15) | not scored | not scored |
| `hgb+smote` | candidate, **selected** | 0.7515 ± 0.0611 (n=15) | 0.8228 [0.7383, 0.8977] | 0.0181 [0.0135, 0.0231] |
| `random_forest` | candidate | 0.7292 ± 0.0635 (n=15) | not scored | not scored |

Paired bootstrap, `hgb+smote` − baseline (same resampled test rows):

| Baseline | Metric | Difference [95% CI] | Win fraction |
|---|---|---|---|
| `dummy_prior` | average_precision | +0.7907 [+0.7062, +0.8657] | 1.000 |
| `dummy_prior` | roc_auc | +0.4589 [+0.4180, +0.4889] | 1.000 |
| `logreg_balanced` | average_precision | +0.3205 [+0.2078, +0.4115] | 1.000 |
| `logreg_balanced` | roc_auc | +0.0364 [-0.0025, +0.0791] | 0.962 |

The OOF selection estimate (0.7515) lies **inside** the
test AP 95% CI [0.7383, 0.8977]; the two are consistent. This is not a claim that test performance exceeds CV performance.

### Threshold (run b, selected model)

- **Strategy:** `max_fbeta` with beta=2.0, median of the
  per-repeat thresholds (D15, commit `7ce0891`).
- **Chosen threshold:** **0.6036**. Per-repeat:
  0.6036, 0.5170, 0.6796.

| Precision | Recall | F-beta (beta=2) | MCC | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| 0.6049 [0.5238, 0.7000] | 0.7778 [0.6667, 0.8730] | 0.7357 [0.6476, 0.8187] | 0.6743 [0.5930, 0.7531] | 49 | 32 | 14 | 1869 |

**Recall scope:** the forced-to-train cluster scores below the threshold, so all 3329
of its rows are classified negative and its 7 positives would be missed. Test
recall describes evaluated rows only.

### Calibration disclosure (as rendered in the run (b) report)

- **Scores from models trained with a resampler (`hgb+random_under`, `hgb+smote`) are ranking scores, NOT calibrated probabilities. Resampling changes the class balance seen during training, so these scores do not estimate the probability of the positive class. Do not interpret them as risk.**
- **Class-weighted models (`logreg_balanced`, `random_forest`) also shift scores away from the training prevalence.**

### Duplicate-leakage comparison (different test sets)

| | (a) stratified | (b) duplicate groups |
|---|---|---|
| Test rows duplicating outer-train rows | 632 | 0 |
| Selected-model test AP [95% CI] | 0.6670 [0.5404, 0.7908] (2237 rows, 52 pos) | 0.8228 [0.7383, 0.8977] (1964 rows, 63 pos) |

Full tables, caveats, the data-quality finding and the protocol history are in
[docs/case_study.md](../case_study.md).

### No test set re-scored in T-R3 (stored-prediction hashes)

```text
$ sha256sum -c preds_before_r3.txt
runs/case_study/runs/run-20261022T091904Z-596af186/final_predictions.parquet: OK
runs/case_study/runs/run-20261022T092013Z-2056207e/final_predictions.parquet: OK
docs/case_study/a_stratified/final_predictions.parquet: OK
docs/case_study/b_duplicate_groups/final_predictions.parquet: OK
```

### Hash-regeneration check

```text
$ python scripts/verify_case_study_hashes.py
a_stratified: run run-20261022T091904Z-596af186
  [OK] dataset sha256: eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed
  [OK] test-index sha256: ee4a3c8a3d3efbbfac7e1c20ba4c7fae2c3d9cec55bdd2101aed8a75a2a271c7
  [OK] fold-index canonical sha256: 273eb075663b91f47cad5b3600106b2b8617408cc133e221ca2f251fcb6da372
  [OK] fold_indices.json file sha256: 08f33088e508526127d5e886bfc98cb7aed2cf777a17ec3aeee67b734583733b
  [OK] oof_predictions.parquet file sha256: b30cbcdfec258860e48b80e66a0a46d42191aba937e7206763d458fa75e6b361
  [OK] summary.json content: f29ba9ba182453ffdd29e2963b050c60d361d829658ad4844acab68969a33ed7
b_duplicate_groups: run run-20261022T092013Z-2056207e
  [OK] dataset sha256: eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed
  [OK] test-index sha256: 7ee8afda21eac8e55d32cec3c391e8d48d7034924747d626e357f536c5ebdd89
  [OK] fold-index canonical sha256: f59d5586847fafdfbb5f7ea5f808783f63a2ac15f918acdf1c14aa3716e8ffd0
  [OK] fold_indices.json file sha256: 106649ffae70a01601dbb1c4c8f47d284b700e7d3cf9726f321d03c21b66dd17
  [OK] summary.json content: 8c952d75f52a384b561116037725b85bde83029327d534a1eb6cff2ca7e5be9a
ALL CHECKS PASSED
```

## 4. `git ls-files` (at `f96c85a`)

```text
.gitattributes
.github/workflows/ci.yml
.gitignore
README.md
data/raw/.gitkeep
docs/case_study.md
docs/case_study/a_stratified/NOTICE.md
docs/case_study/a_stratified/OMITTED_FILES.json
docs/case_study/a_stratified/PROVENANCE.json
docs/case_study/a_stratified/config.json
docs/case_study/a_stratified/dataset_sha256.txt
docs/case_study/a_stratified/duplicate_sensitivity.json
docs/case_study/a_stratified/environment.json
docs/case_study/a_stratified/final_evaluation.json
docs/case_study/a_stratified/final_evaluation_log.jsonl
docs/case_study/a_stratified/final_predictions.parquet
docs/case_study/a_stratified/fold_metrics.json
docs/case_study/a_stratified/holdout.json
docs/case_study/a_stratified/profile.json
docs/case_study/a_stratified/report/figures/oof_pr.png
docs/case_study/a_stratified/report/figures/oof_roc.png
docs/case_study/a_stratified/report/figures/test_pr.png
docs/case_study/a_stratified/report/figures/test_reliability.png
docs/case_study/a_stratified/report/figures/test_roc.png
docs/case_study/a_stratified/report/report.html
docs/case_study/a_stratified/report/report.md
docs/case_study/a_stratified/run.json
docs/case_study/a_stratified/summary.json
docs/case_study/a_stratified/thresholds.json
docs/case_study/b_duplicate_groups/NOTICE.md
docs/case_study/b_duplicate_groups/OMITTED_FILES.json
docs/case_study/b_duplicate_groups/PROVENANCE.json
docs/case_study/b_duplicate_groups/config.json
docs/case_study/b_duplicate_groups/dataset_sha256.txt
docs/case_study/b_duplicate_groups/duplicate_sensitivity.json
docs/case_study/b_duplicate_groups/environment.json
docs/case_study/b_duplicate_groups/final_evaluation.json
docs/case_study/b_duplicate_groups/final_evaluation_log.jsonl
docs/case_study/b_duplicate_groups/final_predictions.parquet
docs/case_study/b_duplicate_groups/fold_metrics.json
docs/case_study/b_duplicate_groups/holdout.json
docs/case_study/b_duplicate_groups/oof_predictions.parquet
docs/case_study/b_duplicate_groups/profile.json
docs/case_study/b_duplicate_groups/report/figures/oof_pr.png
docs/case_study/b_duplicate_groups/report/figures/oof_roc.png
docs/case_study/b_duplicate_groups/report/figures/test_pr.png
docs/case_study/b_duplicate_groups/report/figures/test_reliability.png
docs/case_study/b_duplicate_groups/report/figures/test_roc.png
docs/case_study/b_duplicate_groups/report/report.html
docs/case_study/b_duplicate_groups/report/report.md
docs/case_study/b_duplicate_groups/run.json
docs/case_study/b_duplicate_groups/summary.json
docs/case_study/b_duplicate_groups/thresholds.json
docs/process/FINAL_REPORT.md
docs/process/IMPLEMENTATION_PLAN.md
docs/process/PROJECT_STATUS.md
docs/process/REVIEW_PACKET.md
docs/screenshots/01_upload_and_profile.png
docs/screenshots/02_run_experiment.png
docs/screenshots/03_results_and_thresholds.png
docs/screenshots/04_final_evaluation.png
docs/screenshots/05_final_evaluation_refused.png
docs/screenshots/06_report.png
docs/screenshots/ui_check.json
frontend/README.md
frontend/api_client.py
frontend/app.py
pyproject.toml
requirements-lock.txt
runs/.gitkeep
scripts/check_committed_files.py
scripts/check_links.py
scripts/gate.sh
scripts/run_case_study.py
scripts/smoke_api.py
scripts/ui_screenshots.py
scripts/verify_case_study_hashes.py
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
src/imbalancelab/evaluation/calibration.py
src/imbalancelab/evaluation/config.py
src/imbalancelab/evaluation/final.py
src/imbalancelab/evaluation/metrics.py
src/imbalancelab/evaluation/runner.py
src/imbalancelab/evaluation/thresholds.py
src/imbalancelab/evaluation/uncertainty.py
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
src/imbalancelab/splitting/coverage.py
src/imbalancelab/splitting/duplicates.py
src/imbalancelab/splitting/groups.py
src/imbalancelab/splitting/splits.py
src/imbalancelab/tracking/__init__.py
src/imbalancelab/tracking/records.py
src/imbalancelab/workflow.py
tests/conftest.py
tests/snapshots/report_structure.md
tests/test_api.py
tests/test_calibration_paired.py
tests/test_data_loader.py
tests/test_duplicate_groups.py
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
tests/test_uncertainty.py
```

## 5. Deviations, limitations, open items

- **Deviations:** D27 (connected-components merge), D28 (oversized groups pinned), D29 (RF
  `n_jobs=1`), D30 (amend, not re-score), D32 (calibration disclosed, not fixed), D34 (`httpx2`
  added to dev extras), D35 (process docs moved).
- **Limitations:** binary targets only; small fixed configs; scores not calibrated; synchronous
  API with no auth; one case-study dataset with single test draws; pinned groups are not
  evaluated; joblib artifacts are pickles (SHA-256 checked).
- **Open items:** none. Supervisor verification is pending.
