#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
[ -f .env ] || cp .env.example .env
docker compose config -q
docker compose build
docker compose pull db
echo 'Preparado. Antes de clase: bash iniciar.sh'
