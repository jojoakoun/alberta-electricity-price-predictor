# WattWise — Alberta Electricity Price Predictor

WattWise is a full-stack machine-learning project for forecasting hourly
electricity pool prices in Alberta, Canada.

This public repository contains the application and machine-learning source
code. Internal operating documentation, deployment configuration, private
automation, generated datasets, trained models, and development reports are
intentionally excluded.

## Project capabilities

- Hourly electricity-price forecasting across multiple horizons
- Electricity-price spike classification
- Chronological model training and validation
- Leakage-aware feature engineering
- Candidate model comparison and controlled model activation
- PostgreSQL-backed prediction storage
- Express API for current and daily forecasts
- Responsive React user interface
- English and French interface support
- Automated Python, API, and frontend tests

## Technology

### Machine learning

- Python
- pandas
- NumPy
- scikit-learn
- joblib

### Backend

- Node.js
- Express
- PostgreSQL

### Frontend

- React
- Vite
- Vitest

## Public repository structure

```text
src/
  electricity_predictor/
    contracts/
    data/
    features/
    modeling/
    serving/
    worker/

app/
  server/
  client/

tests/
configs/
migrations/
Model-safety principles
Time-series data is split chronologically.
Future actual prices are never used as live prediction inputs.
Training and model activation are separate operations.
Model comparison occurs before activation.
Protected final evaluation data is isolated from routine model development.
Scheduled prediction work does not silently promote models.
Scope

This repository is provided as a source-code portfolio and technical reference.

Operational documentation, infrastructure definitions, private automation,
environment files, datasets, generated reports, trained model artifacts, and
production credentials are not distributed in this public snapshot.
