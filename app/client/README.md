# WattWise Client

The client is a React application built with Vite.

## Commands

Run from the repository root:

```bash
npm --prefix app/client test -- --run
npm --prefix app/client run lint
npm --prefix app/client run build
```

Start the complete local application with:

```bash
make dev
```

## Structure

- `src/pages/`: application pages
- `src/components/`: reusable UI components
- `src/layout/`: page layout and navigation
- `src/api/`: API clients
- `src/domain/`: client-side business interpretation
- `src/i18n/`: English and French wording
- `src/styles/`: responsive application styles

## API

Development requests are proxied to the Express API.

The main application endpoints are:

- `/api/v1/health`
- `/api/v1/now`
- `/api/v1/today`

Backend prices use dollars per megawatt-hour. The frontend may convert values
for consumer-facing display where the interface explicitly requires it.
