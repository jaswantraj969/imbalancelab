# ImbalanceLab

ImbalanceLab is a Python library (planned API and frontend to follow) for running leakage-safe,
reproducible experiments on imbalanced binary classification problems and producing
evidence-based audit reports.

**Status:** project skeleton only (milestone M0). No ML functionality is implemented yet.
See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Install

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev,ui]"
```

## Run checks

```bash
ruff check .
ruff format --check .
pytest -q
```
