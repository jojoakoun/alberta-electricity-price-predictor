# Alberta Electricity Price Predictor

A machine learning project that predicts Alberta electricity prices and turns those predictions into simple usage recommendations.

## Project Goal

This project helps Alberta households on variable-rate electricity plans decide when to use flexible electricity loads.

Examples include:

- laundry
- dishwashing
- electric vehicle charging
- other shiftable household usage

The final product will not only show predicted prices. It will also classify hours as `recommended`, `acceptable`, or `avoid`.

## Why This Matters

Alberta electricity prices can change sharply from hour to hour. A raw price forecast is useful, but most households need a simpler answer:

> When should I use electricity, and when should I avoid it?

This project turns hourly market data into practical decision support.

## Data Sources

The project uses two data sources:

- historical hourly Alberta electricity data from a local CSV file
- recent pool price data from the AESO API

The historical CSV supports data preparation, EDA, feature engineering, and model training. The AESO API supports extending the historical dataset with newer pool price records.

## Current Project Status

Current phase: **Phase 4 — Classification and Spike-Risk Modeling**.

The repository foundation, Phase 1 data engineering, Phase 2 feature engineering, ML preprocessing, Phase 3 regression modeling, and Phase 4 classification implementation are complete. The project is currently undergoing a Phase 4 coherence and pre-deployment audit.

The project can currently:

- load and validate historical Alberta electricity price data
- fetch and normalize recent AESO pool price API data
- combine historical and API records
- generate data quality reports
- create model-ready time, lag, and rolling features
- prepare a clean training dataset
- split the data chronologically into train, validation, and test sets
- train and compare multiple regression models
- tune selected regression models with `TimeSeriesSplit`
- select the best validation regression model separately for each forecast horizon
- calculate spike thresholds from the chronological train split only
- create horizon-specific binary spike targets without future-distribution leakage
- evaluate a naive spike classification baseline on validation data

A full status summary is available here:

[View project status](docs/PROJECT_STATUS.md)

Technical and product decisions are tracked here:

[View project decisions](DECISIONS.md)

## Current Machine Learning Status

The project compares regression and spike-risk classification models across five forecast horizons:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours

Regression winners are selected independently by lowest validation MAE.

| Horizon | Selected predictor | Validation MAE | Validation RMSE |
|---:|---|---:|---:|
| 1h | `lasso_regression_tuned` | 33.3837 | 80.2968 |
| 3h | `random_forest_regressor_tuned` | 46.7901 | 98.5419 |
| 6h | `lasso_regression_tuned` | 55.6364 | 110.0355 |
| 12h | `lasso_regression_tuned` | 59.8615 | 114.3262 |
| 24h | `naive_baseline` | 55.7267 | 136.6736 |

The selected model summary is written to:

    reports/best_regression_model.csv

The full model comparison summary is written to:

    reports/model_results.csv

## Final Regression Test Evaluation

The validation-selected regression predictors have been evaluated on the protected chronological test split.

| Horizon | Selected predictor | Test MAE | Test RMSE |
|---:|---|---:|---:|
| 1h | `lasso_regression_tuned` | 26.5647 | 80.3551 |
| 3h | `random_forest_regressor_tuned` | 42.4166 | 96.5281 |
| 6h | `lasso_regression_tuned` | 44.3965 | 100.3084 |
| 12h | `lasso_regression_tuned` | 48.1140 | 101.4838 |
| 24h | `naive_baseline` | 42.7081 | 127.9325 |

The final test summary is written to:

    reports/final_regression_test_results.csv

## Saved Regression Model Artifacts

Selected regression predictors can be saved locally with:

```bash
make save-selected-regression-models
```

The generated `.joblib` files are saved under:

```text
models/regression/
```

Learned predictors are saved as fitted model artifacts. Selected naive baselines are saved as rule artifacts. Generated artifacts are ignored by Git.

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

## Current Data Pipeline

The current data pipeline can:

