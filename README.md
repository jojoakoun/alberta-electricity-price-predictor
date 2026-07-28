# WattWise

<p align="center">
  <img src="app/client/public/wattwise-mark.svg" alt="WattWise mark" width="96">
</p>

WattWise is an end-to-end machine-learning application that predicts Alberta
hourly electricity pool prices and converts them into understandable consumer
recommendations.

## Product

- Current and future hourly price guidance
- `Good time`, `Okay time`, and `Better to wait` recommendations
- Regression and spike-classification models
- Controlled candidate review and manual model activation
- PostgreSQL, Express, React, and an hourly Python worker
- Anonymous private product analytics

## System flow

```text
AESO data
  → cleaning and validation
  → feature engineering
  → regression and classification
  → candidate evaluation
  → manual activation
  → hourly prediction worker
  → PostgreSQL
  → Express API
  → React application
```

## Start locally

```bash
make install
make start
make check
```

## Main workflow

```bash
make reset CONFIRM=YES
make rebuild
# Review the generated reports.
make activate
make sync
make start
```

`make rebuild` does not activate a model. `make activate` is always an explicit
maintainer decision.

## Primary commands

| Command | Purpose |
|---|---|
| `make install` | Install project dependencies |
| `make start` | Start the local API and client |
| `make stop` | Stop local application processes |
| `make check` | Check the public endpoints |
| `make status` | Inspect Git, database, model, and output state |
| `make verify` | Run authorized tests, lint, and production build |
| `make sync` | Refresh operational data and generate predictions |
| `make reset CONFIRM=YES` | Reset generated local state |
| `make rebuild` | Reconstruct data, reports, models, and candidate |
| `make activate` | Promote the approved candidate manually |
| `make analytics` | Read the protected analytics summary |

## Documentation

| Document | Purpose |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System boundaries and runtime flow |
| [`docs/DATA_AND_FEATURES.md`](docs/DATA_AND_FEATURES.md) | Data lineage and feature contract |
| [`docs/MODEL_LIFECYCLE.md`](docs/MODEL_LIFECYCLE.md) | Training, candidates, promotion, and rollback |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) | Local development and verification |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Docker and Railway deployment |
| [`docs/ACCESS_CONTROL.md`](docs/ACCESS_CONTROL.md) | Public, private, maintainer, and secret boundaries |
| [`docs/PRODUCTION_OPERATIONS.md`](docs/PRODUCTION_OPERATIONS.md) | Operational runbook |
| [`docs/WATTWISE_STUDY_MANUAL.md`](docs/WATTWISE_STUDY_MANUAL.md) | Visual engineering and ML study guide |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | Architecture decisions |
| [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) | Current state and next phase |

## Security

Never commit `.env`, production credentials, model artifacts, generated reports,
or local databases. Production secrets belong in Railway variables. Local secrets
belong in `.env`.

## License

MIT
