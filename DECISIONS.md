# Project Decisions

This file records the main technical and product decisions for the Alberta Electricity Price Predictor.

Each entry explains:

- what we chose
- why we chose it
- what we rejected
- what comes next

## Phase 0 — Repository Setup

### Decision 1 — Build a clean public-first project

We chose to build the project from zero with a clean public repository structure.

Why: the repository must be easy to understand, easy to run, and easy to maintain.

Rejected: starting with unnecessary complexity before the core product works.

Next: create the project foundation, then add data engineering in Phase 1.

### Decision 2 — Keep the public product name simple

We chose to use `Alberta Electricity Price Predictor` as the project name for now.

Why: this name is clear and describes the project directly.

Rejected: using a separate brand name before the product direction is stable.

Next: revisit branding only after the core product works.

## Phase 1 — Data Engineering

### Decision 3 — Keep CSV as the interim data format

We chose to keep interim datasets as CSV files.

Why: CSV is simple, readable, easy to inspect, and enough for the current phase.

Rejected: switching to Excel or a heavier data format before the project needs it.

Next: continue using CSV for interim outputs unless scale or performance requires another format.

### Decision 4 — Separate historical ingestion from API ingestion

We chose to keep historical CSV ingestion and AESO API ingestion in separate modules.

Why: the two sources have different formats, validation needs, and failure modes.

Rejected: mixing CSV and API logic in one large script.

Next: keep each source clean, then combine them through the pipeline layer.

### Decision 5 — Use project-standard column names

We chose to rename raw source columns into stable project names.

Current standard columns include:

- `datetime_universal_time`
- `datetime_local_time`
- `actual_price`
- `forecast_price`
- `alberta_internal_load`

Why: stable names make downstream code easier to read and maintain.

Rejected: using source-specific names such as `Date_Begin_GMT` or `ACTUAL_AIL` throughout the project.

Next: use these names consistently in validation, EDA, feature engineering, and modeling.

### Decision 6 — Extend historical data without overwriting it

We chose to let AESO API data extend the historical CSV data only after the last historical UTC timestamp.

Why: the historical CSV remains the trusted base for older records, while the API adds newer records.

Rejected: allowing API rows to overwrite existing historical rows.

Next: continue checking for duplicate UTC timestamps after merging.

### Decision 7 — Keep recent incomplete API rows in the source dataset

We chose to keep recent API rows even when `actual_price` is not finalized yet.

Why: recent market data may include hours where the actual pool price is not available yet. These rows are useful for live data awareness but not for training.

Rejected: deleting incomplete recent rows from the source dataset.

Next: exclude rows without finalized `actual_price` when creating modeling datasets.

### Decision 8 — Do not use `alberta_internal_load` in the first modeling dataset unless recent load data is added

We found that `alberta_internal_load` is available in the historical CSV but missing for recent AESO pool price API records.

Why: a model that relies on this feature would not work consistently on current API-extended data unless a recent AIL source is added.

Rejected: forcing `alberta_internal_load` into the first modeling dataset despite recent missing values.

Next: either exclude this feature from the first model or add a reliable recent AIL source later.

### Decision 9 — Add explicit data quality reporting before feature engineering

We chose to add a data quality report before building features.

Why: feature engineering should not start until the project understands coverage, missing values, duplicate timestamps, hourly continuity, and zero-price behavior.

Rejected: moving directly from data ingestion to feature engineering without quality checks.

Next: use the data quality report as a checkpoint before modeling data preparation.

### Decision 10 — Complete EDA before defining recommendation thresholds

We chose to answer business-focused EDA questions before defining `recommended`, `acceptable`, and `avoid` thresholds.

Why: thresholds should be supported by historical price behavior, spike patterns, forecast usefulness, and model evaluation.

Rejected: hardcoding recommendation thresholds too early.

Next: use EDA findings to guide feature engineering, baseline models, spike-risk classification, and the future decision layer.
