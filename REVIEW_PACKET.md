# Review Packet

The Implementation Engineer fills in one entry per task, appended in order (oldest first), by copying the template
below. Paste command output in full. Do not summarise it. Only the supervisor marks a milestone
`verified`.

## Template

```markdown
### Task <ID> — <title>

**Date:** YYYY-MM-DD
**Milestone(s):** Mx

#### Summary of changes
- ...

#### Files changed
- path — added / modified / deleted

#### Exact commands run
    <command 1>
    <command 2>

#### Full test output
    <verbatim pytest output>

#### Lint output
    <verbatim ruff check / ruff format --check / mypy output>

#### Deviations from instructions
- ... (or "None")

#### Known limitations
- ...

#### Open questions
- ...
```

---

### Task T0 — Project skeleton, tooling, and implementation plan

**Date:** 2026-10-22
**Milestone(s):** M0

#### Summary of changes
- Created an installable src-layout package `imbalancelab` (version 0.1.0) with nine empty
  subpackages: data, profiling, splitting, pipelines, models, evaluation, tracking, reporting,
  and api. Each `__init__.py` contains only a docstring naming the milestone it belongs to.
- `config.py`: a pydantic-settings `Settings` class with `data_dir`, `raw_data_dir`, `runs_dir`,
  and `seed=42`. Values can be overridden through `IMBALANCELAB_*` environment variables or
  `.env`.
- `pyproject.toml`: runtime dependencies plus the `[dev]` and `[ui]` extras, each with a
  compatible range of the form `>=lower,<next-major`. It also holds the ruff configuration
  (line-length 100; rules E, F, W, I, B, UP, SIM), the pytest configuration (`testpaths=tests`,
  `-ra`), and a non-strict mypy configuration.
- Smoke tests check `__version__`, the import of each subpackage (parametrised, 9 cases), and the
  default seed.
- Project records: `IMPLEMENTATION_PLAN.md` (milestones M0–M10, methodology invariants, Not in
  MVP), `PROJECT_STATUS.md`, and this packet.
- `.gitignore`, `README.md`, a placeholder `frontend/README.md`, and `data/raw/.gitkeep` and
  `runs/.gitkeep`.

#### Files changed (all added)
- .gitignore
- pyproject.toml
- README.md
- IMPLEMENTATION_PLAN.md
- PROJECT_STATUS.md
- REVIEW_PACKET.md
- src/imbalancelab/__init__.py
- src/imbalancelab/config.py
- src/imbalancelab/{data,profiling,splitting,pipelines,models,evaluation,tracking,reporting,api}/__init__.py
- frontend/README.md
- tests/conftest.py
- tests/test_smoke.py
- data/raw/.gitkeep
- runs/.gitkeep

#### Exact commands run
All commands were run in Git Bash on Windows 11 from the project root.

    python -m venv .venv
    source .venv/Scripts/activate
    python -m pip install -q --upgrade pip
    pip install -e ".[dev,ui]"          # exit 0
    ruff check .
    ruff format --check .
    pytest -q
    mypy
    python --version
    pip freeze | grep -iE "scikit|imbalanced|fastapi|pandas|numpy"
    find . -maxdepth 3 -not -path "./.venv*" -not -path "*__pycache__*" \
        -not -path "./.*_cache*" -not -path "*.egg-info*" | sort
    git init
    git add -A
    git commit -m "T0: project skeleton, tooling, plan"

