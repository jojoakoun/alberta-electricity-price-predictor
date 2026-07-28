# Project Status

## Current milestone

The architecture cleanup and application feature work are complete and verified.

Verified results before this documentation update:

- 520 authorized Python tests passed;
- 25 server test suites and 134 server tests passed;
- 19 client test files and 65 client tests passed;
- frontend lint reported zero warnings and zero errors;
- the production client build succeeded;
- Git whitespace verification passed.

Protected final-evaluation tests were intentionally not executed.

## Completed work

- architecture responsibility cleanup;
- shared column contract centralization;
- lifecycle promotion ownership;
- worker naming and deployment entry-point normalization;
- current recommendation and Today timeline UX;
- near-zero electricity-price presentation;
- anonymous public analytics ingestion;
- private analytics summary and reset;
- `analytics_events` migration;
- test alignment with current architecture;
- clean documentation set and visual study manual.

## Current operational state

The code foundation is ready to be committed. Generated model, report, and
prediction outputs will then be deliberately cleaned and reconstructed before
Railway deployment.

## Next phase — fresh reconstruction

```text
commit verified code and documentation
  → create production-preparation branch
  → remove generated data/reports/models safely
  → reset local application tables
  → run make rebuild
  → review all model and decision reports
  → run make activate after approval
  → run make sync
  → verify local product behaviour
```

## Following phase — Railway deployment

Deployment starts only after:

- fresh reconstruction succeeds;
- metrics and decision behaviour are reviewed;
- lifecycle comparison succeeds;
- promotion is explicitly approved;
- an active release and fresh prediction run exist;
- migrations and secrets are prepared.
