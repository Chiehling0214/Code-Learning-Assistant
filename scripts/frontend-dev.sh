#!/usr/bin/env bash
# Run the frontend dev server locally (outside Docker).
set -euo pipefail

cd "$(dirname "$0")/../frontend"

[ -f .env ] || cp .env.example .env
npm install
npm run dev
