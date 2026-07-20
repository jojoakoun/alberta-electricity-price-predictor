#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${PROJECT_ROOT}"

cleanup() {
  echo
  echo "Stopping WattWise development servers..."

  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "${SERVER_PID}" 2>/dev/null || true
  fi

  if [[ -n "${CLIENT_PID:-}" ]]; then
    kill "${CLIENT_PID}" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Starting WattWise API at http://127.0.0.1:8000"
npm --prefix app/server run dev &
SERVER_PID=$!

echo "Starting WattWise frontend at http://127.0.0.1:5173"
npm --prefix app/client run dev -- --open &
CLIENT_PID=$!

# macOS Bash does not support `wait -n`.
while kill -0 "${SERVER_PID}" 2>/dev/null &&
      kill -0 "${CLIENT_PID}" 2>/dev/null; do
  sleep 1
done
