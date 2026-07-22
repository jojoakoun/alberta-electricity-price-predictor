# WattWise — Alberta Electricity Price Predictor

WattWise is a production-oriented machine learning application that forecasts hourly Alberta electricity pool prices, estimates spike risk, and converts those forecasts into simple electricity-use recommendations.

The project includes:

- historical and live AESO data ingestion;
- data validation and feature engineering;
- multi-horizon regression and spike classification;
- controlled model lifecycle management;
- secure model release delivery;
- a PostgreSQL operational database;
- an idempotent hourly prediction worker;
- a Node.js and Express REST API;
- a bilingual React frontend;
- Railway production configuration.

---

## Current Status

**Phase 6 remediation: implemented and verified locally; Railway verification pending**

No final remediation commit is designated. The current remediation remains an
uncommitted working tree on `feature/phase-6-production-readiness`.

Canonical verification recorded on 2026-07-21:

```text
Focused serving gate:     16 passed (repeated subset of Python tests)
Complete Python suite:   320 passed
Server suite:            102 passed
Frontend suite:           42 passed
Distinct test total:     464 passed

Frontend lint:            passed
Frontend build:           passed
Git diff check:           passed
Working tree:             modified and not committed
```

The canonical gate verifies configuration, Python compilation, serving, the
complete Python/server/frontend suites, frontend lint, the production build,
and whitespace validity. The focused 16-test serving gate is included in the
320-test Python suite and is not added again to the distinct total.

The production Express/API/SPA smoke, configured-PostgreSQL worker flow,
same-source-hour idempotence, five-horizon integrity, and actual-price backfill
are verified locally. Every Railway gate remains **NOT VERIFIED**. The project
is not described as deployed or production-ready on cloud evidence.

---

## Product Purpose

Alberta pool prices can change significantly from hour to hour.

WattWise helps users understand:

- the latest observed electricity market price;
- predicted prices over the next 24 hours;
- whether the current period is favorable;
- when a lower-price period may occur;
- whether spike risk is elevated;
- whether electricity use should happen now or be delayed.

The consumer recommendations are:

- **Good time**
- **Okay time**
- **Better to wait**

Internally, these map to:

- `Recommended`
- `Acceptable`
- `Avoid`

---

## Forecast Horizons

WattWise generates forecasts for:

- 1 hour;
- 3 hours;
- 6 hours;
- 12 hours;
- 24 hours.

Every successful prediction run must contain exactly:

```text
[1, 3, 6, 12, 24]
```

---

## System Architecture

```text
One-time bootstrap
Historical CSV -> make seed-history -> PostgreSQL hourly_prices

Recurring operational worker
PostgreSQL latest hour -> bounded AESO overlap -> normalize and upsert
-> PostgreSQL inference window -> five predictions -> PostgreSQL persistence
-> Express REST API -> React application

Separate research workflow
Historical CSV + AESO API -> interim/processed datasets -> benchmark reports
```

PostgreSQL is the steady-state operational source of truth. The historical CSV
is a one-time seed and research input; it is not an hourly Railway dependency.

The model lifecycle operates separately from the hourly application worker:

```text
Historical Data
      │
      ▼
Deterministic Expanding Split
      │
      ▼
Isolated Challenger Training
      │
      ▼
Champion–Challenger Comparison
      │
      ▼
Manual Promotion Decision
      │
      ▼
Release Bundle and Active Registry
```

---

## Main Components

### Data Engineering

The research/bootstrap pipeline:

- imports the historical AESO CSV;
- retrieves newer observations from the AESO API;
- normalizes timestamps;
- validates required columns;
- merges historical and API data;
- removes duplicate hours;
- maintains the current clean historical dataset.

The operational path is separate. It derives a bounded two-market-day AESO
overlap from PostgreSQL, upserts revised/new hours, preserves finalized actuals,
allows API actuals to fill nulls, and lets newer non-null API forecasts revise
older forecasts. Inference features are prepared from PostgreSQL only.

Primary modules:

```text
src/electricity_predictor/data/
├── aeso_api.py
├── data_quality.py
├── ingestion.py
└── pipeline.py
```

---

### Feature Engineering

The project generates:

- calendar features;
- hourly lag features;
- rolling statistics;
- AESO forecast features;
- load-based features;
- horizon-specific target columns.

Shared model input columns are centralized in:

