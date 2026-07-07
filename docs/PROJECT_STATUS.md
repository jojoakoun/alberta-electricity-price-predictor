# Project Status

## Alberta Electricity Price Predictor

This document summarizes the current state of the project.

## Current Phase

The project is currently in the data engineering phase.

The repository foundation is complete. The project can load, clean, validate, combine, inspect, and explore historical Alberta electricity price data with recent AESO pool price API data.

## Completed Work

| Area | Status | Summary |
|---|---:|---|
| Repository foundation | Complete | The project has a clean structure with source code, tests, configuration, documentation, and ignored local data files. |
| Python package setup | Complete | The project uses a `src/` package layout with editable install support. |
| Configuration | Complete | Project paths and API settings are centralized in `configs/config.yaml`. |
| Secret management | Complete | API credentials are stored only in `.env`; `.env.example` documents the required variables without exposing secrets. |
| Historical CSV ingestion | Complete | The historical CSV is loaded, renamed into project-standard columns, sorted by UTC time, and validated. |
| AESO API ingestion | Complete | The AESO pool price API connection works using the `API-KEY` header. |
| API normalization | Complete | AESO API responses are normalized into the same project schema used by the historical data. |
| Historical data validation | Complete | Historical data is checked for required columns, required non-null values, duplicate UTC timestamps, and chronological ordering. |
| API data validation | Complete | API data is checked for required columns, required non-null values, duplicate UTC timestamps, and chronological ordering. |
| Data integration | Complete | API data extends the historical dataset without replacing existing historical rows. |
| Current dataset pipeline | Complete | The project can build a current historical dataset using local CSV data plus recent AESO API records. |
| Makefile pipeline command | Complete | The project can run the main data pipeline with `make pipeline`. |
| Data quality reporting | Complete | The project can generate a readable quality summary for the current historical dataset. |
| Makefile data quality command | Complete | The project can run the data quality report with `make data-quality`. |
| Exploratory data analysis | Complete | The project includes an EDA notebook that answers 10 business questions before feature engineering and modeling. |
| Automated tests | Complete | The current test suite passes successfully. |

## Current Data Outputs

| Output file | Description | Git status |
|---|---|---|
| `data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv` | Raw historical electricity data source | Ignored |
| `data/interim/csv_historical_prices_clean.csv` | Cleaned historical dataset created from the local CSV | Ignored |
| `data/interim/current_historical_prices_clean.csv` | Current historical dataset extended with recent AESO API data | Ignored |

## Current Core Modules

| File | Purpose |
|---|---|
| `src/electricity_predictor/config.py` | Loads project configuration. |
| `src/electricity_predictor/logger.py` | Provides a simple reusable logger. |
| `src/electricity_predictor/data/ingestion.py` | Loads, cleans, and validates historical CSV data. |
| `src/electricity_predictor/data/aeso_api.py` | Fetches, normalizes, and validates AESO pool price API data. |
| `src/electricity_predictor/data/pipeline.py` | Builds clean interim datasets from historical and API sources. |
| `src/electricity_predictor/data/data_quality.py` | Generates a readable quality summary for the current historical dataset. |
| `notebooks/01_eda.ipynb` | Explores the current historical dataset before feature engineering and modeling. |
| `tests/test_config.py` | Tests project configuration loading. |
| `tests/test_ingestion.py` | Tests historical ingestion, validation, dataset building, and merge behavior. |
| `tests/test_aeso_api.py` | Tests AESO API response normalization without calling the live API. |

## Current Makefile Commands

| Command | Purpose |
|---|---|
| `make install` | Installs dependencies and registers the local package. |
| `make test` | Runs the project test suite. |
| `make config-check` | Checks that the project configuration can be loaded. |
| `make pipeline` | Builds the current historical dataset from CSV and AESO API data. |
| `make data-quality` | Runs the data quality report for the current historical dataset. |

## Current Validation Status

The current test suite passes successfully.

```text
13 passed
```

## Current Data Quality Snapshot

The current historical dataset quality report shows:

| Check | Current result |
|---|---:|
| Rows | 57,112 |
| Columns | 5 |
| Min UTC time | 2020-01-01 07:00:00 |
| Max UTC time | 2026-07-07 22:00:00 |
| Duplicate UTC timestamps | 0 |
| Missing hourly UTC timestamps | 0 |
| Missing `datetime_universal_time` values | 0 |
| Missing `datetime_local_time` values | 0 |
| Missing `actual_price` values | 3 |
| Missing `forecast_price` values | 0 |
| Missing `alberta_internal_load` values | 8177 |
| Zero `actual_price` values | 1880 |
| Zero `forecast_price` values | 2500 |

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

Recent API rows may contain missing `actual_price` values when the actual price is not finalized yet. These rows are kept in the source dataset but should be excluded later from model training datasets.

The `alberta_internal_load` column is available in the historical CSV but missing for recent AESO pool price API records because the current pool price API response does not provide that field.

Zero price values exist in both `actual_price` and `forecast_price`. These values are not removed automatically because they may represent real market behavior or API-specific reporting behavior. They require EDA before modeling decisions are made.

## Key Design Decisions

| Decision | Current choice |
|---|---|
| Project name | `Alberta Electricity Price Predictor` |
| Interim output format | CSV |
| Secret storage | `.env` only |
| AESO API authentication header | `API-KEY` |
| Main timestamp key | `datetime_universal_time` |
| Local timestamp column | `datetime_local_time` |
| Actual price column | `actual_price` |
| Forecast price column | `forecast_price` |
| Alberta load column | `alberta_internal_load` |
| Historical merge rule | API data extends historical data but does not overwrite existing historical rows |
| Current main dataset | `data/interim/current_historical_prices_clean.csv` |
| Source dataset rule | Keep recent incomplete API rows |
| Training dataset rule | Exclude rows without finalized `actual_price` before model training |
| First modeling dataset rule | Do not rely on `alberta_internal_load` unless a recent AIL source is added |
| Recommendation threshold rule | Do not define final thresholds before feature engineering, modeling, and evaluation |
