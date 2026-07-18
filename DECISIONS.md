# Architecture Decisions

_Last updated: July 2026_

This document records the major technical and architectural decisions made throughout the development of the Alberta Electricity Price Predictor.

Each decision includes:

- context;
- decision;
- consequences.

---

# P0-D01 — Python as the Primary Development Language

## Status

Accepted

## Context

The project requires mature libraries for data engineering, machine learning, model evaluation, testing, and future production deployment.

## Decision

Python was selected as the primary implementation language.

## Consequences

Benefits:

- mature machine learning ecosystem;
- pandas and NumPy support;
- scikit-learn integration;
- excellent testing ecosystem.

Trade-offs:

- slower execution than compiled languages.

---

# P1-D01 — Historical Dataset Strategy

## Status

Accepted

## Context

Model training requires several years of hourly Alberta electricity prices.

## Decision

Use a validated historical CSV as the authoritative training dataset.

New observations are synchronized from the AESO API.

## Consequences

Benefits:

- reproducible training;
- deterministic datasets;
- simple synchronization.

Trade-offs:

- historical CSV must occasionally be refreshed.

---

# P1-D02 — PostgreSQL as the Operational Database

## Status

Accepted

## Context

The application requires persistent storage for historical prices, prediction runs, and future prediction validation.

## Decision

Use PostgreSQL as the production database.

## Consequences

Benefits:

- relational integrity;
- production-ready;
- migration support;
- future API compatibility.

Trade-offs:

- database maintenance required.

---

# P2-D01 — Feature Engineering Strategy

## Status

Accepted

## Context

Electricity prices exhibit temporal dependence and strong seasonality.

## Decision

Generate:

- calendar features;
- lag features;
- rolling statistics;
- AESO forecast features.

## Consequences

Benefits:

- improved predictive performance;
- reusable feature pipeline.

Trade-offs:

- additional preprocessing cost.

---

# P2-D02 — Shared Feature Definitions

## Status

Accepted

## Context

Regression, classification, and the application worker require identical model input columns.

## Decision

Centralize feature definitions in:

```
src/electricity_predictor/features/feature_columns.py
```

## Consequences

Benefits:

- single source of truth;
- eliminates duplicated feature definitions;
- simplifies maintenance.

Trade-offs:

- none.

---

# P3-D01 — Separate Regression and Classification Pipelines

## Status

Accepted

## Context

Predicting price and predicting spike risk are different machine learning problems.

## Decision

Train separate regression and classification models.

## Consequences

Benefits:

- independent optimization;
- independent evaluation;
- easier experimentation.

---

# P3-D02 — Chronological Evaluation

## Status

Accepted

## Context

Random train/test splits introduce future leakage for time series.

## Decision

Use chronological train, validation, and protected test periods.

## Consequences

Benefits:

- realistic evaluation;
- production-like performance estimates.

---

# P3-D03 — Protected Test Set

## Status

Accepted

## Context

Final model evaluation must remain unbiased.

## Decision

Never use the protected test split during model selection.

## Consequences

Benefits:

- trustworthy final metrics.

---

# P4-D01 — Train-only Spike Threshold

## Status

Accepted

## Context

Spike thresholds calculated on validation or test data introduce leakage.

## Decision

Estimate the spike threshold using the training split only.

## Consequences

Benefits:

- statistically correct target generation.

---

# P4-D02 — TimeSeriesSplit with Gap

## Status

Accepted

## Context

Rolling features can leak information across validation folds.

## Decision

Use TimeSeriesSplit with a 24-hour gap.

## Consequences

Benefits:

- leakage prevention;
- more realistic cross-validation.

---

# P4-D03 — Fixed Calendar Splits

## Status

Accepted

## Context

Percentage-based dataset splits drift as additional historical data becomes available.

## Decision

Use fixed calendar periods for:

- training;
- validation;
- testing.

## Consequences

Benefits:

- reproducible experiments;
- stable benchmarks.

---

# P5-D01 — Worker Architecture

## Status

Accepted

## Context

Inference should be isolated from model training.

## Decision

Introduce a dedicated worker responsible for:

- feature preparation;
- prediction;
- decision generation;
- persistence.

## Consequences

Benefits:

- clear separation of responsibilities;
- production-ready architecture.

---

# P5-D02 — Application Pipeline

## Status

Accepted

## Context

Running multiple commands manually increases operational complexity.

