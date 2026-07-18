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