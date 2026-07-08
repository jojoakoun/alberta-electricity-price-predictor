# Project Decisions

This file records the main technical and product decisions for the Alberta Electricity Price Predictor.

Each decision uses this structure:

- **Decision:** what we chose
- **Why:** why the choice makes sense
- **Rejected:** what we chose not to do
- **Next:** what the decision supports next

Decision IDs are organized by phase:

- `P0` = repository setup
- `P1` = data engineering
- `P2` = feature engineering
- `P3` = modeling

---

## Phase 0 — Repository Setup

### P0-D01 — Build a clean public-first project

**Decision:** Build the project from zero with a clean public repository structure.

**Why:** The repository must be easy to understand, run, and maintain.

**Rejected:** Starting with unnecessary complexity before the core product works.

**Next:** Use the project foundation to support data engineering, modeling, and application development.

### P0-D02 — Keep the public product name simple

**Decision:** Use `Alberta Electricity Price Predictor` as the project name.

**Why:** The name is clear and describes the project directly.

**Rejected:** Using a separate brand name before the product direction is stable.

**Next:** Revisit branding only after the core product works.

---

## Phase 1 — Data Engineering

### P1-D01 — Keep CSV as the interim data format

**Decision:** Keep interim datasets as CSV files.

**Why:** CSV is simple, readable, easy to inspect, and enough for the current phase.

**Rejected:** Switching to Excel or a heavier data format before the project needs it.

**Next:** Continue using CSV for interim outputs unless scale or performance requires another format.

### P1-D02 — Separate historical ingestion from API ingestion

**Decision:** Keep historical CSV ingestion and AESO API ingestion in separate modules.

**Why:** The two sources have different formats, validation needs, and failure modes.

**Rejected:** Mixing CSV and API logic in one large script.

**Next:** Keep each source clean, then combine them through the pipeline layer.

### P1-D03 — Use project-standard column names

**Decision:** Rename raw source columns into stable project names.

Current standard columns include:

- `datetime_universal_time`
- `datetime_local_time`
- `actual_price`
- `forecast_price`
- `alberta_internal_load`

**Why:** Stable names make downstream code easier to read and maintain.

**Rejected:** Using source-specific names such as `Date_Begin_GMT` or `ACTUAL_AIL` throughout the project.

**Next:** Use these names consistently in validation, EDA, feature engineering, and modeling.

### P1-D04 — Extend historical data without overwriting it

**Decision:** Let AESO API data extend the historical CSV data only after the last historical UTC timestamp.

**Why:** The historical CSV remains the trusted base for older records, while the API adds newer records.

**Rejected:** Allowing API rows to overwrite existing historical rows.

**Next:** Continue checking for duplicate UTC timestamps after merging.

### P1-D05 — Keep recent incomplete API rows in the source dataset

**Decision:** Keep recent API rows even when `actual_price` is not finalized yet.

**Why:** Recent market data may include hours where the actual pool price is not available yet. These rows are useful for live data awareness but not for training.

**Rejected:** Deleting incomplete recent rows from the source dataset.

**Next:** Exclude rows without finalized `actual_price` when creating modeling datasets.

### P1-D06 — Do not rely on `alberta_internal_load` in the first modeling dataset unless recent load data is added

**Decision:** Do not rely on `alberta_internal_load` as a required feature in the first modeling dataset.

**Why:** This column is available in the historical CSV but missing for recent AESO pool price API records. A model that depends on it would not work consistently on current API-extended data.

**Rejected:** Forcing `alberta_internal_load` into the first modeling dataset despite recent missing values.

**Next:** Either exclude this feature from the first model or add a reliable recent AIL source later.

### P1-D07 — Add explicit data quality reporting before feature engineering

**Decision:** Add a data quality report before building features.

**Why:** Feature engineering should not start until the project understands coverage, missing values, duplicate timestamps, hourly continuity, and zero-price behavior.

**Rejected:** Moving directly from data ingestion to feature engineering without quality checks.

