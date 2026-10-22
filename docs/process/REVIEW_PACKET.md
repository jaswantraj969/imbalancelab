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

---

### Task M5 — Threshold analysis and final evaluation

**Date:** 2026-10-22 · **Milestone:** M5

#### Summary of changes
- `evaluation/thresholds.py`:
  - `PredictionSet(y_true, y_score, provenance)` with provenance oof, validation or test.
    `threshold_curve` and `select_threshold` raise `ProvenanceError` for test predictions, and
    `from_frame` rejects mixed provenance.
  - Curve (a vectorised cumulative-count sweep over distinct scores, plus a "predict nothing"
    point): tp, fp, fn, tn, precision, recall, F-beta, expected cost.
  - Strategies: `max_fbeta`, `target_recall` (maximise precision subject to recall ≥ target),
    `target_precision` (maximise recall subject to precision ≥ target), and `min_cost`
    (cost_fp·FP + cost_fn·FN, per sample). Ties go to the higher threshold.
  - `analyse_thresholds` selects separately on each CV repeat's OOF predictions. It reports the
    per-repeat spread (mean, std, min, max, n) of the threshold, precision, recall, F-beta and
    cost, and chooses the median threshold. It also reports the chosen threshold re-applied to
    each repeat, labelled optimistic.
  - `run_threshold_analysis` stores the latest analysis per model, plus a history, in
    `thresholds.json`.
- `evaluation/final.py`, `final_evaluate(dataset, run_dir, model=None, force=False, reason=None)`:
  - Checks: the run is completed; the dataset SHA matches; the holdout verifies against both
    the dataset and `run.json`; a threshold analysis exists for the model. Baseline thresholds
    are selected on OOF with the same strategy when missing.
  - Refits the chosen model and both baselines on **outer-train rows only**, scores the test
    rows once each, and writes `final_evaluation.json` (metrics at the threshold, threshold
    provenance, test SHA, single-test comparisons) and `final_predictions.parquet`
    (`provenance="test"`).
  - A second call raises `FinalEvaluationExistsError` unless `force=True` and a non-empty
    `reason` are given. A forced call appends a `forced_reevaluation` log entry with the reason
    and the previous file's SHA-256. Every evaluation is appended to
    `final_evaluation_log.jsonl`.

#### Files changed
- added: `src/imbalancelab/evaluation/{thresholds,final}.py`, `tests/test_thresholds_final.py`
- modified: `PROJECT_STATUS.md`, `REVIEW_PACKET.md`

#### Exact commands run
    pytest -q tests/test_thresholds_final.py      # 14 passed on first run
    ruff format . ; ruff check . --fix ; mypy       # 3 files reformatted, 1 import-order fix
    bash scripts/gate.sh

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
36 files already formatted
[exit 0]

