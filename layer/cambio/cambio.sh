#!/usr/bin/env bash
# Demo de cambio: simula que AACT publica una versión nueva y muestra dónde se arregla.
#
#   layer/cambio/cambio.sh probar              las 20 queries, SQL directo y Rastro
#   layer/cambio/cambio.sh renombrar           acto 1: overall_status pasa a llamarse status
#   layer/cambio/cambio.sh valores             acto 2: TERMINATED pasa a ser Terminated
#   layer/cambio/cambio.sh arreglar <acto>     cambia una línea del mapeo y reinicia Ontop
#   layer/cambio/cambio.sh deshacer            deja la base y el mapeo como estaban
#   layer/cambio/cambio.sh registrar           corre los dos actos y guarda el resultado
#                                              para la app (layer/cambio/resultado.json)
#
# Se corre desde cualquier carpeta del repo. Siempre terminar con "deshacer".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MAPPING="$ROOT/mappings/rastro.r2rml.ttl"
ORIGINAL="SELECT nct_id, brief_title, phase, overall_status, start_date, why_stopped"
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
sql() { compose exec -T postgres psql -U rastro -v ON_ERROR_STOP=1 -q -c "$1"; }

# Cambia la línea del mapeo que lee el estado del ensayo
set_mapping() {
  python3 - "$MAPPING" "$ORIGINAL" "$1" <<'EOF'
import re, sys
path, original, new = sys.argv[1:]
text = open(path).read()
line = re.search(r"SELECT nct_id, brief_title, phase, .*?, start_date, why_stopped", text).group(0)
open(path, "w").write(text.replace(line, new))
EOF
}

restart_ontop() {
  echo "Reiniciando Ontop..."
  compose restart ontop >/dev/null
  for _ in $(seq 60); do
    if [ "$(docker inspect -f '{{.State.Health.Status}}' "$(compose ps -aq ontop)" 2>/dev/null)" = "healthy" ]; then
      echo "Ontop listo."; return
    fi
    sleep 2
  done
  echo "Ontop no levantó en 2 minutos. Últimas líneas del log:"
  compose logs --tail 5 ontop
  echo "Para volver al estado normal: cambio.sh deshacer"
  exit 1
}

has_column() {
  compose exec -T postgres psql -U rastro -tAc \
    "SELECT 1 FROM information_schema.columns WHERE table_schema='aact' AND table_name='studies' AND column_name='$1'"
}

case "${1:-}" in
  probar)
    compose run --rm -T layer-eval python /layer/cambio/probar.py ${2:+--guardar "$2"} ;;
  registrar)
    "$0" probar antes
    "$0" renombrar && "$0" probar renombrar
    "$0" arreglar renombrar && "$0" probar renombrar-arreglado
    "$0" deshacer
    "$0" valores && "$0" probar valores
    "$0" arreglar valores && "$0" probar valores-arreglado
    "$0" deshacer
    "$0" probar despues ;;
  renombrar)
    sql "ALTER TABLE aact.studies RENAME COLUMN overall_status TO status"
    echo "Hecho: aact.studies.overall_status ahora se llama status." ;;
  valores)
    sql "UPDATE aact.studies SET overall_status = initcap(overall_status)"
    echo "Hecho: los estados ahora se escriben Terminated, Completed, Recruiting..." ;;
  arreglar)
    case "${2:-}" in
      renombrar) set_mapping "SELECT nct_id, brief_title, phase, status AS overall_status, start_date, why_stopped" ;;
      valores)   set_mapping "SELECT nct_id, brief_title, phase, upper(overall_status) AS overall_status, start_date, why_stopped" ;;
      *) echo "Uso: cambio.sh arreglar renombrar|valores"; exit 1 ;;
    esac
    echo "Mapeo cambiado (una línea):"
    grep -n "SELECT nct_id, brief_title" "$MAPPING"
    restart_ontop ;;
  deshacer)
    if [ -n "$(has_column status)" ]; then sql "ALTER TABLE aact.studies RENAME COLUMN status TO overall_status"; fi
    sql "UPDATE aact.studies SET overall_status = upper(overall_status) WHERE overall_status <> upper(overall_status)"
    set_mapping "$ORIGINAL"
    restart_ontop
    echo "Todo como estaba." ;;
  *)
    sed -n '2,10p' "$0"; exit 1 ;;
esac