**Next:** Use the data quality report as a checkpoint before modeling data preparation.

### P1-D08 — Complete EDA before defining recommendation thresholds

**Decision:** Answer business-focused EDA questions before defining `recommended`, `acceptable`, and `avoid` thresholds.

**Why:** Thresholds should be supported by historical price behavior, spike patterns, forecast usefulness, and model evaluation.

**Rejected:** Hardcoding recommendation thresholds too early.

**Next:** Use EDA findings to guide feature engineering, baseline models, spike-risk classification, and the future decision layer.

---

## Phase 2 — Feature Engineering

### P2-D01 — Create a separate modeling dataset

**Decision:** Create a separate modeling dataset instead of modifying the current historical dataset directly.

**Why:** The current historical dataset is the clean source dataset produced by the data pipeline. Feature engineering adds model-specific columns, removes rows that are not usable for training, and prepares data for machine learning.

**Rejected:** Adding feature columns directly to `data/interim/current_historical_prices_clean.csv`.

**Next:** Create a feature engineering module that reads the current historical dataset and writes a processed modeling dataset.

### P2-D02 — Exclude unfinished target rows from modeling datasets

**Decision:** Exclude rows where `actual_price` is missing from modeling datasets.

**Why:** `actual_price` is the target for price prediction. Rows without a finalized actual price cannot be used to train or evaluate a supervised model.

**Rejected:** Keeping unfinished target rows in the modeling dataset.

**Next:** Keep incomplete recent rows in the source dataset, but remove them when building model-ready data.

### P2-D03 — Build the first feature set with available current data

**Decision:** Build the first modeling dataset using features that are available in the current API-extended dataset.

Initial feature groups may include:

- time features
- forecast price features
- lag features
- rolling price features
- recent spike-history features

**Why:** The first model should work with the data that the project can reliably generate now.

**Rejected:** Depending on unavailable or incomplete external features before the first modeling dataset works.

**Next:** Design and implement the first feature engineering module slowly, with tests and inspection after each step.

### P2-D04 — Keep modeling data separate from training data

**Decision:** Keep `data/processed/modeling_dataset.csv` as the full feature-engineered dataset and create a separate `data/processed/training_dataset.csv` for rows that are ready for model training.

**Why:** Lag and rolling features naturally create missing values in the first rows because there is not enough historical context. Keeping the modeling dataset complete makes feature quality inspection transparent, while the training dataset can remove incomplete rows before modeling.

**Rejected:** Dropping incomplete feature rows directly from the modeling dataset.

**Next:** Use `training_dataset.csv` as the input for Phase 3 baseline modeling.

---

## Phase 3 — Modeling

### P3-D01 — Separate regression and classification modeling code

**Decision:** Organize modeling code under `src/electricity_predictor/modeling/` with separate `regression/` and `classification/` folders.

**Why:** The project has two related but different machine learning tasks. Regression predicts the exact electricity price, while classification will later support `recommended`, `acceptable`, and `avoid` usage categories.

**Rejected:** Keeping all modeling files in one flat folder or mixing regression and classification logic in the same module.

**Next:** Start Phase 3 with a naive regression baseline, then compare it against Linear Regression before adding more complex models.

### P3-D02 — Start modeling with a naive regression baseline

**Decision:** Start Phase 3 with a naive regression baseline that predicts `actual_price` using `actual_price_lag_1h`.

**Why:** A baseline gives the project a simple benchmark. Future models are only useful if they beat this simple prediction. Since electricity prices are time-series data, the previous hour price is a reasonable first comparison point.

**Rejected:** Starting directly with Linear Regression, Random Forest, Gradient Boosting, XGBoost, or Deep Learning before establishing a simple benchmark.

**Next:** Build the naive baseline, evaluate it with MAE and RMSE, then compare later models against it.

### P3-D03 — Use time-based splits for model evaluation

**Decision:** Split modeling data by chronological order instead of random order.

