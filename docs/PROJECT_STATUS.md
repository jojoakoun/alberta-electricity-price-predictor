# Project Status

## Alberta Electricity Price Predictor

This document summarizes the current state of the project.

## Current Phase

The project is currently in Phase 3 — Regression Modeling.

The repository foundation, Phase 1 data engineering, Phase 2 feature engineering, and ML preprocessing work are complete. The project can now build the current historical dataset, create model-ready features, prepare training data, and compare multiple regression models.

Phase 3 regression modeling is in progress. The project now supports baseline, linear, regularized linear, and Random Forest regression models with base and tuned versions where appropriate.

## Completed Work

| Area | Status | Summary |
|---|---:|---|
| Repository foundation | Complete | The project has a clean structure with source code, tests, configuration, documentation, and ignored local data files. |
| Python package setup | Complete | The project uses a `src/` package layout with editable install support. |
| Configuration | Complete | Project paths, API settings, and modeling split ratios are centralized in `configs/config.yaml`. |
| Secret management | Complete | API credentials are stored only in `.env`; `.env.example` documents the required variables without exposing secrets. |
| Historical CSV ingestion | Complete | The historical CSV is loaded, renamed into project-standard columns, sorted by UTC time, and validated. |
| AESO API ingestion | Complete | The AESO pool price API connection works using the `API-KEY` header. |
| API normalization | Complete | AESO API responses are normalized into the same project schema used by the historical data. |
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
| Feature quality reporting | Complete | The project can inspect missing values introduced by lag and rolling features. |
| Training dataset preparation | Complete | The project can create a model-ready training dataset by removing rows with missing engineered features. |
| Time-based splitting | Complete | The project creates chronological train, validation, and test splits for modeling. |
| Regression baseline | Complete | The project evaluates a naive baseline using the previous hour price. |
| Linear Regression | Complete | The project trains and evaluates a base Linear Regression model. |
| Ridge Regression | Complete | The project trains a base Ridge model and tunes `alpha` with `TimeSeriesSplit`. |
| Lasso Regression | Complete | The project trains a base Lasso model and tunes `alpha` with `TimeSeriesSplit`. |
| Elastic Net Regression | Complete | The project trains a base Elastic Net model and tunes `alpha` plus `l1_ratio` with `TimeSeriesSplit`. |
| Random Forest Regression | Complete | The project trains a base Random Forest model and tunes tree parameters with `TimeSeriesSplit`. |
| Regression results summary | Complete | The project writes model comparison results to `reports/model_results.csv`. |
| Best regression model selection | Complete | The project selects the best validation regression model using lowest MAE and writes it to `reports/best_regression_model.csv`. |
| Regression model organization | Complete | Regression models are organized by model family under `modeling/regression/`. |
| Full pipeline command | Complete | The project can run data refresh, quality checks, feature building, training data preparation, regression models, and tests with `make full-pipeline`. |
| Automated tests | Complete | The current test suite passes successfully. |

## Current Data Outputs

| Output file | Description | Git status |
|---|---|---|
| `data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv` | Raw historical electricity data source | Ignored |
| `data/interim/csv_historical_prices_clean.csv` | Cleaned historical dataset created from the local CSV | Ignored |
| `data/interim/current_historical_prices_clean.csv` | Current historical dataset extended with recent AESO API data | Ignored |
| `data/processed/modeling_dataset.csv` | Full feature-engineered dataset with time, lag, and rolling features. It keeps early rows with missing engineered features for transparency. | Ignored |
| `data/processed/training_dataset.csv` | Model-ready dataset with incomplete engineered feature rows removed. This is the input for regression modeling. | Ignored |
| `reports/model_results.csv` | Regression model comparison summary with metrics and model parameters. | Ignored |

## Current Core Modules

