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
