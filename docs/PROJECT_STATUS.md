# Project Status

## Alberta Electricity Price Predictor

This document summarizes the current state of the project.

## Current Phase

Phase 4 — Classification and Spike-Risk Modeling

## Current Status

The project now supports complete multi-horizon regression and Phase 4 classification implementation. The repository is currently undergoing a Phase 4 coherence and pre-deployment audit.

The repository foundation, Phase 1 data engineering, Phase 2 feature engineering, ML preprocessing, and the current Phase 3 regression comparison workflow are complete.

The regression workflow can train, tune, evaluate, and compare models for these forecast horizons:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours

The modeling workflow now produces:

- `reports/model_results.csv`
  - one row per model per horizon
  - current output: 50 rows
- `reports/best_regression_model.csv`
  - one selected validation winner per horizon
  - current output: 5 rows

## Completed Work

| Area | Status | Summary |
|---|---:|---|
| Repository foundation | Complete | The project has a clean structure with source code, tests, configuration, documentation, and ignored local data files. |
| Python package setup | Complete | The project uses a `src/` package layout with editable install support. |
| Configuration | Complete | Project paths, API settings, modeling horizons, and split ratios are centralized in `configs/config.yaml`. |
| Secret management | Complete | API credentials are stored only in `.env`; `.env.example` documents required variables without exposing secrets. |
| Historical CSV ingestion | Complete | The historical CSV is loaded, renamed into project-standard columns, sorted by UTC time, and validated. |
| AESO API ingestion | Complete | The AESO pool price API connection works using the `API-KEY` header. |
| API normalization | Complete | AESO API responses are normalized into the same project schema used by historical data. |
| Historical data validation | Complete | Historical data is checked for required columns, required non-null values, duplicate UTC timestamps, and chronological ordering. |
| API data validation | Complete | API data is checked for required columns, required non-null values, duplicate UTC timestamps, and chronological ordering. |
| Data integration | Complete | API data extends the historical dataset without replacing existing historical rows. |
| Current dataset pipeline | Complete | The project can build a current historical dataset using local CSV data plus recent AESO API records. |
| Data quality reporting | Complete | The project can generate a readable quality summary for the current historical dataset. |
| Exploratory data analysis | Complete | The project includes an EDA notebook that answers 10 business questions before feature engineering and modeling. |
| Basic modeling dataset | Complete | The project can create a processed modeling dataset from the current historical dataset. |
| Time features | Complete | The modeling dataset includes `hour`, `day_of_week`, `month`, and `is_weekend`. |
| Lag features | Complete | The modeling dataset includes past price features that avoid target leakage. |
| Rolling price features | Complete | The modeling dataset includes rolling summaries based only on past actual prices. |
| Multi-horizon target columns | Complete | The modeling dataset includes future target columns for 1h, 3h, 6h, 12h, and 24h horizons. |
| Feature quality reporting | Complete | The project can inspect missing values introduced by lag, rolling, and horizon target creation. |
| Training dataset preparation | Complete | The project creates a model-ready training dataset by removing rows with missing engineered features or horizon targets. |
| Time-based splitting | Complete | The project creates chronological train, validation, and test splits for modeling. |
| Shared training dataset loader | Complete | All modeling workflows reuse the shared `load_training_dataset()` helper from `modeling/split.py`. |
| Shared training dataset path | Complete | All modeling workflows reuse the shared `TRAINING_DATASET_PATH` constant from `modeling/split.py`. |
| Regression baseline | Complete | The project evaluates a naive baseline using the previous hour price against each horizon target. |
| Linear Regression | Complete | The project trains and evaluates Linear Regression for each horizon target. |
| Ridge Regression | Complete | The project trains a base Ridge model and tunes `alpha` with `TimeSeriesSplit`. |
| Lasso Regression | Complete | The project trains a base Lasso model and tunes `alpha` with `TimeSeriesSplit`. |
| Elastic Net Regression | Complete | The project trains a base Elastic Net model and tunes `alpha` plus `l1_ratio` with `TimeSeriesSplit`. |
| Random Forest Regression | Complete | The project trains a base Random Forest model and tunes tree parameters with `TimeSeriesSplit`. |
| Multi-horizon regression results | Complete | The project writes one model result row per model per horizon to `reports/model_results.csv`. |
| Best predictor selection by horizon | Complete | The project selects one best validation predictor per horizon using lowest validation MAE. |
| Regression model organization | Complete | Regression models are organized by model family under `modeling/regression/`. |
| Full pipeline command | Complete | The project can run data refresh, quality checks, feature building, training data preparation, regression models, model selection, and tests with `make full-pipeline`. |
| Classification spike definition | Complete | Candidate spike definitions are compared using thresholds learned from the chronological train split only. |
| Classification target preparation | Complete | Binary spike targets are created after splitting so validation and test prices cannot influence the threshold. |
| Classification baseline | Complete | The project evaluates a naive spike baseline using the previous-hour price against each forecast horizon. |
| Automated tests | Complete | The current test suite passes successfully. |

## Current Validation Status

Latest test result:

```text
132 passed
```