- load the raw historical CSV
- rename raw columns into project-standard column names
- validate required columns
- validate missing values where required
- detect duplicate UTC timestamps
- sort time-series data by UTC time
- fetch AESO pool price data from the API
- normalize AESO API responses into the project schema
- extend the historical dataset with new API records
- avoid replacing existing historical rows during API integration
- generate a readable data quality report
- build a processed modeling dataset
- build a clean training dataset for machine learning

## Feature Engineering

The project creates model-ready features from historical electricity price data.

Current feature groups include:

- time features
- AESO forecast price features
- lag price features
- rolling price features

Current modeling features include:

| Feature | Purpose |
|---|---|
| `forecast_price` | AESO forecast price input. |
| `hour` | Local hour of day. |
| `day_of_week` | Local day of week. |
| `month` | Local month. |
| `is_weekend` | Weekend indicator. |
| `actual_price_lag_1h` | Previous hour actual price. |
| `actual_price_lag_24h` | Same hour previous day actual price. |
| `forecast_price_lag_1h` | Previous hour forecast price. |
| `actual_price_rolling_24h_mean` | Previous 24-hour mean actual price. |
| `actual_price_rolling_24h_max` | Previous 24-hour max actual price. |
| `actual_price_rolling_7d_mean` | Previous 7-day mean actual price. |

Lag and rolling features use past values only. This prevents target leakage.

## Exploratory Data Analysis

The project includes an EDA notebook:

```text
notebooks/01_eda.ipynb
```

The notebook answers 10 business questions about:

- data coverage
- hourly time-series completeness
- price distribution
- zero, low, high, and extreme prices
- spike behavior
- hour-of-day patterns
- day-of-week patterns
- monthly and seasonal patterns
- AESO forecast usefulness
- future recommendation-threshold considerations

The EDA supports the business case by studying when households may safely shift flexible electricity usage and when they should avoid high-risk hours.

## Current Data Outputs

Some generated data files are local outputs and are not tracked by Git.

| Output file | Description |
|---|---|
| `data/interim/csv_historical_prices_clean.csv` | Cleaned historical dataset created from the local CSV. |
| `data/interim/current_historical_prices_clean.csv` | Current historical dataset extended with recent AESO API data. |
| `data/processed/modeling_dataset.csv` | Full feature-engineered dataset with time, lag, and rolling features. |
| `data/processed/training_dataset.csv` | Model-ready dataset with incomplete engineered feature rows removed. |
| `reports/model_results.csv` | Regression model comparison summary with metrics and model parameters. |
| `reports/best_regression_model.csv` | Best validation regression model selected separately for each forecast horizon. |

## Planned Machine Learning Tasks

This project solves two related problems:

1. Regression: predict future electricity prices for configured forecast horizons.
2. Classification: estimate future spike risk. Phase 4 implementation is complete, but deployment remains blocked by the pre-deployment audit findings.

The decision layer will combine both outputs into a recommendation.

## Recommendation Labels

The product will use three simple labels:

- `recommended`
- `acceptable`
- `avoid`

The rule is price-first:

- high predicted price -> avoid
- low predicted price and low spike risk -> recommended
- all other cases -> acceptable

Final recommendation thresholds have not been defined yet. They will be decided after regression evaluation, spike-risk classification, and product-level decision testing.

## Tech Stack

Current and planned stack:

- Python
- pandas
- pytest
- requests
- python-dotenv
- PyYAML
- scikit-learn
- MLflow
- FastAPI
- React
- Vite
- Tailwind CSS

## Repository Structure

```text
alberta-electricity-price-predictor/
├── configs/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docs/
├── notebooks/
├── reports/
├── src/
│   └── electricity_predictor/
│       ├── data/
│       ├── features/
│       ├── modeling/
│       │   ├── classification/
│       │   └── regression/
│       ├── visualization/
│       ├── serving/
│       └── api/
├── tests/
├── logs/
├── README.md
├── LICENSE
├── Makefile
├── pyproject.toml
└── requirements.txt
```

