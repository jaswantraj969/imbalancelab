# ImbalanceLab audit report: run <run_id>

## <n>. Verdict

- Best candidate by mean out-of-fold AP: **hgb** (selected on OOF predictions only; the test set was not used for selection).
- **hgb** <verdict> **dummy_prior** on out-of-fold average precision: mean paired difference <n>, better in <n> of <n> folds (win fraction <n>).
- **hgb** <verdict> **logreg_balanced** on out-of-fold average precision: mean paired difference <n>, better in <n> of <n> folds (win fraction <n>).
- **logreg_balanced** <verdict> **dummy_prior** on out-of-fold average precision: mean paired difference <n>, better in <n> of <n> folds (win fraction <n>).
- **hgb** <verdict> **dummy_prior** on the test set (average_precision: <n> vs <n>, difference <n>; single evaluation, no spread).
- **hgb** <verdict> **logreg_balanced** on the test set (average_precision: <n> vs <n>, difference <n>; single evaluation, no spread).

Comparisons use paired differences on identical stored folds. CV folds are correlated, so no significance test is reported; win fractions and spreads are descriptive.

## <n>. Dataset

| Field | Value |
|---|---|
| Source file | synthetic.csv |
| SHA<n> | `<sha<n>>` |
| Rows | <n> |
| Target / positive label | `label` / `yes` |
| Positives / negatives | <n> / <n> |
| Positive rate | <n> |
| Imbalance ratio (neg:pos) | <n> |
| Feature columns | <n> |
| Split strategy (schema) | stratified |

Features used: <n> numeric, <n> categorical.

## <n>. Data profile warnings

These are **heuristic suspicions with the triggering statistic**, not proof of a problem. Each needs domain review.

| Code | Column | Severity | Message |
|---|---|---|---|
| id_like_column | ts | warning | Column 'ts' looks like a possible identifier (near-unique values); identifiers rarely generalise and may encode row order. |

Duplicates: <n> exact duplicate rows; <n> conflicting-label groups (<n> rows).

## <n>. Split strategy

| Field | Value |
|---|---|
| Outer holdout strategy | stratified |
| Test size (config) | <n> |
| Outer-train rows / test rows / gap rows | <n> / <n> / <n> |
| Test indices SHA<n> | `<sha<n>>` |
| Inner CV strategy | stratified |
| Folds × repeats | <n> × <n> (<n> folds) |
| Fold indices SHA<n> | `<sha<n>>` |
| Duplicate-aware groups | off |
| Oversized groups pinned to training (test / CV) | <n> groups, <n> rows / <n> groups, <n> rows |

CV, model selection and threshold selection use outer-train rows only. All models were fit on identical stored folds.

## <n>. Models

| Name | Role | Sampler | Estimator |
|---|---|---|---|
| dummy_prior | baseline | none | DummyClassifier(strategy='prior'): predicts the training prevalence |
| logreg_balanced | baseline | none | LogisticRegression(class_weight='balanced', max_iter=<n>) |
| hgb | candidate | none | HistGradientBoostingClassifier(max_iter=<n>, learning_rate=<n>, early_stopping=False) |

## <n>. Cross-validation results (out-of-fold)

Mean ± sample std across folds. `@ref` metrics use the fixed reference threshold <n>, not a tuned threshold.

| Model | AP (primary) | ROC AUC | Brier ↓ | Precision@ref | Recall@ref | F<n>@ref |
|---|---|---|---|---|---|---|
| dummy_prior | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | undefined (<n>/<n> folds defined) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) |
| logreg_balanced | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) |
| hgb | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) | <n> ± <n> (n=<n>) |

### Paired comparisons against baselines