| File | Purpose |
|---|---|
| `src/electricity_predictor/config.py` | Loads project configuration. |
| `src/electricity_predictor/logger.py` | Provides a simple reusable logger. |
| `src/electricity_predictor/data/ingestion.py` | Loads, cleans, and validates historical CSV data. |
| `src/electricity_predictor/data/aeso_api.py` | Fetches, normalizes, and validates AESO pool price API data. |
| `src/electricity_predictor/data/pipeline.py` | Builds clean interim datasets from historical and API sources. |
| `src/electricity_predictor/data/data_quality.py` | Generates a readable quality summary for the current historical dataset. |
| `src/electricity_predictor/features/feature_engineering.py` | Builds the processed modeling dataset with time, lag, and rolling features. |
| `src/electricity_predictor/features/feature_columns.py` | Centralizes shared engineered feature column names. |
| `src/electricity_predictor/features/feature_quality.py` | Reports missing values created by lag and rolling feature windows. |
| `src/electricity_predictor/features/training_data.py` | Builds the model-ready training dataset from the modeling dataset. |
| `src/electricity_predictor/modeling/split.py` | Creates chronological train, validation, and test splits. |
| `src/electricity_predictor/modeling/metrics.py` | Provides reusable MAE and RMSE metric functions. |
| `src/electricity_predictor/modeling/model_results.py` | Builds and writes reusable model result summaries. |
| `src/electricity_predictor/modeling/regression/run_regression_models.py` | Runs the current regression model comparison workflow. |
| `src/electricity_predictor/modeling/regression/best_model_selection.py` | Selects the best validation regression model using the lowest MAE. |
| `src/electricity_predictor/modeling/regression/feature_columns.py` | Centralizes regression feature columns. |
| `src/electricity_predictor/modeling/regression/baseline/naive_baseline.py` | Evaluates the previous-hour naive regression baseline. |
| `src/electricity_predictor/modeling/regression/linear/linear_regression.py` | Trains and evaluates Linear Regression. |
| `src/electricity_predictor/modeling/regression/ridge/ridge_regression.py` | Trains and evaluates base Ridge Regression. |
| `src/electricity_predictor/modeling/regression/ridge/ridge_tuning.py` | Tunes Ridge `alpha` with `TimeSeriesSplit`. |
| `src/electricity_predictor/modeling/regression/lasso/lasso_regression.py` | Trains and evaluates base Lasso Regression. |
| `src/electricity_predictor/modeling/regression/lasso/lasso_tuning.py` | Tunes Lasso `alpha` with `TimeSeriesSplit`. |
| `src/electricity_predictor/modeling/regression/elastic_net/elastic_net_regression.py` | Trains and evaluates base Elastic Net Regression. |
| `src/electricity_predictor/modeling/regression/elastic_net/elastic_net_tuning.py` | Tunes Elastic Net `alpha` and `l1_ratio` with `TimeSeriesSplit`. |
| `src/electricity_predictor/modeling/regression/random_forest/random_forest.py` | Trains and evaluates base Random Forest Regression. |
| `src/electricity_predictor/modeling/regression/random_forest/random_forest_tuning.py` | Tunes Random Forest tree parameters with `TimeSeriesSplit`. |
| `notebooks/01_eda.ipynb` | Explores the current historical dataset before feature engineering and modeling. |

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
| `make regression-models` | Runs the current regression model comparison workflow. |
| `make select-best-regression-model` | Selects the best validation regression model from `reports/model_results.csv`. |
| `make full-pipeline` | Runs the full current workflow from data refresh to tests. |

## Current Validation Status

The current test suite passes successfully.

```text
73 passed
```

## Current Modeling Dataset

The modeling dataset is created by:

```bash
make features
```

The output file is:

```text
data/processed/modeling_dataset.csv
```

Current modeling columns:

| Column | Role |
|---|---|
| `datetime_universal_time` | Main UTC timestamp key. |
| `datetime_local_time` | Alberta local timestamp used for household decision timing. |
| `actual_price` | Target value for supervised price prediction. |
| `forecast_price` | AESO forecast price feature. |
| `hour` | Time feature created from local time. |
| `day_of_week` | Time feature created from local time. |
| `month` | Time feature created from local time. |
| `is_weekend` | Weekend indicator created from `day_of_week`. |
| `actual_price_lag_1h` | Actual price from the previous hour. |
| `actual_price_lag_24h` | Actual price from the same hour on the previous day. |
| `forecast_price_lag_1h` | Forecast price from the previous hour. |
| `actual_price_rolling_24h_mean` | Mean actual price from the previous 24 hours. |
| `actual_price_rolling_24h_max` | Maximum actual price from the previous 24 hours. |
| `actual_price_rolling_7d_mean` | Mean actual price from the previous 7 days. |

## Current Training Dataset

The training dataset is created by:

```bash
make training-data
```

The output file is:

```text
data/processed/training_dataset.csv
```

The training dataset is created from `modeling_dataset.csv` by removing rows with missing engineered feature values. This keeps the modeling dataset transparent while giving Phase 3 a clean input for model training and validation.

## Current Regression Models

| Model | Type | Tuning |
|---|---|---|
| `naive_baseline` | Baseline | None |
| `linear_regression` | Linear model | None |
| `ridge_regression` | Regularized linear model | Base `alpha=1.0` |
| `ridge_regression_tuned` | Regularized linear model | `TimeSeriesSplit` over `alpha` |
| `lasso_regression` | Regularized linear model | Base `alpha=1.0` |
| `lasso_regression_tuned` | Regularized linear model | `TimeSeriesSplit` over `alpha` |
| `elastic_net_regression` | Regularized linear model | Base `alpha=1.0`, `l1_ratio=0.5` |
| `elastic_net_regression_tuned` | Regularized linear model | `TimeSeriesSplit` over `alpha` and `l1_ratio` |
| `random_forest_regressor` | Tree ensemble | Base tree settings |
| `random_forest_regressor_tuned` | Tree ensemble | `TimeSeriesSplit` over tree settings |

