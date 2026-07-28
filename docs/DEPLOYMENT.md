# Deployment

## Components

```text
Railway project
├── PostgreSQL database
├── Web service
│   ├── Express API
│   └── built React application
└── Scheduled worker
    └── wattwise-worker
```

## Web service

Configuration: `railway.json`

The web build installs server dependencies, installs client build dependencies,
and builds the React application. Production startup applies database migrations
before the Express server starts.

Health endpoint:

`GET /api/v1/health`

## Scheduled worker

Configuration: `railway.worker.json`

The worker installs `requirements.txt` and the local Python package. Railway
invokes the installed command directly:

```text
wattwise-worker
```

The scheduled worker runs hourly. It performs operational synchronization and
prediction generation only. It cannot train or promote a model.

## Docker

`docker-compose.yml` provides local PostgreSQL. Docker credentials in this file
are development-only values and must never be reused in production.

```text
Docker Compose
  → PostgreSQL container
  → local DATABASE_URL
  → server + Python pipeline
```

Persistent production model files require an appropriate Railway volume or a
versioned remote release mechanism shared by the worker that loads them.

## Environment variables

Store production values only in Railway variables. Store local values only in
`.env`. `.env.example` documents variable names but contains no real secrets.

Important variables include:

- `DATABASE_URL`;
- `ANALYTICS_PRIVATE_KEY`;
- production runtime and client-origin settings documented in `.env.example`.

## Required deployment order

```text
verified repository
  → fresh reconstruction
  → report review
  → explicit activation
  → fresh sync
  → versioned active release
  → PostgreSQL migrations
  → web deployment
  → worker deployment
  → endpoint and freshness checks
```

## Production verification

Verify:

- `/api/v1/health` returns healthy;
- `/api/v1/now` returns current data;
- `/api/v1/today` returns all required horizons;
- the worker completes successfully;
- predictions are fresh;
- the active model version is correct;
- all migrations, including `analytics_events`, are applied;
- private analytics rejects missing or invalid keys.

## Deployment prohibition

Deployment must never silently train, select, promote, or activate a model.
