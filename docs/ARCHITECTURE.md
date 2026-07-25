# Architecture

## System boundaries

WattWise is divided into six main layers.

### Data

`src/electricity_predictor/data/` retrieves and normalizes Alberta Electric
System Operator data.

Raw source data is preserved separately from generated datasets.

### Contracts and features

`src/electricity_predictor/contracts/columns.py` is the authoritative source
for shared column names, model feature lists, forecast horizons, and training
requirements.

`src/electricity_predictor/features/` owns feature construction and feature
quality checks.

### Research modeling

`src/electricity_predictor/modeling/regression/` and
`src/electricity_predictor/modeling/classification/` contain model families,
tuning, selection, and evaluation logic.

Research entry points remain Python modules. The Makefile exposes the approved
orchestration commands rather than one command per individual algorithm.

### Lifecycle

`src/electricity_predictor/modeling/lifecycle/` owns:

- candidate run metadata
- frozen chronological split plans
- lifecycle candidate preparation
- champion and challenger comparison
- promotion decisions
- rollback support
- lifecycle scheduling

Candidate creation, comparison, and promotion are separate responsibilities.

### Live model contract

`src/electricity_predictor/modeling/live_contract/` owns the current live
training contract and validation comparison.

Live candidates use the selected 14-feature contract. Training uses approved
training and validation periods only. The protected test split is not used for
fitting.

### Serving and worker

`src/electricity_predictor/serving/` owns active-model loading, prediction,
release construction, and release installation.

`src/electricity_predictor/worker/` owns the hourly application prediction
cycle and database synchronization required by the application.

### Application

`app/server/` is the Express API.

`app/client/` is the React and Vite user interface.

The API exposes consumer-focused responses. Model and database implementation
details remain behind the API boundary.

## Production flow

```text
AESO data
  → normalized historical records
  → approved feature contract
  → lifecycle candidate preparation
  → validation comparison
  → explicit promotion
  → active model registry
  → worker predictions
  → PostgreSQL
  → Express API
  → React UI
```

## Ownership rules

- Shared column definitions belong in `contracts/columns.py`.
- Feature calculations belong in `features/`.
- Research training belongs in `modeling/`.
- Active registry writes belong in lifecycle promotion logic.
- Live refitting must not activate a model.
- Application predictions use active registered models.
- The worker does not silently train or promote models.
- The protected test split is not part of routine development verification.