## Decision

Create a unified application pipeline that:

1. synchronizes historical data;
2. prepares features;
3. generates predictions;
4. applies the decision layer;
5. persists results.

## Consequences

Benefits:

- reproducible execution;
- simplified deployment.

---

# P5-D03 — Dynamic Decision Context

## Status

Accepted

## Context

Static recommendation thresholds quickly become outdated because Alberta electricity prices vary across market regimes.

## Decision

Build a rolling **720-hour** market context from finalized prices.

Compute recommendation thresholds dynamically.

## Consequences

Benefits:

- adapts to changing markets;
- removes hard-coded thresholds;
- improves recommendation stability.

Trade-offs:

- requires sufficient finalized historical observations.

---

# P5-D04 — Recommendation Categories

## Status

Accepted

## Context

End users should not interpret raw electricity prices.

## Decision

Generate three operational recommendations:

- Recommended
- Acceptable
- Avoid

## Consequences

Benefits:

- simple user experience;
- business-oriented output.

---

# P5-D05 — Prediction Persistence

## Status

Accepted

## Context

Model performance should be evaluated continuously after deployment.

## Decision

Store every prediction together with its future observed price.

Backfill actual prices automatically once they become available.

The `confidence` field is intentionally reserved for a future production confidence score. During Phase 5 it is stored as `NULL` until a deterministic confidence estimation strategy is introduced.

## Consequences

Benefits:

- continuous production evaluation;
- future monitoring support.

Trade-offs:

- production confidence estimation is deferred to Phase 6.

---

# P5-D06 — Production Pipeline

## Status

Accepted

## Context

Daily execution should require a single entry point.

## Decision

Introduce the production pipeline:

```
Historical Refresh
        │
        ▼
Application Pipeline
        │
        ▼
Prediction Persistence
```

## Consequences

Benefits:

- operational simplicity;
- future scheduler integration.

---

# Repository Principles

The project follows these architectural principles:

- chronological evaluation;
- no future leakage;
- single source of truth;
- clear separation of responsibilities;
- reproducible experiments;
- production-oriented design;
- automated testing before integration.

---

# Superseded Decisions

No architectural decisions have been superseded as of the completion of Phase 5.

---

# P6-D01 — Phase 6 Product and Implementation Reconciliation

## Status

Accepted

## Context

The WattWise product specification defines the public product contract.

The completed Phase 5 implementation defines the audited worker, decision layer, and PostgreSQL persistence contract.

Differences between those two sources were reviewed before Phase 6 development began.

## Decision

Phase 6 adopts the following reconciliations.

### Recommendation Labels

The database recommendation values remain:

- `Recommended`
- `Acceptable`
- `Avoid`

The public API normalizes them to:

- `recommended`
- `acceptable`
- `avoid`

The frontend maps the API values to consumer wording in one location:

`app/client/src/copy.ts`

Consumer wording:

- `recommended` maps to `Good time`
- `acceptable` maps to `Okay time`
- `avoid` maps to `Better to wait`

### Decision Layer

Phase 6 consumes the completed Phase 5 decision policy without changing it:

- rolling market window: 720 hours;
- recommended threshold: first quartile;
- avoid threshold: third quartile plus 1.5 times the interquartile range;
- predicted price remains the primary decision input;
- a spike prediction may downgrade a recommendation by no more than one level.

### Public Confidence

The API calculates confidence when data is read.

Confidence is derived from the age of `generated_at` on the latest successful prediction run:

- 75 minutes or less: `high`;
- more than 75 minutes and up to 150 minutes: `moderate`;
- more than 150 minutes: `low`.

When confidence is `low`, the frontend displays the recommendation-unavailable state.

The `prediction_runs.confidence` column remains `NULL`.

### Public Payload Privacy

The implemented PostgreSQL schema is authoritative for Phase 6.

Public payloads never expose:

- spike probability;
- spike prediction;
- internal recommendation thresholds;
- model names.

### Freshness

`prediction_runs.generated_at` represents the latest settled source hour used by the worker.

The API exposes:

- `generatedAt`;
- `stale`;
- `confidence`.

The frontend displays the timestamp in `America/Edmonton` using the wording `Updated {local time}`.

## Consequences

Benefits:

- Phase 6 consumes the audited Phase 5 implementation;
- frozen machine-learning and decision logic remain unchanged;
- public payloads remain consumer-focused;
- recommendation wording is centralized and i18n-ready;
- stale data handling is deterministic;
- internal prediction details remain private.

