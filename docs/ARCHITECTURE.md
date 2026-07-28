# Architecture

## Purpose

This document defines the stable boundaries of WattWise. It explains where each
responsibility belongs and how information travels through the system.

## Visual overview

```text
┌──────────────┐
│ AESO source  │
└──────┬───────┘
       ↓
┌────────────────────────┐
│ Data ingestion         │  src/electricity_predictor/data/
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Contracts and features │  contracts/ + features/
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Research modeling      │  modeling/regression + classification
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Lifecycle              │  candidate → comparison → promotion
└──────────┬─────────────┘
           ↓
┌────────────────────────┐
│ Serving and worker     │  active registry → predictions
└──────────┬─────────────┘
           ↓
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ PostgreSQL   │  →  │ Express API  │  →  │ React client │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Layers and ownership

### 1. Data

Path: `src/electricity_predictor/data/`

Responsibilities:

- fetch and read source records;
- normalize source fields;
- preserve raw inputs;
- validate chronology and data quality;
- produce cleaned historical datasets.

### 2. Contracts and features

Paths:

- `src/electricity_predictor/contracts/columns.py`
- `src/electricity_predictor/features/`

`columns.py` is the authoritative shared contract for column names, feature
lists, horizons, and training requirements. Feature modules own calculations,
not shared naming.

### 3. Research modeling

Paths:

- `src/electricity_predictor/modeling/regression/`
- `src/electricity_predictor/modeling/classification/`
- `src/electricity_predictor/modeling/decision/`

Responsibilities:

- train supported model families;
- tune hyperparameters;
- evaluate validation results;
- select research candidates;
- calibrate the consumer decision policy.

### 4. Lifecycle

Path: `src/electricity_predictor/modeling/lifecycle/`

Responsibilities:

- freeze chronological split plans;
- prepare candidate bundles;
- record lineage and manifests;
- compare challenger and active versions;
- promote approved candidates;
- preserve rollback information.

Candidate construction and activation are separate operations.

### 5. Live model contract

Path: `src/electricity_predictor/modeling/live_contract/`

This layer prepares the selected live training contract and validates the live
regression and classification candidates. It may build candidates, but it cannot
write the active registry.

### 6. Serving and worker

Paths:

- `src/electricity_predictor/serving/`
- `src/electricity_predictor/worker/`

Serving owns active-model loading and release installation. The worker owns the
hourly operational refresh, prediction cycle, and database synchronization.
The worker never silently trains or promotes models.

### 7. Application

Paths:

- `app/server/` — Express API and PostgreSQL repositories
- `app/client/` — React and Vite interface

The API exposes consumer-focused contracts. Database details, model objects, and
private analytics remain behind server boundaries.

## Runtime flows

### Hourly prediction

```text
make sync
  → application_prediction_pipeline
  → operational_refresh
  → feature_preparation
  → active_model_predictions
  → decision_layer
  → prediction_run_database
  → PostgreSQL
  → /api/v1/now and /api/v1/today
```

### Candidate lifecycle

```text
make rebuild
  → data reconstruction
  → feature construction
  → model-family training
  → model selection
  → live candidate preparation
  → lifecycle comparison
  → reports and manifests

manual review
  → make activate
  → active_models.json
  → make sync
```

## Database/application layers

```text
HTTP route
  → service
  → domain/utilities
  → repository
  → PostgreSQL
```

Routes parse HTTP concerns. Services coordinate use cases. Domain modules hold
business decisions. Repositories own SQL.

## Non-negotiable ownership rules

- Shared columns belong in `contracts/columns.py`.
- Feature calculations belong in `features/`.
- Research training belongs in `modeling/`.
- Active-registry writes belong in lifecycle promotion.
- Operational predictions use registered active models.
- SQL belongs in repositories or dedicated database modules.
- Public routes expose no secret or private model implementation details.
- Protected final-evaluation tests are excluded from routine verification.