Last line of `pip install -e ".[dev,ui]"`:

    Successfully installed MarkupSafe-3.0.4 altair-6.3.0 annotated-doc-0.0.5 annotated-types-0.8.0 anyio-4.15.1 attrs-26.1.0 certifi-2026.10.19 charset_normalizer-3.5.2 click-8.5.0 cloudpickle-3.1.2 colorama-0.4.6 contourpy-1.4.0 coverage-7.16.2 cycler-0.12.1 fastapi-0.159.1 fonttools-4.67.0 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 imbalanced-learn-0.14.2 imbalancelab-0.1.0 iniconfig-2.3.1 itsdangerous-2.2.0 jinja2-3.1.6 joblib-1.6.0 jsonschema-4.26.0 jsonschema-specifications-2025.9.1 kiwisolver-1.5.1 librt-0.16.0 matplotlib-3.11.2 mypy-1.20.2 mypy_extensions-1.1.0 narwhals-2.27.1 numpy-2.5.4 opentelemetry-api-1.45.1 packaging-26.3 pandas-3.0.6 pathspec-1.1.1 pillow-13.0.0 pluggy-1.7.0 protobuf-7.36.2 pyarrow-26.0.0 pydantic-2.14.1 pydantic-core-2.50.1 pydantic-settings-2.16.1 pydeck-0.9.3 pygments-2.21.0 pyparsing-3.3.3 pytest-9.1.1 pytest-cov-7.1.0 python-dateutil-3.0.0 python-dotenv-1.2.4 python-multipart-0.0.32 referencing-0.37.0 requests-2.34.2 rpds-py-2026.9.1 ruff-0.17.1 scikit-learn-1.9.1 scipy-1.18.1 six-1.17.0 sklearn-compat-0.1.6 starlette-1.9.0 streamlit-1.66.1 threadpoolctl-3.7.0 typing-extensions-4.16.0 typing-inspection-0.4.4 tzdata-2026.5 urllib3-2.8.0 uvicorn-0.54.0 watchdog-6.0.0 websockets-17.3

Environment:

    $ python --version
    Python 3.13.5
    $ pip freeze | grep -iE "scikit|imbalanced|fastapi|pandas|numpy"
    fastapi==0.159.1
    imbalanced-learn==0.14.2
    numpy==2.5.4
    pandas==3.0.6
    scikit-learn==1.9.1

#### Full test output

    $ pytest -q
    ...........                                                              [100%]
    11 passed in 0.49s

There were 11 tests: 1 version test, 9 subpackage-import tests, and 1 seed test. None were
skipped.

#### Lint output

    $ ruff check .
    All checks passed!
    $ ruff format --check .
    16 files already formatted
    $ mypy
    Success: no issues found in 11 source files

#### Deviations from instructions
- **Project root:** the spec shows the root as `imbalancelab/`. The existing workspace folder
  `ImbalanceLab/` was used as that root, and no nested folder was created.
- **`tree -L 3 -I '.venv|__pycache__'`:** `tree` is not installed in Git Bash on this machine.
  The `find` command listed above, with equivalent exclusions and depth 3, was used instead.
- **Commit message:** the subject is exactly `T0: project skeleton, tooling, plan`. A
  `Co-Authored-By` trailer was appended, following the tool attribution convention in this
  environment.
- **Python version:** the local interpreter is 3.13.5, while the project declares `>=3.11`.
  Installation was not tested on 3.11 or 3.12.
- **Additions:** `mypy` was also run (it was configured but not required), and `conftest.py`
  includes an autouse fixture that clears `IMBALANCELAB_*` environment variables so the
  developer's shell does not leak into tests.

#### Known limitations
- No lock file. Dependencies are given as ranges only, so the exact versions installed are those
  recorded above.
- The `pandas<4` and `numpy<3` upper bounds allow the major versions just released (pandas
  3.0.6, numpy 2.5.4). Their compatibility with code still to be written is unverified.
- No CI configuration. Checks were run only locally.

#### Open questions
- Should a lock file (for example `pip-compile` / `uv lock`) be added for reproducibility of the
  run records in M4?
- Should CI (for example GitHub Actions on 3.11 and 3.13) be part of M0 or deferred?
- The git commit hash cannot be written into the commit that contains it. `git log --oneline` is
  reported in the hand-off message instead.

---

### Task M1 — Data loading, schema validation, profiling

**Date:** 2026-10-22 · **Milestone:** M1 · **Preceded by:** commit `5fbb139` (Part A plan
amendments: invariant 7, M2/M4/M5 amendments, pyarrow, `requirements-lock.txt`, CI workflow)