| Candidate | Baseline | Metric | Pairs | Mean diff | Std diff | W/L/T | Win fraction |
|---|---|---|---|---|---|---|---|
| hgb | dummy_prior | average_precision | <n> | <n> | <n> | <n>/<n>/<n> | <n> |
| hgb | dummy_prior | roc_auc | <n> | <n> | <n> | <n>/<n>/<n> | <n> |
| hgb | logreg_balanced | average_precision | <n> | <n> | <n> | <n>/<n>/<n> | <n> |
| hgb | logreg_balanced | roc_auc | <n> | <n> | <n> | <n>/<n>/<n> | <n> |
| logreg_balanced | dummy_prior | average_precision | <n> | <n> | <n> | <n>/<n>/<n> | <n> |
| logreg_balanced | dummy_prior | roc_auc | <n> | <n> | <n> | <n>/<n>/<n> | <n> |

![OOF curve oof_pr](figures/oof_pr.png)

![OOF curve oof_roc](figures/oof_roc.png)

## <n>. Threshold analysis (out-of-fold predictions only)

| Model | Strategy | Chosen (median) | Per-repeat threshold mean ± std [min, max] | Precision | Recall | F-beta | Repeats |
|---|---|---|---|---|---|---|---|
| hgb | max_fbeta (beta <n>) | <n> | <n> ± <n> [<n>, <n>] | <n> | <n> | <n> | <n> |
| dummy_prior | max_fbeta (beta <n>) | <n> | <n> ± <n> [<n>, <n>] | <n> | <n> | <n> | <n> |
| logreg_balanced | max_fbeta (beta <n>) | <n> | <n> ± <n> [<n>, <n>] | <n> | <n> | <n> | <n> |

Precision, recall and F-beta are per-repeat means at each repeat's own selected threshold, which is optimistic because selection and measurement use the same OOF predictions.

## <n>. Final test evaluation

Model **hgb** refit on <n> outer-train rows and scored once on <n> test rows (<n> positive) at threshold <n> (selected on out-of-fold predictions, strategy `max_fbeta`). Evaluated at <time>.

| Model | Threshold | AP | ROC AUC | Brier ↓ | Precision | Recall | F-beta | MCC | TP/FP/FN/TN |
|---|---|---|---|---|---|---|---|---|---|
| hgb | <n> | <n> | <n> | <n> | <n> | <n> | <n> | <n> | <n>/<n>/<n>/<n> |
| dummy_prior | <n> | <n> | <n> | <n> | <n> | <n> | <n> | undefined | <n>/<n>/<n>/<n> |
| logreg_balanced | <n> | <n> | <n> | <n> | <n> | <n> | <n> | <n> | <n>/<n>/<n>/<n> |

![Test curve test_pr](figures/test_pr.png)

![Test curve test_roc](figures/test_roc.png)

Final-evaluation log: <n> entry.

- <time>: final_evaluation

## <n>. Limitations

- CV folds share training data, so fold scores are correlated; spreads understate uncertainty and no significance claims are made.
- Profile warnings are heuristics; a flagged column is not proven leakage, and an unflagged column is not proven safe.
- Thresholds are selected on out-of-fold predictions; their OOF metrics are optimistic.
- Test results are a single evaluation per model with no spread.
- Only <n> positive test rows: test metrics have high variance.

## <n>. Reproducibility

| Field | Value |
|---|---|
| Run ID | <run_id> |
| Created / finished | <time> / <time> |
| Seed | <n> |
| Dataset SHA<n> | `<sha<n>>` |
| Fold indices SHA<n> | `<sha<n>>` |
| Test indices SHA<n> | `<sha<n>>` |
| Python / platform | <platform> |
| imbalancelab | <n>.<n> |
| numpy | <n>.<n> |
| pandas | <n>.<n> |
| scikit-learn | <n>.<n> |
| imbalanced-learn | <n>.<n> |
| scipy | <n>.<n> |
| joblib | <n>.<n> |
| pyarrow | <n>.<n> |
| pydantic | <n>.<n> |
| matplotlib | <n>.<n> |

Experiment config (`config.json`):

```json
{
  "candidates": [
    {
      "model": "hgb",
      "sampler": "none"
    }
  ],
  "cv": {
    "n_splits": <n>,
    "n_repeats": <n>,
    "gap": <n>,
    "seed": <n>,
    "max_eval_group_fraction": <n>
  },
  "seed": <n>,
  "threshold": <n>,
  "beta": <n>,
  "smote_k_neighbors": <n>
}
```
