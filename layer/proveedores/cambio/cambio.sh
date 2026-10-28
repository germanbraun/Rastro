#!/usr/bin/env bash
# Suppliers change test: simulates a new USAspending version and shows where it is fixed.
#
#   layer/proveedores/cambio/cambio.sh probar          las 9 queries, sin Rastro y con Rastro
#   layer/proveedores/cambio/cambio.sh renombrar       acto 1: awarding_agency pasa a llamarse agency_name
#   layer/proveedores/cambio/cambio.sh valores         acto 2: los montos pasan a estar en miles de dólares
#   layer/proveedores/cambio/cambio.sh arreglar <acto> cambia una línea del mapeo y reinicia Ontop
#   layer/proveedores/cambio/cambio.sh deshacer        deja la base y el mapeo como estaban
#   layer/proveedores/cambio/cambio.sh registrar       corre los dos actos y guarda el resultado
#                                                      para la app (resultado.json, en esta carpeta)
#
# Runs from any folder of the repo. Only "registrar" and "probar" run on their own: the acts run inside the
# guard (layer/change_guard.py), which snapshots the mapping and the contracts table and restores them exactly.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

if [ -z "${RASTRO_CHANGE_GUARD:-}" ]; then
  case "${1:-}" in
    registrar) exec python3 "$ROOT/layer/change_guard.py" run cambio proveedores ;;
    probar) ;;
    deshacer) exec python3 "$ROOT/layer/change_guard.py" recover ;;
    *) echo "Use registrar (guarded); recover with python3 layer/change_guard.py recover"; exit 1 ;;
  esac
fi
MAPPING="$ROOT/mappings/proveedores.r2rml.ttl"
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
sql() { compose exec -T postgres psql -U rastro -v ON_ERROR_STOP=1 -q -c "$1"; }

# Changes one line of the contracts mapping: the one matching $1 becomes $2
set_line() {
  python3 - "$MAPPING" "$1" "$2" <<'PY'
import re, sys
path, pattern, new = sys.argv[1:]
text = open(path).read()
line = re.search(pattern, text).group(0)
open(path, "w").write(text.replace(line, new))
PY
}

restart_ontop() {
  echo "Reiniciando Ontop de proveedores..."
  compose restart ontop-proveedores >/dev/null
  for _ in $(seq 60); do
    if [ "$(docker inspect -f '{{.State.Health.Status}}' "$(compose ps -aq ontop-proveedores)" 2>/dev/null)" = "healthy" ]; then
      echo "Ontop listo."; return
    fi
    sleep 2
  done
  echo "Ontop no levantó en 2 minutos (es lo esperado si el mapeo no coincide con la base)."
}

case "${1:-}" in
  probar)
    compose run --rm -T layer-eval python /layer/proveedores/cambio/probar.py ${2:+--guardar "$2"} ;;
  registrar)
    "$0" probar antes
    "$0" renombrar && restart_ontop && "$0" probar renombrar
    "$0" arreglar renombrar && "$0" probar renombrar-arreglado
    "$0" deshacer
    "$0" valores && restart_ontop && "$0" probar valores
    "$0" arreglar valores && "$0" probar valores-arreglado
    "$0" deshacer
    "$0" probar despues ;;
  renombrar)
    sql "ALTER TABLE usaspending.contract RENAME COLUMN awarding_agency TO agency_name"
    echo "Hecho: usaspending.contract.awarding_agency ahora se llama agency_name." ;;
  valores)
    sql "UPDATE usaspending.contract SET amount = amount / 1000"
    echo "Hecho: los montos ahora están en miles de dólares." ;;
  arreglar)
    case "${2:-}" in
      renombrar) set_line "SELECT generated_internal_id, award_id, recipient_uei, [^\n]*awarding_sub_agency," \
                   "SELECT generated_internal_id, award_id, recipient_uei, agency_name AS awarding_agency, awarding_sub_agency," ;;
      valores)   set_line "naics_code, [^\n]*, start_date, end_date, description" \
                   "naics_code, amount * 1000 AS amount, start_date, end_date, description" ;;
      *) echo "Uso: cambio.sh arreglar renombrar|valores"; exit 1 ;;
    esac
    echo "Mapeo cambiado (una línea):"
    grep -n "agency_name AS\|amount \* 1000" "$MAPPING" || true
    restart_ontop ;;
  deshacer)
    # Restores the mapping and the contracts table from the guard's snapshot, not with inverse arithmetic
    python3 "$ROOT/layer/change_guard.py" restore-source
    restart_ontop
    echo "Todo como estaba." ;;
  *)
    sed -n '2,12p' "$0"; exit 1 ;;
esac
