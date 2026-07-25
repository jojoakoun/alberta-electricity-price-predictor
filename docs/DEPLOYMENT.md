# Deployment

## Web application

`railway.json` defines the Railway web service.

The web build installs server dependencies, installs client build dependencies,
and builds the React application.

The deployment runs database migrations before starting the Express server.

The health endpoint is:

```text
/api/v1/health
```

## Worker

`railway.worker.json` defines the scheduled worker.

The worker build installs `requirements.txt` and the local Python package.

The installed command is:

```text
wattwise-worker
```

The Railway worker invokes this command directly. It does not depend on a
Makefile alias.

The worker schedule is hourly.

## Database

The application uses PostgreSQL.

Local PostgreSQL configuration is defined in `docker-compose.yml`.

Production credentials and connection strings must be provided through
environment variables and must not be committed.

## Model releases

An approved model release can be built with:

```bash
make release-build
```

A prepared release can be installed with:

```bash
make models-install
```

The installer supports the approved local registry and configured remote
release metadata.

Deployment must not silently train or promote a model.

## Required deployment sequence

```text
verified repository
  → approved active model
  → versioned model release
  → database migrations
  → web deployment
  → worker deployment
  → health and prediction checks
```

## Production checks

After deployment, verify:

- `/api/v1/health`
- `/api/v1/now`
- `/api/v1/today`
- worker execution status
- prediction freshness
- active model version
- database migration status
