# ImbalanceLab

ImbalanceLab is a library-first toolkit for **leakage-safe, reproducible experiments on
imbalanced binary classification**. A FastAPI backend and a Streamlit frontend sit on top of
the library. Every number it reports comes from an executed run with a stored, hash-stamped run
record.

- **Data:** schema validation, plus a profile that flags suspected leakage, ID-like columns,
  duplicates and constant columns. These are flagged as *warnings with evidence*, never as
  proof.
- **Splits:** an outer train/test holdout created **once per dataset** (stratified, group, or
  temporal), with inner repeated CV on outer-train rows only.
- **Pipelines:** imblearn pipelines in which imputation, scaling, encoding and resampling are
  fit inside each training fold.
- **Comparison:** Dummy and class-weighted LogReg baselines run on identical stored folds, with
  paired per-fold comparisons and win fractions (no naive significance tests).
- **Thresholds:** selected on out-of-fold predictions per repeat. Test predictions are rejected
  for selection.
- **Final evaluation:** a one-shot test evaluation (a repeat is refused unless forced, and
  forcing is logged), and a Markdown/HTML audit report generated only from run records.
- **Serving:** persisted models with an integrity check and an inference endpoint.

Status per milestone: [PROJECT_STATUS.md](PROJECT_STATUS.md). Plan:
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Worked example on real data:
[docs/case_study.md](docs/case_study.md).

## Install

Requires Python 3.11+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -e ".[dev,ui]"                                  # ranges from pyproject.toml
# or, reproducibly:
pip install -r requirements-lock.txt && pip install -e . --no-deps
```

## Quickstart: library

```python
from pathlib import Path

from imbalancelab.data import DatasetSchema, load_dataset
from imbalancelab.evaluation.config import ExperimentConfig
from imbalancelab.evaluation.final import final_evaluate
from imbalancelab.evaluation.runner import run_experiment
from imbalancelab.evaluation.thresholds import ThresholdStrategy, run_threshold_analysis
from imbalancelab.profiling import profile_dataset
from imbalancelab.reporting import generate_report
from imbalancelab.splitting import HoldoutConfig, get_or_create_holdout

schema = DatasetSchema(target="label", positive_label="yes", id_column="row_id")
ds = load_dataset("my_data.csv", schema)  # validates; computes the file SHA-256
profile = profile_dataset(ds)  # warnings are suspicions with evidence
holdout = get_or_create_holdout(ds, HoldoutConfig(test_size=0.2), Path("holdout.json"))

config = ExperimentConfig.model_validate(
    {"candidates": [{"model": "hgb"}, {"model": "hgb", "sampler": "random_under"}]}
)  # baselines are always added
run = run_experiment(ds, holdout, config, Path("runs"), profile=profile)
best = run.summary["best_candidate_by_mean_oof_ap"]

run_threshold_analysis(run.run_dir, best, ThresholdStrategy(kind="max_fbeta", beta=2.0))
final = final_evaluate(ds, run.run_dir, best)  # scores the test rows once
print(generate_report(run.run_dir).markdown)  # runs/<run_id>/report/report.md
```

## Quickstart: API

```bash
uvicorn imbalancelab.api.app:app
```

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness and version |
| POST | `/datasets` | multipart `file` (CSV/Parquet) + `schema` JSON (+ optional `holdout` JSON): validate, profile, create holdout |
| GET | `/datasets`, `/datasets/{id}/profile` | registrations and profile |
| POST / GET | `/runs`, `/runs/{id}` | run an experiment (synchronous), list runs, get run details |
| POST | `/runs/{id}/thresholds` | OOF threshold analysis for one model |
| POST | `/runs/{id}/final-evaluation` | one-shot test evaluation; persists the model (returns `model_id`) |
| GET | `/runs/{id}/report?format=html\|markdown` | audit report |
| GET / POST | `/models`, `/models/{id}/predict` | persisted models; predictions at the stored threshold |

Interactive docs are served at `/docs`. Runs execute **synchronously** (MVP). A request returns
when the work is done.

```bash
curl -F file=@my_data.csv -F 'schema={"target":"label","positive_label":"yes"}' \
     http://localhost:8000/datasets
