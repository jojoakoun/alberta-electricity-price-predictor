# Development

## Working directory

Run project commands from the repository root.

Do not change directories inside command sequences. Use the workspace prefixes
provided by npm:

```bash
npm --prefix app/server test
npm --prefix app/client test -- --run
```

## Environment

Install all dependencies with:

```bash
make install
```

Python dependency versions are defined in `requirements.txt`.

`pyproject.toml` owns packaging configuration and the installed
`wattwise-worker` command.

Node dependencies remain in the two application workspaces:

- `app/server/package.json`
- `app/client/package.json`

## Verification

The normal repository checks include:

- Python compilation
- authorized Python tests
- Express tests
- React tests
- frontend linting
- frontend production build
- Makefile parsing
- documentation contract checks
- Git whitespace checks

The protected final-evaluation tests are excluded from routine checks.

## Local application

```bash
make dev
```

The local API normally runs on port 8000.

The Vite client normally runs on port 5173 and proxies API requests to the
backend.

Stop local application processes with:

```bash
make stop
```

## Coding boundaries

- Keep shared names in `contracts/`.
- Keep feature calculations in `features/`.
- Keep model research in `modeling/`.
- Keep active-model behavior in `serving/`.
- Keep scheduled prediction work in `worker/`.
- Keep database access behind repositories or dedicated database modules.
- Keep API response wording centralized and ready for translation.
- Add comments only when they clarify architecture, security, business rules,
  database behavior, or non-obvious decisions.

## Safety

Do not run destructive database operations without explicit confirmation.

Do not train, publish, promote, or activate models as a side effect of an
architecture refactor.

Do not execute the protected final-evaluation tests during normal maintenance.