## Current Best Regression Result

The current best validation model is selected automatically by `make select-best-regression-model`.

The selection criterion is:

```text
lowest validation MAE
```

The current best validation model is:

```text
random_forest_regressor_tuned
```

Current best parameters:

```text
n_estimators=200
max_depth=20
min_samples_leaf=5
random_state=42
```

This model currently has the strongest validation result among the tested regression models.

The selection output is written to:

```text
reports/best_regression_model.csv
```

## Current Data Quality Snapshot

The current historical dataset quality report tracks:

| Check | Current meaning |
|---|---|
| Rows | Number of source hourly records. |
| Columns | Number of source columns. |
| Min UTC time | Earliest UTC timestamp. |
| Max UTC time | Latest UTC timestamp. |
| Duplicate UTC timestamps | Should stay at 0. |
| Missing hourly UTC timestamps | Should stay at 0. |
| Missing `actual_price` values | Recent incomplete API rows may appear here. |
| Missing `alberta_internal_load` values | Expected for recent API-extended records. |
| Zero `actual_price` values | Kept because zero prices may represent real market behavior. |
| Zero `forecast_price` values | Kept for now and evaluated through modeling. |

## EDA Summary

The EDA notebook is located at:

```text
notebooks/01_eda.ipynb
```

The notebook answers 10 business questions covering:

- data coverage
- hourly time-series completeness
- actual price distribution
- zero, low, high, and extreme price ranges
- price spike timing
- hour-of-day patterns
- day-of-week patterns
- monthly and seasonal patterns
- AESO forecast usefulness
- recommendation-threshold considerations

## Important Data Notes

The dataset is hourly and continuous from the first UTC timestamp to the latest UTC timestamp.

Recent API rows may contain missing `actual_price` values when the actual price is not finalized yet. These rows are kept in the source dataset but excluded from the processed modeling dataset.

The `alberta_internal_load` column is available in the historical CSV but missing for recent AESO pool price API records because the current pool price API response does not provide that field.

Zero price values exist in both `actual_price` and `forecast_price`. These values are not removed automatically because they may represent real market behavior or API-specific reporting behavior. They require modeling and evaluation before final decisions are made.

Lag and rolling features are built from past values only. This prevents the model from using the current `actual_price` target as an input feature.

The training dataset removes rows with missing engineered feature values before modeling.

Regression hyperparameter tuning uses `TimeSeriesSplit` inside the train split only. The validation split is used to compare selected models. The test split stays protected until the final regression model is selected.

## Key Design Decisions

| Decision | Current choice |
|---|---|
| Project name | `Alberta Electricity Price Predictor` |
| Interim output format | CSV |
| Processed output format | CSV |
| Secret storage | `.env` only |
| AESO API authentication header | `API-KEY` |
| Main timestamp key | `datetime_universal_time` |
| Local timestamp column | `datetime_local_time` |
| Actual price column | `actual_price` |
| Forecast price column | `forecast_price` |
| Alberta load column | `alberta_internal_load` |
| Historical merge rule | API data extends historical data but does not overwrite existing historical rows |
| Current main dataset | `data/interim/current_historical_prices_clean.csv` |
| Current modeling dataset | `data/processed/modeling_dataset.csv` |
| Current training dataset | `data/processed/training_dataset.csv` |
| Source dataset rule | Keep recent incomplete API rows |
| Training dataset rule | Exclude rows without finalized `actual_price` and rows with missing engineered feature values before model training |
| First modeling dataset rule | Do not rely on `alberta_internal_load` unless a recent AIL source is added |
| Feature leakage rule | Lag and rolling features must use past values only |
| Modeling split rule | Use chronological train, validation, and test splits |
| Tuning rule | Use `TimeSeriesSplit` for regression hyperparameter tuning |
| Results tracking rule | Write model metrics and parameters to `reports/model_results.csv` |
| Best-model selection rule | Select the validation regression model with the lowest MAE |
| Test-set rule | Keep test data protected until final model selection |
| Recommendation threshold rule | Do not define final thresholds before feature engineering, modeling, and evaluation |

## Next Work

| Next step | Purpose |
|---|---|
| Evaluate the selected regression model on the protected test split | Estimate final future-like regression performance. |
| Add feature importance analysis for the best model | Understand which features drive predictions. |
| Save the selected regression model artifact | Prepare the model for serving or later application use. |
| Begin spike-risk classification design | Support future `recommended`, `acceptable`, and `avoid` labels. |
| Define recommendation thresholds later | Use regression and classification evidence before hardcoding decision rules. |