**Why:** Electricity prices are time-series data. A random split can train the model on future records and test it on older records. This creates unrealistic evaluation and possible data leakage.

**Rejected:** Using a random train/test split for model evaluation.

**Next:** Create a reusable split function for train, validation, and test datasets before training Linear Regression or other models.

### P3-D04 — Evaluate baseline models on the time-based test set

**Decision:** Evaluate regression baseline performance on the chronological test set instead of the full training dataset.

**Why:** The test set contains the newest data and better represents future-like model performance. Evaluating on the full dataset can make the score look more general than it really is.

**Rejected:** Reporting the baseline score using all available training rows.

**Next:** Use the same split strategy when evaluating Linear Regression and future regression models.

### P3-D05 — Track model evaluation results in a shared summary file

**Decision:** Save model evaluation results in a shared results summary file.

**Why:** The project will test multiple regression and classification models. A shared summary makes it easier to compare models and choose the best approach at the end.

**Rejected:** Keeping model scores only in terminal output.

**Next:** Create a reusable model results writer before adding Linear Regression.

### P3-D06 — Compare base and tuned regression models

**Decision:** Keep both base and tuned versions of serious regression models in the model results summary.

Current regression models include:

- `naive_baseline`
- `linear_regression`
- `ridge_regression`
- `ridge_regression_tuned`
- `lasso_regression`
- `lasso_regression_tuned`
- `elastic_net_regression`
- `elastic_net_regression_tuned`
- `random_forest_regressor`
- `random_forest_regressor_tuned`

**Why:** Base models show the default model behavior, while tuned models show whether hyperparameter search improves validation performance. Keeping both makes model comparison more transparent.

**Rejected:** Reporting only tuned models and losing the baseline comparison for each model family.

**Next:** Use the validation results to choose the strongest regression candidate before final test-set evaluation.

### P3-D07 — Use TimeSeriesSplit for regression hyperparameter tuning

**Decision:** Use `TimeSeriesSplit` for Ridge, Lasso, Elastic Net, and Random Forest tuning.

**Why:** Electricity prices are time-series data. Hyperparameter tuning must respect chronological order so future rows do not leak into older training folds.

**Rejected:** Using random cross-validation, shuffled folds, or standard `KFold` for time-series model tuning.

**Next:** Continue using chronological validation for all future model tuning, including future classification models.

### P3-D08 — Organize regression models by model family

**Decision:** Organize regression model files into one folder per model family.

Current regression structure includes:

- `baseline/`
- `linear/`
- `ridge/`
- `lasso/`
- `elastic_net/`
- `random_forest/`

**Why:** Each model family can now keep its base model, tuned model, and tests together. This makes the project easier to extend when more models are added.

**Rejected:** Keeping all regression files in one flat folder as the number of models grows.

**Next:** Follow the same structure for future models such as gradient boosting or classification models.

### P3-D09 — Keep test data protected until final model selection

**Decision:** Use the validation split for comparing learned regression models and keep the test split protected until the final model is selected.

**Why:** The test set should estimate future-like performance only once the modeling process has chosen a final candidate. Reusing the test set during model selection would make results less trustworthy.

**Rejected:** Repeatedly using the test split to choose between learned models.

**Next:** Select the best validation model, then evaluate the final chosen regression model on the protected test split.

### P3-D10 — Select the best regression model using validation MAE

**Decision:** Select the best regression model from `reports/model_results.csv` using the lowest validation MAE.

The selected model is written to:

```text
reports/best_regression_model.csv
```

The current selection rule is:

```text
selection_metric = mae
selection_rule = lowest_validation_mae
```

**Why:** MAE is easy to interpret because it shows the average prediction error in dollars per MWh. The validation split is used for model selection so the protected test split remains untouched until final evaluation.

**Rejected:** Selecting the best model using the test split, because that would leak final evaluation information into the model-selection process.

**Next:** Evaluate the selected regression model once on the protected test split, then save the final model artifact.
