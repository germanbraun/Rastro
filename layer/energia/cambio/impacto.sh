#!/usr/bin/env bash
# Impacto de un cambio en la fuente: Rastro dice de antemano qué predicciones dependen de una fractura informada;
# se simula que la fuente la corrige, se rearma Rastro, se publica una corrida y se comprueba que cambiaron
# exactamente esas. Después se deja todo como estaba. El resultado queda en impacto.json, que muestra la app.
#
#   layer/energia/cambio/impacto.sh registrar
#
# Tarda unos 15 minutos (el enlazador corre dos veces).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

# All mutations run under a snapshot guard; never overwrite pre-existing edits.
if [ -z "${RASTRO_CHANGE_GUARD:-}" ]; then
  case "${1:-}" in
    registrar) exec python3 "$ROOT/layer/change_guard.py" run impacto ;;
    *) echo "Use registrar (guarded); recover with python3 layer/change_guard.py recover"; exit 1 ;;
  esac
fi
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
sql() { compose exec -T postgres psql -U "${PG_USER:-rastro}" -d "${PG_DB:-rastro}" -v ON_ERROR_STOP=1 -q -c "$1"; }
REGISTRO=4703
CORRECCION=12

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
    python3 "$ROOT/layer/energia/cambio/impacto.py" antes
    sql "UPDATE fractura.fractura SET cantidad_fracturas = cantidad_fracturas + $CORRECCION WHERE id_base_fractura_adjiv = '$REGISTRO'"
    rearmar
    python3 "$ROOT/layer/energia/cambio/impacto.py" despues ;;
  *) echo "Uso: impacto.sh registrar"; exit 1 ;;
esac
