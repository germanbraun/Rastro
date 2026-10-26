#!/usr/bin/env bash
# Una corrección, todos los resultados: saca la participación corregida de Aguada Pichana Este
# (linking/energia/participaciones-revisadas.csv), rearma Rastro y mide qué cambia en Rastro Layer y en
# Rastro Lab; después la vuelve a poner. El resultado queda en correccion.json, que muestra la app.
#
#   layer/energia/cambio/correccion.sh registrar
#
# Tarda unos 15 minutos (el enlazador corre dos veces). Las respuestas guardadas de la evaluación quedan
# como estaban.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

# All mutations run under a snapshot guard; never overwrite pre-existing edits.
if [ -z "${RASTRO_CHANGE_GUARD:-}" ]; then
  case "${1:-}" in
    registrar) exec python3 "$ROOT/layer/change_guard.py" run correccion ;;
    *) echo "Use registrar (guarded); recover with python3 layer/change_guard.py recover"; exit 1 ;;
  esac
fi
CSV="$ROOT/linking/energia/participaciones-revisadas.csv"
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }

rearmar() {
  echo "Rearmando Rastro..."
  compose run --rm energia-linker >/dev/null
  compose restart ontop-energia >/dev/null
  for _ in $(seq 90); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$(compose ps -aq ontop-energia)")" = "healthy" ] && return
    sleep 2
  done
  echo "Ontop no levantó"; exit 1
}

case "${1:-}" in
  registrar)
    python3 "$ROOT/layer/energia/cambio/correccion.py" con
    # Guard snapshots before the first measurement, including all saved answers.
    head -1 "$CSV" > "$CSV.tmp"
    mv "$CSV.tmp" "$CSV"
    rearmar
    python3 "$ROOT/layer/energia/cambio/correccion.py" sin
    python3 "$ROOT/layer/energia/cambio/correccion.py" verificar ;;
  *) echo "Uso: correccion.sh registrar"; exit 1 ;;
esac
