# Architecture Decisions

## D-01 — One shared column contract

Shared column names, supported horizons, model feature lists, and training
requirements are defined in `src/electricity_predictor/contracts/columns.py`.
Feature behaviour remains in feature modules.

## D-02 — One pinned Python dependency file

Python runtime, research, and test packages are pinned in `requirements.txt`.
`pyproject.toml` owns package metadata and installed commands.

## D-03 — Canonical public Make commands

Primary developer operations are `install`, `start`, `stop`, `check`, `status`,
`verify`, `sync`, `reset`, `rebuild`, and `activate`. Help output groups commands
by normal operational importance. Compatibility aliases are temporary and must
not be used in new automation.

## D-04 — Destructive commands require confirmation

`make reset`, `make db-clean`, and `make analytics-reset` require `CONFIRM=YES`.
The reset preserves the raw source and PostgreSQL schema.

## D-05 — Candidate creation and activation are separate

Training or refitting a candidate never activates it. Only lifecycle promotion
may write the active registry.

## D-06 — First activation is explicit

A fresh installation may contain no active model. The first activation follows
the same review and promotion boundary as later replacements.

## D-07 — Protected final-test isolation

Final regression and classification evaluation tests are excluded from routine
verification. Their results cannot influence training, features, tuning,
thresholds, or candidate selection.

## D-08 — Railway uses direct runtime entry points

The web service uses npm scripts. The worker uses the installed
`wattwise-worker` command. Railway does not depend on compatibility Make aliases.

## D-09 — Architecture work has no ML side effects

Refactoring and documentation updates must not train models, generate production
predictions, promote candidates, or change the active registry.

## D-10 — Anonymous analytics minimizes collected data

Analytics excludes direct personal identifiers, IP addresses, user agents,
location data, and browser fingerprints. Private summaries require a server-side
key.

## D-11 — Database schema changes require migrations

Every table used by repositories, including `analytics_events`, must be created
through a committed migration before deployment.

## D-12 — Documentation has one responsibility per file

The README orients. Specialized documents define architecture, data, lifecycle,
development, deployment, access, operations, status, and decisions. The Study
Manual teaches the entire system and links theory to source functions.
