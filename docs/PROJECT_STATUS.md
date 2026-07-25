# Project Status

## Foundation

The repository architecture cleanup is complete.

Completed foundation work includes:

- dead-code and unused-import cleanup
- worker naming normalization
- lifecycle ownership separation
- active-registry write isolation
- removal of legacy lifecycle candidate trainers
- shared column contract centralization
- single Python requirements file
- Makefile reduction from 82 targets to 49
- removal of obsolete Makefile aliases
- removal of the destructive reset shortcut
- replacement of obsolete documentation

## Current architecture

```text
live model construction
  → lifecycle candidate preparation
  → lifecycle comparison
  → lifecycle promotion
  → active model registry
```

Candidate preparation does not activate models.

Live refitting does not activate models.

Promotion owns first activation and later active-version changes.

## Application

The repository includes:

- PostgreSQL storage
- Express API
- React frontend
- scheduled Python worker
- Railway web configuration
- Railway worker configuration

## Current operational state

The foundation is ready for a fresh manual rebuild.

Generated training outputs, model reports, and active-model state may be absent
until the rebuild and promotion steps are deliberately executed.

This absence is an expected initial state, not an architecture failure.

## Next phases

### B5 — Manual reconstruction

The developer will explicitly run the approved data and modeling reconstruction
and review its report.

No automatic reconstruction is performed by the cleanup process.

### B6 — Deployment

Deployment begins only after:

- reconstruction succeeds;
- model results are reviewed;
- lifecycle comparison succeeds;
- promotion is explicitly approved;
- an active release is available.
