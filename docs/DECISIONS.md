# Architecture Decisions

## D-01 — One shared column contract

Shared column names, supported horizons, model feature lists, and training
requirements are defined in:

`src/electricity_predictor/contracts/columns.py`

Feature behavior remains in the feature modules.

## D-02 — One Python dependency file

All Python runtime, research, and test packages are pinned in:

`requirements.txt`

`pyproject.toml` remains responsible for packaging and installed commands.

## D-03 — Canonical Makefile commands

The Makefile exposes 49 canonical targets.

Compatibility aliases and individual algorithm shortcuts were removed.

Research algorithms remain executable through their Python modules and approved
research orchestration.

## D-04 — No destructive reset shortcut

The combined local reset command was removed.

Database cleanup remains separately available only through:

```bash
make db-clean CONFIRM=YES
```

## D-05 — Candidate preparation and activation are separate

Training or refitting a candidate does not activate it.

Only lifecycle promotion can write the active model registry.

## D-06 — First activation is explicit

A fresh installation may contain no active model.

The first activation follows the same review and promotion boundary as later
model replacements.

## D-07 — Protected final test isolation

The final regression and classification evaluation tests are excluded from
routine verification.

Protected test results do not influence training, feature design,
hyperparameter tuning, threshold tuning, or candidate selection.

## D-08 — Railway uses direct entry points

The Railway web service uses npm commands directly.

The Railway worker uses the installed `wattwise-worker` command directly.

Deployment does not depend on legacy Makefile aliases.

## D-09 — No model or database side effects during refactoring

Architecture cleanup, documentation updates, and foundation verification must
not:

- train models;
- generate production predictions;
- modify PostgreSQL;
- promote candidates;
- change the active registry;
- push commits.

## D-10 — Documentation is organized by responsibility

The root README provides orientation.

Detailed truth is separated into architecture, data, lifecycle, development,
deployment, project status, and decision documents.