## Current Forecast Horizons

Configured horizons are stored in `configs/config.yaml`:

```text
horizons_hours: [1, 3, 6, 12, 24]
```

## Current Regression Results

| Output file | Description |
|---|---|
| `reports/model_results.csv` | Multi-horizon regression model comparison table. Current output: 50 rows. |
| `reports/best_regression_model.csv` | One selected validation winner per forecast horizon. Current output: 5 rows. |

## Current Best Regression Predictors

| Horizon | Selected predictor | Validation MAE | Validation RMSE |
|---:|---|---:|---:|
| 1h | `random_forest_regressor_tuned` | 25.4158 | 70.0433 |
| 3h | `naive_baseline` | 37.3273 | 114.5003 |
| 6h | `naive_baseline` | 42.9455 | 125.1047 |
| 12h | `naive_baseline` | 45.5370 | 128.0298 |
| 24h | `naive_baseline` | 43.1670 | 122.0370 |

## Current Data Outputs

Some generated data files are local outputs and are not tracked by Git.

| Output file | Description | Git status |
|---|---|---|
| `data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv` | Raw historical electricity data source. | Ignored |
| `data/interim/csv_historical_prices_clean.csv` | Cleaned historical dataset created from the local CSV. | Ignored |
| `data/interim/current_historical_prices_clean.csv` | Current historical dataset extended with recent AESO API data. | Ignored |
| `data/processed/modeling_dataset.csv` | Full feature-engineered dataset with time, lag, rolling, and future horizon target columns. | Ignored |
| `data/processed/training_dataset.csv` | Model-ready dataset with incomplete engineered feature rows and incomplete horizon target rows removed. | Ignored |
| `reports/model_results.csv` | Multi-horizon regression model comparison summary. | Tracked |
| `reports/best_regression_model.csv` | Best validation regression model selected separately for each forecast horizon. | Tracked |

## Current Core Modules

| File | Purpose |
|---|---|
| `src/electricity_predictor/config.py` | Loads project configuration. |
| `src/electricity_predictor/data/ingestion.py` | Loads, cleans, and validates historical CSV data. |
| `src/electricity_predictor/data/aeso_api.py` | Fetches, normalizes, and validates AESO pool price API data. |
| `src/electricity_predictor/data/pipeline.py` | Builds clean interim datasets from historical and API sources. |
| `src/electricity_predictor/data/data_quality.py` | Generates a readable quality summary for the current historical dataset. |
| `src/electricity_predictor/features/feature_engineering.py` | Builds the processed modeling dataset with time, lag, rolling, and future target features. |
| `src/electricity_predictor/features/feature_columns.py` | Centralizes engineered feature and horizon target column names. |
| `src/electricity_predictor/features/feature_quality.py` | Reports missing values created by feature engineering. |
| `src/electricity_predictor/features/training_data.py` | Builds the model-ready training dataset from the modeling dataset. |
| `src/electricity_predictor/modeling/split.py` | Defines the shared training dataset path, loads and chronologically sorts the training dataset, and creates chronological train, validation, and test splits. |
| `src/electricity_predictor/modeling/metrics.py` | Provides reusable regression and binary-classification metric functions. |
| `src/electricity_predictor/modeling/classification/spike_definition.py` | Calculates and applies train-derived spike thresholds. |
| `src/electricity_predictor/modeling/classification/analyze_spike_definition.py` | Compares candidate spike definitions across chronological splits. |
| `src/electricity_predictor/modeling/classification/target_builder.py` | Creates horizon-specific binary spike targets using one frozen train threshold. |
| `src/electricity_predictor/modeling/classification/baseline/naive_spike_baseline.py` | Evaluates the naive spike baseline on validation data. |
| `src/electricity_predictor/modeling/model_results.py` | Builds and writes reusable model result summaries with horizon context. |
| `src/electricity_predictor/modeling/regression/run_regression_models.py` | Runs the multi-horizon regression model comparison workflow. |
| `src/electricity_predictor/modeling/regression/best_model_selection.py` | Selects the best validation regression model separately for each horizon. |
| `src/electricity_predictor/modeling/regression/feature_columns.py` | Centralizes regression feature columns. |

## Current Makefile Commands

| Command | Purpose |
|---|---|
| `make install` | Installs dependencies and registers the local package. |
| `make test` | Runs the project test suite. |
| `make config-check` | Checks that the project configuration can be loaded. |
| `make pipeline` | Builds the current historical dataset from CSV and AESO API data. |
| `make data-quality` | Runs the data quality report for the current historical dataset. |
| `make features` | Builds the processed modeling dataset for machine learning. |
| `make feature-quality` | Inspects missing values created by feature engineering. |
| `make training-data` | Builds the model-ready training dataset. |
| `make baseline` | Runs the naive regression baseline. |
| `make linear-regression` | Runs the base Linear Regression model. |
| `make ridge-regression` | Runs the base Ridge Regression model. |
| `make lasso-regression` | Runs the base Lasso Regression model. |
| `make lasso-tuning` | Tunes Lasso Regression with `TimeSeriesSplit`. |
| `make elastic-net-regression` | Runs the base Elastic Net Regression model. |
| `make elastic-net-tuning` | Tunes Elastic Net Regression with `TimeSeriesSplit`. |
| `make regression-models` | Runs the full multi-horizon regression model comparison workflow. |
| `make select-best-regression-model` | Selects the best validation regression model for each horizon. |
| `make full-pipeline` | Runs the full current workflow from data refresh to tests. |

