# ImbalanceLab — Implementation Plan

ImbalanceLab is a library-first toolkit for leakage-safe, reproducible experiments on imbalanced
binary classification. The FastAPI service and the Streamlit frontend are thin layers over the
library. This plan is the contract for each milestone. A milestone is **done** when the engineer's
acceptance criteria pass, and **verified** only when the supervisor has reviewed it.

## Methodology invariants

These hold for every milestone. Any change that would break one is a defect.

1. **All preprocessing, feature selection, and resampling are fit inside training folds only.**
   No statistic (mean, scaler parameters, encoder vocabulary, selected features, synthetic
   samples) may be computed on data that is later used for validation or testing.
2. **Resampling is done through an `imblearn.pipeline.Pipeline` and is never applied to
   validation or test data.** Samplers run only during `fit`. Predictions and scoring use the
   original, unresampled data.
3. **Thresholds are chosen on validation or out-of-fold predictions only. The test set is used
   once**, for final reporting after every modelling and threshold decision has been fixed.
4. **The primary metric is average precision (area under the precision-recall curve).** Every
   result is reported against a `DummyClassifier` baseline and a class-weighted logistic
   regression baseline run on the same splits.
5. **Every run records its seed, full config, dataset SHA-256, and library versions** (Python,
   numpy, pandas, scikit-learn, imbalanced-learn, and others in use).
6. **No fabricated metrics.** Every number in reports, docs, the README, or the case study comes
   from an executed run with a stored run record. Illustrative examples are labelled as such and
   contain no numbers that look like results.

## Milestones

### M0 — Project skeleton and tooling
**Objective:** An installable src-layout package with lint, format, type-check, and test tooling,
plus the three project records.

**Acceptance criteria**
- `pip install -e ".[dev,ui]"` succeeds on Python ≥ 3.11.
- `ruff check .` and `ruff format --check .` report zero issues.
- `pytest` passes with no skips. The smoke tests cover `__version__`, the import of every
  subpackage, and the default seed of 42.
- `IMPLEMENTATION_PLAN.md`, `PROJECT_STATUS.md`, and `REVIEW_PACKET.md` exist with their
  required sections.
- No ML logic exists. Each subpackage contains only an `__init__.py` docstring.

### M1 — Data loading, schema validation, profiling
**Objective:** Load tabular data (CSV/Parquet), validate it against a declared schema, and
produce a dataset profile that brings risks to the surface without overstating them.

**Acceptance criteria**
- The loader accepts a path and a schema (target column, the positive label, optional ID, group,
  and time columns, and expected dtypes). It raises clear errors for missing columns, a
  non-binary target, a positive label that is absent, or an empty dataset.
- A dataset SHA-256 is computed from the file bytes and returned with the loaded data.
- The profile reports:
  - class counts, class proportions, and the imbalance ratio
  - missingness for each column
  - exact duplicate rows, and duplicates that differ only in their label (conflicting labels)
  - constant and near-constant columns
  - ID-like columns (a high-cardinality unique key, or a monotonic integer)
  - target-leak suspects: features that alone almost perfectly separate the target, or features
    whose names match the target.
- Leak suspects, ID-like columns, and other heuristics are reported as **WARNINGS with the
  evidence behind them, not as proof**. The report wording says "suspected" and gives the
  statistic that triggered the warning.
- Unit tests use small synthetic DataFrames built in the tests. No downloaded datasets.

### M2 — Splitting and leakage-safe pipeline builder
**Objective:** Provide stratified, group, and temporal split strategies, and a builder that
produces leakage-safe imblearn pipelines.

**Acceptance criteria**
- Stratified: the class proportions of every fold stay within tolerance of the overall
  proportions, and the folds are reproducible for a given seed.
- Group: no group appears on both sides of any split (tested).
- Temporal: every validation or test timestamp is later than every training timestamp, with an
  optional gap (tested).
- Errors are raised for folds that cannot be built (for example, fewer minority samples than
  folds).
- The pipeline builder composes preprocessing, an optional sampler, and an estimator into an
  `imblearn.pipeline.Pipeline`.
- Tests show that the preprocessing parameters fitted in each fold come only from the training
  rows, and that the sampler does not change the data at predict or score time.

### M3 — Metrics module
**Objective:** A metric suite for imbalanced problems that handles undefined metrics
explicitly.

**Acceptance criteria**
- Metrics: average precision (primary), ROC AUC, precision, recall, F1, F-beta, balanced
  accuracy, MCC, Brier score, and the confusion matrix at a given threshold.
