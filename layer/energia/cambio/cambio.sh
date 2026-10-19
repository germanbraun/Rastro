#!/usr/bin/env bash
# Demo de cambio del dominio de petróleo y gas: simula que la Secretaría de Energía publica una
# versión nueva del Capítulo IV y muestra dónde se arregla.
#
#   layer/energia/cambio/cambio.sh probar          las queries guardadas, sin Rastro y con Rastro
#   layer/energia/cambio/cambio.sh renombrar       acto 1: prod_pet pasa a llamarse petroleo
#   layer/energia/cambio/cambio.sh valores         acto 2: el petróleo pasa a estar en barriles
#   layer/energia/cambio/cambio.sh arreglar <acto> cambia una línea del mapeo y reinicia Ontop
#   layer/energia/cambio/cambio.sh deshacer        deja la base y el mapeo como estaban
#   layer/energia/cambio/cambio.sh registrar       corre los dos actos y guarda el resultado
#                                                  para la app (resultado.json, en esta carpeta)
#
# Como en oncología, el mapeo lee el petróleo y el gas de la tabla original del Capítulo IV: el
# arreglo es una línea de mappings/energia.r2rml.ttl y reiniciar Ontop.
# Se corre desde cualquier carpeta del repo. Siempre terminar con "deshacer".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MAPPING="$ROOT/mappings/energia.r2rml.ttl"
ORIGINAL="       sum(p.prod_pet) AS petroleo_m3, sum(p.prod_gas) AS gas_mm3"
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
sql() { compose exec -T postgres psql -U rastro -v ON_ERROR_STOP=1 -q -c "$1"; }

# Cambia la línea del mapeo que suma el petróleo de cada pozo
set_line() {
  python3 - "$MAPPING" "$1" <<'PY'
import re, sys
path, new = sys.argv[1:]
text = open(path).read()
line = re.search(r"       sum\(p\.[^\n]*\) AS petroleo_m3, sum\(p\.prod_gas\) AS gas_mm3", text).group(0)
open(path, "w").write(text.replace(line, new))
PY
}

restart_ontop() {
  echo "Reiniciando Ontop..."
  compose restart ontop-energia >/dev/null
  for _ in $(seq 90); do
    if [ "$(docker inspect -f '{{.State.Health.Status}}' "$(compose ps -aq ontop-energia)" 2>/dev/null)" = "healthy" ]; then
      echo "Ontop listo."; return
    fi
    sleep 2
  done
  echo "Ontop no levantó en 3 minutos (es lo esperado si la fuente cambió y el mapeo no). Últimas líneas del log:"
  compose logs --tail 5 ontop-energia
}

has_column() {
  compose exec -T postgres psql -U rastro -tAc \
    "SELECT 1 FROM information_schema.columns WHERE table_schema='capitulo4' AND table_name='produccion' AND column_name='$1'"
}

case "${1:-}" in
  probar)
    compose run --rm -T layer-eval python /layer/energia/cambio/probar.py ${2:+--guardar "$2"} ;;
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
    sql "ALTER TABLE capitulo4.produccion RENAME COLUMN prod_pet TO petroleo"
    echo "Hecho: capitulo4.produccion.prod_pet ahora se llama petroleo." ;;
  valores)
    sql "UPDATE capitulo4.produccion SET prod_pet = prod_pet * 6.2898"
    echo "Hecho: el petróleo ahora está en barriles." ;;
  arreglar)
    case "${2:-}" in
      renombrar) set_line "       sum(p.petroleo) AS petroleo_m3, sum(p.prod_gas) AS gas_mm3" ;;
      valores)   set_line "       sum(p.prod_pet / 6.2898) AS petroleo_m3, sum(p.prod_gas) AS gas_mm3" ;;
      *) echo "Uso: cambio.sh arreglar renombrar|valores"; exit 1 ;;
    esac
    echo "Mapeo cambiado (una línea):"
    grep -n "AS petroleo_m3" "$MAPPING" || true
    restart_ontop ;;
  deshacer)
    if [ -n "$(has_column petroleo)" ]; then sql "ALTER TABLE capitulo4.produccion RENAME COLUMN petroleo TO prod_pet"; fi
    # Si el petróleo de 2025 suma más de 100 millones, está en barriles: vuelve a m³
    sql "UPDATE capitulo4.produccion SET prod_pet = prod_pet / 6.2898 WHERE (SELECT sum(prod_pet) FROM capitulo4.produccion) > 100000000"
    set_line "$ORIGINAL"
    restart_ontop
    echo "Todo como estaba." ;;
  *)
    sed -n '2,15p' "$0"; exit 1 ;;
esac