#### Summary of changes
- `data/schema.py`: `DatasetSchema` (pydantic, `extra="forbid"`): `target`, `positive_label`,
  optional `id_column` / `group_column` / `time_column`, `expected_dtypes`
  (numeric/categorical/datetime/boolean), and `split_strategy` (stratified/group/temporal).
  Validates that group/temporal strategies name their column and that special columns are
  distinct.
- `data/loader.py`: `load_dataset(path, schema)` for CSV and Parquet. Computes the SHA-256 of the
  file bytes. Raises custom errors (`data/errors.py`) for an unsupported format, empty data,
  missing columns, a NaN target, a non-binary target, an absent positive label, and dtype
  mismatches. The positive label falls back to string comparison, which is recorded in
  `positive_label_coerced` and `notes`. Binary `y` (int8) is derived without modifying the
  target column. Integer codes declared categorical become strings, and datetime strings are
  parsed; both conversions are recorded in notes.
- `profiling/profile.py`: `profile_dataset` returns a JSON-serialisable `DatasetProfile`. It covers:
  - class balance
  - per-column missingness and cardinality
  - exact duplicates (ignoring the ID column) and conflicting-label duplicates
  - constant, near-constant and all-missing columns, and high missingness
  - ID-like columns (near-unique non-float values, or monotonic unique integers)
  - target-leak suspects: univariate AUC ≥ threshold (NaNs dropped and counted), pure
    high-support categories (purity is flagged only when its probability under the base rate is
    below `pure_category_max_chance`), and name matches with the target.
- Every heuristic is a `ProfileWarning(code, column, severity, message, evidence)`, worded
  "suspected" or "possible", with the triggering statistic in `evidence`. Thresholds are
  configurable through `ProfileThresholds`.
- `scripts/gate.sh` runs the milestone gate and prints real output. `.gitattributes` enforces LF
  line endings, so snapshot tests behave the same on every OS.

#### Files changed
- added: `src/imbalancelab/data/{schema,errors,loader}.py`,
  `src/imbalancelab/profiling/{profile,warnings}.py`, `tests/test_data_loader.py`,
  `tests/test_profiling.py`, `scripts/gate.sh`, `.gitattributes`
- modified: `src/imbalancelab/data/__init__.py`, `src/imbalancelab/profiling/__init__.py`
  (re-exports), `tests/conftest.py` (CSV fixture and a synthetic-frame helper),
  `pyproject.toml` (mypy `python_version` removed, see D4), `PROJECT_STATUS.md`,
  `REVIEW_PACKET.md`

#### Exact commands run
    source .venv/Scripts/activate
    pytest -q -x                      # first run: 1 failure, a test bug (see Deviations)
    ruff format .                     # 2 files reformatted
    bash scripts/gate.sh              # output below

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
21 files already formatted
[exit 0]

