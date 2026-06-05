# Alberta Electricity Price Predictor

A machine learning project that predicts Alberta electricity prices and turns those predictions into simple usage recommendations.

## Project Goal

This project helps Alberta households on variable-rate electricity plans decide when to use flexible electricity loads.

Examples include:

- laundry
- dishwashing
- electric vehicle charging
- other shiftable household usage

The final product will not only show predicted prices. It will also classify hours as recommended, acceptable, or avoid.

## Why This Matters

Alberta electricity prices can change sharply from hour to hour. A raw price forecast is useful, but most households need a simpler answer:

> When should I use electricity, and when should I avoid it?

This project turns hourly market data into practical decision support.

## Data Sources

The project uses two data sources:

- historical hourly Alberta electricity data from a local CSV file
- recent pool price data from the AESO API

The historical CSV supports data preparation and future model training. The AESO API supports extending the historical dataset with newer pool price records.

## Current Project Status

Current phase: data engineering.

The repository foundation is complete. The project can currently load, clean, validate, and combine historical Alberta electricity price data with recent AESO pool price API data.

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

## Current Data Outputs

The generated data files are local outputs and are not tracked by Git.

| Output file | Description |
|---|---|
| `data/interim/csv_historical_prices_clean.csv` | Cleaned historical dataset created from the local CSV |
| `data/interim/extended_historical_prices_clean.csv` | Historical dataset extended with recent AESO API data |

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