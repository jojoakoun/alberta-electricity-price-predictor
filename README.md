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

The historical CSV supports data preparation, EDA, and future model training. The AESO API supports extending the historical dataset with newer pool price records.

## Current Project Status

Current phase: data engineering.

The repository foundation is complete. The project can currently load, clean, validate, combine, inspect, and explore historical Alberta electricity price data with recent AESO pool price API data.

A short status summary is available here:

[View project status](docs/PROJECT_STATUS.md)

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

## Exploratory Data Analysis

The project includes an EDA notebook:

- `notebooks/01_eda.ipynb`

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

The generated data files are local outputs and are not tracked by Git.

| Output file | Description |
|---|---|
| `data/interim/csv_historical_prices_clean.csv` | Cleaned historical dataset created from the local CSV |
| `data/interim/current_historical_prices_clean.csv` | Current historical dataset extended with recent AESO API data |

## Planned Machine Learning Tasks

This project will solve two related problems:

1. Regression: predict future electricity prices.
2. Classification: estimate future spike risk.

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

Final recommendation thresholds have not been defined yet. They will be decided after feature engineering, baseline models, spike-risk classification, and model evaluation.

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
├── src/
│   └── electricity_predictor/
│       ├── data/
│       ├── features/
│       ├── modeling/
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
| `notebooks/01_eda.ipynb` | Explores the current historical dataset before feature engineering and modeling. |

## Testing

Run the full test suite with:

```bash
make test
```

## Main Commands

| Command | Purpose |
|---|---|
| `make install` | Installs dependencies and registers the local package. |
| `make test` | Runs the project test suite. |
| `make config-check` | Checks that the project configuration can be loaded. |
| `make pipeline` | Builds the current historical dataset from CSV and AESO API data. |
| `make data-quality` | Runs the data quality report for the current historical dataset. |

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