$ mypy
Success: no issues found in 16 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
....................................                                     [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                      Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------
src\imbalancelab\__init__.py                  2      0   100%
src\imbalancelab\api\__init__.py              0      0   100%
src\imbalancelab\config.py                   12      1    92%   24
src\imbalancelab\data\__init__.py             4      0   100%
src\imbalancelab\data\errors.py              21      0   100%
src\imbalancelab\data\loader.py             143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py              37      0   100%
src\imbalancelab\evaluation\__init__.py       0      0   100%
src\imbalancelab\models\__init__.py           0      0   100%
src\imbalancelab\pipelines\__init__.py        0      0   100%
src\imbalancelab\profiling\__init__.py        3      0   100%
src\imbalancelab\profiling\profile.py       169      5    97%   83, 85, 301, 341, 363
src\imbalancelab\profiling\warnings.py        9      0   100%
src\imbalancelab\reporting\__init__.py        0      0   100%
src\imbalancelab\splitting\__init__.py        0      0   100%
src\imbalancelab\tracking\__init__.py         0      0   100%
-----------------------------------------------------------------------
TOTAL                                       400     11    97%
36 passed in 2.93s
[exit 0]
```

#### Invariant re-check
- 1–3 and 7: M1 contains no fitting, resampling, or thresholding. The profile is descriptive
  only, is never used to fit a model, and its results do not feed model selection.
- 5: the dataset SHA-256 is computed from the file bytes, ready to be recorded by runs (M4).
- 6: no metrics are produced.

#### Deviations from instructions
- **First test run (1 failure):** `test_target_leak_suspects_are_warnings_with_evidence` expected
  the first pure-category warning to be category "P". The code also, correctly, flagged
  categories "A" and "B" (about 90 all-negative rows each; chance 0.9^90 ≈ 7.6e-5 < 1e-4). I
  fixed the test to look up warnings by category and to assert that A is flagged with its chance
  probability. This makes the assertion stricter, not looser.
- **Profiling scope:** the profile is computed on the full dataset, before the outer holdout,
  because it is descriptive. See D5.

#### Known limitations
- Univariate AUC leak detection covers numeric and boolean features only. Categorical columns use
  the pure-category check, and datetime features are skipped.
- Duplicate detection hashes rows with `pandas.util.hash_pandas_object`. Collisions are
  theoretically possible but negligible.

---

### Task M2 — Splitting and leakage-safe pipeline builder

**Date:** 2026-10-22 · **Milestone:** M2

#### Summary of changes
- `splitting/splits.py`:
  - `make_holdout` builds the outer train/test holdout for each strategy:
    - stratified: per-class sampling with a seeded RNG
    - group: the first fold of `StratifiedGroupKFold`
    - temporal: the last ~`test_size` fraction of distinct time values, with an optional `gap`
      of excluded distinct time values
  - `Holdout` stores the train, test and gap indices, the dataset SHA-256, and the test-index
    SHA-256.
  - `get_or_create_holdout` creates the holdout once per dataset. It reuses the stored one only
    when the dataset SHA, strategy and config all match and the stored test hash verifies;
    otherwise it raises `HoldoutMismatchError`.
  - `make_cv_folds` builds inner CV on outer-train rows only:
    - stratified: `RepeatedStratifiedKFold`
    - group: `StratifiedGroupKFold`, reseeded for each repeat
    - temporal: expanding window over distinct time values with an optional gap; `n_repeats` is
      forced to 1 and an info warning is recorded
  - The fold-index SHA-256 is stored. `SplitError` is raised for impossible folds (fewer
    minority samples or groups than folds, too few time values, single-class training or test
    sides, missing group or time values). Single-class validation folds produce a warning.
- `splitting/duplicates.py`: `cross_boundary_duplicates` counts evaluation rows whose feature
  values exactly duplicate a training row, across the test boundary and every CV fold. It
  returns one WARNING with the counts as evidence.
- `pipelines/builder.py`:
  - `infer_feature_spec` assigns columns to numeric or categorical by dtype. Datetime and
    all-missing columns are dropped, and the reason is recorded.
  - `build_preprocessor` is a `ColumnTransformer`: median impute + `StandardScaler` for
    numerics; `"__missing__"` fill + `OneHotEncoder(handle_unknown="ignore", max_categories=50)`
    for categoricals.
  - `build_pipeline` assembles an imblearn `Pipeline` of preprocess → optional sampler (none,
    random_under, random_over, or smote) → model.

#### Files changed
- added: `src/imbalancelab/splitting/{splits,duplicates}.py`,
  `src/imbalancelab/pipelines/builder.py`, `tests/test_splitting.py`, `tests/test_pipelines.py`
- modified: `src/imbalancelab/splitting/__init__.py`, `src/imbalancelab/pipelines/__init__.py`,
  `PROJECT_STATUS.md` (and LF line-ending fix of M1's records), `REVIEW_PACKET.md`

#### Exact commands run
    pytest -q tests/test_splitting.py tests/test_pipelines.py   # 1 failure: test-helper bug
    pytest -q tests/test_splitting.py tests/test_pipelines.py   # 24 passed
    ruff format . ; ruff check . --fix ; mypy                     # 1 file reformatted, 2 import-order fixes
    bash scripts/gate.sh

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
26 files already formatted
[exit 0]

$ mypy
Success: no issues found in 19 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
............................................................             [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src\imbalancelab\__init__.py                   2      0   100%
src\imbalancelab\api\__init__.py               0      0   100%
src\imbalancelab\config.py                    12      1    92%   24
src\imbalancelab\data\__init__.py              4      0   100%
src\imbalancelab\data\errors.py               21      0   100%
src\imbalancelab\data\loader.py              143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py               37      0   100%
src\imbalancelab\evaluation\__init__.py        0      0   100%
src\imbalancelab\models\__init__.py            0      0   100%
src\imbalancelab\pipelines\__init__.py         2      0   100%
src\imbalancelab\pipelines\builder.py         66      0   100%
src\imbalancelab\profiling\__init__.py         3      0   100%
src\imbalancelab\profiling\profile.py        169      5    97%   83, 85, 301, 341, 363
src\imbalancelab\profiling\warnings.py         9      0   100%
src\imbalancelab\reporting\__init__.py         0      0   100%
src\imbalancelab\splitting\__init__.py         3      0   100%
src\imbalancelab\splitting\duplicates.py      24      0   100%
src\imbalancelab\splitting\splits.py         195      3    98%   96, 102, 114
src\imbalancelab\tracking\__init__.py          0      0   100%
------------------------------------------------------------------------
TOTAL                                        690     14    98%
60 passed in 4.30s
[exit 0]
```

#### Tests that prove the required properties
- **No group crosses splits:** `test_group_splits_never_share_groups` checks the holdout and
  every CV fold.
- **Temporal ordering holds:** `test_temporal_ordering_holds[0|3]` checks train max < eval min,
  exactly `gap` distinct time values in between, and an expanding window.
  `test_temporal_ties_never_straddle_boundary` checks that tied timestamps never straddle a
  boundary.
- **Scaler parameters come from training rows only:**
  `test_scaler_parameters_come_from_training_rows_only` checks that `mean_` and `scale_` equal
  the median-imputed training-row statistics and differ from the full-data ones.
  `test_categories_learned_from_training_rows_only` checks that categories seen only outside
  training are not learned.
- **Sampler does not alter predict-time data:**
  `test_sampler_changes_fit_data_but_not_predict_data[random_over|random_under|smote]`. A
  recording estimator shows that the classes are balanced at fit, while at predict the
  estimator receives exactly `preprocess.transform(X_val)` with the original row count.

#### Invariant re-check
- 1 and 2: every learned transform and sampler sits inside one imblearn Pipeline, and samplers
  act only during fit (tested).
- 4: fold indices are stored in `CVPlan`, ready for every model to share (M4).
- 5: `fold_indices_sha256` and `test_sha256` are computed.
- 7: the holdout is created once, stored, and verified on reuse. Inner folds are drawn only from
  `holdout.train_idx` (tested: validation ∩ test = ∅, folds ⊆ outer-train).

#### Deviations from instructions
- **First test run:** the independent duplicate count in `test_cross_boundary_duplicates_detected`
  used `astype(str)`, which keeps NaN as a float under pandas 3, so `str.join` failed. I replaced
  the key with `repr(tuple(row))`. Assertions unchanged.

#### Known limitations
- Temporal CV uses an expanding window with equal-sized chunks of *distinct time values*, not
  equal row counts.
- SMOTE interpolates one-hot columns, producing fractional values. SMOTENC is not used in the
  MVP.

---

### Task M3 — Metrics module

**Date:** 2026-10-22 · **Milestone:** M3

#### Summary of changes
- `evaluation/metrics.py`:
  - `MetricResult(name, value, defined, reason, note)`, `ConfusionCounts`, and `MetricSet`.
  - Metrics: average precision (primary), ROC AUC, Brier, precision, recall, F1, F-beta,
    balanced accuracy, MCC, and the confusion matrix at a threshold (`score >= threshold`
    predicts positive).
  - Threshold metrics are computed from confusion counts. Each is undefined exactly when its
    denominator is zero, with a stated reason:
    - precision: no positive predictions
    - recall: no positives in y_true
    - F-beta: no positives and no positive predictions
    - balanced accuracy: single-class y_true
    - MCC: single-class y_true, or constant predictions
  - Ranking metrics are undefined for single-class or empty y_true. Brier is undefined for
    empty input or scores outside [0, 1].
  - Malformed input raises `ValueError`: length mismatch, NaN/inf scores, or non-binary y_true.
- Tests compare every metric with scikit-learn on 9 (threshold, beta) combinations and cover
  single-class folds (both classes), no positive predictions, constant scores, perfect
  predictions, empty input, and input validation.

#### Files changed
- added: `src/imbalancelab/evaluation/metrics.py`, `tests/test_metrics.py`
- modified: `src/imbalancelab/evaluation/__init__.py`, `PROJECT_STATUS.md`, `REVIEW_PACKET.md`

#### Exact commands run
    pytest -q tests/test_metrics.py     # 17 passed on first run
    ruff format . ; ruff check . ; mypy
    bash scripts/gate.sh

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
28 files already formatted
[exit 0]

$ mypy
Success: no issues found in 20 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 93%]
.....                                                                    [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src\imbalancelab\__init__.py                   2      0   100%
src\imbalancelab\api\__init__.py               0      0   100%
src\imbalancelab\config.py                    12      1    92%   24
src\imbalancelab\data\__init__.py              4      0   100%
src\imbalancelab\data\errors.py               21      0   100%
src\imbalancelab\data\loader.py              143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py               37      0   100%
src\imbalancelab\evaluation\__init__.py        2      0   100%
src\imbalancelab\evaluation\metrics.py       115      0   100%
src\imbalancelab\models\__init__.py            0      0   100%
src\imbalancelab\pipelines\__init__.py         2      0   100%
src\imbalancelab\pipelines\builder.py         66      0   100%
src\imbalancelab\profiling\__init__.py         3      0   100%
src\imbalancelab\profiling\profile.py        169      5    97%   83, 85, 301, 341, 363
src\imbalancelab\profiling\warnings.py         9      0   100%
src\imbalancelab\reporting\__init__.py         0      0   100%
src\imbalancelab\splitting\__init__.py         3      0   100%
src\imbalancelab\splitting\duplicates.py      24      0   100%
src\imbalancelab\splitting\splits.py         195      3    98%   96, 102, 114
src\imbalancelab\tracking\__init__.py          0      0   100%
------------------------------------------------------------------------
TOTAL                                        807     14    98%
77 passed in 7.01s
[exit 0]
```

#### Invariant re-check
- 4: `PRIMARY_METRIC = "average_precision"`.
- 6: metrics are pure functions of the predictions they receive. Nothing is fabricated, and
  undefined values are explicit (`value=None`, `defined=False`).

#### Deviations from instructions
- **Constant scores** are handled as an edge case, but AP and ROC AUC stay *defined* (AP equals
  prevalence, AUC is 0.5) and carry a `note`. MCC and precision become undefined when constant
  scores produce constant predictions. See D11.

#### Known limitations
- No confidence intervals per metric. Spread across folds is reported by the runner (M4).

---

### Task M4 — Experiment runner, baselines, run records

**Date:** 2026-10-22 · **Milestone:** M4

#### Summary of changes
- `models/registry.py`: fixed small configs for `dummy_prior` (baseline), `logreg_balanced`
  (baseline, `class_weight="balanced"`), `hgb` (`HistGradientBoostingClassifier`, 200 iterations,
  no early stopping), and `random_forest` (optional, 300 trees, `balanced_subsample`).
- `evaluation/config.py`: `ExperimentConfig` (candidates as model + sampler, `CVConfig`, seed,
  reference threshold, beta, SMOTE k). Baselines are always added and run without a sampler.
- `evaluation/runner.py`, `run_experiment(dataset, holdout, config, runs_dir)`:
  - Verifies the holdout, builds inner folds once with the **schema's split strategy**, and fits
    every model on the **same stored fold indices** (outer-train rows only).
  - Records per-fold metrics, a summary (mean, std, min, max, n, n_undefined), out-of-fold
    predictions for each repeat, and paired per-fold differences against each baseline (and
    logreg against dummy) on AP and ROC AUC, with wins, losses, ties and win fraction. No
    significance test is run.
  - Picks the best candidate by mean OOF AP. Test data is not used.
  - A model failure marks `run.json` as `status: failed` with the error and raises `RunError`.
- `tracking/records.py`:
  - `RunStore` creates and resolves run directories, rejecting path-traversal IDs.
  - `RunRecord` is a read-only view of a run.
  - `environment_info` records Python, platform and package versions.
- Run directory `runs/<run_id>/` contains: `run.json` (status, timestamps, dataset SHA-256 and
  schema, holdout summary with test SHA-256, CV config, fold-index SHA-256, seed, models,
  feature spec, split warnings), `config.json`, `environment.json`, `dataset_sha256.txt`,
  `holdout.json`, `fold_indices.json`, `profile.json`, `fold_metrics.json`, `summary.json`, and
  `oof_predictions.parquet`.

#### Files changed
- added: `src/imbalancelab/models/registry.py`, `src/imbalancelab/evaluation/{config,runner}.py`,
  `src/imbalancelab/tracking/records.py`, `tests/test_runner.py`
- modified: `src/imbalancelab/models/__init__.py`, `src/imbalancelab/tracking/__init__.py`,
  `PROJECT_STATUS.md`, `REVIEW_PACKET.md`

#### Exact commands run
    pytest -q tests/test_runner.py --durations=5      # 12 passed on first run
    ruff format . ; ruff check . --fix ; mypy           # 3 files reformatted, 1 import-order fix
    bash scripts/gate.sh

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
33 files already formatted
[exit 0]

$ mypy
Success: no issues found in 24 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 80%]
.................                                                        [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                       Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
src\imbalancelab\__init__.py                   2      0   100%
src\imbalancelab\api\__init__.py               0      0   100%
src\imbalancelab\config.py                    12      1    92%   24
src\imbalancelab\data\__init__.py              4      0   100%
src\imbalancelab\data\errors.py               21      0   100%
src\imbalancelab\data\loader.py              143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py               37      0   100%
src\imbalancelab\evaluation\__init__.py        2      0   100%
src\imbalancelab\evaluation\config.py         35      0   100%
src\imbalancelab\evaluation\metrics.py       115      0   100%
src\imbalancelab\evaluation\runner.py        117      0   100%
src\imbalancelab\models\__init__.py            2      0   100%
src\imbalancelab\models\registry.py           18      0   100%
src\imbalancelab\pipelines\__init__.py         2      0   100%
src\imbalancelab\pipelines\builder.py         66      0   100%
src\imbalancelab\profiling\__init__.py         3      0   100%
src\imbalancelab\profiling\profile.py        169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py         9      0   100%
src\imbalancelab\reporting\__init__.py         0      0   100%
src\imbalancelab\splitting\__init__.py         3      0   100%
src\imbalancelab\splitting\duplicates.py      24      0   100%
src\imbalancelab\splitting\splits.py         195      3    98%   96, 102, 114
src\imbalancelab\tracking\__init__.py          2      0   100%
src\imbalancelab\tracking\records.py         120      6    95%   89-90, 135, 170, 195-196
------------------------------------------------------------------------
TOTAL                                       1101     18    98%
89 passed in 31.30s
[exit 0]
```

#### Invariant re-check
- 1 and 2: each fold fits a fresh imblearn pipeline on `train_idx` only (M2 builder).
- 4: `test_all_models_share_identical_folds_and_never_see_test` checks that the
  (repeat, fold, row_index) sets are identical for every model. Baselines are always run.
- 5: run records hold the seed, config, dataset SHA-256, fold-index SHA-256 (re-verified in a
  test), and environment versions.
- 6: every summary value is computed from `fold_metrics.json` (tested against numpy).
- 7: OOF rows equal outer-train rows exactly and never intersect the test indices (tested).
  `check_holdout` runs before CV.
- Reproducibility: `test_same_seed_and_config_give_identical_metrics` checks that fold metrics
  (minus timing), OOF predictions and the summary are identical, and that a different CV seed
  changes the fold hash.

#### Deviations from instructions
- None.

#### Known limitations
- Execution is sequential (folds × models). Random forest uses `n_jobs=-1`.
- The reference-threshold metrics in CV use a fixed `threshold` (default 0.5). Tuned thresholds
  come in M5.