## Important Modeling Notes

The current best-model selection is based on validation MAE.

The protected test split is used only after validation-based model selection for final future-like evaluation.

The full multi-horizon regression workflow is slower than earlier single-target runs because it evaluates 10 model results across 5 horizons. Random Forest tuning is the most expensive part, so Random Forest now uses `n_jobs=-1` to use available CPU cores.

## Final Protected Test Results

| Horizon | Selected predictor | Test MAE | Test RMSE |
|---:|---|---:|---:|
| 1h | `random_forest_regressor_tuned` | 26.4863 | 78.8549 |
| 3h | `naive_baseline` | 38.9598 | 127.9055 |
| 6h | `naive_baseline` | 44.7939 | 139.9731 |
| 12h | `naive_baseline` | 47.7167 | 144.7407 |
| 24h | `naive_baseline` | 44.0096 | 133.3663 |

## Saved Regression Model Artifacts

Selected regression predictors can be generated with:

```bash
make save-selected-regression-models
```

The generated artifacts are local outputs under:

```text
models/regression/
```

These artifacts are ignored by Git because they can be regenerated from the tracked code, data pipeline outputs, and selected model metadata.

## Next Steps

1. Train Logistic Regression classifiers for each forecast horizon.
2. Compare learned classifiers with the naive spike baseline on validation data.
3. Select one classification predictor per horizon before protected test evaluation.
4. Use regression and classification outputs together later in the recommendation layer.

<!-- PHASE_4_FINAL_STATUS_START -->
## Phase 4 completion

Phase 4 is implemented end to end for the following forecast horizons:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours

The project now includes:

- chronological train, validation, and protected test splits;
- multi-horizon regression;
- train-only spike-threshold estimation;
- horizon-specific spike classification targets;
- naive baselines;
- Logistic Regression;
- Random Forest;
- Gradient Boosting;
- chronological hyperparameter tuning with `TimeSeriesSplit`;
- one selected regression model per horizon;
- one selected classification model per horizon;
- final protected test evaluation;
- saved model artifacts and metadata;
- **165 passing automated tests**.

### Final regression results

Regression models are selected using the lowest validation MAE within each
forecast horizon.

| Horizon | Selected model | Validation MAE | Test MAE | Test RMSE |
|---:|---|---:|---:|---:|
| 1h | `random_forest_regressor_tuned` | 25.3714 | 26.4665 | 78.8523 |
| 3h | `naive_baseline` | 37.2918 | 38.9494 | 127.8833 |
| 6h | `naive_baseline` | 42.9041 | 44.7949 | 139.9497 |
| 12h | `naive_baseline` | 45.5107 | 47.7019 | 144.7153 |
| 24h | `naive_baseline` | 43.1519 | 43.9927 | 133.3420 |

### Final classification results

Classification models are selected using the highest validation F1 within each
forecast horizon.

| Horizon | Selected model | Validation F1 | Test precision | Test recall | Test F1 | Test accuracy |
|---:|---|---:|---:|---:|---:|---:|
| 1h | `logistic_regression` | 0.4659 | 0.4012 | 0.4891 | 0.4408 | 0.9603 |
| 3h | `gradient_boosting_classifier` | 0.3025 | 0.2450 | 0.3139 | 0.2752 | 0.9471 |
| 6h | `gradient_boosting_classifier_tuned` | 0.2610 | 0.1862 | 0.2372 | 0.2087 | 0.9424 |
| 12h | `gradient_boosting_classifier` | 0.1755 | 0.1707 | 0.2810 | 0.2124 | 0.9333 |
| 24h | `gradient_boosting_classifier` | 0.1714 | 0.1873 | 0.2810 | 0.2248 | 0.9380 |

### Current stage

Phase 4 implementation is complete.

The project is now entering a dedicated **Phase 4 coherence and
pre-deployment audit**. Phase 5 application development must not begin until
the audit findings have been reviewed and all accepted blocker and
high-severity findings have been corrected.

### Classification artifacts

Selected classification models and their reproducibility metadata are saved under:

```text
models/classification/
```

The metadata includes the forecast horizon, selected model, hyperparameters, ordered feature columns, frozen spike threshold, target column, training window, scikit-learn version, selection rule, and artifact path.

The artifacts can be generated with:

```bash
make save-selected-classification-models
```

No inference, monitoring, logging, or drift-detection workflow currently consumes these artifacts. This remains a deployment blocker tracked by the Phase 4 pre-deployment audit.


### Historical CSV provenance

The historical source is currently stored locally at:

```text
data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv
```

The current audit export does not include the original download URL, download date, dataset version, or publication record.

Cannot verify from project_context_full_audit.txt.

Complete provenance must be documented before deployment.
