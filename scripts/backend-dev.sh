#!/usr/bin/env bash
# Run the backend locally (outside Docker). Requires a reachable PostgreSQL and
# a populated backend/.env.
set -euo pipefail

cd "$(dirname "$0")/../backend"

python -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port "${BACKEND_PORT:-8000}"