- Undefined cases (single-class `y_true`, no positive predictions, constant scores) return an
  explicit "undefined" result with a reason. They never return a silent 0, a NaN without
  explanation, or a crash.
- Tests cover single-class folds, all-negative predictions, perfect predictions, and constant
  scores, and compare values with scikit-learn on ordinary inputs.

### M4 — Experiment runner, baselines, run records
**Objective:** Run reproducible repeated stratified CV experiments and save the results as
file-based run records.

**Acceptance criteria**
- The model registry contains a `DummyClassifier` (prior/stratified), a class-weighted
  `LogisticRegression`, and one tree ensemble (for example `HistGradientBoostingClassifier` or
  `RandomForestClassifier`).
- The runner performs repeated stratified K-fold CV. It produces metrics for each fold, a
  summary (mean, std, and fold count), and stored out-of-fold predictions.
- Each run writes a directory under `runs/` containing the config, seed, dataset SHA-256,
  library versions, per-fold metrics, the summary, OOF predictions, and timestamps.
- Re-running with the same seed and config gives identical metrics (tested).
- Baselines always run alongside the candidate models.

### M5 — Threshold analysis
**Objective:** Choose and analyse decision thresholds without touching the test set.

**Acceptance criteria**
- Threshold curves (precision, recall, F-beta, and cost when a cost matrix is given) are computed
  from OOF or validation predictions only.
- Selection strategies: maximise F-beta, reach a target recall or precision, and minimise
  expected cost.
- The API rejects test-set predictions passed as threshold-selection input. Provenance is
  checked, and a test covers this.
- The chosen threshold and its provenance are saved in the run record.

### M6 — Evidence-based audit report
**Objective:** Generate a Markdown/HTML audit report from run records alone.

**Acceptance criteria**
- The report includes the dataset profile and warnings, the split strategy, models compared
  with baselines, metric tables with spread across folds, threshold analysis, the limitations,
  and the reproducibility metadata (seed, SHA-256, versions).
- Every number in the report traces to a field in a run record. The generator reads only run
  records.
- The report states when a model does not beat the baselines.
- A snapshot test runs on a small synthetic run.

### M7 — FastAPI endpoints
**Objective:** Expose the library over HTTP.

**Acceptance criteria**
- Endpoints for health, dataset upload/profile, starting and listing experiment runs, getting
  run details and metrics, threshold analysis, and report retrieval.
- Route handlers only validate requests and call library functions. They contain no ML logic.
- Request and response models use pydantic. Errors map to appropriate HTTP status codes.
- Tests use `fastapi.testclient` / `httpx`.

### M8 — Streamlit frontend
**Objective:** A simple UI that talks to the API only.

**Acceptance criteria**
- Pages: upload/profile, configure and launch a run, view results and thresholds, view the
  report.
- Uses `requests` against the API. It never imports `imbalancelab` library internals (checked by
  a test or lint rule).
- The API base URL is configurable.

### M9 — Model persistence and inference
**Objective:** Persist trained pipelines and serve predictions.

**Acceptance criteria**
- The final pipeline is refit on the full training data and saved with joblib, together with
  metadata (run ID, threshold, feature schema, library versions, SHA-256 of the artifact).
- Loading checks the schema and warns when library versions differ.
- The inference endpoint validates input columns and returns probabilities and labels at the
  stored threshold.
- A round-trip test checks that save → load → predict matches the in-memory predictions.

### M10 — Documentation and case study
**Objective:** User documentation, plus a case study built from real executed results.

**Acceptance criteria**
- The README covers installation, the quickstart, the library API, and the use of the API and
  UI.
- The case study uses a public dataset with its source, licence, and SHA-256 recorded. Its
  numbers come only from run records stored or linked in the repo, and the commands to
  reproduce them are included.
- The documentation states the limitations and the invariants.

## Not in MVP

- MLflow or any other external experiment-tracking server (tracking is file-based only)
- Docker or container orchestration
- Databases (all storage is on the file system)
- Authentication, authorisation, and multi-user support
- React or any other JavaScript frontend (Streamlit only)
- Multiclass and multilabel targets (binary only)
- Deep learning models, GPU support, and distributed training
- Hyperparameter search beyond small fixed grids
- Automated feature engineering
- Cloud deployment and production monitoring or drift detection
- Probability calibration as a separate stage (may be revisited after M10)
