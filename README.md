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

Current phase: **Phase 3 — Regression Modeling**.

The repository foundation, Phase 1 data engineering, Phase 2 feature engineering, ML preprocessing, and Phase 3 regression model comparison work are complete.

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

The current best validation regression models are selected separately for each horizon using lowest validation MAE.

| Horizon | Selected model | Validation MAE | Validation RMSE |
|---:|---|---:|---:|
| 1h | `random_forest_regressor_tuned` | 25.3681 | 69.9702 |
| 3h | `lasso_regression_tuned` | 37.8507 | 90.7098 |
| 6h | `lasso_regression_tuned` | 44.2625 | 94.5843 |
| 12h | `lasso_regression_tuned` | 48.3116 | 96.7578 |
| 24h | `lasso_regression_tuned` | 47.7392 | 97.0931 |

The selected model summary is written to:

```text
reports/best_regression_model.csv
```

The full model comparison summary is written to:

```text
reports/model_results.csv
```

## Final Regression Test Evaluation

The validation-selected regression models have been evaluated on the protected chronological test split.

| Horizon | Selected model | Test MAE | Test RMSE |
|---:|---|---:|---:|
| 1h | `random_forest_regressor_tuned` | 26.5252 | 78.8670 |
| 3h | `lasso_regression_tuned` | 38.6983 | 100.7950 |
| 6h | `lasso_regression_tuned` | 44.9226 | 104.8689 |
| 12h | `lasso_regression_tuned` | 48.1701 | 105.4968 |
| 24h | `lasso_regression_tuned` | 46.6238 | 103.7971 |

The final test summary is written to:

```text
reports/final_regression_test_results.csv
```

## Saved Regression Model Artifacts

Selected regression models can be saved locally with:

```bash
make save-selected-regression-models
```

The generated `.joblib` files are saved under:

```text
models/regression/
```

Model artifacts are ignored by Git because they are generated outputs.

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
2. Classification: estimate future spike risk. This is planned for Phase 4.

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
| `src/electricity_predictor/modeling/metrics.py` | Provides reusable MAE and RMSE metric functions. |
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
81 passed
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
| `make regression-models` | Runs the current regression model comparison workflow. |
| `make select-best-regression-model` | Selects the best validation regression model from `reports/model_results.csv`. |
| `make full-pipeline` | Runs the full current workflow from data refresh to tests. |

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
