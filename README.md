# Alberta Electricity Price Predictor

A production-oriented machine learning system that forecasts hourly Alberta electricity prices, estimates spike risk, and generates operational recommendations through a complete data engineering, machine learning, and application pipeline.

---

## Overview

The project predicts future Alberta electricity pool prices for multiple forecast horizons and converts those predictions into actionable recommendations for households and businesses operating under variable electricity pricing.

Instead of presenting only a predicted market price, the system produces operational recommendations:

- Recommended
- Acceptable
- Avoid

The repository is organized as a complete machine learning application rather than a standalone collection of predictive models.

---

## Objectives

The project is designed to:

- maintain an up-to-date historical Alberta electricity dataset;
- train and evaluate forecasting models;
- estimate future spike risk;
- generate operational recommendations;
- persist predictions for later validation;
- provide a foundation for a future REST API and web application.

---

## System Architecture

```text
                    Historical CSV
                           │
                    AESO Pool Price API
                           │
                           ▼
                    Data Pipeline
                           │
                           ▼
                 Feature Engineering
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
  Regression Models               Classification Models
          │                                 │
          └────────────────┬────────────────┘
                           ▼
                     Selected Models
                           │
                           ▼
                 Application Pipeline
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
     Data Synchronization              Worker Pipeline
                                               │
                                               ▼
                                      Feature Preparation
                                               │
                                               ▼
                                         Price Prediction
                                               │
                                               ▼
                                        Decision Layer
                                               │
                                               ▼
                                           PostgreSQL
                                               │
                                               ▼
                                      Future API / Frontend
```

---

## Repository Structure

```text
alberta-electricity-price-predictor/
├── app/
├── configs/
├── data/
├── docs/
├── notebooks/
├── reports/
├── src/
│   └── electricity_predictor/
│       ├── data/
│       ├── features/
│       ├── modeling/
│       ├── serving/
│       └── worker/
├── tests/
└── Makefile
```

---

## Machine Learning Pipeline

The offline machine learning pipeline performs:

1. historical data ingestion;
2. AESO synchronization;
3. feature engineering;
4. chronological dataset preparation;
5. regression training;
6. spike classification;
7. model selection;
8. final protected evaluation;
9. model export.

The pipeline follows a strict chronological evaluation protocol to prevent future information leakage.

---

## Application Pipeline

The production-oriented application pipeline performs:

1. synchronize the historical database;
2. prepare the latest feature vector;
3. generate multi-horizon predictions;
4. build the current decision context;
5. classify each prediction into operational recommendations;
6. persist predictions in PostgreSQL;
7. backfill observed prices when they become available.

---

## Decision Layer

The recommendation engine combines:

- predicted electricity price;
- predicted spike probability;
- dynamic market context computed from recent finalized prices.

The current implementation uses a rolling market window to derive adaptive recommendation thresholds instead of fixed hard-coded values.

---

## Database

PostgreSQL stores:

- historical hourly prices;
- prediction runs;
- individual predictions;
- observed prices after validation.

This allows continuous evaluation of real-world prediction performance.

---

## Testing

The repository contains automated unit tests covering:

- data ingestion;
- feature engineering;
- model training;
- prediction serving;
- decision logic;
- persistence;
- application pipeline.

Current status:

```text
221 tests passed
```

---

## Main Commands

| Command | Purpose |
|---------|---------|
| `make pipeline` | Refresh historical dataset |
| `make features` | Build modeling features |
| `make training-data` | Build training dataset |
| `make ml-pipeline` | Execute the machine learning workflow |
| `make application-pipeline` | Execute one application prediction cycle |
| `make production-pipeline` | Refresh data then execute the application pipeline |
| `make test` | Run the complete test suite |

---

## Documentation

Detailed project information is available in:

- `docs/PROJECT_STATUS.md`
- `DECISIONS.md`

---

## Current Status

The repository currently contains:

- complete data engineering pipeline;
- feature engineering pipeline;
- multi-horizon regression models;
- spike-risk classification models;
- application worker;
- adaptive decision layer;
- PostgreSQL persistence;
- production pipeline;
- automated test suite.

---

## Roadmap

Upcoming work includes:

- REST API;
- frontend application;
- scheduled execution;
- monitoring;
- production deployment.

---

## License

MIT License.