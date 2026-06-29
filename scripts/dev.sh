#!/usr/bin/env bash
# Start the full local stack via Docker Compose.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found — creating one from .env.example"
  cp .env.example .env
fi

exec docker compose up --build "$@"