$ mypy
Success: no issues found in 26 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 69%]
...............................                                          [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
src\imbalancelab\__init__.py                    2      0   100%
src\imbalancelab\api\__init__.py                0      0   100%
src\imbalancelab\config.py                     12      1    92%   24
src\imbalancelab\data\__init__.py               4      0   100%
src\imbalancelab\data\errors.py                21      0   100%
src\imbalancelab\data\loader.py               143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                37      0   100%
src\imbalancelab\evaluation\__init__.py         2      0   100%
src\imbalancelab\evaluation\config.py          35      0   100%
src\imbalancelab\evaluation\final.py          102      4    96%   74-75, 102, 160
src\imbalancelab\evaluation\metrics.py        115      0   100%
src\imbalancelab\evaluation\runner.py         117      0   100%
src\imbalancelab\evaluation\thresholds.py     138      0   100%
src\imbalancelab\models\__init__.py             2      0   100%
src\imbalancelab\models\registry.py            18      0   100%
src\imbalancelab\pipelines\__init__.py          2      0   100%
src\imbalancelab\pipelines\builder.py          66      0   100%
src\imbalancelab\profiling\__init__.py          3      0   100%
src\imbalancelab\profiling\profile.py         169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py          9      0   100%
src\imbalancelab\reporting\__init__.py          0      0   100%
src\imbalancelab\splitting\__init__.py          3      0   100%
src\imbalancelab\splitting\duplicates.py       24      0   100%
src\imbalancelab\splitting\splits.py          195      3    98%   96, 102, 114
src\imbalancelab\tracking\__init__.py           2      0   100%
src\imbalancelab\tracking\records.py          120      3    98%   89-90, 170
-------------------------------------------------------------------------
TOTAL                                        1341     19    99%
103 passed in 44.12s
[exit 0]
```

#### Invariant re-check
- 3: `test_test_provenance_is_rejected` covers curve, select and analyse rejecting test
  provenance. `test_final_evaluation_once_and_forced_logging` checks that the stored test
  predictions cannot be passed to `analyse_thresholds`.
- 7: final evaluation refits on `holdout.train_idx` only (`test_final_pipeline_refit_on_outer_train_only`
  checks the scaler statistics). Every model's test rows equal `holdout.test_idx` exactly. A
  second scoring is refused, and a forced one is logged.
- Selection correctness: every strategy is checked against an exhaustive brute-force reference,
  and the curve is checked against `sklearn.metrics.precision_recall_curve`.

#### Deviations from instructions
- None.

#### Known limitations
- The chosen threshold is the median of the per-repeat selections. The OOF metrics at that
  threshold are optimistic (the same data informed the selection), and this is labelled.
- Final test results are single numbers per model, with no spread. The report says so.

---

### Task M6 — Evidence-based audit report

**Date:** 2026-10-22 · **Milestone:** M6

#### Summary of changes
- `reporting/report.py`: `generate_report(run_dir)` reads **only** `RunRecord` files (run,
  config, environment, profile, summary, fold metrics via the summary, OOF predictions,
  thresholds, final evaluation, final predictions, final log). It writes
  `report/report.md`, `report/report.html` and `report/figures/*.png` inside the run directory.
  Sections:
  1. Verdict, a plain-language "beats" or "does NOT beat" for every AP comparison. A candidate
     beats a baseline only if its mean paired diff > 0 *and* its win fraction > 0.5. Test
     verdicts are added when a final evaluation exists.
  2. Dataset
  3. Profile warnings, labelled as heuristic suspicions
  4. Split strategy, with hashes and split warnings
  5. Models
  6. CV results (mean ± std, n, undefined counts) and paired comparisons, with OOF PR and ROC
     curves
  7. Threshold analysis, with per-repeat spread
  8. Final test results, with test PR and ROC curves and the evaluation log, or "Not yet
     performed"
  9. Limitations (data-dependent items included, e.g. few test positives)
  10. Reproducibility (seed, SHA-256s, versions, config)
- `reporting/render.py`: a minimal document model rendered to Markdown and self-contained
  HTML. Images are embedded as base64, all text is HTML-escaped, and there are no scripts.
- `reporting/figures.py`: matplotlib (Agg) PR and ROC curves from stored predictions, with
  single-class models skipped.
- `evaluation/runner.py`: `run.json` now also stores `model_specs` (name, model, sampler,
  description), so the report's model table comes from the run record rather than from code.

#### Files changed
- added: `src/imbalancelab/reporting/{report,render,figures}.py`, `tests/test_reporting.py`,
  `tests/snapshots/report_structure.md`
- modified: `src/imbalancelab/reporting/__init__.py`, `src/imbalancelab/evaluation/runner.py`,
  `PROJECT_STATUS.md`, `REVIEW_PACKET.md`

#### Exact commands run
    UPDATE_SNAPSHOTS=1 pytest -q tests/test_reporting.py -k snapshot   # create snapshot (reviewed)
    pytest -q tests/test_reporting.py                                     # 6 passed
    ruff format . ; ruff check . --fix ; mypy      # E501 x2 in report.py -> fixed by hand
    bash scripts/gate.sh                           # first run: exit 1 (the E501s), rerun below

#### Gate output (verbatim, final run)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
41 files already formatted
[exit 0]

$ mypy
Success: no issues found in 29 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 66%]
.....................................                                    [100%]
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                        Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
src\imbalancelab\__init__.py                    2      0   100%
src\imbalancelab\api\__init__.py                0      0   100%
src\imbalancelab\config.py                     12      1    92%   24
src\imbalancelab\data\__init__.py               4      0   100%
src\imbalancelab\data\errors.py                21      0   100%
src\imbalancelab\data\loader.py               143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                37      0   100%
src\imbalancelab\evaluation\__init__.py         2      0   100%
src\imbalancelab\evaluation\config.py          35      0   100%
src\imbalancelab\evaluation\final.py          102      4    96%   74-75, 102, 160
src\imbalancelab\evaluation\metrics.py        115      0   100%
src\imbalancelab\evaluation\runner.py         117      0   100%
src\imbalancelab\evaluation\thresholds.py     138      0   100%
src\imbalancelab\models\__init__.py             2      0   100%
src\imbalancelab\models\registry.py            18      0   100%
src\imbalancelab\pipelines\__init__.py          2      0   100%
src\imbalancelab\pipelines\builder.py          66      0   100%
src\imbalancelab\profiling\__init__.py          3      0   100%
src\imbalancelab\profiling\profile.py         169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py          9      0   100%
src\imbalancelab\reporting\__init__.py          2      0   100%
src\imbalancelab\reporting\figures.py          44      1    98%   28
src\imbalancelab\reporting\render.py           82      0   100%
src\imbalancelab\reporting\report.py          163      8    95%   59, 125, 172, 202, 245, 382, 440, 442
src\imbalancelab\splitting\__init__.py          3      0   100%
src\imbalancelab\splitting\duplicates.py       24      0   100%
src\imbalancelab\splitting\splits.py          195      3    98%   96, 102, 114
src\imbalancelab\tracking\__init__.py           2      0   100%
src\imbalancelab\tracking\records.py          120      3    98%   89-90, 170
-------------------------------------------------------------------------
TOTAL                                        1632     28    98%
109 passed in 49.73s
[exit 0]
```

#### Tests
- `test_report_structure_snapshot`: a structural snapshot of the Markdown report for a small
  synthetic run. IDs, hashes, timestamps, numbers, the platform and the verdict words are
  masked, so it checks structure and wording without being brittle across platforms.
- `test_report_numbers_trace_to_run_records`: the CV AP cells equal `fmt_summary(summary.json)`,
  the test rows equal `final_evaluation.json`, the chosen threshold equals `thresholds.json`,
  the hashes are present, the 4 figures exist and are referenced, and the HTML embeds 4 images
  with no `<script>`.
- `test_verdict_states_plainly_when_not_beating_baseline`: covers the mean-up-but-mostly-losses
  case, ties, no pairs, and test verdicts.
- Also tested: the report before final evaluation states that no test results exist, an
  incomplete run is refused, and Markdown/HTML escaping works.

#### Invariant re-check
- 4 and 6: the report reads only run records. Every number in it comes from those files
  (traceability test), and baseline comparisons are always shown.
- The synthetic run's own report states "**hgb** does NOT beat **logreg_balanced**" (the data
  has a linear signal). This is the plain-statement requirement working on real output.

#### Deviations from instructions
- None. (The first gate run failed on 2 E501 lines, which I fixed by restructuring the
  f-string.)

#### Known limitations
- The snapshot test masks numbers. Numeric correctness is covered by the traceability test, not
  by the snapshot.
- HTML is self-contained (base64 images), so file size grows with the figures (about 4 × 30 KB).

---

### Task M7 — FastAPI endpoints

**Date:** 2026-10-22 · **Milestone:** M7

#### Summary of changes
- `workflow.py` (library service layer): a `Workspace` (datasets, runs and models
  directories, created lazily) and these functions:
  - `register_dataset`: copies into a generated `ds-<time>-<hex>` directory, validates,
    profiles, and creates the holdout once. On any failure it removes the directory.
  - `get_registration`, `list_datasets`, `get_profile`
  - `load_registered`: reuses the stored holdout and never re-draws it
  - `start_run`, `list_runs`, `get_run`, `analyse_thresholds`, `finalize_run`, `report_path`
- `api/app.py`, `create_app(settings)`, with `app = create_app()` for `uvicorn imbalancelab.api.app:app`.
  - Endpoints:
    - `GET /health`
    - `POST /datasets` (multipart: `file` plus `schema` JSON plus optional `holdout` JSON) and
      `GET /datasets`
    - `GET /datasets/{id}/profile`
    - `POST /runs`, `GET /runs`, `GET /runs/{id}`
    - `POST /runs/{id}/thresholds`, `POST /runs/{id}/final-evaluation`
    - `GET /runs/{id}/report?format=html|markdown`
    - `POST /models/{id}/predict`: returns 404 until M9 adds persistence (D19)
  - Each handler parses or validates input, then makes one `workflow` call.
  - Exceptions map to status codes: 400 invalid ID; 404 not found; 409 final evaluation
    exists or a precondition fails; 413 upload too large; 422 data, split, threshold,
    provenance, run and validation errors.
  - Uploads stream to a temp file (limit `max_upload_bytes`). The client filename is used only
    for its suffix (allowlist `.csv`, `.parquet`) and as a display name, and is never part of a
    path. IDs are regex-validated (`^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$`).
  - Execution is synchronous (documented in the module and app description).
- `api/schemas.py`: pydantic request and response models.
- `config.py`: adds `datasets_dir`, `models_dir`, and `max_upload_bytes` (50 MiB default).

#### Files changed
- added: `src/imbalancelab/workflow.py`, `src/imbalancelab/api/{app,schemas}.py`,
  `tests/test_api.py`
- modified: `src/imbalancelab/api/__init__.py`, `src/imbalancelab/config.py`, `.gitignore`
  (`data/registered/`, `models/`), `PROJECT_STATUS.md`, `REVIEW_PACKET.md`

#### Exact commands run
    pytest -q tests/test_api.py      # 8 passed; pydantic "schema" shadow warning
    # renamed the form parameter (alias "schema"): schema_json also shadows; then schema_text
    pytest -q tests/test_api.py      # 8 passed, 1 upstream warning
    ruff format . ; ruff check . --fix ; mypy
    bash scripts/gate.sh

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
45 files already formatted
[exit 0]

$ mypy
Success: no issues found in 32 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 61%]
.............................................                            [100%]
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
src\imbalancelab\api\app.py                   110      0   100%
src\imbalancelab\api\schemas.py                45      0   100%
src\imbalancelab\config.py                     15      1    93%   27
src\imbalancelab\data\__init__.py               4      0   100%
src\imbalancelab\data\errors.py                21      0   100%
src\imbalancelab\data\loader.py               143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                37      0   100%
src\imbalancelab\evaluation\__init__.py         2      0   100%
src\imbalancelab\evaluation\config.py          35      0   100%
src\imbalancelab\evaluation\final.py          102      4    96%   74-75, 102, 160
src\imbalancelab\evaluation\metrics.py        115      0   100%
src\imbalancelab\evaluation\runner.py         117      0   100%
src\imbalancelab\evaluation\thresholds.py     138      0   100%
src\imbalancelab\models\__init__.py             2      0   100%
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
src\imbalancelab\workflow.py                  120      5    96%   59-60, 87, 132, 220
-------------------------------------------------------------------------
TOTAL                                        1910     32    98%
117 passed, 1 warning in 50.64s
[exit 0]
```

#### Tests
- `test_full_run_lifecycle` exercises run → detail → final evaluation before thresholds (409)
  → thresholds → final (200) → repeat (409) → forced without a reason (409) → forced with a
  reason (200, `forced: true`) → HTML and Markdown report → bad format (422).
- `test_upload_validation_errors` covers bad JSON, a bad schema, a wrong extension, a missing
  target, an empty file, an oversize upload (413), and a single-class split error. It also
  checks that no dataset directory or temp file is left behind.
- `test_client_filename_cannot_escape_workspace` uploads as `../../../evil.csv` and checks
  that nothing is written outside the workspace.
- `test_invalid_and_unknown_ids` checks 400 for malformed IDs (including `..\..\x`) and 404
  for unknown ones.
- `test_routes_contain_no_ml_code` parses `api/app.py` and checks that it imports none of
  sklearn, imblearn, numpy, pandas or joblib.

#### Invariant re-check
- 7: the holdout is created at dataset registration and stored next to the data. Every run and
  final evaluation reloads it through `get_or_create_holdout`, which verifies the SHA-256 and
  config. The test set is never re-drawn.
- 3: thresholds are selected only through `POST /runs/{id}/thresholds` (OOF). Final evaluation
  requires that step and is refused a second time without force and a reason.

#### Deviations from instructions
- **`POST /models/{id}/predict`** exists but returns 404 until M9 (D19).

#### Known limitations
- Synchronous execution: long runs hold the HTTP request open. There is no job queue (MVP).
- Starlette warns that `httpx` with its TestClient is deprecated in favour of `httpx2`. This is
  an upstream warning, and the dev dependency stays `httpx` as specified.
- `ValueError` from library code maps to 422 (`invalid_request`). A genuine bug raising
  `ValueError` would surface as a 422 instead of a 500.

---

### Task M8 — Streamlit frontend

**Date:** 2026-10-22 · **Milestone:** M8

#### Summary of changes
- `frontend/api_client.py`: an `ApiClient` built on `requests.Session` with one method per
  endpoint. `ApiError(status, error, detail)` is raised on HTTP errors. The base URL comes from
  `IMBALANCELAB_API_URL` (default `http://localhost:8000`).
- `frontend/app.py`: Streamlit pages, chosen from a sidebar radio, with an API health check in
  the sidebar:
  1. **Upload & profile**: schema form, holdout config, upload, then profile metrics, warnings
     (captioned as heuristic suspicions) and the columns table.
  2. **Run experiment**: candidate multiselect, folds, repeats and seed, then a synchronous run.
  3. **Results & thresholds**: CV summary, paired AP comparisons, and a threshold form (all 4
     strategies).
  4. **Final evaluation**: limited to models that have a threshold analysis. Warns when a final
     evaluation already exists, and offers force + reason.
  5. **Report**: embedded HTML report and download.
- No `imbalancelab` imports anywhere in `frontend/`.
- `pyproject.toml`: mypy now also checks `frontend/` (`mypy_path = "frontend"`).
- `.gitignore`: anchored the M7 patterns to `/data/registered/` and `/models/`. The unanchored
  `models/` would have ignored `src/imbalancelab/models/`; I found this before any file was
  lost and verified it with `git check-ignore`.

#### Files changed
- added: `frontend/app.py`, `frontend/api_client.py`, `tests/test_frontend.py`
- modified: `frontend/README.md`, `pyproject.toml` (mypy), `.gitignore`, `PROJECT_STATUS.md`,
  `REVIEW_PACKET.md`

#### Exact commands run
    git check-ignore -v src/imbalancelab/models/_probe.py   # exit 1 = not ignored (after fix)
    pytest -q tests/test_frontend.py        # 9 passed, then 10 after adding the UI flow test
    ruff format . ; ruff check . --fix ; mypy
    bash scripts/gate.sh                    # output below (173 s wall time, see note)
    pytest -q --cov=imbalancelab --durations=8   # re-timing: 127 passed in 62.47s

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
48 files already formatted
[exit 0]

$ mypy
Success: no issues found in 34 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 56%]
.......................................................                  [100%]
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
src\imbalancelab\api\app.py                   110      0   100%
src\imbalancelab\api\schemas.py                45      0   100%
src\imbalancelab\config.py                     15      1    93%   27
src\imbalancelab\data\__init__.py               4      0   100%
src\imbalancelab\data\errors.py                21      0   100%
src\imbalancelab\data\loader.py               143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                37      0   100%
src\imbalancelab\evaluation\__init__.py         2      0   100%
src\imbalancelab\evaluation\config.py          35      0   100%
src\imbalancelab\evaluation\final.py          102      4    96%   74-75, 102, 160
src\imbalancelab\evaluation\metrics.py        115      0   100%
src\imbalancelab\evaluation\runner.py         117      0   100%
src\imbalancelab\evaluation\thresholds.py     138      0   100%
src\imbalancelab\models\__init__.py             2      0   100%
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
src\imbalancelab\workflow.py                  120      5    96%   59-60, 87, 132, 220
-------------------------------------------------------------------------
TOTAL                                        1910     32    98%
127 passed, 1 warning in 173.07s (0:02:53)
[exit 0]
```

#### Tests (tests/test_frontend.py)
- `test_frontend_never_imports_imbalancelab`: AST scan of every `frontend/*.py` for `import`,
  `from … import` and `__import__` of `imbalancelab`.
- A live uvicorn server on a free port, with a temporary workspace, started in a thread.
- `test_api_client_round_trip`: every client method against the live API, including mapping a
  404 to `ApiError`.
- `test_every_page_renders_against_live_api[5 pages]`: Streamlit `AppTest`. Each page renders
  with no exception and no error element.
- `test_threshold_then_final_evaluation_through_ui`: submits the threshold form
  (`target_recall`), then clicks final evaluation. The test verifies through the API that the
  final evaluation used that strategy, and that a second click shows the 409 refusal.
- `test_app_reports_unreachable_api`: a graceful sidebar error, with no exception.

#### Invariant re-check
- The UI cannot bypass the library's guards. It can only call the API, so threshold provenance
  and the one-shot test scoring are enforced server-side (the 409 is shown in the UI test).

#### Deviations from instructions
- None.

#### Known limitations
- `st.file_uploader` is not exercised by `AppTest`. The upload path is covered by
  `test_api_client_round_trip` (same client method).
- The gate run above took 173 s of wall time. A re-run of the identical suite took 62 s (the
  durations show no single slow test), which points to transient machine load. Recorded for
  transparency.

---

### Task M9 — Model persistence and inference endpoint

**Date:** 2026-10-22 · **Milestone:** M9

#### Summary of changes
- `models/persistence.py`:
  - `save_model` writes `models/<model_id>/model.joblib` plus `metadata.json`: model ID, run
    ID, model name, threshold, threshold provenance, `trained_on: "outer-train rows only"`,
    number of training rows, dataset and test SHA-256, `FeatureSpec`, environment versions,
    and the artifact SHA-256.
  - `load_model` checks the artifact SHA-256 **before** unpickling (`ModelIntegrityError` on
    mismatch or a missing file). It emits a `VersionMismatchWarning` for each mismatch in
    Python, numpy, pandas, scikit-learn, imbalanced-learn or joblib, and returns them.
  - `validate_input` raises `InputSchemaError` for missing feature columns or non-numeric values
    in numeric columns. Unused extra columns are ignored, with a note.
  - `predict` returns the probability plus a label at the stored threshold.
- `workflow.finalize_run(..., persist_model=True)` saves the pipeline that final evaluation
  refit on outer-train rows and links it with `persisted_model_id` in `final_evaluation.json`
  (plus a `model_persisted` log entry). `list_models` and `predict_records` are new.
- API changes:
  - `POST /runs/{id}/final-evaluation` returns `model_id` (`persist_model` flag, default true).
  - `POST /models/{id}/predict` is implemented, and `GET /models` is added.
  - Errors map to 409 `model_integrity_error` and 422 `input_schema_error`.

#### Files changed
- added: `src/imbalancelab/models/persistence.py`, `tests/test_persistence.py`
- modified: `src/imbalancelab/workflow.py`, `src/imbalancelab/evaluation/final.py`
  (`record_persisted_model`), `src/imbalancelab/api/app.py`, `PROJECT_STATUS.md`,
  `REVIEW_PACKET.md`

#### Exact commands run
    pytest -q tests/test_persistence.py tests/test_api.py   # 14 passed
    pytest -q tests/test_persistence.py                     # after tidying 2 tests: 6 passed
    ruff format . ; ruff check . --fix ; mypy
    bash scripts/gate.sh

#### Gate output (verbatim)
```text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
50 files already formatted
[exit 0]

$ mypy
Success: no issues found in 35 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 54%]
.............................................................            [100%]
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
src\imbalancelab\workflow.py                  144      6    96%   62-63, 90, 135, 228, 252
-------------------------------------------------------------------------
TOTAL                                        2045     33    98%
133 passed, 1 warning in 73.49s (0:01:13)
[exit 0]
```

#### Tests
- `test_round_trip_predictions_identical`: probabilities after save → load → predict are
  **bit-identical** (`assert_array_equal`) to the in-memory pipeline, and to the stored
  final-evaluation test predictions.
- `test_tampered_artifact_is_rejected_before_unpickling`: covers a modified artifact, a deleted
  artifact, and an unknown ID.
- `test_version_mismatch_warns`: 2 edited versions produce 2 warnings, also returned in
  `loaded.warnings`.
- `test_input_validation`: covers a missing column, a non-numeric value, no records, an extra
  column note, and an unseen category handled.
- `test_api_final_evaluation_persists_and_predicts`: the full HTTP flow. It checks that
  `model_id` is linked in the run record, `GET /models`, that predict probabilities equal the
  library's (`atol=1e-12` after the JSON round trip), 422 for missing columns,
  `persist_model=false`, and 409 for a tampered artifact.

#### Invariant re-check
- 7: the persisted pipeline is the one `final_evaluate` refit on `holdout.train_idx` only (M5
  test checks its scaler statistics). Metadata records `trained_on` and `n_train_rows`.
- 5: metadata records the dataset SHA, test SHA, versions, and the artifact SHA.

#### Deviations from instructions
- None.

#### Known limitations
- joblib artifacts are pickles. The SHA check guards against replaced files, not against a
  malicious metadata+artifact pair written together. Only load artifacts from a trusted
  workspace (documented in the module docstring).
- Probabilities are not calibrated (calibration is out of MVP scope).

---

### Task M10 — Documentation and case study

**Date:** 2026-10-22 · **Milestone:** M10

#### Summary of changes
- **README.md**:
  - purpose and features, and install (ranges or lock)
  - library quickstart, **executed verbatim by `tests/test_readme.py`**
  - API quickstart: `uvicorn imbalancelab.api.app:app`, an endpoint table, and curl examples
  - UI quickstart: `streamlit run frontend/app.py`
  - architecture, run-directory layout, the 7 invariants, checks, and limitations
- **scripts/run_case_study.py**: a fixed, pre-specified protocol on `mammography`
  (imbalanced-learn benchmark, Zenodo DOI 10.5281/zenodo.61452, licence ODC-ODbL as listed
  on the Zenodo record, which I fetched from the Zenodo API on 2026-10-22).
  - Steps: download, CSV, register (profile + holdout), 5×3 CV over 2 baselines and 4
    candidates, F2 threshold on OOF for the best candidate by OOF AP, one-shot final
    evaluation plus persistence, report, export of the run record to `docs/case_study/<run_id>/`
    (files > 1 MB listed with SHA-256 in `OMITTED_FILES.json`), `PROVENANCE.json`, a
    duplicate-sensitivity record, and **`docs/case_study.md` generated from those records**.
  - On a download failure it exits with code 2 and does not substitute synthetic data.
- **scripts/smoke_api.py**: an end-to-end smoke test against a real uvicorn subprocess (used for
  FINAL_REPORT.md).
- **Runner/workflow fix found during the smoke test:** `run.json` recorded the workspace file
  name (`data.csv`) as `source_name`. Runs now record the registered upload name
  (`run_experiment(..., source_name=...)`), and `tests/test_api.py` asserts it.
- **pyproject.toml**: mypy also checks `scripts/`.

#### Case-study findings (from the run record `run-20261022T083838Z-b12a4417`)
- The selected candidate is `hgb+smote` (by OOF AP). It beats both baselines on OOF AP in 15
  of 15 paired folds, and on the single test evaluation. See `docs/case_study.md` for the
  numbers.
- **The tool's duplicate checks fired on real data:** 3334 exact-duplicate rows, and 632 of 2237
  test rows duplicate outer-train feature rows (only 2 of them positive). I added a post-hoc
  sensitivity check that re-slices the *stored* test predictions only (no refit, no re-scoring,
  no selection). It is reported with its prevalence caveat and the statement that it does not
  cover CV.
- **Reproducibility check:** the case study ran 3 times during this milestone (twice before the
  caveat-wording change, once after). Test AP for `hgb+smote` was 0.6670 in every run, and 0.7060
  on the non-duplicate subset in both runs that computed it. Dataset SHA-256, test-index
  SHA-256 and fold-index SHA-256 were identical across runs.

#### Files changed
- added: `docs/case_study.md`, `docs/case_study/run-20261022T083838Z-b12a4417/**`, `scripts/run_case_study.py`,
  `scripts/smoke_api.py`, `tests/test_readme.py`
- modified: `README.md`, `pyproject.toml`, `src/imbalancelab/evaluation/runner.py`,
  `src/imbalancelab/workflow.py`, `tests/test_api.py`, `PROJECT_STATUS.md`, `REVIEW_PACKET.md`

#### Exact commands run
    curl -sS https://zenodo.org/api/records/61452     # licence/DOI/creators metadata
    python scripts/run_case_study.py                  # run 1: FileNotFoundError (wrong .npz name
                                                      #   guessed; download itself succeeded)
    python scripts/run_case_study.py                  # run 2: stopped by me to fix source_name
    python scripts/smoke_api.py                       # exit 0 (found the source_name issue)
    python scripts/run_case_study.py                  # runs 3-5: exit 0 (5 = final, committed)
    bash scripts/gate.sh

Final case-study script output:

    downloaded <project-root>\data\raw\imblearn\zenodo\x25data.npz sha256=73480c315d42bc5b33c2c73b9078d0034113d26f0511facd9fc5bb07f2d6438a
    registered ds-20261022T083837Z-2d9c08c1: 11183 rows, sha256=eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed
    run run-20261022T083838Z-b12a4417 completed; best candidate by OOF AP: hgb+smote
    final evaluation done; persisted model model-20261022T083913Z-86d46690
    wrote docs/case_study.md and docs\case_study\run-20261022T083838Z-b12a4417

#### Gate output (verbatim)
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
134 passed, 1 warning in 82.87s (0:01:22)
[exit 0]
```

#### Invariant re-check
- 6: `docs/case_study.md` is generated by code from the exported run record. Every number in
  it is read from `summary.json`, `final_evaluation.json`, `thresholds.json`, `profile.json`,
  `run.json` or `duplicate_sensitivity.json` in `docs/case_study/run-20261022T083838Z-b12a4417/`.
- 3 and 7: the case study selected model and threshold on OOF data only, and scored the test set
  once. The post-hoc duplicate check re-slices stored test predictions and selects nothing.

#### Deviations from instructions
- **Run record export:** the run record is exported in full except two files over 1 MB
  (`fold_indices.json` 2.0 MB, `oof_predictions.parquet` 1.2 MB), which are listed with
  SHA-256. The spec allows a summarised copy.
- **Extra analysis:** the post-hoc duplicate sensitivity check was added beyond the spec,
  because the profile and split checks fired on real data.

#### Known limitations
- The case study's pre-specified protocol used stratified (not duplicate-grouped) splitting.
  A duplicate-aware split (e.g. `group_column` = a feature-row hash) was not run.
- `.github/workflows/ci.yml` has **never been executed**: the repo has no remote. CI is
  defined but unverified (environment limitation).

---

### Task T-R1 — Supervisor review fixes

**Date:** 2026-10-22 · **Commit:** `e727ca4` (code, records, docs). This packet entry and the
regenerated FINAL_REPORT.md follow in a separate commit.

#### Summary
- **H1 (duplicate-aware splitting):**
  - `DatasetSchema.duplicate_groups` and `splitting/groups.py` (`resolve_groups`,
    `duplicate_cluster_ids`). Feature-row hash clusters are used as split groups. With a declared
    `group_column`, declared groups linked by a shared cluster are merged (connected components)
    and a warning is raised (D27). Conflicting-label rows stay in one cluster and are counted.
  - The holdout and CV use `StratifiedGroupKFold` whenever groups resolve.
  - `duplicate_groups`, `group_info` (clusters, rows, conflicts, spanning) and pinned-group
    counts are recorded in `holdout.json` and `run.json` and shown in the report.
- **H1 defect found on real data, and fixed (D28):** the first run (b) produced a degenerate test
  set; details are below. Groups larger than `max_eval_group_fraction` (default 0.25) of the
  target evaluation size are now pinned to training, test-fold counts are sized for the eligible
  rows, and the holdout warns on size deviation, prevalence deviation and domination by one
  group (> 50%).
- **H2, M1, M2 (case study):** `scripts/run_case_study.py` runs (a) `a_stratified` and
  (b) `b_duplicate_groups` with identical constants. `docs/case_study.md` is regenerated from both
  records:
  - the headline is test AP from (b) with n_rows, positives and prevalence
  - OOF AP is labelled "selection estimate (optimistic: used for model selection)"
  - the (a)-vs-(b) table includes the OOF-minus-test gap
  - the (a) re-slice reports n, positives, prevalence and the prevalence caveat
  - the pre-specification statement is explicit, including that git cannot prove the ordering
    and that (b) was requested after (a)'s results were seen
- **M3 (thresholds):** the chosen threshold, strategy, per-repeat values and spread, and test
  precision, recall, F2, MCC and confusion matrix for run (b) are in the case study and
  FINAL_REPORT.
- **M4 (CI):** no remote is configured. The full gate was run locally on **Python 3.11.15**
  (`uv venv --python 3.11 .venv311` + `requirements-lock.txt`) and on 3.13.5. Both pass.
  GitHub Actions has **not** run.
- **M5 (frontend):** `scripts/ui_screenshots.py` (Playwright 1.64.0 with the installed Edge, and a
  synthetic dataset) exercises all 5 pages, including the expected 409 refusal, and saves 6
  screenshots. No page errored. One UI addition: a `duplicate_groups` checkbox on the upload
  page, so the H1 option is reachable from the UI.
- **L1:** the metrics docstring and a README table document the edge cases (single-class →
  undefined; constant scores → AP = prevalence, ROC AUC = 0.5, defined). An explicit
  contract test was added.
- **L2:** `scripts/verify_case_study_hashes.py` regenerates the omitted files and checks their
  SHA-256. Its first run **failed** on run (a)'s `oof_predictions.parquet`. Root cause:
  `random_forest(n_jobs=-1)` is not bit-reproducible (≤ 2.2e-16 differences). Fixed with
  `n_jobs=1` and a bitwise regression test (D29). After re-running the case study, all checks
  pass.

#### Defect found during H2: degenerate StratifiedGroupKFold holdout (not committed)
The first run (b), with `duplicate_groups=True` and no pinning (run
`run-20261022T090141Z-9165d0cb`, never committed), reported `hgb+smote` and `logreg_balanced`
with an identical test AP of 0.8295, and 0 false positives. Investigation output (verbatim):

````text
top clusters: [3329, 5, 4, 1, 1]
giant cluster feature values: (-0.78441482, -0.47019533, -0.59163147, -0.85955255, -0.37786573, -0.94572324)
giant cluster rows: 3329 positives: 7
test rows: 3374 in giant cluster: 3329 outside: 45
test positives inside giant: 7 outside: 45
````

The test set was the 3329-row cluster plus 45 rows that were **all positive**, as
`StratifiedGroupKFold` rebalanced the class ratio around the unsplittable group. The numbers were
meaningless, so they were discarded, and the pinning and balance checks were added. A regression
test covers each: `test_giant_cluster_is_pinned_to_train_and_test_stays_representative` and
`test_without_pinning_a_dominated_test_set_is_flagged`.

#### Test fixes during T-R1 (no assertion weakened)
- **`test_giant_cluster_...`:** the fixture's `group` column was a feature that differed per
  row, so its rows were not identical. The independent cluster key now uses
  `ds.feature_columns`, and the fixture drops `group`.
- **`test_without_pinning_...`:** this exposed that `holdout_dominated_by_group` reused the
  pinning fraction, so it could never fire with pinning off. It now uses a fixed 50% limit
  (code fix, not a test change).
- **Report snapshot:** regenerated twice. Each diff was reviewed: two new split-table rows and
  the new `max_eval_group_fraction` config field. Nothing else changed.

#### git diff --stat 91c6f54..e727ca4
````text
 .gitignore                                         |     1 +
 FINAL_REPORT.md                                    |   528 +
 PROJECT_STATUS.md                                  |    37 +-
 README.md                                          |    19 +-
 docs/case_study.md                                 |   176 +-
 docs/case_study/a_stratified/OMITTED_FILES.json    |    10 +
 .../PROVENANCE.json                                |     2 +-
 .../config.json                                    |     3 +-
 .../dataset_sha256.txt                             |     0
 .../duplicate_sensitivity.json                     |    20 +-
 .../environment.json                               |     0
 .../final_evaluation.json                          |    14 +-
 .../a_stratified/final_evaluation_log.jsonl        |     2 +
 .../final_predictions.parquet                      |   Bin
 .../fold_metrics.json                              |   180 +-
 .../holdout.json                                   |    10 +-
 .../profile.json                                   |     0
 .../report/figures/oof_pr.png                      |   Bin
 .../report/figures/oof_roc.png                     |   Bin
 .../report/figures/test_pr.png                     |   Bin
 .../report/figures/test_roc.png                    |   Bin
 .../report/report.html                             |    15 +-
 .../report/report.md                               |    17 +-
 .../run.json                                       |    29 +-
 .../summary.json                                   |     0
 .../thresholds.json                                |    12 +-
 .../b_duplicate_groups/OMITTED_FILES.json          |     6 +
 docs/case_study/b_duplicate_groups/PROVENANCE.json |    13 +
 docs/case_study/b_duplicate_groups/config.json     |    31 +
 .../b_duplicate_groups/dataset_sha256.txt          |     1 +
 .../b_duplicate_groups/duplicate_sensitivity.json  |    58 +
 .../case_study/b_duplicate_groups/environment.json |    17 +
 .../b_duplicate_groups/final_evaluation.json       |   298 +
 .../b_duplicate_groups/final_evaluation_log.jsonl  |     2 +
 .../b_duplicate_groups/final_predictions.parquet   |   Bin 0 -> 53710 bytes
 .../b_duplicate_groups/fold_metrics.json           |  7472 ++++++++++++
 docs/case_study/b_duplicate_groups/holdout.json    | 11240 +++++++++++++++++++
 .../b_duplicate_groups/oof_predictions.parquet     |   Bin 0 -> 986610 bytes
 docs/case_study/b_duplicate_groups/profile.json    |   109 +
 .../b_duplicate_groups/report/figures/oof_pr.png   |   Bin 0 -> 62121 bytes
 .../b_duplicate_groups/report/figures/oof_roc.png  |   Bin 0 -> 47617 bytes
 .../b_duplicate_groups/report/figures/test_pr.png  |   Bin 0 -> 28919 bytes
 .../b_duplicate_groups/report/figures/test_roc.png |   Bin 0 -> 32182 bytes
 .../b_duplicate_groups/report/report.html          |    85 +
 .../case_study/b_duplicate_groups/report/report.md |   211 +
 docs/case_study/b_duplicate_groups/run.json        |   177 +
 docs/case_study/b_duplicate_groups/summary.json    |   725 ++
 docs/case_study/b_duplicate_groups/thresholds.json |   417 +
 .../OMITTED_FILES.json                             |    10 -
 .../final_evaluation_log.jsonl                     |     2 -
 docs/screenshots/01_upload_and_profile.png         |   Bin 0 -> 119397 bytes
 docs/screenshots/02_run_experiment.png             |   Bin 0 -> 99501 bytes
 docs/screenshots/03_results_and_thresholds.png     |   Bin 0 -> 120081 bytes
 docs/screenshots/04_final_evaluation.png           |   Bin 0 -> 84818 bytes
 docs/screenshots/05_final_evaluation_refused.png   |   Bin 0 -> 164761 bytes
 docs/screenshots/06_report.png                     |   Bin 0 -> 129156 bytes
 docs/screenshots/ui_check.json                     |    52 +
 frontend/app.py                                    |     4 +
 scripts/run_case_study.py                          |   740 +-
 scripts/ui_screenshots.py                          |   219 +
 scripts/verify_case_study_hashes.py                |    93 +
 src/imbalancelab/data/schema.py                    |     4 +
 src/imbalancelab/evaluation/metrics.py             |    12 +
 src/imbalancelab/evaluation/runner.py              |    16 +-
 src/imbalancelab/models/registry.py                |     2 +-
 src/imbalancelab/reporting/report.py               |    22 +
 src/imbalancelab/splitting/groups.py               |   174 +
 src/imbalancelab/splitting/splits.py               |   185 +-
 tests/snapshots/report_structure.md                |     5 +-
 tests/test_duplicate_groups.py                     |   270 +
 tests/test_metrics.py                              |    14 +
 tests/test_runner.py                               |    22 +
 72 files changed, 23251 insertions(+), 532 deletions(-)
````

#### Full gate output, Python 3.13.5 (verbatim)
````text
$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
61 files already formatted
[exit 0]

$ mypy
Success: no issues found in 40 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 48%]
........................................................................ [ 96%]
.....                                                                    [100%]
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
src\imbalancelab\data\schema.py                40      0   100%
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
src\imbalancelab\reporting\report.py          172     11    94%   59, 105, 107-109, 141, 188, 218, 267, 462, 464
src\imbalancelab\splitting\__init__.py          3      0   100%
src\imbalancelab\splitting\duplicates.py       24      0   100%
src\imbalancelab\splitting\groups.py           76      1    99%   61
src\imbalancelab\splitting\splits.py          251      2    99%   117, 123
src\imbalancelab\tracking\__init__.py           2      0   100%
src\imbalancelab\tracking\records.py          120      3    98%   89-90, 170
src\imbalancelab\workflow.py                  144      6    96%   62-63, 90, 135, 234, 258
-------------------------------------------------------------------------
TOTAL                                        2189     37    98%
149 passed, 1 warning in 113.28s (0:01:53)
[exit 0]
````

#### Full gate output, Python 3.11.15, local `.venv311` (verbatim; this is NOT a CI run)
````text
$ python --version
Python 3.11.15

$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
61 files already formatted
[exit 0]

$ mypy
Success: no issues found in 40 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 48%]
........................................................................ [ 96%]
.....                                                                    [100%]
============================== warnings summary ===============================
.venv311\Lib\site-packages\fastapi\testclient.py:1
  <project-root>\.venv311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.11.15-final-0 _______________

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
src\imbalancelab\data\schema.py                40      0   100%
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
src\imbalancelab\reporting\report.py          172     11    94%   59, 105, 107-109, 141, 188, 218, 267, 462, 464
src\imbalancelab\splitting\__init__.py          3      0   100%
src\imbalancelab\splitting\duplicates.py       24      0   100%
src\imbalancelab\splitting\groups.py           76      1    99%   61
src\imbalancelab\splitting\splits.py          251      2    99%   117, 123
src\imbalancelab\tracking\__init__.py           2      0   100%
src\imbalancelab\tracking\records.py          120      3    98%   89-90, 170
src\imbalancelab\workflow.py                  144      6    96%   62-63, 90, 135, 234, 258
-------------------------------------------------------------------------
TOTAL                                        2189     37    98%
149 passed, 1 warning in 149.68s (0:02:29)
[exit 0]
````

Tool paths and key versions in `.venv311`: `python`, `ruff`, `mypy` and `pytest` all resolve
from `.venv311/Scripts/`. numpy 2.4.6, pandas 3.0.6, scikit-learn 1.9.1, imbalanced-learn
0.14.2.

#### Source: src/imbalancelab/splitting/groups.py (verbatim)
````python
"""Group IDs for group-aware splitting: declared groups and/or exact-duplicate clusters.

With ``schema.duplicate_groups=True`` every set of rows with identical feature values (the
target, id, group and time columns are excluded) forms one *duplicate cluster*. Rows with
identical features but different labels are kept and stay in the same cluster. Splitting on
these clusters guarantees that no duplicate cluster crosses any train/validation/test boundary.

If the schema also declares a ``group_column``, declared groups are combined with duplicate
clusters by connected components: declared groups linked by a shared duplicate cluster are
merged into one split group. A declared group is therefore never split, no duplicate cluster
crosses a boundary, and a warning reports how many clusters spanned declared groups.
"""

from typing import Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

from imbalancelab.data.loader import LoadedDataset
from imbalancelab.profiling.profile import feature_row_hashes
from imbalancelab.profiling.warnings import ProfileWarning

GroupSource = Literal["declared", "duplicates", "declared+duplicates"]


class GroupInfo(BaseModel):
    """How split groups were formed; recorded in holdouts and run records."""

    source: GroupSource
    duplicate_groups: bool
    n_rows: int
    n_groups: int
    n_duplicate_clusters: int  # clusters of identical feature rows with more than one row
    n_rows_in_duplicate_clusters: int
    n_conflicting_label_clusters: int  # duplicate clusters whose rows have different labels
    n_rows_in_conflicting_clusters: int
    n_clusters_spanning_declared_groups: int = 0
    n_declared_groups: int | None = None
    n_declared_groups_merged: int = 0  # declared groups absorbed into a merged split group


class GroupingError(ValueError):
    """Groups cannot be formed (e.g. missing values in the declared group column)."""


def duplicate_cluster_ids(dataset: LoadedDataset) -> np.ndarray:
    """Integer cluster ID per row; rows with identical feature values share an ID."""
    if not dataset.feature_columns:
        raise GroupingError("duplicate_groups needs at least one feature column")
    hashes = feature_row_hashes(dataset.frame, dataset.feature_columns)
    codes, _ = pd.factorize(pd.Series(hashes), sort=False)
    return np.asarray(codes, dtype=np.int64)


def _declared(dataset: LoadedDataset) -> np.ndarray:
    col = dataset.schema.group_column
    if col is None:
        raise GroupingError("group strategy requires schema.group_column")
    series = dataset.frame[col]
    if series.isna().any():
        raise GroupingError(f"group column {col!r} has missing values")
    codes, _ = pd.factorize(series.astype(str), sort=True)
    return np.asarray(codes, dtype=np.int64)


def _cluster_stats(clusters: np.ndarray, y: np.ndarray) -> dict[str, int]:
    frame = pd.DataFrame({"c": clusters, "y": y})
    grouped = frame.groupby("c")["y"]
    sizes = grouped.size()
    multi = sizes[sizes > 1]
    conflicting = grouped.nunique()
    conflicting = conflicting[conflicting > 1]
    return {
        "n_duplicate_clusters": len(multi),
        "n_rows_in_duplicate_clusters": int(multi.sum()),
        "n_conflicting_label_clusters": len(conflicting),
        "n_rows_in_conflicting_clusters": int(sizes.loc[conflicting.index].sum()),
    }


def resolve_groups(
    dataset: LoadedDataset,
) -> tuple[np.ndarray | None, GroupInfo | None, list[ProfileWarning]]:
    """Split groups for ``dataset``: ``(None, None, [])`` when splitting is not group-aware."""
    schema = dataset.schema
    if schema.split_strategy == "temporal":
        return None, None, []
    declared = _declared(dataset) if schema.split_strategy == "group" else None
    if not schema.duplicate_groups:
        if declared is None:
            return None, None, []
        info = GroupInfo(
            source="declared",
            duplicate_groups=False,
            n_rows=dataset.n_rows,
            n_groups=int(len(np.unique(declared))),
            n_duplicate_clusters=0,
            n_rows_in_duplicate_clusters=0,
            n_conflicting_label_clusters=0,
            n_rows_in_conflicting_clusters=0,
            n_declared_groups=int(len(np.unique(declared))),
        )
        return declared, info, []

    clusters = duplicate_cluster_ids(dataset)
    stats = _cluster_stats(clusters, dataset.y)
    warnings: list[ProfileWarning] = []
    if stats["n_conflicting_label_clusters"]:
        warnings.append(
            ProfileWarning(
                code="conflicting_label_clusters",
                severity="info",
                message=(
                    f"{stats['n_conflicting_label_clusters']} duplicate cluster(s) "
                    f"({stats['n_rows_in_conflicting_clusters']} rows) have identical features "
                    "but different labels; they are kept and split together."
                ),
                evidence={
                    "n_clusters": stats["n_conflicting_label_clusters"],
                    "n_rows": stats["n_rows_in_conflicting_clusters"],
                },
            )
        )
    if declared is None:
        info = GroupInfo(
            source="duplicates",
            duplicate_groups=True,
            n_rows=dataset.n_rows,
            n_groups=int(len(np.unique(clusters))),
            **stats,
        )
        return clusters, info, warnings

    # connected components over a bipartite graph: declared-group nodes + cluster nodes
    n_declared = int(declared.max()) + 1
    n_nodes = n_declared + int(clusters.max()) + 1
    graph = coo_matrix(
        (np.ones(len(declared)), (declared, n_declared + clusters)), shape=(n_nodes, n_nodes)
    )
    _, component = connected_components(graph, directed=False)
    groups = np.asarray(component[declared], dtype=np.int64)
    spans = pd.DataFrame({"c": clusters, "d": declared}).groupby("c")["d"].nunique()
    n_spanning = int((spans > 1).sum())
    n_merged_groups = int(len(np.unique(groups)))
    info = GroupInfo(
        source="declared+duplicates",
        duplicate_groups=True,
        n_rows=dataset.n_rows,
        n_groups=n_merged_groups,
        n_clusters_spanning_declared_groups=n_spanning,
        n_declared_groups=n_declared,
        n_declared_groups_merged=n_declared - n_merged_groups,
        **stats,
    )
    if n_spanning:
        warnings.append(
            ProfileWarning(
                code="duplicate_clusters_span_declared_groups",
                message=(
                    f"{n_spanning} duplicate cluster(s) contain rows from more than one declared "
                    f"group; {n_declared} declared groups were merged into {n_merged_groups} "
                    "split groups so that no duplicate cluster crosses a split boundary."
                ),
                evidence={
                    "n_clusters_spanning": n_spanning,
                    "n_declared_groups": n_declared,
                    "n_split_groups": n_merged_groups,
                },
            )
        )
    return groups, info, warnings
````

#### Source: group-aware parts of src/imbalancelab/splitting/splits.py (verbatim excerpt)
````python
def pin_oversized_groups(groups: np.ndarray, eval_size: float, fraction: float) -> np.ndarray:
    """Boolean mask of rows whose group is too large to sit in an evaluation set.

    A group larger than ``fraction * eval_size`` rows cannot be placed in a test or validation
    set without dominating it: ``StratifiedGroupKFold`` then fills the rest of that set with
    whatever rebalances the class ratio, and the evaluation set stops being representative.
    Such groups are pinned to the training side instead. The evaluation population then excludes
    their rows, and callers record and report this.
    """
    sizes = pd.Series(groups).value_counts()
    oversized = sizes.index[sizes > fraction * eval_size]
    return np.isin(groups, np.asarray(oversized))


def _pinned_warning(
    where: str, mask: np.ndarray, groups: np.ndarray, limit: float
) -> ProfileWarning:
    n_groups = int(len(np.unique(groups[mask])))
    return ProfileWarning(
        code="oversized_groups_pinned_to_train",
        message=(
            f"{n_groups} group(s) covering {int(mask.sum())} rows exceed {limit:.0f} rows "
            f"(max_eval_group_fraction of the {where} size) and are always on the training "
            f"side; {where} metrics do not cover these rows."
        ),
        evidence={
            "where": where,
            "n_groups": n_groups,
            "n_rows": int(mask.sum()),
            "row_limit": float(limit),
        },
    )


def _balance_warnings(
    y: np.ndarray,
    test_idx: np.ndarray,
    eligible: np.ndarray,
    config: HoldoutConfig,
    n: int,
    groups: np.ndarray,
) -> list[ProfileWarning]:
    """Warn when the test set's size, prevalence or group composition is far from requested."""
    out: list[ProfileWarning] = []
    largest = float(pd.Series(groups[test_idx]).value_counts().iloc[0]) / max(len(test_idx), 1)
    if largest > DOMINANT_GROUP_SHARE:
        out.append(
            ProfileWarning(
                code="holdout_dominated_by_group",
                message=(
                    f"One split group makes up {largest:.1%} of the test set (more than "
                    f"{DOMINANT_GROUP_SHARE:.0%}); the test set may not be representative."
                ),
                evidence={"largest_group_share": largest},
            )
        )
    frac = len(test_idx) / n
    if abs(frac - config.test_size) > 0.25 * config.test_size:
        out.append(
            ProfileWarning(
                code="holdout_size_deviation",
                message=f"Test set is {frac:.1%} of rows; requested {config.test_size:.1%}.",
                evidence={"test_fraction": frac, "requested": config.test_size},
            )
        )
    ref = float(y[eligible].mean())
    prev = float(y[test_idx].mean())
    if ref > 0 and abs(prev - ref) > 0.25 * ref:
        out.append(
            ProfileWarning(
                code="holdout_prevalence_deviation",
                message=(
                    f"Test prevalence {prev:.4f} differs from {ref:.4f} (rows eligible for test) "
                    "by more than 25%."
                ),
                evidence={"test_prevalence": prev, "eligible_prevalence": ref},
            )
        )
    return out


def make_holdout(dataset: LoadedDataset, config: HoldoutConfig | None = None) -> Holdout:
    """Create the outer train/test holdout using the schema's split strategy."""
    config = config or HoldoutConfig()
    strategy = dataset.schema.split_strategy
    n = dataset.n_rows
    y = dataset.y
    all_idx = np.arange(n)
    gap_idx = np.array([], dtype=int)
    groups, group_info, group_warnings = _resolve(dataset)
    n_pinned_groups = n_pinned_rows = 0

    if strategy != "temporal" and groups is None:
        n_test = int(np.ceil(config.test_size * n))
        n_pos = int(y.sum())
        if min(n_pos, n - n_pos) < 2 or n_test < 2 or n - n_test < 2:
            raise SplitError("stratified holdout needs at least 2 samples of each class per side")
        rng = np.random.default_rng(config.seed)
        test_parts = []
        for cls in (0, 1):
            members = all_idx[y == cls]
            k = int(round(config.test_size * len(members)))
            k = min(max(k, 1), len(members) - 1)
            test_parts.append(rng.choice(members, size=k, replace=False))
        test_idx = np.concatenate(test_parts)
        train_idx = np.setdiff1d(all_idx, test_idx)
    elif groups is not None:
        target = config.test_size * n
        pinned = pin_oversized_groups(groups, target, config.max_eval_group_fraction)
        eligible = all_idx[~pinned]
        n_folds = max(2, int(round(len(eligible) / target)))
        n_eligible_groups = len(np.unique(groups[eligible]))
        if n_eligible_groups < n_folds:
            raise SplitError(
                f"group holdout needs at least {n_folds} distinct groups, found {n_eligible_groups}"
            )
        sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=config.seed)
        tr, te = next(iter(sgkf.split(eligible, y[eligible], groups[eligible])))
        test_idx = eligible[te]
        train_idx = np.concatenate([eligible[tr], all_idx[pinned]])
        n_pinned_groups, n_pinned_rows = int(len(np.unique(groups[pinned]))), int(pinned.sum())
        if n_pinned_rows:
            limit = config.max_eval_group_fraction * target
            group_warnings = [*group_warnings, _pinned_warning("test set", pinned, groups, limit)]
        group_warnings = [
            *group_warnings,
            *_balance_warnings(y, np.asarray(test_idx), eligible, config, n, groups),
        ]
    else:
        t = _time_values(dataset)
        uniq = np.unique(t)
        if len(uniq) < 2 + config.gap:
            raise SplitError("temporal holdout needs more distinct time values than gap + 1")
        counts = np.array([np.sum(t == u) for u in uniq])
        rows_from_end = np.cumsum(counts[::-1])[::-1]  # rows with time >= uniq[k]
        target = config.test_size * n
        candidates = np.arange(1 + config.gap, len(uniq))
        k = int(candidates[np.argmin(np.abs(rows_from_end[candidates] - target))])
        test_idx = all_idx[t >= uniq[k]]
        train_idx = all_idx[t < uniq[k - config.gap]]
        gap_idx = all_idx[(t >= uniq[k - config.gap]) & (t < uniq[k])]

    _require_both_classes(y, np.asarray(train_idx), "outer-train split")
    _require_both_classes(y, np.asarray(test_idx), "test split")
    test_list = _sorted_list(np.asarray(test_idx))
    return Holdout(
        strategy=strategy,
        config=config,
        dataset_sha256=dataset.sha256,
        n_rows=n,
        train_idx=_sorted_list(np.asarray(train_idx)),
        test_idx=test_list,
        gap_idx=_sorted_list(gap_idx),
        test_sha256=indices_sha256(test_list),
        duplicate_groups=dataset.schema.duplicate_groups,
        group_info=group_info,
        n_pinned_groups=n_pinned_groups,
        n_pinned_rows=n_pinned_rows,
        warnings=group_warnings,
    )


def make_cv_folds(
    dataset: LoadedDataset, holdout: Holdout, config: CVConfig | None = None
) -> CVPlan:
    """Inner CV folds over outer-train rows, using the schema's split strategy."""
    config = config or CVConfig()
    check_holdout(dataset, holdout)
    strategy = dataset.schema.split_strategy
    outer = np.asarray(holdout.train_idx)
    y = dataset.y
    y_outer = y[outer]
    warnings: list[ProfileWarning] = []
    folds: list[Fold] = []
    n_repeats = config.n_repeats
    all_groups, _, _ = _resolve(dataset)
    n_groups: int | None = None
    n_pinned_groups = n_pinned_rows = 0

    if strategy != "temporal" and all_groups is None:
        n_min = int(min(y_outer.sum(), len(y_outer) - y_outer.sum()))
        if n_min < config.n_splits:
            raise SplitError(
                f"only {n_min} minority samples in outer-train; cannot build "
                f"{config.n_splits} stratified folds"
            )
        rskf = RepeatedStratifiedKFold(
            n_splits=config.n_splits, n_repeats=config.n_repeats, random_state=config.seed
        )
        for i, (tr, va) in enumerate(rskf.split(outer, y_outer)):
            folds.append(_fold(i // config.n_splits, i % config.n_splits, outer[tr], outer[va]))
    elif all_groups is not None:
        groups = all_groups[outer]
        n_groups = len(np.unique(groups))
        fold_size = len(outer) / config.n_splits
        pinned = pin_oversized_groups(groups, fold_size, config.max_eval_group_fraction)
        eligible, always_train = outer[~pinned], outer[pinned]
        n_eligible_groups = len(np.unique(groups[~pinned]))
        if n_eligible_groups < config.n_splits:
            raise SplitError(
                f"only {n_eligible_groups} groups in outer-train; cannot build "
                f"{config.n_splits} folds"
            )
        if pinned.any():
            n_pinned_groups = int(len(np.unique(groups[pinned])))
            n_pinned_rows = int(pinned.sum())
            limit = config.max_eval_group_fraction * fold_size
            warnings.append(_pinned_warning("validation fold", pinned, groups, limit))
        for r in range(config.n_repeats):
            sgkf = StratifiedGroupKFold(
                n_splits=config.n_splits, shuffle=True, random_state=config.seed + r
            )
            for f, (tr, va) in enumerate(sgkf.split(eligible, y[eligible], groups[~pinned])):
                folds.append(
                    _fold(r, f, np.concatenate([eligible[tr], always_train]), eligible[va])
                )
    else:
        if config.n_repeats != 1:
            warnings.append(
                ProfileWarning(
                    code="temporal_repeats_ignored",
                    severity="info",
                    message="Temporal CV is deterministic; n_repeats was set to 1.",
                    evidence={"requested_n_repeats": config.n_repeats},
                )
            )
        n_repeats = 1
        t = _time_values(dataset)[outer]
        uniq = np.unique(t)
        chunks = np.array_split(np.arange(len(uniq)), config.n_splits + 1)
        if any(len(c) <= config.gap for c in chunks[1:]):
            raise SplitError(
                f"{len(uniq)} distinct time values are too few for {config.n_splits} temporal "
                f"folds with gap {config.gap}"
            )
        for f in range(config.n_splits):
            train_end = uniq[chunks[f][-1]]
            val_chunk = chunks[f + 1][config.gap :]
            val_start, val_end = uniq[val_chunk[0]], uniq[val_chunk[-1]]
            tr = outer[t <= train_end]
            va = outer[(t >= val_start) & (t <= val_end)]
            folds.append(_fold(0, f, tr, va))

    for fold in folds:
        _require_both_classes(y, np.asarray(fold.train_idx), f"training fold {fold.fold}")
        n_pos = int(y[fold.val_idx].sum())
        if n_pos == 0 or n_pos == len(fold.val_idx):
            warnings.append(
                ProfileWarning(
                    code="single_class_validation_fold",
                    message=(
                        f"Validation fold (repeat {fold.repeat}, fold {fold.fold}) has a single "
                        "class; ranking metrics are undefined for it."
                    ),
                    evidence={"repeat": fold.repeat, "fold": fold.fold, "n_positive": n_pos},
                )
            )
    return CVPlan(
        strategy=strategy,
        config=config,
        n_repeats_effective=n_repeats,
        folds=folds,
        fold_indices_sha256=folds_sha256(folds),
        warnings=warnings,
        duplicate_groups=dataset.schema.duplicate_groups,
        n_groups=n_groups,
        n_pinned_groups=n_pinned_groups,
        n_pinned_rows=n_pinned_rows,
    )
````

#### Tests: tests/test_duplicate_groups.py (verbatim)
````python
"""H1: duplicate-aware splitting. No duplicate cluster may cross any split boundary."""

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from conftest import make_imbalanced_frame
from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.splitting import (
    CVConfig,
    HoldoutConfig,
    HoldoutMismatchError,
    SplitError,
    cross_boundary_duplicates,
    get_or_create_holdout,
    make_cv_folds,
    make_holdout,
)
from imbalancelab.splitting.groups import resolve_groups
from imbalancelab.tracking import RunRecord


def duplicated_frame(n: int = 400, dup_fraction: float = 0.5, seed: int = 0) -> pd.DataFrame:
    """Synthetic frame where ~dup_fraction of rows are copied 1-3 times (new row ids)."""
    base = make_imbalanced_frame(n=n, positive_rate=0.15, seed=seed)
    base = base.drop(columns=["ts"])
    rng = np.random.default_rng(seed)
    src = rng.choice(n, size=int(n * dup_fraction), replace=False)
    copies = base.iloc[np.repeat(src, rng.integers(1, 4, size=len(src)))].copy()
    # a few copies get the opposite label -> conflicting-label clusters
    flip = copies.index[:5]
    copies.loc[flip, "label"] = np.where(copies.loc[flip, "label"] == "yes", "no", "yes")
    frame = pd.concat([base, copies], ignore_index=True)
    frame["row_id"] = np.arange(len(frame))
    return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _ds(write_csv, frame=None, name="dup.csv", **kw):
    schema = DatasetSchema.model_validate(
        {
            "target": "label",
            "positive_label": "yes",
            "id_column": "row_id",
            "duplicate_groups": True,
            **kw,
        }
    )
    return load_dataset(write_csv(duplicated_frame() if frame is None else frame, name), schema)


def independent_clusters(ds) -> np.ndarray:
    """Cluster key computed independently of the library (repr of the feature tuple)."""
    return np.array([repr(tuple(r)) for r in ds.frame[ds.feature_columns].itertuples(index=False)])


def _crossing(keys: np.ndarray, a: list[int], b: list[int]) -> int:
    return len(set(keys[a]) & set(keys[b]))


def test_no_duplicate_cluster_crosses_outer_or_inner_boundaries(write_csv) -> None:
    ds = _ds(write_csv)
    keys = independent_clusters(ds)
    assert len(np.unique(keys)) < ds.n_rows  # the fixture really has duplicates
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=1))
    assert holdout.duplicate_groups is True
    assert _crossing(keys, holdout.train_idx, holdout.test_idx) == 0
    assert sorted(holdout.train_idx + holdout.test_idx) == list(range(ds.n_rows))
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=3, seed=2))
    assert plan.duplicate_groups is True and len(plan.folds) == 12
    for fold in plan.folds:
        assert _crossing(keys, fold.train_idx, fold.val_idx) == 0
        assert not set(fold.val_idx) & set(holdout.test_idx)
    # the existing cross-boundary duplicate check must report zero
    assert cross_boundary_duplicates(ds, holdout, plan) == []


def test_without_duplicate_groups_the_same_data_crosses_boundaries(write_csv) -> None:
    ds = _ds(write_csv, duplicate_groups=False)
    holdout = make_holdout(ds, HoldoutConfig(seed=1))
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=1))
    warnings = cross_boundary_duplicates(ds, holdout, plan)
    assert warnings and warnings[0].evidence["test_rows_duplicating_train"] > 0


def test_reproducible_by_seed(write_csv) -> None:
    ds = _ds(write_csv)
    a = make_holdout(ds, HoldoutConfig(seed=5))
    b = make_holdout(ds, HoldoutConfig(seed=5))
    c = make_holdout(ds, HoldoutConfig(seed=6))
    assert a == b and a.test_idx != c.test_idx
    cv = CVConfig(n_splits=4, n_repeats=2, seed=3)
    assert (
        make_cv_folds(ds, a, cv).fold_indices_sha256 == make_cv_folds(ds, a, cv).fold_indices_sha256
    )
    other = CVConfig(n_splits=4, n_repeats=2, seed=4)
    assert (
        make_cv_folds(ds, a, other).fold_indices_sha256
        != make_cv_folds(ds, a, cv).fold_indices_sha256
    )


def test_stratification_within_tolerance(write_csv) -> None:
    ds = _ds(write_csv)
    rate = ds.y.mean()
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=1))
    assert abs(ds.y[holdout.test_idx].mean() - rate) < 0.03
    assert len(holdout.test_idx) == pytest.approx(0.2 * ds.n_rows, rel=0.15)
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2))
    outer_rate = ds.y[holdout.train_idx].mean()
    for fold in plan.folds:
        assert abs(ds.y[fold.val_idx].mean() - outer_rate) < 0.05


def test_conflicting_labels_kept_in_one_cluster_and_counted(write_csv) -> None:
    ds = _ds(write_csv)
    groups, info, warnings = resolve_groups(ds)
    assert groups is not None and info is not None
    keys = independent_clusters(ds)
    frame = pd.DataFrame({"k": keys, "y": ds.y})
    expected_conflicts = int((frame.groupby("k")["y"].nunique() > 1).sum())
    sizes = frame.groupby("k").size()
    assert expected_conflicts > 0
    assert info.n_conflicting_label_clusters == expected_conflicts
    assert info.n_duplicate_clusters == int((sizes > 1).sum())
    assert info.n_rows_in_duplicate_clusters == int(sizes[sizes > 1].sum())
    assert info.n_groups == len(np.unique(keys)) and info.source == "duplicates"
    assert "conflicting_label_clusters" in {w.code for w in warnings}
    # same key <=> same group id
    for key in np.unique(keys)[:50]:
        assert len(np.unique(groups[keys == key])) == 1


def test_combined_with_declared_groups(write_csv) -> None:
    frame = duplicated_frame()
    frame["group"] = np.arange(len(frame)) % 40  # duplicates land in different declared groups
    ds = _ds(write_csv, frame, "g.csv", group_column="group", split_strategy="group")
    groups, info, warnings = resolve_groups(ds)
    assert info is not None and info.source == "declared+duplicates"
    assert info.n_clusters_spanning_declared_groups > 0
    assert info.n_groups <= 40 and info.n_declared_groups_merged == 40 - info.n_groups
    assert "duplicate_clusters_span_declared_groups" in {w.code for w in warnings}
    declared = ds.frame["group"].to_numpy()
    for g in np.unique(declared):  # a declared group is never split across merged groups
        assert len(np.unique(groups[declared == g])) == 1

    sparse = duplicated_frame(n=600, dup_fraction=0.05, seed=3)
    sparse["group"] = np.arange(len(sparse)) % 60
    ds2 = _ds(write_csv, sparse, "g2.csv", group_column="group", split_strategy="group")
    holdout = make_holdout(ds2, HoldoutConfig(test_size=0.25, seed=0))
    keys = independent_clusters(ds2)
    assert _crossing(keys, holdout.train_idx, holdout.test_idx) == 0
    assert not set(declared_of(ds2, holdout.train_idx)) & set(declared_of(ds2, holdout.test_idx))
    plan = make_cv_folds(ds2, holdout, CVConfig(n_splits=3, n_repeats=1))
    for fold in plan.folds:
        assert _crossing(keys, fold.train_idx, fold.val_idx) == 0


def declared_of(ds, idx):
    return ds.frame["group"].to_numpy()[idx]


def test_declared_groups_without_duplicate_flag_unchanged(write_csv) -> None:
    frame = make_imbalanced_frame()
    ds = _ds(
        write_csv,
        frame,
        "plain.csv",
        group_column="group",
        split_strategy="group",
        duplicate_groups=False,
    )
    _, info, warnings = resolve_groups(ds)
    assert info is not None and info.source == "declared" and warnings == []
    assert make_holdout(ds).group_info == info


def test_run_record_contains_duplicate_groups(write_csv, tmp_path) -> None:
    ds = _ds(write_csv)
    holdout = make_holdout(ds)
    cfg = ExperimentConfig.model_validate({"candidates": [], "cv": {"n_splits": 3, "n_repeats": 1}})
    result = run_experiment(ds, holdout, cfg, tmp_path / "runs")
    run = RunRecord(result.run_dir).run
    assert run["holdout"]["duplicate_groups"] is True
    assert run["cv"]["duplicate_groups"] is True
    info = run["holdout"]["group_info"]
    assert info["n_duplicate_clusters"] > 0 and info["n_groups"] < ds.n_rows
    assert run["cv"]["n_groups_outer_train"] > 0
    codes = {w["code"] for w in run["split_warnings"]}
    assert "cross_boundary_duplicates" not in codes
    assert "conflicting_label_clusters" in codes


def test_flag_change_is_a_holdout_mismatch_and_temporal_is_rejected(write_csv, tmp_path) -> None:
    ds = _ds(write_csv)
    path = tmp_path / "holdout.json"
    get_or_create_holdout(ds, HoldoutConfig(), path)
    plain = _ds(write_csv, duplicate_groups=False)
    assert plain.sha256 == ds.sha256
    with pytest.raises(HoldoutMismatchError, match="duplicate_groups"):
        get_or_create_holdout(plain, None, path)
    with pytest.raises(ValidationError, match="temporal"):
        DatasetSchema(
            target="label",
            positive_label="yes",
            time_column="ts",
            split_strategy="temporal",
            duplicate_groups=True,
        )


def test_no_features_is_a_split_error(write_csv) -> None:
    frame = pd.DataFrame({"row_id": range(40), "label": ["yes", "no", "no", "no"] * 10})
    ds = _ds(write_csv, frame, "nofeat.csv")
    with pytest.raises(SplitError, match="feature"):
        make_holdout(ds)


def giant_cluster_frame(n: int = 1000, giant: int = 300, seed: int = 0) -> pd.DataFrame:
    """Mirror of the mammography failure mode: one cluster of `giant` identical rows with only a
    few positives, plus ordinary unique rows."""
    frame = make_imbalanced_frame(n=n, positive_rate=0.08, seed=seed).drop(columns=["ts", "group"])
    frame.loc[: giant - 1, ["x_signal", "x_noise", "color"]] = [-1.0, 0.0, "a"]
    frame.loc[: giant - 1, "label"] = "no"
    frame.loc[[0, 1], "label"] = "yes"  # 2 conflicting positives inside the giant cluster
    return frame.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def test_giant_cluster_is_pinned_to_train_and_test_stays_representative(write_csv) -> None:
    ds = _ds(write_csv, giant_cluster_frame(), "giant.csv")
    keys = independent_clusters(ds)
    giant_key = pd.Series(keys).value_counts().index[0]
    in_giant = keys == giant_key
    assert in_giant.sum() == 300
    holdout = make_holdout(ds, HoldoutConfig(test_size=0.2, seed=0))
    assert not in_giant[holdout.test_idx].any()  # giant cluster entirely on the training side
    assert holdout.n_pinned_groups == 1 and holdout.n_pinned_rows == 300
    codes = {w.code for w in holdout.warnings}
    assert "oversized_groups_pinned_to_train" in codes
    assert "holdout_size_deviation" not in codes and "holdout_prevalence_deviation" not in codes
    eligible = ~in_giant
    assert abs(ds.y[holdout.test_idx].mean() - ds.y[eligible].mean()) < 0.03
    assert abs(len(holdout.test_idx) / ds.n_rows - 0.2) < 0.05
    plan = make_cv_folds(ds, holdout, CVConfig(n_splits=4, n_repeats=2))
    assert plan.n_pinned_groups == 1 and plan.n_pinned_rows == 300
    outer_eligible = np.asarray(holdout.train_idx)[~in_giant[holdout.train_idx]]
    for fold in plan.folds:
        assert in_giant[fold.train_idx].sum() == 300 and not in_giant[fold.val_idx].any()
        assert _crossing(keys, fold.train_idx, fold.val_idx) == 0
        assert abs(ds.y[fold.val_idx].mean() - ds.y[outer_eligible].mean()) < 0.05
    assert cross_boundary_duplicates(ds, holdout, plan) == []


def test_without_pinning_a_dominated_test_set_is_flagged(write_csv) -> None:
    """max_eval_group_fraction=1.0 lets a cluster just below the test size into the test set;
    the balance check must then report that one group dominates it (the T-R1 mammography
    failure mode)."""
    ds = _ds(write_csv, giant_cluster_frame(giant=180), "giant2.csv")
    keys = independent_clusters(ds)
    giant_key = pd.Series(keys).value_counts().index[0]
    for seed in range(20):
        holdout = make_holdout(ds, HoldoutConfig(seed=seed, max_eval_group_fraction=1.0))
        assert holdout.n_pinned_rows == 0
        if (keys[holdout.test_idx] == giant_key).any():
            codes = {w.code for w in holdout.warnings}
            assert "holdout_dominated_by_group" in codes
            return
    pytest.fail("no seed placed the giant cluster in the test set")
````

#### Run (a) summary.json (verbatim, docs/case_study/a_stratified/summary.json)
````json
{
  "primary_metric": "average_precision",
  "reference_threshold": 0.5,
  "beta": 1.0,
  "models": {
    "dummy_prior": {
      "average_precision": {
        "mean": 0.023250590979636575,
        "std": 0.0002812770375963889,
        "min": 0.022917831190609278,
        "max": 0.023476802683063163,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.5,
        "std": 0.0,
        "min": 0.5,
        "max": 0.5,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.022710042532557245,
        "std": 0.00026817979627044087,
        "min": 0.022392777233411217,
        "max": 0.022925722353373645,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": null,
        "std": null,
        "min": null,
        "max": null,
        "n": 0,
        "n_undefined": 15
      },
      "recall": {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.5,
        "std": 0.0,
        "min": 0.5,
        "max": 0.5,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": null,
        "std": null,
        "min": null,
        "max": null,
        "n": 0,
        "n_undefined": 15
      }
    },
    "logreg_balanced": {
      "average_precision": {
        "mean": 0.542749884580708,
        "std": 0.07827691541305688,
        "min": 0.43176624611436953,
        "max": 0.6932320574104825,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9268102624271075,
        "std": 0.024018929034882026,
        "min": 0.8962623951182302,
        "max": 0.9681308254730144,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.08294895381802032,
        "std": 0.004145577116287495,
        "min": 0.07485619693343284,
        "max": 0.09031470882185776,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.16511623002181525,
        "std": 0.00995453730312922,
        "min": 0.14782608695652175,
        "max": 0.1891891891891892,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.8447154471544718,
        "std": 0.03761178644437668,
        "min": 0.7619047619047619,
        "max": 0.9024390243902439,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.27606090604812444,
        "std": 0.014188916603150008,
        "min": 0.25092250922509224,
        "max": 0.30837004405286345,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.27606090604812444,
        "std": 0.014188916603150008,
        "min": 0.25092250922509224,
        "max": 0.30837004405286345,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.8713738204756127,
        "std": 0.017541526147519457,
        "min": 0.8323253786640514,
        "max": 0.8977298096779596,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.34567071119222825,
        "std": 0.01585569496318345,
        "min": 0.31797130517093397,
        "max": 0.37168744959905,
        "n": 15,
        "n_undefined": 0
      }
    },
    "hgb": {
      "average_precision": {
        "mean": 0.7174977970301364,
        "std": 0.05410481600986274,
        "min": 0.6150266188799941,
        "max": 0.8114997412534143,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9144164893031659,
        "std": 0.020920168690610527,
        "min": 0.8757529915228828,
        "max": 0.9457883840034871,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.011096713537263447,
        "std": 0.001984478615040447,
        "min": 0.0072485310553078485,
        "max": 0.015014957686322923,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.8197989821213884,
        "std": 0.07917924080730196,
        "min": 0.6363636363636364,
        "max": 0.9354838709677419,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.5818041037553232,
        "std": 0.06761724913071775,
        "min": 0.4634146341463415,
        "max": 0.7073170731707317,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.6791143062406891,
        "std": 0.06612055409671563,
        "min": 0.56,
        "max": 0.8055555555555556,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.6791143062406891,
        "std": 0.06612055409671563,
        "min": 0.56,
        "max": 0.8055555555555556,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.7893571238174848,
        "std": 0.034137601277815274,
        "min": 0.7297050287436513,
        "max": 0.8530864542055031,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.6838811228067845,
        "std": 0.06685172428530259,
        "min": 0.5549046270646663,
        "max": 0.8098105167523445,
        "n": 15,
        "n_undefined": 0
      }
    },
    "hgb+random_under": {
      "average_precision": {
        "mean": 0.6075196099292566,
        "std": 0.09861280385697968,
        "min": 0.45818531281262553,
        "max": 0.7697662948687506,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.945851219084043,
        "std": 0.016678699431005493,
        "min": 0.9153736674666517,
        "max": 0.9742279281489357,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.07938705691945844,
        "std": 0.010543555679419881,
        "min": 0.052509757228916744,
        "max": 0.09246671977801667,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.18379769548608332,
        "std": 0.02061327443251326,
        "min": 0.15879828326180256,
        "max": 0.24305555555555555,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.8910956252419668,
        "std": 0.03459821137342898,
        "min": 0.8333333333333334,
        "max": 0.9761904761904762,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.30399422347944044,
        "std": 0.02606880903122591,
        "min": 0.2690909090909091,
        "max": 0.3763440860215054,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.30399422347944044,
        "std": 0.02606880903122591,
        "min": 0.2690909090909091,
        "max": 0.3763440860215054,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.8977682039467255,
        "std": 0.013508022646766567,
        "min": 0.8802304674730304,
        "max": 0.9291370240139558,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.37879744182085745,
        "std": 0.020161588260878216,
        "min": 0.34585985657629337,
        "max": 0.4290697051835578,
        "n": 15,
        "n_undefined": 0
      }
    },
    "hgb+smote": {
      "average_precision": {
        "mean": 0.7449044689702335,
        "std": 0.03624711551815831,
        "min": 0.667465757597999,
        "max": 0.7937392978749368,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9230474668272123,
        "std": 0.023144446378935504,
        "min": 0.8815440642964782,
        "max": 0.9725515850301196,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.015239935221823604,
        "std": 0.0014362250452288473,
        "min": 0.012526806592581676,
        "max": 0.017708196510980278,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.6016771510054831,
        "std": 0.05491327851545918,
        "min": 0.5283018867924528,
        "max": 0.7142857142857143,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.7595818815331012,
        "std": 0.04376421811577722,
        "min": 0.6829268292682927,
        "max": 0.8095238095238095,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.6693712873152541,
        "std": 0.03382704020309724,
        "min": 0.5957446808510638,
        "max": 0.717391304347826,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.6693712873152541,
        "std": 0.03382704020309724,
        "min": 0.5957446808510638,
        "max": 0.717391304347826,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.8736873861057765,
        "std": 0.021313413223717943,
        "min": 0.8343123848858627,
        "max": 0.8987550397733464,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.6663690483727182,
        "std": 0.033368556343529955,
        "min": 0.5901090955947271,
        "max": 0.7128344655191368,
        "n": 15,
        "n_undefined": 0
      }
    },
    "random_forest": {
      "average_precision": {
        "mean": 0.7094237356099369,
        "std": 0.0706666530975776,
        "min": 0.5437541717189296,
        "max": 0.812411611679706,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9310155276577087,
        "std": 0.015557121545298322,
        "min": 0.8998437238376961,
        "max": 0.9583217056426857,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.012612330590953942,
        "std": 0.0016286640602924975,
        "min": 0.00991477175322428,
        "max": 0.01623888625528412,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.7680970584126471,
        "std": 0.09598772385107618,
        "min": 0.5294117647058824,
        "max": 0.8787878787878788,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.5578010065814945,
        "std": 0.10286847847726083,
        "min": 0.3902439024390244,
        "max": 0.7804878048780488,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.6431289828021449,
        "std": 0.09316213430685173,
        "min": 0.48,
        "max": 0.8205128205128205,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.6431289828021449,
        "std": 0.09316213430685173,
        "min": 0.48,
        "max": 0.8205128205128205,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.7768787635053813,
        "std": 0.051805809098377585,
        "min": 0.69254758051013,
        "max": 0.8888136964893676,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.6461457859756273,
        "std": 0.092374232746749,
        "min": 0.4711105655031107,
        "max": 0.8176478146968102,
        "n": 15,
        "n_undefined": 0
      }
    }
  },
  "comparisons": [
    {
      "candidate": "hgb",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.6942472060504998,
      "std_diff": 0.054137055608483794,
      "min_diff": 0.5921087876893848,
      "max_diff": 0.7880360541025763,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.4144164893031658,
      "std_diff": 0.020920168690610527,
      "min_diff": 0.3757529915228828,
      "max_diff": 0.4457883840034871,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.1747479124494283,
      "std_diff": 0.08557163061389875,
      "min_diff": 0.028545074853885466,
      "max_diff": 0.3179166265678247,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": -0.012393773123941795,
      "std_diff": 0.01917308409836345,
      "min_diff": -0.05384741188977027,
      "max_diff": 0.009458391255758203,
      "wins": 5,
      "losses": 10,
      "ties": 0,
      "win_fraction": 0.3333333333333333
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.5842690189496199,
      "std_diff": 0.09850506020371595,
      "min_diff": 0.43526748162201623,
      "max_diff": 0.7468484636781413,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.44585121908404307,
      "std_diff": 0.016678699431005493,
      "min_diff": 0.4153736674666517,
      "max_diff": 0.47422792814893566,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.0647697253485484,
      "std_diff": 0.09317354432744823,
      "min_diff": -0.12126928516753577,
      "max_diff": 0.2227356105896493,
      "wins": 12,
      "losses": 3,
      "ties": 0,
      "win_fraction": 0.8
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.019040956656935414,
      "std_diff": 0.021551183528178027,
      "min_diff": -0.033069152201819496,
      "max_diff": 0.050573477702740344,
      "wins": 13,
      "losses": 2,
      "ties": 0,
      "win_fraction": 0.8666666666666667
    },
    {
      "candidate": "hgb+smote",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.7216538779905971,
      "std_diff": 0.03620037440605197,
      "min_diff": 0.6445479264073897,
      "max_diff": 0.7708214666843275,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+smote",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.4230474668272125,
      "std_diff": 0.023144446378935504,
      "min_diff": 0.38154406429647825,
      "max_diff": 0.4725515850301196,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+smote",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.20215458438952555,
      "std_diff": 0.07528606515761209,
      "min_diff": 0.056444356609292035,
      "max_diff": 0.32552291104026343,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+smote",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": -0.0037627955998951633,
      "std_diff": 0.03314185657182657,
      "min_diff": -0.06862197912596968,
      "max_diff": 0.06156131599749226,
      "wins": 8,
      "losses": 7,
      "ties": 0,
      "win_fraction": 0.5333333333333333
    },
    {
      "candidate": "random_forest",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.6861731446303004,
      "std_diff": 0.07063265803512479,
      "min_diff": 0.5208363405283203,
      "max_diff": 0.788947924528868,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "random_forest",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.43101552765770884,
      "std_diff": 0.015557121545298322,
      "min_diff": 0.39984372383769606,
      "max_diff": 0.4583217056426857,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "random_forest",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.16667385102922877,
      "std_diff": 0.09107584484822627,
      "min_diff": -0.03570042626123171,
      "max_diff": 0.33248637101499956,
      "wins": 14,
      "losses": 1,
      "ties": 0,
      "win_fraction": 0.9333333333333333
    },
    {
      "candidate": "random_forest",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.004205265230601089,
      "std_diff": 0.0218813096515085,
      "min_diff": -0.02822525690299016,
      "max_diff": 0.03867855098536277,
      "wins": 10,
      "losses": 5,
      "ties": 0,
      "win_fraction": 0.6666666666666666
    },
    {
      "candidate": "logreg_balanced",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.5194992936010714,
      "std_diff": 0.07827250771309853,
      "min_diff": 0.40884841492376023,
      "max_diff": 0.6697552547274194,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "logreg_balanced",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.4268102624271077,
      "std_diff": 0.024018929034882026,
      "min_diff": 0.39626239511823025,
      "max_diff": 0.46813082547301443,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    }
  ],
  "best_candidate_by_mean_oof_ap": "hgb+smote",
  "selection_rule": "candidate with the highest mean out-of-fold average precision; test data is not used"
}
````

#### Run (b) summary.json (verbatim, docs/case_study/b_duplicate_groups/summary.json)
````json
{
  "primary_metric": "average_precision",
  "reference_threshold": 0.5,
  "beta": 1.0,
  "models": {
    "dummy_prior": {
      "average_precision": {
        "mean": 0.03225806451612902,
        "std": 1.436487510905098e-17,
        "min": 0.03225806451612903,
        "max": 0.03225806451612903,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.5,
        "std": 0.0,
        "min": 0.5,
        "max": 0.5,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.031373342146110934,
        "std": 5.2453107553144695e-18,
        "min": 0.031373342146110934,
        "max": 0.03137334214611094,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": null,
        "std": null,
        "min": null,
        "max": null,
        "n": 0,
        "n_undefined": 15
      },
      "recall": {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.0,
        "std": 0.0,
        "min": 0.0,
        "max": 0.0,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.5,
        "std": 0.0,
        "min": 0.5,
        "max": 0.5,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": null,
        "std": null,
        "min": null,
        "max": null,
        "n": 0,
        "n_undefined": 15
      }
    },
    "logreg_balanced": {
      "average_precision": {
        "mean": 0.5681025594697137,
        "std": 0.0931561503908793,
        "min": 0.4151768009656199,
        "max": 0.7477918636283148,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9244859956909818,
        "std": 0.01768070941471875,
        "min": 0.8870960295475531,
        "max": 0.9479916897506925,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.12775782791419305,
        "std": 0.006512026180518908,
        "min": 0.11668719734599665,
        "max": 0.13475839519574712,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.1439815170456348,
        "std": 0.007828472672958076,
        "min": 0.1350210970464135,
        "max": 0.16097560975609757,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.8842105263157894,
        "std": 0.034167121105268455,
        "min": 0.8157894736842105,
        "max": 0.9473684210526315,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.24750969672766734,
        "std": 0.01150288241344175,
        "min": 0.23272727272727273,
        "max": 0.2716049382716049,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.24750969672766734,
        "std": 0.01150288241344175,
        "min": 0.23272727272727273,
        "max": 0.2716049382716049,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.8542105263157895,
        "std": 0.01436868575346558,
        "min": 0.8263157894736842,
        "max": 0.8776315789473683,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.31407887602419055,
        "std": 0.013146664773799575,
        "min": 0.29188873847581265,
        "max": 0.3376550543717895,
        "n": 15,
        "n_undefined": 0
      }
    },
    "hgb": {
      "average_precision": {
        "mean": 0.7294648617617147,
        "std": 0.058943023430714586,
        "min": 0.6216735912885784,
        "max": 0.7941863533931367,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9542005232379194,
        "std": 0.019121049792658804,
        "min": 0.9145198522622345,
        "max": 0.9821329639889197,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.01558278406078144,
        "std": 0.0025070761759704795,
        "min": 0.012725904886995194,
        "max": 0.021367502300019797,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.812059648917279,
        "std": 0.06664040954663779,
        "min": 0.72,
        "max": 0.9230769230769231,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.5964912280701754,
        "std": 0.08301945902281647,
        "min": 0.42105263157894735,
        "max": 0.6842105263157895,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.6838433151895539,
        "std": 0.06300190724600722,
        "min": 0.5517241379310345,
        "max": 0.7575757575757576,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.6838433151895539,
        "std": 0.06300190724600722,
        "min": 0.5517241379310345,
        "max": 0.7575757575757576,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.7958771929824561,
        "std": 0.04118465425839463,
        "min": 0.7087719298245614,
        "max": 0.8390350877192982,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.6855777102021887,
        "std": 0.05985417053524367,
        "min": 0.5710538289272977,
        "max": 0.760032281105863,
        "n": 15,
        "n_undefined": 0
      }
    },
    "hgb+random_under": {
      "average_precision": {
        "mean": 0.546461061472672,
        "std": 0.06938836673997291,
        "min": 0.4614143512359903,
        "max": 0.7023027701820778,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9493744228993536,
        "std": 0.016792378915905147,
        "min": 0.9186172668513389,
        "max": 0.9779085872576178,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.13982173863718372,
        "std": 0.025983640297729992,
        "min": 0.10722462332884795,
        "max": 0.18908826468849846,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.1581021089583363,
        "std": 0.021542235888760485,
        "min": 0.1259259259259259,
        "max": 0.19170984455958548,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.9245614035087718,
        "std": 0.032788047535735415,
        "min": 0.868421052631579,
        "max": 1.0,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.2693843705026079,
        "std": 0.03139402127213861,
        "min": 0.22077922077922077,
        "max": 0.3203463203463203,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.2693843705026079,
        "std": 0.03139402127213861,
        "min": 0.22077922077922077,
        "max": 0.3203463203463203,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.8784502923976608,
        "std": 0.018243314471758594,
        "min": 0.843859649122807,
        "max": 0.918421052631579,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.34215462853104645,
        "std": 0.03046325590475478,
        "min": 0.2890883757190989,
        "max": 0.3994762621574004,
        "n": 15,
        "n_undefined": 0
      }
    },
    "hgb+smote": {
      "average_precision": {
        "mean": 0.7514744607150611,
        "std": 0.06107757682018092,
        "min": 0.622730649002376,
        "max": 0.8226454252464432,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9540089258233303,
        "std": 0.020004860339869476,
        "min": 0.9229916897506925,
        "max": 0.9792936288088643,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.021944604076699913,
        "std": 0.0033102852893959465,
        "min": 0.01384333568804327,
        "max": 0.02771788088011965,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.5653066310664039,
        "std": 0.06513718476785084,
        "min": 0.48,
        "max": 0.75,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.7596491228070176,
        "std": 0.06358460696149837,
        "min": 0.631578947368421,
        "max": 0.8421052631578947,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.6467190294053662,
        "std": 0.05581224529039938,
        "min": 0.5454545454545454,
        "max": 0.7692307692307693,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.6467190294053662,
        "std": 0.05581224529039938,
        "min": 0.5454545454545454,
        "max": 0.7692307692307693,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.8699415204678362,
        "std": 0.032151531820466026,
        "min": 0.8043859649122806,
        "max": 0.9105263157894736,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.6413803431322559,
        "std": 0.05761343740986128,
        "min": 0.5335305486433719,
        "max": 0.7616023099362901,
        "n": 15,
        "n_undefined": 0
      }
    },
    "random_forest": {
      "average_precision": {
        "mean": 0.7291530723629748,
        "std": 0.0634741359612328,
        "min": 0.5965455691935722,
        "max": 0.7891793113678627,
        "n": 15,
        "n_undefined": 0
      },
      "roc_auc": {
        "mean": 0.9567951677439213,
        "std": 0.020061915071379076,
        "min": 0.9075484764542936,
        "max": 0.9818328716528162,
        "n": 15,
        "n_undefined": 0
      },
      "brier": {
        "mean": 0.015401740099179701,
        "std": 0.001908010631353047,
        "min": 0.01350366138505304,
        "max": 0.019324738946612702,
        "n": 15,
        "n_undefined": 0
      },
      "precision": {
        "mean": 0.768268419924076,
        "std": 0.07972814621559725,
        "min": 0.5769230769230769,
        "max": 0.88,
        "n": 15,
        "n_undefined": 0
      },
      "recall": {
        "mean": 0.5631578947368421,
        "std": 0.0877318286789678,
        "min": 0.39473684210526316,
        "max": 0.6842105263157895,
        "n": 15,
        "n_undefined": 0
      },
      "f1": {
        "mean": 0.6476307862577217,
        "std": 0.07938907086452253,
        "min": 0.46875,
        "max": 0.7647058823529411,
        "n": 15,
        "n_undefined": 0
      },
      "fbeta": {
        "mean": 0.6476307862577217,
        "std": 0.07938907086452253,
        "min": 0.46875,
        "max": 0.7647058823529411,
        "n": 15,
        "n_undefined": 0
      },
      "balanced_accuracy": {
        "mean": 0.7787426900584795,
        "std": 0.04416618030243771,
        "min": 0.6925438596491228,
        "max": 0.8403508771929824,
        "n": 15,
        "n_undefined": 0
      },
      "mcc": {
        "mean": 0.6471569856191964,
        "std": 0.07889697175347718,
        "min": 0.46311727307263506,
        "max": 0.7634305280239022,
        "n": 15,
        "n_undefined": 0
      }
    }
  },
  "comparisons": [
    {
      "candidate": "hgb",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.6972067972455854,
      "std_diff": 0.05894302343071459,
      "min_diff": 0.5894155267724493,
      "max_diff": 0.7619282888770077,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.4542005232379193,
      "std_diff": 0.019121049792658804,
      "min_diff": 0.41451985226223453,
      "max_diff": 0.4821329639889197,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.16136230229200088,
      "std_diff": 0.07757477408097929,
      "min_diff": 0.04274039393669371,
      "max_diff": 0.323005380950343,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.029714527546937538,
      "std_diff": 0.015488755252309512,
      "min_diff": 0.00023084025854114287,
      "max_diff": 0.04979224376731317,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.5142029969565429,
      "std_diff": 0.06938836673997291,
      "min_diff": 0.4291562867198613,
      "max_diff": 0.6700447056659488,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.4493744228993537,
      "std_diff": 0.016792378915905144,
      "min_diff": 0.41861726685133893,
      "max_diff": 0.47790858725761776,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": -0.02164149799704173,
      "std_diff": 0.11443262134604855,
      "min_diff": -0.2299345713852281,
      "max_diff": 0.22714835958263985,
      "wins": 6,
      "losses": 9,
      "ties": 0,
      "win_fraction": 0.4
    },
    {
      "candidate": "hgb+random_under",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.024888427208371824,
      "std_diff": 0.018976041425458296,
      "min_diff": -0.0036588180978761597,
      "max_diff": 0.06391966759002765,
      "wins": 14,
      "losses": 1,
      "ties": 0,
      "win_fraction": 0.9333333333333333
    },
    {
      "candidate": "hgb+smote",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.7192163961989322,
      "std_diff": 0.061077576820180925,
      "min_diff": 0.590472584486247,
      "max_diff": 0.7903873607303142,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+smote",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.4540089258233302,
      "std_diff": 0.020004860339869476,
      "min_diff": 0.42299168975069246,
      "max_diff": 0.4792936288088643,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+smote",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.18337190124534727,
      "std_diff": 0.07442670691202855,
      "min_diff": 0.0748535616181284,
      "max_diff": 0.3156079982237386,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "hgb+smote",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.029522930132348434,
      "std_diff": 0.013013569207571785,
      "min_diff": 4.616805170820637e-05,
      "max_diff": 0.05041551246537379,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "random_forest",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.6968950078468459,
      "std_diff": 0.0634741359612328,
      "min_diff": 0.5642875046774432,
      "max_diff": 0.7569212468517337,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "random_forest",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.45679516774392126,
      "std_diff": 0.020061915071379076,
      "min_diff": 0.4075484764542936,
      "max_diff": 0.4818328716528162,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "random_forest",
      "baseline": "logreg_balanced",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.16105051289326103,
      "std_diff": 0.09115560025030114,
      "min_diff": 0.008526313820762188,
      "max_diff": 0.3078169984366718,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "random_forest",
      "baseline": "logreg_balanced",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.032309172052939435,
      "std_diff": 0.014382117245295865,
      "min_diff": 0.008818097876269637,
      "max_diff": 0.06161126500461678,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "logreg_balanced",
      "baseline": "dummy_prior",
      "metric": "average_precision",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.5358444949535848,
      "std_diff": 0.09315615039087931,
      "min_diff": 0.3829187364494908,
      "max_diff": 0.7155337991121858,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    },
    {
      "candidate": "logreg_balanced",
      "baseline": "dummy_prior",
      "metric": "roc_auc",
      "n_pairs": 15,
      "n_pairs_skipped_undefined": 0,
      "mean_diff": 0.42448599569098183,
      "std_diff": 0.017680709414718748,
      "min_diff": 0.38709602954755307,
      "max_diff": 0.4479916897506925,
      "wins": 15,
      "losses": 0,
      "ties": 0,
      "win_fraction": 1.0
    }
  ],
  "best_candidate_by_mean_oof_ap": "hgb+smote",
  "selection_rule": "candidate with the highest mean out-of-fold average precision; test data is not used"
}
````

#### Case-study script output (final execution)
````text
downloaded <project-root>\data\raw\imblearn\zenodo\x25data.npz sha256=73480c315d42bc5b33c2c73b9078d0034113d26f0511facd9fc5bb07f2d6438a
[a_stratified] registered ds-20261022T091903Z-cd54094f: 11183 rows, sha256=eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed
[a_stratified] run run-20261022T091904Z-596af186 completed; best candidate by OOF AP: hgb+smote
[a_stratified] final evaluation done; persisted model model-20261022T092002Z-aedecb57
[b_duplicate_groups] registered ds-20261022T092006Z-f006ea5d: 11183 rows, sha256=eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed
[b_duplicate_groups] run run-20261022T092013Z-2056207e completed; best candidate by OOF AP: hgb+smote
[b_duplicate_groups] final evaluation done; persisted model model-20261022T092115Z-819a6e87
wrote docs/case_study.md, docs/case_study/a_stratified, docs/case_study/b_duplicate_groups

real	3m39.994s
user	0m0.000s
sys	0m0.046s
````

#### docs/case_study.md (full)
````markdown
# Case study: `mammography` (imbalanced-learn benchmark)

> Generated by `scripts/run_case_study.py` from two run records: (a) `run-20261022T091904Z-596af186` in [`case_study/a_stratified/`](case_study/a_stratified/) and (b) `run-20261022T092013Z-2056207e` in [`case_study/b_duplicate_groups/`](case_study/b_duplicate_groups/). Every number below is read from files in those folders. Nothing was typed in by hand.

## Headline (run b: duplicate-aware split)

The selected model **`hgb+smote`** scored **test AP 0.8228** on a single evaluation of 1964 test rows with 63 positives (prevalence 0.0321). On the same test rows, the baselines scored:

| Model | Test AP (scored once) | Test rows | Positives | Prevalence |
|---|---|---|---|---|
| `hgb+smote` | 0.8228 | 1964 | 63 | 0.0321 |
| `dummy_prior` | 0.0321 | 1964 | 63 | 0.0321 |
| `logreg_balanced` | 0.5023 | 1964 | 63 | 0.0321 |

Run (b) is the headline because in run (a) exact-duplicate rows cross the train/test and CV boundaries (see the duplicate-leakage finding below). In run (b) no duplicate cluster crosses any boundary: the cross-boundary duplicate check reports 0 test rows and 0 affected folds.

**Evaluation population (run b):** 1 duplicate cluster(s) of 3329 identical rows (7 positive) are too large to sit in a test or validation set without dominating it. They are pinned to the training side of the holdout and of every CV fold, so **no test or validation metric covers those rows**. The test set is drawn from the remaining rows.

## Data source

| Field | Value |
|---|---|
| Dataset | `mammography` |
| Collection | imbalanced-learn benchmark collection (imblearn.datasets.fetch_datasets) |
| Zenodo record / DOI | https://zenodo.org/records/61452 / `10.5281/zenodo.61452` |
| Creators | Lemaitre, Nogueira, Aridas, Oliveira (2016) |
| Licence | ODC-ODbL (Open Database License), as listed on the Zenodo record |
| Original repository | UCI (per the imbalanced-learn dataset table; benchmark proposed by Ding, Z., 'Diversified Ensemble Classifiers for Highly Imbalanced Data Learning and their Application in Bioinformatics', 2011) |
| SHA-256 of extracted `x25data.npz` | `73480c315d42bc5b33c2c73b9078d0034113d26f0511facd9fc5bb07f2d6438a` |
| SHA-256 of CSV used (both runs) | `eaed6c1612644fd5db935ca74257792ec473e64cd3925161e6030bdaf144e0ed` |
| Rows / features | 11183 / 6 |
| Positives / negatives | 260 / 10923 (prevalence 0.0232, ratio 42.0:1) |
| Exact duplicate rows (profile) | 3334 |

## Protocol

Both runs use the same protocol. The only difference is the split.

- **Candidates (full list):** `hgb`, `hgb+random_under`, `hgb+smote`, `random_forest`. **Baselines:** `dummy_prior`, `logreg_balanced`. Small fixed configs (see `run.json` `model_specs`). Samplers run inside the imblearn pipeline during fit only.
- **Selection rule:** the non-baseline candidate with the highest mean out-of-fold average precision (summary.best_candidate_by_mean_oof_ap); test data is not used.
- **Threshold rule:** `max_fbeta` with beta=2.0, selected on each CV repeat's OOF predictions for the selected model; the median of the per-repeat thresholds is used.
- **Seeds and CV:** holdout test_size 0.2 with seed 42; 5-fold × 3 repeats with seed 42; estimator seed 42.
- **Final evaluation:** the selected model and both baselines are refit on outer-train rows, and the test rows are scored once.
- **(a) `a_stratified`:** a stratified holdout and stratified CV (the original M10 protocol).
- **(b) `b_duplicate_groups`:** `duplicate_groups=True`. Rows with identical feature values form one group, and both the holdout and CV use `StratifiedGroupKFold`. There are 7848 split groups, of which 3 are duplicate clusters covering 3338 rows; 1 cluster(s) have conflicting labels (3329 rows, kept). Groups larger than 25% of the target test or validation size are pinned to training: 1 group(s) and 3329 rows for the holdout, 1 group(s) and 3329 rows for CV.

### Was the protocol fixed before results were seen?

- The candidate list, seeds, CV settings, selection rule and threshold strategy were written into `scripts/run_case_study.py` before its first execution in M10. They have not been changed since; this rewrite keeps the same constants.
- **Git history cannot prove this ordering.** The script's first commit (`91c6f54`, M10) came after those executions. The evidence is the M10 command log in `REVIEW_PACKET.md`: the first execution failed before producing results (a file-path bug), the second was stopped before its output was read, and later executions changed only report wording.
- **Run (b) was not pre-specified.** It was requested by the supervisor after the run (a) results were seen. Its candidate set, seeds and selection rule are those of run (a), unchanged.

## Results, run (b)

OOF AP is a **selection estimate (optimistic: used for model selection)**. Test AP is a single scoring of the held-out rows.

| Model | Role | OOF AP: selection estimate (optimistic) | OOF ROC AUC | Test AP (scored once) | Test rows / positives / prevalence |
|---|---|---|---|---|---|
| `dummy_prior` | baseline | 0.0323 ± 0.0000 (n=15) | 0.5000 ± 0.0000 (n=15) | 0.0321 | 1964 / 63 / 0.0321 |
| `logreg_balanced` | baseline | 0.5681 ± 0.0932 (n=15) | 0.9245 ± 0.0177 (n=15) | 0.5023 | 1964 / 63 / 0.0321 |
| `hgb` | candidate | 0.7295 ± 0.0589 (n=15) | 0.9542 ± 0.0191 (n=15) | not scored | — |
| `hgb+random_under` | candidate | 0.5465 ± 0.0694 (n=15) | 0.9494 ± 0.0168 (n=15) | not scored | — |
| `hgb+smote` | candidate (selected) | 0.7515 ± 0.0611 (n=15) | 0.9540 ± 0.0200 (n=15) | 0.8228 | 1964 / 63 / 0.0321 |
| `random_forest` | candidate | 0.7292 ± 0.0635 (n=15) | 0.9568 ± 0.0201 (n=15) | not scored | — |

Paired comparisons on identical folds (run b, OOF AP, descriptive):

- **hgb** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.6972, better in 15 of 15 folds (win fraction 1.00).
- **hgb** beats **logreg_balanced** on out-of-fold average precision: mean paired difference +0.1614, better in 15 of 15 folds (win fraction 1.00).
- **hgb+random_under** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.5142, better in 15 of 15 folds (win fraction 1.00).
- **hgb+random_under** does NOT beat **logreg_balanced** on out-of-fold average precision: mean paired difference -0.0216, better in 6 of 15 folds (win fraction 0.40).
- **hgb+smote** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.7192, better in 15 of 15 folds (win fraction 1.00).
- **hgb+smote** beats **logreg_balanced** on out-of-fold average precision: mean paired difference +0.1834, better in 15 of 15 folds (win fraction 1.00).
- **random_forest** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.6969, better in 15 of 15 folds (win fraction 1.00).
- **random_forest** beats **logreg_balanced** on out-of-fold average precision: mean paired difference +0.1611, better in 15 of 15 folds (win fraction 1.00).
- **logreg_balanced** beats **dummy_prior** on out-of-fold average precision: mean paired difference +0.5358, better in 15 of 15 folds (win fraction 1.00).
- **hgb+smote** beats **dummy_prior** on the test set (average_precision: 0.8228 vs 0.0321, difference +0.7907; single evaluation, no spread).
- **hgb+smote** beats **logreg_balanced** on the test set (average_precision: 0.8228 vs 0.5023, difference +0.3205; single evaluation, no spread).

## Threshold, run (b)

- **Model:** `hgb+smote`. **Strategy:** `max_fbeta` with beta=2.0, selected on OOF predictions for each of 3 CV repeats. **Rule:** median of per-repeat thresholds selected on out-of-fold predictions.
- **Chosen threshold:** 0.6036. Per-repeat thresholds: mean 0.6001 ± 0.0814 (sample std), range [0.5170, 0.6796]. Individual values: repeat 0: 0.6036, repeat 1: 0.5170, repeat 2: 0.6796.
- **Test metrics at the chosen threshold** (scored once):

| Precision | Recall | F-beta (beta=2) | MCC | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| 0.6049 | 0.7778 | 0.7357 | 0.6743 | 49 | 32 | 14 | 1869 |

## Duplicate-leakage finding: run (a) vs run (b)

The two runs use **different test sets**. Each split strategy draws its own holdout, so differences between the columns combine the effect of duplicates crossing boundaries with the effect of a different test sample.

| | (a) stratified | (b) duplicate groups |
|---|---|---|
| Run ID | `run-20261022T091904Z-596af186` | `run-20261022T092013Z-2056207e` |
| Test rows duplicating outer-train rows | 632 | 0 |
| CV folds with validation rows duplicating training rows | 15 of 15 | 0 of 15 |
| Selected model (same rule) | `hgb+smote` | `hgb+smote` |
| Selected model OOF AP: selection estimate (optimistic) | 0.7449 ± 0.0362 (n=15) | 0.7515 ± 0.0611 (n=15) |
| Selected model test AP (scored once) | 0.6670 | 0.8228 |
| Test rows / positives / prevalence | 2237 / 52 / 0.0232 | 1964 / 63 / 0.0321 |
| **OOF-minus-test AP gap (selected model)** | +0.0779 | -0.0713 |
| `dummy_prior` OOF / test AP (gap) | 0.0233 / 0.0232 (+0.0000) | 0.0323 / 0.0321 (+0.0002) |
| `logreg_balanced` OOF / test AP (gap) | 0.5427 / 0.4669 (+0.0758) | 0.5681 / 0.5023 (+0.0658) |

OOF values are means over folds. The gap is OOF mean minus the single test value. A positive gap means the selection estimate was higher than the test result.

### Duplicate-removed re-slice of run (a)'s test predictions

This is a post-hoc re-slice of run (a)'s *stored* test predictions: no refit, no re-scoring, nothing selected. It excludes test rows whose features exactly duplicate an outer-train row (632 rows, of which 2 positive).

| Model | Subset | Rows | Positives | Prevalence | AP | ROC AUC |
|---|---|---|---|---|---|---|
| `hgb+smote` | all test rows | 2237 | 52 | 0.0232 | 0.6670 | 0.8917 |
| `hgb+smote` | excluding duplicates of train | 1605 | 50 | 0.0312 | 0.7060 | 0.9249 |
| `dummy_prior` | all test rows | 2237 | 52 | 0.0232 | 0.0232 | 0.5000 |
| `dummy_prior` | excluding duplicates of train | 1605 | 50 | 0.0312 | 0.0312 | 0.5000 |
| `logreg_balanced` | all test rows | 2237 | 52 | 0.0232 | 0.4669 | 0.9167 |
| `logreg_balanced` | excluding duplicates of train | 1605 | 50 | 0.0312 | 0.4849 | 0.9277 |

**AP depends on prevalence.** The two subsets have different prevalence, so their AP values are not directly comparable. Compare each model with `dummy_prior` *within the same subset* (dummy AP equals that subset's prevalence). This re-slice covers the test set only and does not show the effect of duplicates on run (a)'s CV estimates. Run (b) addresses that by construction. In run (b) the re-slice excludes 0 rows.

## Data profile and split warnings (heuristic, not proof)

- `exact_duplicates`: 3334 row(s) duplicate an earlier row; duplicates crossing split boundaries can inflate scores.
- `conflicting_duplicates`: 1 group(s) of rows have identical features but different labels (possible label noise).
- (a) split check `cross_boundary_duplicates`: 632 test row(s) exactly duplicate outer-train feature rows, and 15 CV fold(s) have validation rows duplicating their training rows (max 581). Scores on duplicated rows may be optimistic.
- (b) split check `conflicting_label_clusters`: 1 duplicate cluster(s) (3329 rows) have identical features but different labels; they are kept and split together.
- (b) split check `oversized_groups_pinned_to_train`: 1 group(s) covering 3329 rows exceed 559 rows (max_eval_group_fraction of the test set size) and are always on the training side; test set metrics do not cover these rows.
- (b) split check `oversized_groups_pinned_to_train`: 1 group(s) covering 3329 rows exceed 461 rows (max_eval_group_fraction of the validation fold size) and are always on the training side; validation fold metrics do not cover these rows.

## Limitations

- One dataset. Each run has one outer split, so the test numbers are single draws with no spread, and runs (a) and (b) use different test rows.
- Test sets are small in positives (52 in (a), 63 in (b)).
- Fixed small model configs with no hyperparameter search (MVP scope). Probabilities are not calibrated.
- The features are anonymised numeric measurements, so the duplicates could not be reviewed against domain knowledge. Whether they are repeated measurements or artefacts is unknown.

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-lock.txt && pip install -e . --no-deps
python scripts/run_case_study.py            # both runs + this document
python scripts/verify_case_study_hashes.py  # regenerate large files, check SHA-256
```

## Run records

- (a): [`case_study/a_stratified/`](case_study/a_stratified/) (report: [`report/report.md`](case_study/a_stratified/report/report.md))
- (b): [`case_study/b_duplicate_groups/`](case_study/b_duplicate_groups/) (report: [`report/report.md`](case_study/b_duplicate_groups/report/report.md))
- Files over 1 MB are not committed and are listed with SHA-256 in each `OMITTED_FILES.json` (run b: `fold_indices.json`). `scripts/verify_case_study_hashes.py` regenerates them and checks the hashes.
- Environment: Python 3.13.5, scikit-learn 1.9.1, imbalanced-learn 0.14.2, numpy 2.5.4, pandas 3.0.6.
````

#### Hash-regeneration check (final, verbatim)
````text
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
````

The first execution, before the RF fix, failed on one file (verbatim excerpt):

````text
  [MISMATCH] oof_predictions.parquet file sha256: e3494b7b73ae5ff2103f58d7e78069aa6cf34710dee43b00dbe25db20cafde29 != 429ce7f852fe1e94141fbeea4066d87771fc21d82d59a881ace9fa26b2bfbc0b
  [OK] summary.json content: f29ba9ba182453ffdd29e2963b050c60d361d829658ad4844acab68969a33ed7
SOME CHECKS FAILED
````

Diagnosis: `max |score diff|: 2.220446049250313e-16 rows differing: 2901 {'random_forest': 2901}`.
RF on test-sized data gave 8 distinct outputs in 8 fits with `n_jobs=-1`, and 1 with
`n_jobs=1`. The `summary.json` content hash is identical before and after the fix
(`f29ba9…`, `8c952d…`), so no reported metric changed.

#### Frontend evidence
`python scripts/ui_screenshots.py` printed:
````text
01_upload_and_profile: errors=[] exceptions=0 console_errors=0
02_run_experiment: errors=[] exceptions=0 console_errors=0
03_results_and_thresholds: errors=[] exceptions=0 console_errors=0
04_final_evaluation: errors=[] exceptions=0 console_errors=0
05_final_evaluation_refused: errors=['API error 409 (final_evaluation_exists): this run already has a final evaluation; the test set is scored once. Pass force=True with a reason to re-evaluate (this is logged).'] exceptions=0 console_errors=0
06_report: errors=[] exceptions=0 console_errors=0
ALL PAGES OK
````

Screenshot files (`docs/screenshots/`):
````text
01_upload_and_profile.png
02_run_experiment.png
03_results_and_thresholds.png
04_final_evaluation.png
05_final_evaluation_refused.png
06_report.png
ui_check.json
````

- **Pages fixed:** none of them errored.
- **UI change:** a `duplicate_groups` checkbox on the upload form.
- **Script fix:** the first screenshot run used a 1000 px viewport. Streamlit scrolls inside its
  own container, so `full_page` captured only the first screen (the threshold result was cut
  off). The viewport is now 2400 px.
- I inspected the screenshots visually: 01 (upload + profile), 03 (results + thresholds), 04
  (final evaluation table + persisted model ID), 06 (embedded report).

#### Deviations
- **D27:** declared + duplicate groups are merged by connected components, which is my
  interpretation of "combine".
- **D28:** oversized groups are pinned to training, so the evaluation population excludes them.
  This is stated in the case study.
- **CI:** not run on GitHub (no remote). A local 3.11 gate was run instead, as instructed.
- **Playwright:** used as an optional tool and not added to the project dependencies.

#### Known limitations
- Runs (a) and (b) have different test sets, so their difference is not a clean estimate of
  duplicate leakage. This is stated in the case study.
- Run (b)'s metrics do not cover the 3329-row cluster (7 positives), which is pinned to
  training.

---

### Task T-R2 — Uncertainty, evaluation coverage, cluster analysis, CI

**Date:** 2026-10-22 · **Code/records commit:** `01a9d51`. This entry and the regenerated
FINAL_REPORT.md follow in the next commit.

#### Summary
- **H1 (bootstrap CIs):** `evaluation/uncertainty.py` implements a stratified bootstrap.
  - Positives and negatives are resampled separately, so class counts are fixed. Percentile
    95% interval; `n_resamples` defaults to 2000 and is seeded.
  - Covers AP, ROC AUC, and precision/recall/F-beta/MCC at the stored threshold. Undefined
    resamples are counted in `n_undefined`.
  - The implementation is vectorised. A test checks it against scikit-learn on resamples with
    heavy ties.
  - `final_evaluate` stores per-model `ci` plus `bootstrap` (method, n_resamples, seed,
    confidence). `amend_bootstrap_cis` adds them to an existing run from its stored test
    predictions only.
  - The report and case study show point [95% CI] for every test metric. OOF metrics are not
    bootstrapped. API: `bootstrap_resamples` and `bootstrap_seed` fields.
- **M1 (evaluation coverage):** `splitting/coverage.py`. A row counts as evaluated if it is in
  the test set or any validation fold.
  - `run.json["evaluation_coverage"]` holds: forced-to-train rows and positives, % of rows and
    of positives, group count, sizes and positives, gap rows, other never-evaluated rows, and the
    cut-off (holdout and CV `max_eval_group_fraction`, both config parameters, plus their row
    limits).
  - Report section 5 "Evaluation coverage" is always present. When forced-to-train rows exceed
    10% it shows a **WARNING** and adds the `evaluation_coverage_gap` split warning.
    `amend_evaluation_coverage` rebuilds folds from the stored holdout and refuses if the fold
    SHA-256 differs.
- **M2 (cluster analysis):** `cluster_analysis()` in the case-study script. Output is below and
  in docs/case_study.md "Data-quality finding".
- **M3 + L1 (disclosures):** a "Protocol history" subsection covers all 9 case-study executions,
  the discarded split v1, the large-group rule added afterwards, the reported split v2, that run
  (b) was added after run (a) results were seen, and test-set reuse counts. The median rule is
  D15 / commit `7ce0891` (13:05:52 +05:00), which precedes the first case-study scoring (13:34:55
  +05:00).
- **L2:** `resolve_groups` logs `logger.warning(...)` with the number of declared groups merged
  (D27), and the count is in the warning evidence. Tested with `caplog`.
- **L3:** an ODbL attribution banner and section in docs/case_study.md, and `NOTICE.md` in
  `docs/case_study/a_stratified/` and `b_duplicate_groups/`.
- **M4 (GitHub CI): BLOCKED.** The task text has the placeholder `<REPO_URL>` and no actual
  URL. `git remote -v` is empty. `gh` is authenticated (account `jaswantraj969`), but creating
  and publishing a repository on the user's account is an outward-facing action that was not
  authorised, so it was not done. Nothing was pushed, and **GitHub Actions has not run**. The
  hygiene check (no file over 1 MB, no secrets or .env) was done and passes; output is below.
- **D30:** the committed case-study runs were **amended** (`--amend-existing`), not re-run, so no
  test set was scored again. The stored `final_predictions.parquet` files were verified
  byte-identical before and after (`sha256sum -c`: OK).

#### git diff --stat 924b401..01a9d51
````text
 PROJECT_STATUS.md                                  |  24 +-
 README.md                                          |   8 +-
 docs/case_study.md                                 | 158 ++++--
 docs/case_study/a_stratified/NOTICE.md             |  13 +
 docs/case_study/a_stratified/PROVENANCE.json       |   4 +-
 .../a_stratified/duplicate_sensitivity.json        | 148 +++++-
 docs/case_study/a_stratified/final_evaluation.json | 203 +++++++-
 .../a_stratified/final_evaluation_log.jsonl        |   1 +
 docs/case_study/a_stratified/report/report.html    |  25 +-
 docs/case_study/a_stratified/report/report.md      |  43 +-
 docs/case_study/a_stratified/run.json              |  37 +-
 docs/case_study/b_duplicate_groups/NOTICE.md       |  13 +
 docs/case_study/b_duplicate_groups/PROVENANCE.json |   4 +-
 .../b_duplicate_groups/duplicate_sensitivity.json  | 148 +++++-
 .../b_duplicate_groups/final_evaluation.json       | 203 +++++++-
 .../b_duplicate_groups/final_evaluation_log.jsonl  |   1 +
 .../b_duplicate_groups/report/report.html          |  28 +-
 .../case_study/b_duplicate_groups/report/report.md |  47 +-
 docs/case_study/b_duplicate_groups/run.json        |  53 +-
 scripts/check_committed_files.py                   |  62 +++
 scripts/run_case_study.py                          | 559 +++++++++++++++------
 src/imbalancelab/api/app.py                        |   4 +
 src/imbalancelab/api/schemas.py                    |   2 +
 src/imbalancelab/evaluation/final.py               |  73 ++-
 src/imbalancelab/evaluation/runner.py              |  63 +++
 src/imbalancelab/evaluation/uncertainty.py         | 145 ++++++
 src/imbalancelab/reporting/report.py               | 128 ++++-
 src/imbalancelab/splitting/coverage.py             |  95 ++++
 src/imbalancelab/splitting/groups.py               |  12 +
 src/imbalancelab/workflow.py                       |   6 +-
 tests/snapshots/report_structure.md                |  28 +-
 tests/test_duplicate_groups.py                     |  85 +++-
 tests/test_reporting.py                            |   9 +-
 tests/test_thresholds_final.py                     |  29 ++
 tests/test_uncertainty.py                          |  93 ++++
 35 files changed, 2258 insertions(+), 296 deletions(-)
````

#### Gate, Python 3.13.5 (verbatim)
````text
$ python --version
Python 3.13.5

$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
67 files already formatted
[exit 0]

$ mypy
Success: no issues found in 43 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 45%]
........................................................................ [ 91%]
..............                                                           [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  <project-root>\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.5-final-0 _______________

Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
src\imbalancelab\__init__.py                     2      0   100%
src\imbalancelab\api\__init__.py                 0      0   100%
src\imbalancelab\api\app.py                    115      0   100%
src\imbalancelab\api\schemas.py                 47      0   100%
src\imbalancelab\config.py                      15      1    93%   27
src\imbalancelab\data\__init__.py                4      0   100%
src\imbalancelab\data\errors.py                 21      0   100%
src\imbalancelab\data\loader.py                143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                 40      0   100%
src\imbalancelab\evaluation\__init__.py          2      0   100%
src\imbalancelab\evaluation\config.py           35      0   100%
src\imbalancelab\evaluation\final.py           132      5    96%   79-80, 107, 165, 277
src\imbalancelab\evaluation\metrics.py         115      0   100%
src\imbalancelab\evaluation\runner.py          143      0   100%
src\imbalancelab\evaluation\thresholds.py      138      0   100%
src\imbalancelab\evaluation\uncertainty.py      79      1    99%   60
src\imbalancelab\models\__init__.py              2      0   100%
src\imbalancelab\models\persistence.py         100      0   100%
src\imbalancelab\models\registry.py             18      0   100%
src\imbalancelab\pipelines\__init__.py           2      0   100%
src\imbalancelab\pipelines\builder.py           66      0   100%
src\imbalancelab\profiling\__init__.py           3      0   100%
src\imbalancelab\profiling\profile.py          169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py           9      0   100%
src\imbalancelab\reporting\__init__.py           2      0   100%
src\imbalancelab\reporting\figures.py           44      1    98%   28
src\imbalancelab\reporting\render.py            82      0   100%
src\imbalancelab\reporting\report.py           206      8    96%   59, 123, 180, 183, 263, 293, 514, 556
src\imbalancelab\splitting\__init__.py           3      0   100%
src\imbalancelab\splitting\coverage.py          40      2    95%   34-35
src\imbalancelab\splitting\duplicates.py        24      0   100%
src\imbalancelab\splitting\groups.py            79      1    99%   64
src\imbalancelab\splitting\splits.py           251      2    99%   117, 123
src\imbalancelab\tracking\__init__.py            2      0   100%
src\imbalancelab\tracking\records.py           120      3    98%   89-90, 170
src\imbalancelab\workflow.py                   145      6    96%   63-64, 91, 136, 236, 262
--------------------------------------------------------------------------
TOTAL                                         2398     38    98%
158 passed, 1 warning in 110.36s (0:01:50)
[exit 0]
````

#### Gate, Python 3.11.15, local `.venv311` (verbatim; NOT a CI run)
````text
$ python --version
Python 3.11.15

$ ruff check .
All checks passed!
[exit 0]

$ ruff format --check .
67 files already formatted
[exit 0]

$ mypy
Success: no issues found in 43 source files
[exit 0]

$ pytest -q --cov=imbalancelab --cov-report=term-missing
........................................................................ [ 45%]
........................................................................ [ 91%]
..............                                                           [100%]
============================== warnings summary ===============================
.venv311\Lib\site-packages\fastapi\testclient.py:1
  <project-root>\.venv311\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============================== tests coverage ================================
______________ coverage: platform win32, python 3.11.15-final-0 _______________

Name                                         Stmts   Miss  Cover   Missing
--------------------------------------------------------------------------
src\imbalancelab\__init__.py                     2      0   100%
src\imbalancelab\api\__init__.py                 0      0   100%
src\imbalancelab\api\app.py                    115      0   100%
src\imbalancelab\api\schemas.py                 47      0   100%
src\imbalancelab\config.py                      15      1    93%   27
src\imbalancelab\data\__init__.py                4      0   100%
src\imbalancelab\data\errors.py                 21      0   100%
src\imbalancelab\data\loader.py                143      5    97%   127-128, 144, 148, 195
src\imbalancelab\data\schema.py                 40      0   100%
src\imbalancelab\evaluation\__init__.py          2      0   100%
src\imbalancelab\evaluation\config.py           35      0   100%
src\imbalancelab\evaluation\final.py           132      5    96%   79-80, 107, 165, 277
src\imbalancelab\evaluation\metrics.py         115      0   100%
src\imbalancelab\evaluation\runner.py          143      0   100%
src\imbalancelab\evaluation\thresholds.py      138      0   100%
src\imbalancelab\evaluation\uncertainty.py      79      1    99%   60
src\imbalancelab\models\__init__.py              2      0   100%
src\imbalancelab\models\persistence.py         100      0   100%
src\imbalancelab\models\registry.py             18      0   100%
src\imbalancelab\pipelines\__init__.py           2      0   100%
src\imbalancelab\pipelines\builder.py           66      0   100%
src\imbalancelab\profiling\__init__.py           3      0   100%
src\imbalancelab\profiling\profile.py          169      3    98%   301, 341, 363
src\imbalancelab\profiling\warnings.py           9      0   100%
src\imbalancelab\reporting\__init__.py           2      0   100%
src\imbalancelab\reporting\figures.py           44      1    98%   28
src\imbalancelab\reporting\render.py            82      0   100%
src\imbalancelab\reporting\report.py           206      8    96%   59, 123, 180, 183, 263, 293, 514, 556
src\imbalancelab\splitting\__init__.py           3      0   100%
src\imbalancelab\splitting\coverage.py          40      2    95%   34-35
src\imbalancelab\splitting\duplicates.py        24      0   100%
src\imbalancelab\splitting\groups.py            79      1    99%   64
src\imbalancelab\splitting\splits.py           251      2    99%   117, 123
src\imbalancelab\tracking\__init__.py            2      0   100%
src\imbalancelab\tracking\records.py           120      3    98%   89-90, 170
src\imbalancelab\workflow.py                   145      6    96%   63-64, 91, 136, 236, 262
--------------------------------------------------------------------------
TOTAL                                         2398     38    98%
158 passed, 1 warning in 102.85s (0:01:42)
[exit 0]
````

#### Case-study amendment run (verbatim)
````text
$ sha256sum runs/case_study/runs/*/final_predictions.parquet > preds_before.txt
$ python scripts/run_case_study.py --amend-existing
downloaded <project-root>\data\raw\imblearn\zenodo\x25data.npz sha256=73480c315d42bc5b33c2c73b9078d0034113d26f0511facd9fc5bb07f2d6438a
[a_stratified] amended run-20261022T091904Z-596af186: coverage forced_to_train=0 rows (0 positive); bootstrap CIs added from stored predictions
[b_duplicate_groups] amended run-20261022T092013Z-2056207e: coverage forced_to_train=3329 rows (7 positive); bootstrap CIs added from stored predictions
Largest duplicate cluster (run run-20261022T092013Z-2056207e, duplicate_groups=True)
rows: 3329 of 11183 (29.77% of the dataset)   positives: 7   negatives: 3322
rows in the cluster that are in the test set: 0
identical feature vector of all 3329 rows (all rows equal: True):
  feature_0 = -0.78441482   column min -0.78441482, median -0.10857689, max 31.50844300   is column min: yes   is column max: no   rows with exactly this value: 3360 (30.05%)   rows below it: 0
  feature_1 = -0.47019533   column min -0.47019533, median -0.39499410, max 5.08584910   is column min: yes   is column max: no   rows with exactly this value: 3329 (29.77%)   rows below it: 0
  feature_2 = -0.59163147   column min -0.59163147, median -0.23097900, max 29.47776900   is column min: yes   is column max: no   rows with exactly this value: 3410 (30.49%)   rows below it: 0
  feature_3 = -0.85955255   column min -0.85955255, median -0.85955255, max 9.59116400   is column min: yes   is column max: no   rows with exactly this value: 5766 (51.56%)   rows below it: 0
  feature_4 = -0.37786573   column min -0.37786573, median -0.37786573, max 23.61712200   is column min: yes   is column max: no   rows with exactly this value: 8521 (76.20%)   rows below it: 0
  feature_5 = -0.94572324   column min -0.94572324, median -0.94572324, max 1.94902730   is column min: yes   is column max: no   rows with exactly this value: 5766 (51.56%)   rows below it: 0
features equal to their column minimum: 6 of 6
features equal to 0: 0 of 6
distinct values within the vector: 6
selected model: hgb+smote (persisted model model-20261022T092115Z-819a6e87, refit on outer-train rows only, artifact SHA-256 verified on load)
predicted probability for the cluster's feature vector: 0.08894896   distinct predicted values over the 3329 rows: 1
stored threshold: 0.60359672   predicted label: 0   (training prevalence of the cluster: 0.002103)
wrote docs/case_study.md, docs/case_study/a_stratified, docs/case_study/b_duplicate_groups
$ sha256sum -c preds_before.txt
runs/case_study/runs/run-20261022T091904Z-596af186/final_predictions.parquet: OK
runs/case_study/runs/run-20261022T092013Z-2056207e/final_predictions.parquet: OK
````

#### Hash-regeneration check after amendment (verbatim)
````text
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
````

#### Large-file / secrets check (verbatim)
````text
$ git add -A && python scripts/check_committed_files.py
tracked files checked: 127
total tracked bytes: 4046277
largest tracked files:
     986610  docs/case_study/b_duplicate_groups/oof_predictions.parquet
     246755  docs/case_study/b_duplicate_groups/report/report.html
     244536  docs/case_study/a_stratified/report/report.html
     181007  REVIEW_PACKET.md
     172401  docs/case_study/a_stratified/fold_metrics.json
files over 1000000 bytes: 0
sensitive file names (.env, keys): 0
OK: no problems found
$ git check-ignore -v .env runs/x .venv311/x
.gitignore:11:.env	.env
.gitignore:15:runs/*	runs/x
.gitignore:2:.venv311/	.venv311/x
````

#### Evaluation coverage section, as generated by the run (b) report (verbatim)
````markdown
## 5. Evaluation coverage

**WARNING:** 3329 rows (29.8% of the dataset, 7 positives) were never in any test or validation set. **The reported results do not describe these rows.**

| Field | Value |
|---|---|
| Rows / positives in dataset | 11183 / 260 |
| Rows evaluated (test or any validation fold) | 7854 |
| Forced to train, never evaluated: rows / positives | 3329 / 7 |
| Forced to train: % of rows / % of positives | 29.77% / 2.69% |
| Large-group cut-off | groups larger than 25% of the target test size (559 rows) or 25% of the target validation-fold size (461 rows) are forced to train |
| Forced-to-train groups | 1: 3329 rows (7 positive) |
| Temporal gap rows | 0 |
| Other never-evaluated rows | 0 (not in any test or validation fold) |
| Warning threshold | 10% of rows |
````

#### Headline (docs/case_study.md, verbatim)
````markdown
## Headline (run b: duplicate-aware split)

The selected model **`hgb+smote`** scored **test AP 0.8228 [0.7383, 0.8977]** on a single evaluation of 1964 test rows with 63 positives (prevalence 0.0321). On the same test rows:

| Model | Test AP [95% CI] | Test ROC AUC [95% CI] | Test rows | Positives | Prevalence |
|---|---|---|---|---|---|
| `hgb+smote` | 0.8228 [0.7383, 0.8977] | 0.9589 [0.9180, 0.9889] | 1964 | 63 | 0.0321 |
| `dummy_prior` | 0.0321 [0.0321, 0.0321] | 0.5000 [0.5000, 0.5000] | 1964 | 63 | 0.0321 |
| `logreg_balanced` | 0.5023 [0.3926, 0.6442] | 0.9225 [0.8764, 0.9611] | 1964 | 63 | 0.0321 |

Brackets are 95% CIs from a stratified bootstrap of the test rows (2000 resamples, seed 42; positives and negatives resampled separately). They reflect test-sample variation only.

**Evaluation coverage (run b): 3329 rows (29.8% of the dataset, 7 positives) are never in any test or validation set.** They form one oversized duplicate cluster that is forced to training, so the results above do not describe those rows. See [Evaluation coverage](#evaluation-coverage-run-b) and the [data-quality finding](#data-quality-finding-the-3329-row-cluster).

Run (b) is the headline because in run (a) exact-duplicate rows cross the train/test and CV boundaries. In run (b) the cross-boundary duplicate check reports 0 test rows and 0 affected folds.
````

#### Protocol history (docs/case_study.md, verbatim)
````markdown
### Protocol history

Every execution of this case study, from the command logs in `REVIEW_PACKET.md`:

| # | When | Run (a) stratified | Run (b) duplicate groups | Test set scored? | Outcome |
|---|---|---|---|---|---|
| 1 | M10 | (none: failed before CV) | — | no | `FileNotFoundError` on the extracted file name |
| 2 | M10 | (stopped by me) | — | unknown | stopped to fix `source_name`; its log was overwritten, so whether it reached final evaluation is unknown |
| 3 | M10 | `run-20261022T083455Z-ef809093` | — | yes | superseded (report wording) |
| 4 | M10 | `run-20261022T083728Z-db0f0d23` | — | yes | superseded (report wording) |
| 5 | M10 | `run-20261022T083838Z-b12a4417` | — | yes | committed in M10, superseded in T-R1 |
| 6 | T-R1 | `run-20261022T090059Z-c27d4eb9` | `run-20261022T090141Z-9165d0cb` (**split v1**, no large-group rule) | yes | run (b) found **degenerate** and discarded (see below) |
| 7 | T-R1 | `run-20261022T090930Z-8ca49f38` | `run-20261022T091037Z-8d492e51` (**split v2**) | yes | superseded: the hash check exposed random-forest non-determinism (D29) |
| 8 | T-R1 | `run-20261022T091904Z-596af186` | `run-20261022T092013Z-2056207e` (split v2) | yes | **reported runs** |
| 9 | T-R2 | same as #8 | same as #8 | **no** | bootstrap CIs and evaluation coverage added from stored predictions and indices |

- **Run (b) was added after run (a) results had been seen.** The supervisor requested it in review T-R1, after the M10 case study (run a protocol) was reported.
- **The first run (b) split (split v1, execution 6) was produced, scored, found degenerate, and discarded.** Its test set was one 3329-row duplicate cluster plus 45 other rows that were all positive. `StratifiedGroupKFold` had rebalanced the class ratio around the unsplittable cluster, and two different models scored the same test AP. The degeneracy was found by inspecting that run's test predictions.
- **The large-group rule was then added.** Groups above 25% of the target test or validation size are forced to train, and holdout size, prevalence and dominant-group warnings were added (PROJECT_STATUS D28). Only this one cut-off value was tried. The reported run (b) uses **the second split (split v2)**.
- **Test-set reuse:** the run (a) test set (test-index SHA-256 `ee4a3c8a3d3efbbf…`) was scored in executions 3–8, six times with the same protocol, plus possibly execution 2. The split v2 test set (SHA-256 `7ee8afda21eac8e5…`) was scored in executions 7 and 8. The change between 7 and 8 (random-forest threads, D29) came from the out-of-fold hash check, not from test results, and did not change any reported metric. Execution 9 scored nothing.
- **Fixed before any case-study test scoring:** the candidate list, seeds, CV settings and selection rule were written into this script before execution 1. Git cannot prove that ordering, because the script was first committed in M10 (`91c6f54`) after those executions.
- **Threshold aggregation rule (median across repeats):** decided in M5 as PROJECT_STATUS decision **D15** and implemented in commit **`7ce0891`** (2026-10-22 13:05:52 +05:00). This **precedes** the first case-study execution (execution 3, run `run-20261022T083455Z-ef809093` = 08:34:55Z = 13:34:55 +05:00) and so all test scoring.
````

#### Data-quality finding (docs/case_study.md, verbatim)
````markdown
## Data-quality finding: the 3329-row cluster

Output of `cluster_analysis()` in `scripts/run_case_study.py`. The data and the persisted run (b) model (refit on outer-train rows, as in the final evaluation) are used. This describes values only and makes no claim about their cause.

```text
Largest duplicate cluster (run run-20261022T092013Z-2056207e, duplicate_groups=True)
rows: 3329 of 11183 (29.77% of the dataset)   positives: 7   negatives: 3322
rows in the cluster that are in the test set: 0
identical feature vector of all 3329 rows (all rows equal: True):
  feature_0 = -0.78441482   column min -0.78441482, median -0.10857689, max 31.50844300   is column min: yes   is column max: no   rows with exactly this value: 3360 (30.05%)   rows below it: 0
  feature_1 = -0.47019533   column min -0.47019533, median -0.39499410, max 5.08584910   is column min: yes   is column max: no   rows with exactly this value: 3329 (29.77%)   rows below it: 0
  feature_2 = -0.59163147   column min -0.59163147, median -0.23097900, max 29.47776900   is column min: yes   is column max: no   rows with exactly this value: 3410 (30.49%)   rows below it: 0
  feature_3 = -0.85955255   column min -0.85955255, median -0.85955255, max 9.59116400   is column min: yes   is column max: no   rows with exactly this value: 5766 (51.56%)   rows below it: 0
  feature_4 = -0.37786573   column min -0.37786573, median -0.37786573, max 23.61712200   is column min: yes   is column max: no   rows with exactly this value: 8521 (76.20%)   rows below it: 0
  feature_5 = -0.94572324   column min -0.94572324, median -0.94572324, max 1.94902730   is column min: yes   is column max: no   rows with exactly this value: 5766 (51.56%)   rows below it: 0
features equal to their column minimum: 6 of 6
features equal to 0: 0 of 6
distinct values within the vector: 6
selected model: hgb+smote (persisted model model-20261022T092115Z-819a6e87, refit on outer-train rows only, artifact SHA-256 verified on load)
predicted probability for the cluster's feature vector: 0.08894896   distinct predicted values over the 3329 rows: 1
stored threshold: 0.60359672   predicted label: 0   (training prevalence of the cluster: 0.002103)
```
````

#### Threshold, run (b) (docs/case_study.md, verbatim)
````markdown
## Threshold, run (b)

- **Model:** `hgb+smote`. **Strategy:** `max_fbeta` with beta=2.0, selected on OOF predictions for each of 3 CV repeats. **Rule:** median of per-repeat thresholds selected on out-of-fold predictions (decided in M5, D15 / `7ce0891`).
- **Chosen threshold:** 0.6036. Per-repeat thresholds: mean 0.6001 ± 0.0814 (sample std), range [0.5170, 0.6796]. Individual values: repeat 0: 0.6036, repeat 1: 0.5170, repeat 2: 0.6796.
- **Test metrics at the chosen threshold** (scored once; [95% CI]):

| Precision | Recall | F-beta (beta=2) | MCC | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| 0.6049 [0.5238, 0.7000] | 0.7778 [0.6667, 0.8730] | 0.7357 [0.6476, 0.8187] | 0.6743 [0.5930, 0.7531] | 49 | 32 | 14 | 1869 |

Brackets are 95% CIs from a stratified bootstrap of the test rows (2000 resamples, seed 42; positives and negatives resampled separately). They reflect test-sample variation only.
````

#### Deviations
- **D30:** records were amended instead of re-running the case study, to avoid scoring the test
  sets again. Fresh runs compute CIs and coverage natively.
- **M4:** blocked, because no repository URL was given and publishing was not authorised.
- **FINAL_REPORT.md** was regenerated, so that its test metrics also carry CIs.

#### Known limitations
- Bootstrap CIs cover test-sample variation only, not re-splitting or re-training.
- Run (b) results do not describe the 3329 forced-to-train rows (29.8% of the dataset).

---

### Task T-R3 — GitHub CI, calibration disclosure, paired bootstrap, repo tidy

**Date:** 2026-10-23 · **Code/records commit:** `f96c85a`. This entry and the regenerated
FINAL_REPORT.md follow in the next commit. **No test set was re-scored.**

#### M4: GitHub + CI
- **Repository setup:**
  - `git branch -m master main`, then `gh repo create jaswantraj969/imbalancelab --private
    --source . --push`.
  - `gh repo view` reports `"visibility":"PRIVATE"`, default branch `main`.
- **First Actions run (commit `573b2ba`, T-R2 code):** https://github.com/jaswantraj969/imbalancelab/actions/runs/39795270360, conclusion `success`. Its logs
  show 158 passed on each job, plus the `httpx` warning.
- **T-R3 run (commit `f96c85a`):** https://github.com/jaswantraj969/imbalancelab/actions/runs/39841242556, conclusion **success**.

| Job | Result | Started | Completed |
|---|---|---|---|
| checks (3.13) | **success** | 2026-10-22T19:34:14Z | 2026-10-22T19:37:42Z |
| checks (3.11) | **success** | 2026-10-22T19:34:14Z | 2026-10-22T19:36:10Z |

CI log lines (from `gh run view --log`):
````text
checks (3.13)	Ruff lint All checks passed!
checks (3.13)	Ruff format 70 files already formatted
checks (3.13)	Mypy Success: no issues found in 45 source files
checks (3.13)	Pytest TOTAL                                         2524     43    98%
checks (3.13)	Pytest 166 passed in 127.64s (0:02:07)
checks (3.11)	Ruff lint All checks passed!
checks (3.11)	Ruff format 70 files already formatted
checks (3.11)	Mypy Success: no issues found in 45 source files
checks (3.11)	Pytest TOTAL                                         2524     43    98%
checks (3.11)	Pytest 166 passed in 64.29s (0:01:04)
````

The commit with this packet entry triggers another run, which is reported in the hand-off.

#### H1: calibration disclosure (no calibration stage)
- `evaluation/calibration.py`:
  - `reliability_curve`: 10 quantile bins; tied edges merge; n, positives, mean score and
    observed rate per bin.
  - `calibration_disclosure`: the resampler note, or the no-resampler note, plus a
    class-weighting note.
- The final evaluation stores per-model `calibration` (Brier plus its bootstrap CI, and the
  reliability curve). Brier was added to `CI_METRICS`.
- **Report:** a "Calibration (disclosure only…)" subsection with the rendered notes, a Brier
  [CI], a reliability table with n per bin, and the `test_reliability.png` figure. A limitations
  line was added.
- **README:** the limitation is reworded. **API:** `Prediction.probability` has an OpenAPI
  description, and `PredictResponse.score_note` is set per model.
- **Case study:** a "Calibration" section, including the cluster fact as evidence.
- **Tests (`tests/test_calibration_paired.py`):**
  - bins are exact on a synthetic case
  - ties and constant scores
  - disclosure texts
  - the report contains the resampler note when `hgb+smote` is configured, and the no-resampler
    note otherwise
  - the API schema text

#### M1, M2, M3, L3 (case study)
- **M1:** a "Recall scope" statement next to the test recall, using values from
  `cluster_analysis()`.
- **M2:** `paired_bootstrap_difference`, a paired stratified bootstrap that uses the same
  resample indices for both models.
  - It reports the point, 95% CI, win fraction and tie fraction, and is stored in
    `final_evaluation.json["paired_bootstrap"]` for the selected model against each baseline
    (AP, ROC AUC).
  - Shown in the report and in the case-study headline.
  - Tests: identical models give 0 with CI [0, 0] (win 0, tie 1); deterministic by seed; a
    better model gives a positive difference.
- **M3:** the headline sentence is generated from the record. It states whether the OOF
  selection estimate lies inside the test AP CI, with no claim that test exceeds CV.
- **L3:** "(consistent with a floor or zero-measurement value)" is appended to the
  column-minimum line only.

#### L1: the pytest warning
Verbatim, before the fix:
````text
.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa
````

- **Cause:** Starlette 1.9.0's `starlette/testclient.py` does `try: import httpx2 as httpx except
  ModuleNotFoundError: import httpx; warnings.warn(...)`.
- **Fix:** add `httpx2>=2.16,<3` to the `[dev]` extras and regenerate `requirements-lock.txt`
  (httpx2==2.16.0). `httpx` is kept, as T0 specified (D34).
- **Result:** the local gates and both CI jobs report `166 passed` with no warnings summary.

#### L2: process documents moved
- `git mv` IMPLEMENTATION_PLAN.md, PROJECT_STATUS.md, REVIEW_PACKET.md and FINAL_REPORT.md to
  `docs/process/`.
- README has a "Development process" section linking all four. The case-study script links
  `process/REVIEW_PACKET.md`. FINAL_REPORT now links `../case_study.md`.
- `scripts/check_links.py` resolves every relative link in tracked Markdown, excluding fenced
  code and the test snapshot fixture. Its result is included in the hand-off.
- Historical REVIEW_PACKET entries keep their original root-level paths, because they are
  verbatim logs.

#### No test set re-scored (verbatim)
````text
$ sha256sum runs/case_study/runs/*/final_predictions.parquet docs/case_study/*/final_predictions.parquet > preds_before_r3.txt
2649dd787260c792827d7297f3377bb19dc6a4eef39349874b22680a32cc4d3f *runs/case_study/runs/run-20261022T091904Z-596af186/final_predictions.parquet
54816c099b469da1d38b955011cec5c3d7772884b4eda99508030857614c6089 *runs/case_study/runs/run-20261022T092013Z-2056207e/final_predictions.parquet
2649dd787260c792827d7297f3377bb19dc6a4eef39349874b22680a32cc4d3f *docs/case_study/a_stratified/final_predictions.parquet
54816c099b469da1d38b955011cec5c3d7772884b4eda99508030857614c6089 *docs/case_study/b_duplicate_groups/final_predictions.parquet
$ python scripts/run_case_study.py --amend-existing
downloaded <project-root>\data\raw\imblearn\zenodo\x25data.npz sha256=73480c315d42bc5b33c2c73b9078d0034113d26f0511facd9fc5bb07f2d6438a
[a_stratified] amended run-20261022T091904Z-596af186: coverage forced_to_train=0 rows (0 positive); bootstrap CIs added from stored predictions
[b_duplicate_groups] amended run-20261022T092013Z-2056207e: coverage forced_to_train=3329 rows (7 positive); bootstrap CIs added from stored predictions
Largest duplicate cluster (run run-20261022T092013Z-2056207e, duplicate_groups=True)
rows: 3329 of 11183 (29.77% of the dataset)   positives: 7   negatives: 3322
rows in the cluster that are in the test set: 0
identical feature vector of all 3329 rows (all rows equal: True):
  feature_0 = -0.78441482   column min -0.78441482, median -0.10857689, max 31.50844300   is column min: yes   is column max: no   rows with exactly this value: 3360 (30.05%)   rows below it: 0
  feature_1 = -0.47019533   column min -0.47019533, median -0.39499410, max 5.08584910   is column min: yes   is column max: no   rows with exactly this value: 3329 (29.77%)   rows below it: 0
  feature_2 = -0.59163147   column min -0.59163147, median -0.23097900, max 29.47776900   is column min: yes   is column max: no   rows with exactly this value: 3410 (30.49%)   rows below it: 0
  feature_3 = -0.85955255   column min -0.85955255, median -0.85955255, max 9.59116400   is column min: yes   is column max: no   rows with exactly this value: 5766 (51.56%)   rows below it: 0
  feature_4 = -0.37786573   column min -0.37786573, median -0.37786573, max 23.61712200   is column min: yes   is column max: no   rows with exactly this value: 8521 (76.20%)   rows below it: 0
  feature_5 = -0.94572324   column min -0.94572324, median -0.94572324, max 1.94902730   is column min: yes   is column max: no   rows with exactly this value: 5766 (51.56%)   rows below it: 0
features equal to their column minimum: 6 of 6 (consistent with a floor or zero-measurement value)
features equal to 0: 0 of 6
distinct values within the vector: 6
selected model: hgb+smote (persisted model model-20261022T092115Z-819a6e87, refit on outer-train rows only, artifact SHA-256 verified on load)
predicted probability for the cluster's feature vector: 0.08894896   distinct predicted values over the 3329 rows: 1
stored threshold: 0.60359672   predicted label: 0   (training prevalence of the cluster: 0.002103)
wrote docs/case_study.md, docs/case_study/a_stratified, docs/case_study/b_duplicate_groups
$ sha256sum -c preds_before_r3.txt
runs/case_study/runs/run-20261022T091904Z-596af186/final_predictions.parquet: OK
runs/case_study/runs/run-20261022T092013Z-2056207e/final_predictions.parquet: OK
docs/case_study/a_stratified/final_predictions.parquet: OK
docs/case_study/b_duplicate_groups/final_predictions.parquet: OK
````

#### Hash-regeneration check after amendment
````text
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
````

#### Headline, calibration and recall scope (docs/case_study.md, verbatim)
````markdown
## Headline (run b: duplicate-aware split)

The selected model **`hgb+smote`** scored **test AP 0.8228 [0.7383, 0.8977]** on a single evaluation of 1964 test rows with 63 positives (prevalence 0.0321). On the same test rows:

| Model | Test AP [95% CI] | Test ROC AUC [95% CI] | Test Brier [95% CI] (lower is better) | Test rows | Positives | Prevalence |
|---|---|---|---|---|---|---|
| `hgb+smote` | 0.8228 [0.7383, 0.8977] | 0.9589 [0.9180, 0.9889] | 0.0181 [0.0135, 0.0231] | 1964 | 63 | 0.0321 |
| `dummy_prior` | 0.0321 [0.0321, 0.0321] | 0.5000 [0.5000, 0.5000] | 0.0312 [0.0312, 0.0312] | 1964 | 63 | 0.0321 |
| `logreg_balanced` | 0.5023 [0.3926, 0.6442] | 0.9225 [0.8764, 0.9611] | 0.1182 [0.1101, 0.1267] | 1964 | 63 | 0.0321 |

Paired bootstrap of the test difference (`hgb+smote` − baseline; same resampled rows for both models):

| Baseline | Metric | Difference [95% CI] | Win fraction |
|---|---|---|---|
| `dummy_prior` | average_precision | +0.7907 [+0.7062, +0.8657] | 1.000 |
| `dummy_prior` | roc_auc | +0.4589 [+0.4180, +0.4889] | 1.000 |
| `logreg_balanced` | average_precision | +0.3205 [+0.2078, +0.4115] | 1.000 |
| `logreg_balanced` | roc_auc | +0.0364 [-0.0025, +0.0791] | 0.962 |

The OOF selection estimate for `hgb+smote` (mean AP 0.7515, optimistic because it was used for selection) **lies inside** the test AP 95% CI [0.7383, 0.8977]. The two are consistent. This does **not** show that test performance exceeds CV performance.

Brackets are 95% CIs from a stratified bootstrap of the test rows (2000 resamples, seed 42; positives and negatives resampled separately). They reflect test-sample variation only.

**Evaluation coverage (run b): 3329 rows (29.8% of the dataset, 7 positives) are never in any test or validation set.** They form one oversized duplicate cluster that is forced to training, so the results above do not describe those rows. See [Evaluation coverage](#evaluation-coverage-run-b) and the [data-quality finding](#data-quality-finding-the-3329-row-cluster).

Run (b) is the headline because in run (a) exact-duplicate rows cross the train/test and CV boundaries. In run (b) the cross-boundary duplicate check reports 0 test rows and 0 affected folds.
````

````markdown
## Calibration (disclosure only; no calibration stage)

- **Scores from models trained with a resampler (`hgb+random_under`, `hgb+smote`) are ranking scores, NOT calibrated probabilities. Resampling changes the class balance seen during training, so these scores do not estimate the probability of the positive class. Do not interpret them as risk.**
- **Class-weighted models (`logreg_balanced`, `random_forest`) also shift scores away from the training prevalence.**
- Test Brier score of `hgb+smote`: 0.0181 [0.0135, 0.0231]. The reliability curve (quantile bins, n per bin) is in the run (b) audit report, section 9.
- **Evidence from the cluster:** for the 3329-row cluster, `hgb+smote` outputs 0.0889, while the cluster's observed positive rate is 0.0021 (7/3329, in training rows). That is 42× higher, so this score does not estimate the probability of the positive class.
````

````markdown
**Recall scope:** the 3329 forced-to-train rows all have the same score, 0.0889, which is below the stored threshold 0.6036, so all of them are classified **negative** (label 0). Their 7 positives would therefore be missed. The test recall above describes only the evaluated rows.
````

#### Calibration disclosure as rendered in the run (b) report (verbatim)
````markdown
### Calibration (disclosure only; no calibration stage)

- **Scores from models trained with a resampler (`hgb+random_under`, `hgb+smote`) are ranking scores, NOT calibrated probabilities. Resampling changes the class balance seen during training, so these scores do not estimate the probability of the positive class. Do not interpret them as risk.**
- **Class-weighted models (`logreg_balanced`, `random_forest`) also shift scores away from the training prevalence.**

Test Brier score (hgb+smote): 0.0181 [0.0135, 0.0231] (lower is better). Reliability bins for the selected model (quantile bins of its test scores; n per bin shown):

| Bin | Score range | n | Positives | Mean score | Observed rate |
|---|---|---|---|---|---|
| 1 | [0.0000, 0.0000] | 197 | 1 | 0.0000 | 0.0051 |
| 2 | [0.0000, 0.0001] | 196 | 0 | 0.0000 | 0.0000 |
| 3 | [0.0001, 0.0001] | 196 | 0 | 0.0001 | 0.0000 |
| 4 | [0.0001, 0.0002] | 197 | 1 | 0.0002 | 0.0051 |
| 5 | [0.0002, 0.0003] | 196 | 0 | 0.0003 | 0.0000 |
| 6 | [0.0003, 0.0006] | 196 | 0 | 0.0004 | 0.0000 |
| 7 | [0.0006, 0.0011] | 197 | 1 | 0.0008 | 0.0051 |
| 8 | [0.0011, 0.0034] | 196 | 1 | 0.0020 | 0.0051 |
| 9 | [0.0034, 0.0229] | 196 | 1 | 0.0082 | 0.0051 |
| 10 | [0.0229, 1.0000] | 197 | 58 | 0.4565 | 0.2944 |
````

#### git diff --stat 573b2ba..f96c85a
````text
 README.md                                          |  24 +-
 docs/case_study.md                                 |  34 ++-
 docs/case_study/a_stratified/final_evaluation.json | 291 ++++++++++++++++++-
 .../a_stratified/final_evaluation_log.jsonl        |   1 +
 .../report/figures/test_reliability.png            | Bin 0 -> 37475 bytes
 docs/case_study/a_stratified/report/report.html    |  16 +-
 docs/case_study/a_stratified/report/report.md      |  41 ++-
 docs/case_study/a_stratified/run.json              |   4 +
 .../b_duplicate_groups/final_evaluation.json       | 323 ++++++++++++++++++++-
 .../b_duplicate_groups/final_evaluation_log.jsonl  |   1 +
 .../report/figures/test_reliability.png            | Bin 0 -> 40753 bytes
 .../b_duplicate_groups/report/report.html          |  16 +-
 .../case_study/b_duplicate_groups/report/report.md |  43 ++-
 docs/case_study/b_duplicate_groups/run.json        |   4 +
 FINAL_REPORT.md => docs/process/FINAL_REPORT.md    |   0
 .../process/IMPLEMENTATION_PLAN.md                 |   0
 .../process/PROJECT_STATUS.md                      |  35 ++-
 REVIEW_PACKET.md => docs/process/REVIEW_PACKET.md  |   0
 pyproject.toml                                     |   1 +
 requirements-lock.txt                              |  14 +
 scripts/check_links.py                             |  41 +++
 scripts/run_case_study.py                          |  98 ++++++-
 src/imbalancelab/api/schemas.py                    |  16 +-
 src/imbalancelab/evaluation/calibration.py         |  73 +++++
 src/imbalancelab/evaluation/final.py               |  41 ++-
 src/imbalancelab/evaluation/uncertainty.py         |  72 ++++-
 src/imbalancelab/reporting/figures.py              |  34 +++
 src/imbalancelab/reporting/report.py               |  85 +++++-
 src/imbalancelab/workflow.py                       |  14 +
 tests/snapshots/report_structure.md                |  40 ++-
 tests/test_calibration_paired.py                   | 151 ++++++++++
 tests/test_reporting.py                            |   3 +-
 32 files changed, 1456 insertions(+), 60 deletions(-)
````

#### Gate, Python 3.13.5 (verbatim)
````text
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
````

#### Gate, Python 3.11.15 (verbatim)
````text
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
````

#### Deviations
- **D34:** `httpx2` was added to the dev extras, which is a dependency change relative to T0's
  list, justified above.
- **Process docs:** the review-packet and status files are now under `docs/process/`.
- **Report snapshot:** regenerated once. The reviewed diff contains only the Brier CI, the
  paired table, the calibration subsection, the reliability figure line and the limitation
  line. The traceability test's figure set was extended to 5, which is stricter.
