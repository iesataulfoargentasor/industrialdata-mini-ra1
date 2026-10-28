#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d --no-build --pull never --wait db
docker compose run --rm --no-deps simulator
docker compose up -d --no-build --pull never --wait dashboard notebook
echo 'Jupyter: http://localhost:18889/tree · Panel: http://localhost:18501'
echo 'Empieza por 00_Abrir_la_fabrica.ipynb. El pipeline se ejecuta en el cuaderno 04.'
