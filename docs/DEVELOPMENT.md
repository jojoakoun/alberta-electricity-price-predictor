# Development

## Working directory

Run every command from the repository root. Use npm workspace prefixes instead
of changing directories.

```bash
npm --prefix app/server test
npm --prefix app/client test
```

## Setup

```bash
make install
```

Dependencies are owned by:

- `requirements.txt` — pinned Python dependencies;
- `pyproject.toml` — Python package and installed commands;
- `app/server/package.json` — server dependencies and scripts;
- `app/client/package.json` — client dependencies and scripts.

## Daily workflow

```text
inspect status
  → make start
  → make check
  → make verify
  → inspect git diff
  → commit
```

Commands:

```bash
make status
make start
make check
make verify
make stop
```

## Verification contract

`make verify` runs:

- Python configuration and compilation checks;
- authorized Python tests;
- Express/Jest tests;
- React/Vitest tests;
- frontend linting;
- frontend production build;
- Git whitespace validation.

Protected final-evaluation tests remain excluded.

## Code placement

| Responsibility | Path |
|---|---|
| Shared contracts | `src/electricity_predictor/contracts/` |
| Data ingestion and normalization | `src/electricity_predictor/data/` |
| Feature calculations | `src/electricity_predictor/features/` |
| Research modeling | `src/electricity_predictor/modeling/` |
| Active-model serving | `src/electricity_predictor/serving/` |
| Scheduled predictions | `src/electricity_predictor/worker/` |
| Express API | `app/server/` |
| React interface | `app/client/` |

## Comments

Use short English comments only where they clarify architecture, validation,
security, business rules, database behaviour, or non-obvious decisions. Avoid
comments that merely repeat syntax.

## Safety

- Do not run destructive database operations without explicit confirmation.
- Do not train or promote models during an architecture-only change.
- Do not run protected final evaluations during normal maintenance.
- Do not commit `.env`, generated models, reports, caches, or local databases.