## Current Core Modules

| File | Purpose |
|---|---|
| `src/electricity_predictor/config.py` | Loads project configuration from `configs/config.yaml`. |
| `src/electricity_predictor/logger.py` | Provides a simple reusable logger. |
| `src/electricity_predictor/data/ingestion.py` | Loads, cleans, and validates historical CSV data. |
| `src/electricity_predictor/data/aeso_api.py` | Fetches, normalizes, and validates AESO pool price API data. |
| `src/electricity_predictor/data/pipeline.py` | Builds clean interim datasets from historical and API sources. |
| `src/electricity_predictor/data/data_quality.py` | Generates a readable quality summary for the current historical dataset. |
| `src/electricity_predictor/features/feature_engineering.py` | Builds the processed modeling dataset with time, lag, and rolling features. |
| `src/electricity_predictor/features/feature_quality.py` | Reports missing values created by lag and rolling feature windows. |
| `src/electricity_predictor/features/training_data.py` | Builds the model-ready training dataset. |
| `src/electricity_predictor/modeling/split.py` | Creates chronological train, validation, and test splits. |
| `src/electricity_predictor/modeling/metrics.py` | Provides reusable regression and binary-classification metrics. |
| `src/electricity_predictor/modeling/classification/spike_definition.py` | Calculates and applies train-derived spike thresholds. |
| `src/electricity_predictor/modeling/classification/analyze_spike_definition.py` | Compares candidate spike definitions across chronological splits. |
| `src/electricity_predictor/modeling/classification/target_builder.py` | Creates binary spike targets for configured horizons. |
| `src/electricity_predictor/modeling/classification/baseline/naive_spike_baseline.py` | Evaluates the naive spike classification baseline. |
| `src/electricity_predictor/modeling/model_results.py` | Builds and writes reusable model result summaries. |
| `src/electricity_predictor/modeling/regression/run_regression_models.py` | Runs the current regression model comparison workflow. |
| `src/electricity_predictor/modeling/regression/best_model_selection.py` | Selects the best validation regression model using the lowest MAE. |
| `notebooks/01_eda.ipynb` | Explores the current historical dataset before feature engineering and modeling. |

## Testing

Run the full test suite with:

```bash
make test
```

Current test status:

```text
200 passed
```

## Main Commands

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
| `make regression-models` | Runs the multi-horizon regression model comparison workflow. |
| `make select-best-regression-model` | Selects the best validation predictor for each horizon. |
| `make final-regression-evaluation` | Evaluates the selected predictors on the protected chronological test split. |
| `make save-selected-regression-models` | Saves the selected fitted model or baseline rule artifact for each horizon. |
| `make full-pipeline` | Runs the full workflow from data refresh through protected evaluation, artifact saving, and tests. |

## Environment Variables

The project uses `.env` for local secrets and `.env.example` as the public template.

Required AESO variables:

```env
AESO_API_BASE_URL=https://apimgw.aeso.ca/public/poolprice-api/v1.1
AESO_API_SUBSCRIPTION_KEY=
```

The real subscription key must only be stored in `.env`.

## Documentation Principles

This repository follows clear technical writing principles:

- short sentences
- active voice
- clear headings
- concise explanations
- documentation that helps readers find answers quickly

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

<!-- PHASE_4_FINAL_STATUS_START -->
## Phase 4 completion

Phase 4 implements multi-horizon electricity-price regression and spike-risk classification.

Supported horizons:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours

### Evaluation protocol

The project uses fixed UTC periods:

| Split | Period | Rows |
|---|---|---:|
| Train | `2020-01-08 07:00:00` to `2023-12-30 23:00:00` | 34,865 |
| Validation | `2024-01-01 00:00:00` to `2024-12-30 23:00:00` | 8,760 |
| Test | `2025-01-01 00:00:00` to `2026-06-30 23:00:00` | 13,104 |

The final 24 hours of train and validation are removed. This prevents the longest target horizon from crossing into the next split.