curl -X POST http://localhost:8000/runs -H 'content-type: application/json' \
     -d '{"dataset_id":"<id>","config":{"candidates":[{"model":"hgb"}]}}'
```

Settings come from environment variables prefixed `IMBALANCELAB_` (`DATASETS_DIR`, `RUNS_DIR`,
`MODELS_DIR`, `MAX_UPLOAD_BYTES`, `SEED`). See `src/imbalancelab/config.py`.

## Quickstart: UI

```bash
uvicorn imbalancelab.api.app:app                      # terminal 1
IMBALANCELAB_API_URL=http://localhost:8000 streamlit run frontend/app.py   # terminal 2
```

The Streamlit app talks to the API only. It never imports the library, and a test enforces
this.

## Architecture

```
src/imbalancelab/
  data/        schema (pydantic) + CSV/Parquet loader with explicit validation errors
  profiling/   DatasetProfile + ProfileWarning heuristics
  splitting/   outer holdout (stored, hash-verified), inner CV, cross-boundary duplicates
  pipelines/   FeatureSpec + imblearn Pipeline builder (preprocess -> sampler -> model)
  models/      registry (baselines + candidates), persistence (joblib + metadata + SHA-256)
  evaluation/  metrics (explicit undefined cases), runner, thresholds, final evaluation
  tracking/    file-based run records (RunStore, RunRecord, environment capture)
  reporting/   Markdown/HTML audit report + PR/ROC figures from stored predictions
  workflow.py  workspace-level orchestration used by the API
  api/         FastAPI app: validation + one workflow call per route
frontend/      Streamlit client (requests only)
scripts/       gate.sh (milestone gate), run_case_study.py
```

A run directory (`runs/<run_id>/`) contains `run.json`, `config.json`, `environment.json`,
`dataset_sha256.txt`, `holdout.json`, `fold_indices.json`, `profile.json`, `fold_metrics.json`,
`summary.json` and `oof_predictions.parquet`. After later steps it also contains
`thresholds.json`, `final_evaluation.json`, `final_predictions.parquet`,
`final_evaluation_log.jsonl` and `report/`.

## Methodology invariants

1. All preprocessing, feature selection and resampling are fit inside training folds only.
2. Resampling happens only through `imblearn.pipeline.Pipeline` and is never applied to
   validation or test data.
3. Thresholds are selected on out-of-fold or validation predictions only. Test-provenance
   predictions raise `ProvenanceError`.
4. The primary metric is average precision. Every result is reported against
   `DummyClassifier` and class-weighted `LogisticRegression` baselines on identical stored
   fold indices.
5. Every run records the seed, full config, dataset SHA-256, fold-index SHA-256 and library
   versions.
6. No fabricated metrics. Reports read run records only.
7. The outer holdout is created once per dataset and its test indices are hashed. CV,
   selection and thresholds use outer-train rows. Test rows are scored once, after model and
   threshold are fixed. Persisted models are refit on outer-train rows only.

## Run checks

```bash
bash scripts/gate.sh        # ruff check, ruff format --check, mypy, pytest + coverage
```

CI (`.github/workflows/ci.yml`) runs the same checks on Python 3.11 and 3.13.

## Limitations

- Binary targets only. Small fixed model configs, with no hyperparameter search.
- Synchronous API with no job queue, auth, or database (all storage is files). Intended for
  local or single-user use.
- Datetime features are dropped, not encoded. SMOTE interpolates one-hot columns.
- Probabilities are not calibrated. Test results are single evaluations with no spread.
- Profile heuristics can miss leakage and can flag innocent columns. They need domain review.
- joblib artifacts are pickles. Only load models from a workspace you trust (the SHA-256 is
  checked before loading).
