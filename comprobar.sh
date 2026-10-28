#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose run --rm --no-deps pipeline python -m pytest -q
docker compose run --rm --no-deps pipeline
docker compose run --rm --no-deps pipeline python scripts/comprobar_postgres.py
