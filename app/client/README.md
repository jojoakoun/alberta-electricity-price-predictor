# WattWise client

The WattWise browser application is a React frontend written in JavaScript and
JSX. Vite provides the development server, production build, and Vitest test
environment; Oxlint checks the source.

## Commands

Run these commands from the repository root:

```bash
npm --prefix app/client run dev
npm --prefix app/client test
npm --prefix app/client run lint
npm --prefix app/client run build
```

The development server forwards `/api` requests to the local Express service
at `http://127.0.0.1:8000`. The production build targets ECMAScript 2016 and is
served by Express from `app/client/dist`.

## Runtime contracts

Responses from the Now and Today APIs are validated at the network boundary.
The Today API owns price comparison and best-time selection; the browser only
renders those decisions. The +24-hour persistence reference remains visible
for context but cannot be highlighted as a savings opportunity.