All seven tuning workflows use `TimeSeriesSplit(gap=24)`.

### Spike definition

The classification workflow uses one IQR threshold calculated from the chronological train split only:

    170.77 $/MWh

The threshold remains frozen across train, validation, test, metadata, artifacts, and inference.

| Split | Spike rate |
|---|---:|
| Train | 13.98% |
| Validation | 6.83% |
| Test | 2.92% |

The yearly analysis documents a material market-regime shift. The project retains one absolute threshold so the business meaning of a spike remains stable over time.

### Selected regression models

| Horizon | Validation winner | Validation MAE | Test MAE |
|---:|---|---:|---:|
| 1h | `lasso_regression_tuned` | 33.3837 | 26.5647 |
| 3h | `random_forest_regressor_tuned` | 46.7901 | 42.4166 |
| 6h | `lasso_regression_tuned` | 55.6364 | 44.3965 |
| 12h | `lasso_regression_tuned` | 59.8615 | 48.1140 |
| 24h | `naive_baseline` | 55.7267 | 42.7081 |

Learned regression gains over credible baselines are modest at several horizons. The naive baseline remains the selected 24-hour predictor.

### Selected classification models

`random_forest_classifier_tuned` is the validation winner for all five horizons.

| Horizon | Validation F1 | Test F1 | Test PR-AUC | Decision cutoff |
|---:|---:|---:|---:|---:|
| 1h | 0.6009 | 0.2679 | 0.3055 | 0.45 |
| 3h | 0.5025 | 0.2310 | 0.1739 | 0.45 |
| 6h | 0.3971 | 0.1586 | 0.1016 | 0.45 |
| 12h | 0.3652 | 0.1202 | 0.0716 | 0.45 |
| 24h | 0.3524 | 0.1284 | 0.0955 | 0.50 |

The 24-hour validation winner exceeds the classification baseline by only about `0.019` F1. This margin is not strong enough to claim decisive superiority.

Protected test performance is substantially lower than validation performance. Product claims must reflect this limitation.

### Classification uncertainty

The project estimates 95% F1 confidence intervals with a 24-hour block bootstrap and 1,000 iterations.

| Horizon | Test F1 | 95% confidence interval |
|---:|---:|---:|
| 1h | 0.2679 | 0.2058 to 0.3275 |
| 3h | 0.2310 | 0.1588 to 0.2998 |
| 6h | 0.1586 | 0.0935 to 0.2283 |
| 12h | 0.1202 | 0.0678 to 0.1757 |
| 24h | 0.1284 | 0.0771 to 0.1827 |

Confusion matrices are persisted separately so final metrics can be traced to exact classification counts.

### Methodological limitations

Probability cutoffs are selected from validation predictions produced by models fitted on train data. Final models are then refitted on train plus validation. Phase 4 assumes the selected cutoff remains suitable after refitting.

Classification labels inside tuning folds use the spike threshold calculated from the complete train period. The threshold does not use validation or test prices, but it is not recalculated independently inside each fold.

### Verification

The current automated verification result is:

    200 passed

Source compilation also passes.

### Known technical debt

The following items are intentionally deferred:

- tuning modules load configuration at import time;
- serving paths remain relative to the repository root;
- inference needs stronger dtype and `classes_` edge-case handling;
- the audit export tolerates missing optional files;
- some learned-model gains over baselines are modest;
- horizon workflows remain repeated rather than centrally orchestrated;
- feature-column definitions remain coupled across modeling modules;
- the regression baseline uses `actual_price_lag_1h`, including at 24 hours;
- some selected regularization values lie at the edge of the search grid;
- some standalone workflow code remains duplicated;
- historical data provenance still needs its URL, download date, version, publication record, and checksum.

Data provenance blocks public publication, but it does not block Phase 5 application development.

### Phase status

Phase 4 will close after:

1. the baseline-inference edge case is corrected;
2. final verification remains green;
3. the audit export is regenerated;
4. the branch is pushed and merged.