Trade-offs:

- the API must normalize the existing database labels;
- confidence is calculated during reads instead of persisted;
- low confidence is handled as a product state rather than an API error.

---

# P6-D02 — Phase 5 Prediction Persistence Contract

## Status

Accepted

## Context

The completed Phase 5 implementation differs from the original product specification in two important ways.

Successful prediction runs are stored with status `success` rather than `ok`.

The worker computes dynamic recommendation thresholds, but those thresholds are not persisted in the `predictions` table.

## Decision

Phase 6 consumes the existing persistence contract without modification.

The API identifies the latest completed prediction run using:

- `prediction_runs.status = 'success'`

Failed worker executions continue to use:

- `prediction_runs.status = 'failed'`

No migration will rename the successful status during Phase 6.

Dynamic recommendation thresholds remain internal worker values.

Dynamic recommendation thresholds are never exposed through the public API.

Phase 6 will not add threshold columns solely to match earlier specification drafts.

## Consequences

Benefits:

- no migration of validated Phase 5 production data;
- the API reads the values actually persisted by the worker;
- the worker remains the single source of truth;
- internal thresholds remain private.

Trade-offs:

- the API uses `success` rather than `ok`;
- historical threshold values cannot be reconstructed from stored prediction rows alone.

---

# P6-D03 — Public Explanation Keys

## Status

Accepted

## Context

The Phase 5 worker persists complete English explanation sentences.

The WattWise public API contract requires stable explanation keys so frontend copy remains centralized and i18n-ready.

The Phase 5 worker and decision layer are frozen.

## Decision

The API maps the known Phase 5 explanation sentences to stable public keys:

- `Predicted price is favorable compared with the recent market.` → `lower_than_usual`
- `Predicted price is acceptable but market risk is increasing.` → `acceptable_market_risk`
- `Predicted price is high compared with the recent market.` → `higher_than_usual`

The mapping is implemented in one API utility.

An unknown persisted explanation is treated as an internal contract error and is never exposed directly.

## Consequences

Benefits:

- the frozen Phase 5 worker remains unchanged;
- frontend copy remains centralized;
- public payloads expose keys rather than internal English sentences;
- unexpected persistence values fail deterministically.

Trade-offs:

- the API must maintain a compatibility mapping for the Phase 5 explanation sentences.

---

# P6-D04 — Public Now Presentation Keys

## Status

Accepted

## Context

The product specification requires `contextKey`, `actionKey`, and Alberta-local target times for the public Now response.

The specification does not define the exact key names or the current-price context algorithm.

## Decision

The API classifies the current finalized price against the first and third quartiles of the latest 720 finalized hourly prices:

- at or below Q1 → `lower_than_usual`;
- at or above Q3 → `higher_than_usual`;
- otherwise → `about_average`.

This market context is supporting presentation data. It does not alter the frozen Phase 5 recommendation.

Public action keys are:

- `recommended` → `run_heavy_appliances`;
- `acceptable` → `use_if_needed`;
- `avoid` → `wait_if_possible`.

Local target times are formatted by the API using `America/Edmonton`.

## Consequences

Benefits:

- the current price has an empirically grounded consumer context;
- frontend copy remains centralized and i18n-ready;
- all local-time conversion happens at the API boundary;
- the Phase 5 decision layer remains unchanged.

Trade-offs:

- the API maintains presentation mappings that are not persisted by the worker.

---

# P6-D05 — Today Temporal Wording Fallback

## Status

Accepted

## Context

The product specification defines temporal wording for:

- targets within 90 minutes;
- targets within four hours;
- afternoon targets;
- evening targets;
- overnight targets;
- targets at least twenty hours away.

It does not define wording for a target between 6:00 AM and 11:59 AM local time when that target is more than four hours and less than twenty hours away.

## Decision

The API exposes the fallback key `later_today` for the uncovered morning case.

Temporal wording is calculated from the viewing time rather than the prediction generation time.

The API returns both the absolute Alberta-local target time and the temporal wording key.

## Consequences

Benefits:

- every genuine forecast receives deterministic wording;
- the frontend does not invent temporal copy;
- wording remains accurate when a user opens the page after prediction generation.

Trade-offs:

- the API adds one wording key not explicitly named in the original specification.
