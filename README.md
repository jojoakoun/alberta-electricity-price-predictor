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

The project now compares regression models across five forecast horizons:

- 1 hour
- 3 hours
- 6 hours
- 12 hours
- 24 hours

The current best validation predictors are selected separately for each horizon using the lowest validation MAE. A naive baseline remains eligible when it outperforms learned models.

| Horizon | Selected predictor | Validation MAE | Validation RMSE |
|---:|---|---:|---:|
| 1h | `random_forest_regressor_tuned` | 25.4158 | 70.0433 |
| 3h | `naive_baseline` | 37.3273 | 114.5003 |
| 6h | `naive_baseline` | 42.9455 | 125.1047 |
| 12h | `naive_baseline` | 45.5370 | 128.0298 |
| 24h | `naive_baseline` | 43.1670 | 122.0370 |

The selected model summary is written to:

```text
reports/best_regression_model.csv
```

The full model comparison summary is written to:

```text
reports/model_results.csv
```

## Final Regression Test Evaluation

The validation-selected regression predictors have been evaluated on the protected chronological test split.

| Horizon | Selected predictor | Test MAE | Test RMSE |
|---:|---|---:|---:|
| 1h | `random_forest_regressor_tuned` | 26.4863 | 78.8549 |
| 3h | `naive_baseline` | 38.9598 | 127.9055 |
| 6h | `naive_baseline` | 44.7939 | 139.9731 |
| 12h | `naive_baseline` | 47.7167 | 144.7407 |
| 24h | `naive_baseline` | 44.0096 | 133.3663 |

The final test summary is written to:

```text
reports/final_regression_test_results.csv
```

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
132 passed
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

### Current classification limitations

The reported classification accuracy (~0.94) should not be interpreted in isolation.

The chronological data shows a significant distribution shift in spike frequency:

| Split | Spike rate |
|------|-----------:|
| Train | 13.64% |
| Validation | 3.38% |
| Test | 3.20% |

Because spike events become much rarer after the training period, overall accuracy remains high even when spike detection is difficult. Precision, recall, and F1 therefore provide a more meaningful evaluation than accuracy alone.

Current limitations identified during the pre-deployment audit include:

- significant non-stationarity between training and evaluation periods;
- chronological split boundaries still defined by dataset ratios instead of fixed dates;
- no purge/gap between train, validation, and test horizons;
- fixed probability cutoff of 0.5;
- PR-AUC and bootstrap confidence intervals not yet reported;
- confusion matrices not yet persisted as project artifacts;
- no inference or monitoring pipeline yet exists for saved classification artifacts.

These limitations are tracked as part of the Phase 4 pre-deployment audit and will be addressed before deployment.

### Spike definition rationale

Several candidate spike definitions were evaluated before selecting the project threshold.

The current project uses the IQR-based threshold learned from the chronological training split only.

| Definition | Approximate test spike rate |
|-----------|----------------------------:|
| IQR | 3.20% |
| q95 | 1.58% |
| q99 | 0.58% |

The IQR definition was selected because it produces enough positive events to train and evaluate classification models while still identifying unusually high electricity prices.

Higher thresholds such as q95 and q99 create much rarer events, making model evaluation less stable and increasing uncertainty in performance metrics.

The threshold is learned once from the chronological training split and then frozen for validation, test, and future inference to avoid data leakage.

### Classification artifacts

Each selected classification model is saved together with reproducibility metadata.

The metadata records:

- forecast horizon;
- selected model and hyperparameters;
- ordered feature columns;
- frozen spike threshold;
- target column;
- training window;
- scikit-learn version;
- selection rule;
- artifact path.

Classification artifacts are generated with:

```bash
make save-selected-classification-models
```

The generated files are stored under:

```text
models/classification/
```

At the current project stage, no inference pipeline, monitoring, logging, or drift-detection component consumes these artifacts. Deployment remains blocked until the pre-deployment audit findings are resolved.

### Historical CSV provenance

The historical dataset is loaded locally from:

```text
data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv
```

The repository export confirms the filename and its role in the data pipeline, but it does not contain the original download URL, download date, dataset version, or source publication record.

Cannot verify from project_context_full_audit.txt.

This provenance information must be recorded before deployment.