```text
src/electricity_predictor/features/feature_columns.py
```

This prevents training and serving from using different feature definitions.

---

## Machine Learning

### Regression

Regression predicts future Alberta pool prices.

Implemented model families include:

- Naive Baseline;
- Linear Regression;
- Ridge Regression;
- Lasso Regression;
- Elastic Net;
- Random Forest Regression.

The active regression lineage is the manually promoted candidate
`candidate-expanding-20260719T130000-dd356b9313f2`:

| Horizon | Model |
|---:|---|
| 1 h | `lasso_regression_tuned` |
| 3 h | `random_forest_regressor_tuned` |
| 6 h | `lasso_regression_tuned` |
| 12 h | `lasso_regression_tuned` |
| 24 h | `naive_baseline` persistence reference |

The +24 h output uses `prediction_column=actual_price_lag_1h`. It is an
authentic persistence/reference forecast, not an independently learned future
price. It remains visible in Today, reports, and persistence, but it cannot
create the product's best-time or savings headline.

### Classification

Classification estimates whether the future price will exceed the train-derived spike threshold.

Implemented model families include:

- Naive Spike Baseline;
- Logistic Regression;
- Random Forest Classification;
- Gradient Boosting Classification.

The active classification lineage intentionally remains `legacy-unversioned`
from `models/classification/`. The latest classification challenger did not pass
its metric gate and was not promoted.

Regression and classification versions are managed independently.

---

## Evaluation Protocol

The project uses chronological evaluation only.

Safeguards include:

- no random train/test split;
- protected final test periods;
- fixed benchmark periods for reproducible historical comparison;
- expanding lifecycle splits for future challengers;
- a 24-hour purge between partitions;
- `TimeSeriesSplit` with `gap=24`;
- train-only spike threshold estimation;
- no validation or test data used to construct training targets;
- manual model promotion.

The lifecycle configuration currently defines:

```text
Split strategy:             expanding
Validation window:          365 days
Protected test window:      180 days
Purge between partitions:   24 hours
Minimum training history:   1095 days
Retraining interval:        90 days
Promotion policy:           manual
Automatic promotion:        disabled
```

---

### Report and artifact scope

| Location | Meaning |
|---|---|
| `reports/*.csv` | Fixed-calendar historical benchmark and research evidence; not the current production-candidate report set |
| `models/candidates/candidate-expanding-20260719T130000-dd356b9313f2/reports/` | Latest lifecycle candidate evaluation and comparison evidence |
| `models/candidates/candidate-expanding-20260719T130000-dd356b9313f2/regression/` | Active promoted regression metadata and artifacts |
| `models/classification/` | Active legacy classification metadata and artifacts |
| `models/production/active_models.json` | Authoritative serving-lineage registry |

The candidate classification reports describe a rejected challenger, not the
served classifier. Likewise, `models/regression/` contains legacy regression
artifacts and is not the active regression source.

---

## Spike Threshold

The operational spike threshold is derived only from training data.

The currently active production threshold is approximately:

```text
170.77 $/MWh
```

The rejected classification challenger derived `157.885 $/MWh`, a measured
train-derived threshold change of `-12.885 $/MWh` from the active threshold.
That change is evidence to monitor, not authority to change production. Because
the classification gate failed, both the challenger and its threshold were not
promoted; active classification continues to use `170.77 $/MWh`.

---

## Model Lifecycle

Lifecycle modules are located in:

```text
src/electricity_predictor/modeling/lifecycle/
```

The lifecycle supports:

- deterministic dataset hashing;
- deterministic split identifiers;
- isolated candidate directories;
- regression candidate training;
- classification candidate training;
- champion–challenger comparisons;
- component-specific promotion gates;
- manual promotion;
- rollback;
- active-model registry updates;
- release bundle generation;
- lifecycle state tracking.

The latest isolated lifecycle evaluation completed with:

```text
Regression gate:      passed
Classification gate:  failed
Automatic promotion:  not performed
```

The regression challenger was promoted manually.

The classification champion remained unchanged. The combined summary reports
`promotion_ready: false` because classification failed; component-specific gates
still allowed the independently passing regression component to be promoted.

---

## Active Model Registry

Active model versions are resolved through:

```text
models/production/active_models.json
```

The registry supports separate active versions for:

- regression;
- classification.

Current entries:

- regression: `candidate-expanding-20260719T130000-dd356b9313f2`, source
  `candidate`;
- classification: `legacy-unversioned`, source `legacy`.

Serving code does not silently select arbitrary model directories.

Missing or invalid model registry entries produce explicit errors.

---

## Model Releases

Model artifacts are intentionally excluded from Git.

Production model delivery uses:

- a compressed release archive;
- an internal release manifest;
- per-file SHA-256 checksums;
- an archive-level SHA-256 checksum;
- a secure installer;
- atomic activation;
- rollback protection.

The installer validates:

- archive checksum;
- manifest checksum;
- internal file checksums;
- expected forecast horizons;
- active registry structure;
- path traversal attempts;
- absolute paths;
- symbolic links;
- hard links;
- partial installations.

Production installation variables:

```env
MODEL_RELEASE_URL=
MODEL_RELEASE_SHA256=
```

Both variables must be set together in production. Because `models/` is
excluded from Git, they are required for a clean Railway worker build. They may
be omitted only in local development when a complete active registry and every
referenced artifact are already installed.

Manual/local installation command:

```bash
make models-install
```

The `wattwise-worker` production entry point performs the same model preflight
and installs a configured release automatically.

---

## Hourly Operational Worker

The hourly worker is separate from model training.

Canonical command:

```bash
make worker-run
```

The separate one-time database bootstrap is:

```bash
make seed-history
```

That is the local wrapper. An environment without Make can run:

```bash
python -m electricity_predictor.worker.historical_seed
```

`railway.worker.json` is configured to invoke the installed
`wattwise-worker` entry point directly. The recurring worker never reads
raw/interim/processed CSV files: it derives an AESO overlap from PostgreSQL,
upserts revisions, then prepares inference from the database.

The worker:

1. installs or validates the configured model release;
2. refreshes AESO data;
3. synchronizes PostgreSQL;
4. prepares the latest feature vector;
5. loads active regression and classification models;
6. generates five forecasts;
7. applies the decision layer;
8. persists one successful prediction run;
9. backfills observed prices;
10. exits cleanly.

Successful prediction runs are idempotent by `generated_at`.

Here `generated_at` is the source market-data hour used as the forecast origin,
not wall-clock execution time. `created_at` is the initial database persistence
time and is not refreshed when an idempotent run is reused.

Running the same hourly cycle twice:

- reuses the same prediction run;
- replaces its five prediction rows transactionally;
- does not create duplicate successful runs.

The database enforces this rule with a partial unique index.

---

## Decision Layer

The decision layer combines:

- predicted price;
- predicted spike risk;
- recent finalized market behavior.

It uses a rolling **720-hour** market context.

Recommendation thresholds are calculated dynamically from recent finalized prices rather than being permanently hard-coded.

A spike prediction may downgrade the price-based recommendation by no more than one level.

Internal recommendations:

```text
Recommended
Acceptable
Avoid
```

Public API recommendations:

```text
recommended
acceptable
avoid
```

Consumer wording is managed by the frontend translation layer.

---

## PostgreSQL

PostgreSQL stores:

### `hourly_prices`

- historical hourly prices;
- AESO forecast prices;
- Alberta internal load;
- source metadata.

### `prediction_runs`

- forecast source/reference market-data hour (`generated_at`);
- initial persistence timestamp (`created_at`);
- run status;
- confidence placeholder;
- active spike threshold;
- diagnostic detail.

### `predictions`

- forecast horizon;
- target timestamp;
- predicted price;
- later observed price;
- spike probability;
- spike prediction;
- recommendation;
- explanation.

Database migrations are located in:

```text
app/server/migrations/
```

Production migrations run with:

```bash
npm --prefix app/server run migrate:prod
```

The migration command uses `DATABASE_URL` directly and does not depend on a local `.env` file.

---

## REST API

The Express server exposes:

```text
GET /api/v1/health
GET /api/v1/now
GET /api/v1/today
```

### Health

`/api/v1/health` verifies:

- server availability;
- PostgreSQL connectivity;
- the latest successful forecast source market-data hour through
  `latestForecastSourceAt`.

`latestForecastSourceAt` exposes `prediction_runs.generated_at`. It is not a
worker execution timestamp and is not replaced with `created_at`, which records
only the run's initial persistence time.

### Now

`/api/v1/now` returns:

- recommendation derived from the latest finalized observed price;
- current observed price and its market hour;
- market context;
- action key;
- observed-price freshness state.

Now does not use a forecast and does not expose a separate recommendation-update
time. `generatedAt` is retained as a compatibility alias of the observation
hour; `price.observedAtUtc` is the explicit observation timestamp.

### Today

`/api/v1/today` returns:

- five authentic forecast horizons;
- absolute UTC target times;
- Alberta-local target times;
- consumer temporal wording;
- recommendation keys;
- price values in cents per kWh;
- forecast provenance through `forecastKind`;
- the lowest eligible future model forecast, excluding persistence references;
- server-owned comparison with the latest finalized observed price;
- explicit future-target and freshness states.

Past targets are never selected as the best future time.

A passed target is labeled honestly as:

```text
recently_passed
```

The API distinguishes:

- `available`: at least one eligible future model forecast remains;
- `none_remaining`: no future target remains;
- `reference_only`: only a persistence reference remains;
- `provenance_unavailable`: future provenance cannot support selection;
- comparison states `forecast_lower`, `forecast_equal`, `current_lower`, and
  `unavailable`.

No-lower-price is a valid comparison result and is not conflated with missing or
expired forecasts. The +24 h persistence reference stays visible but is never
eligible for `bestTime`. `generatedAt` is the forecast source market-data hour,
not the wall-clock execution time.

Internal spike probabilities, internal thresholds, and model names are not exposed publicly.

---

## Frontend

The frontend uses:

- React;
- JavaScript and JSX;
- Vite;
- TanStack Query;
- React Router;
- Tailwind CSS;
- Vitest;
- Testing Library;
- Oxlint.

Routes:

```text
/
├── /today
├── /learn
└── /project
```

### Now page

Displays:

- current recommendation;
- current observed price;
- observed-price timestamp;
- confidence;
- freshness;
- clear action guidance.

The recommendation stays visible when the observation is stale, alongside a
clear delayed-data warning.

### Today page

Displays:

- five forecast points;
- the eligible future model forecast and its observed-price comparison;
- a planning recommendation;
- lower/equal/current-lower/unavailable states;
- distinct no-future, reference-only, and provenance-unavailable states;
- an explicit persistence-reference label at +24 h;
- stale forecast details that remain inspectable under a warning;
- an explanatory forecast chart.

The graph shows only the five authentic horizon outputs, including the labeled
persistence/reference output.

Any connecting line is a visual guide and does not represent additional predictions between forecast points.

### Learn page

Explains:

- Alberta pool prices;
- data sources;
- confidence states;
- recommendation categories;
- limitations;
- periodic model review and approval.

### Project page

Summarizes the engineering workflow:

1. AESO data;
2. data engineering;
3. feature engineering;
4. machine learning;
5. API;
6. React interface.

### Internationalization

The application supports:

- English;
- French.

Consumer copy and temporal wording are centralized in the frontend translation files.

---

## Price Units

Model and database prices use:

```text
$/MWh
```

The public frontend displays consumer-friendly prices in:

```text
¢/kWh
```

Conversion:

```text
1 $/MWh = 0.1 ¢/kWh
```

---

## Freshness Policy

Freshness is calculated at API read time, with separate timestamp meanings and
thresholds.

Forecast-source freshness uses `prediction_runs.generated_at`:

| Source-hour age | Confidence | Product state |
|---:|---|---|
| Up to and including 75 minutes | `high` | Current |
| More than 75 and up to and including 150 minutes | `moderate` | Delayed warning |
| More than 150 minutes | `low` | Stale warning; details remain visible |

Observed-price freshness uses the finalized price's `datetime_utc`:

| Observation age | Confidence | Product state |
|---:|---|---|
| Up to and including 150 minutes | `high` | Current |
| More than 150 and up to and including 240 minutes | `moderate` | Delayed warning |
| More than 240 minutes | `low` | Stale warning; recommendation remains visible |

These confidence values describe source freshness, not statistical prediction
uncertainty.

The database `prediction_runs.confidence` column remains reserved for future persisted confidence scoring.

---

## Production Web Service

The web service is configured through:

```text
railway.json
```

Production workflow:

1. install server dependencies;
2. install frontend build dependencies;
3. build the React application;
4. execute PostgreSQL migrations;
5. start Express;
6. expose `/api/v1/health` as the healthcheck.

