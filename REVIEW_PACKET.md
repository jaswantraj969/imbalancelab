# Review Packet

The Implementation Engineer fills in one entry per task, newest first, by copying the template
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
