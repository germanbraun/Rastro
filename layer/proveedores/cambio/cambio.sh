#!/usr/bin/env bash
# Demo de cambio del dominio de proveedores: simula que USAspending publica una versión
# nueva y muestra dónde se arregla.
#
#   layer/proveedores/cambio/cambio.sh probar          las 9 queries, sin Rastro y con Rastro
#   layer/proveedores/cambio/cambio.sh renombrar       acto 1: awarding_agency pasa a llamarse agency_name
#   layer/proveedores/cambio/cambio.sh valores         acto 2: los montos pasan a estar en miles de dólares
#   layer/proveedores/cambio/cambio.sh arreglar <acto> cambia una línea del mapeo y reinicia Ontop
#   layer/proveedores/cambio/cambio.sh deshacer        deja la base y el mapeo como estaban
#   layer/proveedores/cambio/cambio.sh registrar       corre los dos actos y guarda el resultado
#                                                      para la app (resultado.json, en esta carpeta)
#
# Se corre desde cualquier carpeta del repo. Siempre terminar con "deshacer".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MAPPING="$ROOT/mappings/proveedores.r2rml.ttl"
AGENCY="SELECT generated_internal_id, award_id, recipient_uei, awarding_agency, awarding_sub_agency,"
AMOUNT="naics_code, amount, start_date, end_date, description"
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
sql() { compose exec -T postgres psql -U rastro -v ON_ERROR_STOP=1 -q -c "$1"; }

# Cambia una línea del mapeo de contratos: la que contiene el patrón $1 pasa a ser $2
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

has_column() {
  compose exec -T postgres psql -U rastro -tAc \
    "SELECT 1 FROM information_schema.columns WHERE table_schema='usaspending' AND table_name='contract' AND column_name='$1'"
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
    if [ -n "$(has_column agency_name)" ]; then sql "ALTER TABLE usaspending.contract RENAME COLUMN agency_name TO awarding_agency"; fi
    # Los montos del recorte superan US$10 millones: si hay menos, están en miles
    sql "UPDATE usaspending.contract SET amount = amount * 1000 WHERE (SELECT min(amount) FROM usaspending.contract) < 10000000"
    set_line "SELECT generated_internal_id, award_id, recipient_uei, [^\n]*awarding_sub_agency," "$AGENCY"
    set_line "naics_code, [^\n]*, start_date, end_date, description" "$AMOUNT"
    restart_ontop
    echo "Todo como estaba." ;;
  *)
    sed -n '2,12p' "$0"; exit 1 ;;
esac