Express:

- reads the Railway `PORT`;
- binds to `0.0.0.0` in production;
- serves the built React assets;
- preserves `/api/...` routes;
- supports direct React route refreshes;
- returns JSON for unknown API routes.

---

## Railway Worker

The scheduled worker is configured separately through:

```text
railway.worker.json
```

Current worker configuration:

```text
Start command:  wattwise-worker
Cron schedule:  15 * * * *
Restart policy: NEVER
```

Railway cron schedules use UTC.

The worker must finish and exit before the next scheduled execution.

The Python 3.14 local environment generated the console command through
`pip install -e .`; two direct `.venv/bin/wattwise-worker` cycles resolved and
completed, with the second reusing run 9 for source hour
`2026-07-21T17:00:00Z`. This is local packaging/runtime evidence only. Actual
Railway command resolution, runtime duration, first/second cycles, and cron
behavior remain **NOT VERIFIED**.

---

## Runtime Versions

Validated and pinned runtime versions:

```text
Python: 3.14.5
Node:   22.22.3
```

Runtime files:

```text
.python-version
.nvmrc
```

Python package compatibility:

```toml
requires-python = ">=3.14,<3.15"
```

Both Node applications constrain Node to version 22.

---

## Repository Structure

```text
alberta-electricity-price-predictor/
├── app/
│   ├── client/                 # React frontend
│   └── server/                 # Express API and migrations
├── configs/                    # Project and lifecycle configuration
├── data/                       # Raw, interim, and processed data
├── notebooks/                  # Exploratory analysis
├── scripts/                    # Local utilities and export verification
├── src/
│   └── electricity_predictor/
│       ├── data/
│       ├── features/
│       ├── modeling/
│       │   └── lifecycle/
│       ├── serving/
│       └── worker/
├── tests/
├── Makefile
├── railway.json
├── railway.worker.json
└── README.md
```

---

## Main Commands

### Dependency scopes

`make install` installs `requirements-dev.txt`, which includes the research and
runtime dependency files without changing their pinned versions. Railway uses
only `requirements.txt`; plotting dependencies live in
`requirements-research.txt`, and test dependencies live in
`requirements-dev.txt`.

### Local application

| Command | Purpose |
|---|---|
| `make dev` | Start the local API and frontend |
| `make stop` | Stop local application processes |
| `make app-refresh` | Refresh AESO data and publish predictions |
| `make worker-run` | Install models and execute one operational worker cycle |
| `make seed-history` | Seed PostgreSQL once from the historical bootstrap CSV |

### Verification

| Command | Purpose |
|---|---|
| `make verify` | Run Python, server, frontend, lint, build, and diff checks |
| `make inference-check` | Run focused serving tests |
| `make config-check` | Validate project configuration |
| `make compile-check` | Compile Python source files |

### Model lifecycle

| Command | Purpose |
|---|---|
| `make lifecycle-status` | Show lifecycle status and next due date |
| `make lifecycle-run` | Run lifecycle only when due |
| `make lifecycle-run FORCE=1` | Force an isolated lifecycle execution |
| `make lifecycle-promote` | Manually promote approved components |
| `make lifecycle-rollback` | Restore a previous active registry |
| `make release-build` | Build a production model release |

### Research rebuilds

| Command | Purpose |
|---|---|
| `make research-rebuild` | Rebuild the selected research workflow |
| `make research-rebuild-all` | Run the complete research pipeline |

### Audit exports

| Command | Purpose |
|---|---|
| `make project-context` | Export project text context |
| `make project-zip` | Build the complete audit ZIP |
| `make project-export` | Generate context, ZIP, and manifests |
| `make project-export-check` | Verify ZIP integrity and all manifest checksums |

The export verifier checks:

- ZIP corruption;
- missing files;
- unexpected files;
- duplicate paths;
- unsafe archive paths;
- file sizes;
- SHA-256 checksums;
- forbidden local or secret paths.

---

## Environment Configuration

Start from:

```bash
cp .env.example .env
```

Main variables:

```env
LOG_LEVEL=INFO

AESO_API_BASE_URL=https://apimgw.aeso.ca/public/poolprice-api/v1.1
AESO_API_SUBSCRIPTION_KEY=       # required by the production worker

DATABASE_URL=                    # required by production web and worker services

NODE_ENV=development

MODEL_RELEASE_URL=               # required by a clean production worker build
MODEL_RELEASE_SHA256=            # required with MODEL_RELEASE_URL
```

