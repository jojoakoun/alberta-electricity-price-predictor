# WattWise — Alberta Electricity Price Predictor

WattWise predicts hourly Alberta electricity pool prices and supports
consumer-facing recommendations such as recommended, acceptable, or avoid.

The repository contains the complete data, machine-learning, worker, API, and
React application stack.

## Architecture

The authoritative production flow is:

```text
historical and forecast data
  → feature construction
  → lifecycle candidate preparation
  → lifecycle comparison
  → manual lifecycle promotion
  → active model registry
  → hourly prediction worker
  → Express API
  → React application
```

The protected final test split is never used to fit models. Normal lifecycle
comparisons use validation data and the currently active model versions.
Activation remains a separate, explicit promotion action.

## Repository structure

- `src/electricity_predictor/data/`: AESO ingestion and data preparation
- `src/electricity_predictor/contracts/`: shared column contracts
- `src/electricity_predictor/features/`: feature construction and validation
- `src/electricity_predictor/modeling/`: research and lifecycle logic
- `src/electricity_predictor/serving/`: active-model prediction and releases
- `src/electricity_predictor/worker/`: scheduled application prediction work
- `app/server/`: Node and Express API
- `app/client/`: React and Vite frontend
- `tests/`: Python automated verification
- `docs/`: authoritative project documentation

## Installation

Run commands from the repository root.

```bash
make install
```

Python packages are defined only in `requirements.txt`. Python packaging and
the `wattwise-worker` command are defined in `pyproject.toml`.

## Main commands

### Verification

```bash
make verify
make app-check
make database-check
```

Routine maintenance must not execute the two protected final-evaluation tests
unless final evaluation has been explicitly authorized:

- `tests/modeling/regression/test_final_test_evaluation.py`
- `tests/modeling/classification/test_final_test_evaluation.py`

### Local application

```bash
make dev
make stop
```

### Data and application predictions

```bash
make sync-history
make sync-and-predict
make worker-run
```

### Research rebuild

```bash
make research-rebuild
make research-rebuild-all
```

`research-rebuild-all` is a deliberate full research operation and must only
be run when final evaluation and generated artifacts are explicitly intended.

### Model lifecycle

```bash
make lifecycle-status
make lifecycle-run
make lifecycle-promote
make lifecycle-rollback
```

### Releases and scheduled work

```bash
make release-build
make models-install
make hourly-refresh
make retrain-if-due
```

### Local maintenance

```bash
make local-bootstrap
make db-clean CONFIRM=YES
```

`db-clean` is destructive and requires explicit confirmation.

## Documentation

- `docs/ARCHITECTURE.md`
- `docs/DATA_AND_FEATURES.md`
- `docs/MODEL_LIFECYCLE.md`
- `docs/DEVELOPMENT.md`
- `docs/DEPLOYMENT.md`
- `docs/PROJECT_STATUS.md`
- `docs/DECISIONS.md`

## Current position

The repository foundation has been reorganized and verified. The next phase is
a deliberate manual reconstruction of research outputs and live model
candidates before deployment.