Active serving artifacts are resolved exclusively through
`models/production/active_models.json`; directory names are not used as an
implicit winner-selection rule.

Never commit `.env`.

---

## Local Verification Evidence

The canonical automated gate run on 2026-07-21 confirmed:

```text
Focused serving gate:          16 passed (subset of Python suite)
Complete Python suite:        320 passed
Express suite:                102 passed
Frontend suite:                42 passed
Distinct test total:          464 passed
Frontend lint:                 passed
Frontend production build:    passed
Python compile/config checks:  passed
Git diff check:                passed
Working tree:                  modified; remediation not committed
```

`codex-final-verification.txt` remains the earlier runtime-smoke record with
307 Python, 97 server, and 27 frontend tests (431 distinct). The current
canonical counts above include the later closure and readability-contract tests
and are the source of truth.

The final local runtime record in `codex-final-verification.txt` confirmed the
production Express smoke, Now and Today payloads, all four direct SPA routes,
and the structured JSON API 404. Configured PostgreSQL worker evidence showed:

- zero duplicate successful source hours;
- zero duplicate horizons;
- zero orphan predictions;
- zero incomplete successful runs;
- exactly `[1, 3, 6, 12, 24]` for every successful run;
- 12 elapsed predictions backfilled from finalized source actuals;
- 2 elapsed predictions classified as source not finalized;
- zero backfill defects.

The subsequent console-command closure regenerated and executed
`.venv/bin/wattwise-worker` under Python 3.14.5. Its first cycle created run 9
for a newer source hour and its immediate second cycle reused run 9 for that
same `generated_at`.

---

## Known Limitations

- The first real Railway deployment has not yet been completed.
- Every Railway gate remains **NOT VERIFIED** until supported by real logs.
- Railway PostgreSQL migrations still require cloud evidence on a new database.
- The remote model release installation still requires cloud evidence.
- Two scheduled Railway worker cycles still require production observation.
- Classification performance is weaker than regression performance, particularly at longer horizons.
- Active classification intentionally remains `legacy-unversioned`; the failed
  challenger derived `157.885 $/MWh`, but the active threshold remains
  `170.77 $/MWh`.
- The +24 h regression output is a persistence reference based on
  `actual_price_lag_1h`, not an independent learned forecast.
- Forecasts exist only at the five authentic horizons; intermediate hourly
  values are not fabricated.
- Model lifecycle state and candidate artifacts do not yet have durable cloud storage.
- Automated cloud lifecycle execution is intentionally deferred.
- Model promotion remains manual by design.
- WattWise provides decision support and does not guarantee electricity cost savings.

---

## Deployment Status

### Completed

- local application development;
- complete API;
- complete bilingual frontend;
- PostgreSQL persistence;
- migration definitions and local migration tests;
- idempotent hourly worker;
- runtime pinning;
- Railway web configuration;
- Railway worker configuration;
- active model registry;
- model release installer;
- manual promotion and rollback;
- controlled local lifecycle;
- canonical local automated verification;
- production Express, Now, Today, SPA-route, and structured API 404 smoke tests;
- configured-PostgreSQL worker execution and same-source-hour idempotence;
- exact five-horizon persistence and actual-price backfill verification;
- local Python 3.14 `wattwise-worker` console-command resolution.

### Remaining

- Railway PostgreSQL provisioning — **NOT VERIFIED**;
- forward migrations on a fresh Railway database — **NOT VERIFIED**;
- one-time historical Railway database seed — **NOT VERIFIED**;
- production environment variables — **NOT VERIFIED**;
- hosted release download and SHA-256 validation — **NOT VERIFIED**;
- production model installation — **NOT VERIFIED**;
- web healthcheck, public Now/Today APIs, and direct routes — **NOT VERIFIED**;
- first and second scheduled worker cycles — **NOT VERIFIED**;
- duplicate-run, five-horizon, observed-price backfill, and cron-duration gates — **NOT VERIFIED**.

---

## Documentation


README.md is the canonical tracked project documentation.

Local project notes and generated outputs under `docs/`, `reports/`, `models/`, and `context_exports/` remain local-only and are not tracked by Git.

---

## License

MIT License.
