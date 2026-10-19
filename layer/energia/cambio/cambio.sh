#!/usr/bin/env bash
# Demo de cambio del dominio de petróleo y gas: simula que la Secretaría de Energía publica una
# versión nueva del Capítulo IV y muestra dónde se arregla.
#
#   layer/energia/cambio/cambio.sh probar          las queries guardadas, sin Rastro y con Rastro
#   layer/energia/cambio/cambio.sh renombrar       acto 1: prod_pet pasa a llamarse petroleo
#   layer/energia/cambio/cambio.sh valores         acto 2: el petróleo pasa a estar en barriles
#   layer/energia/cambio/cambio.sh arreglar <acto> cambia una línea de los enlaces y los vuelve a armar
#   layer/energia/cambio/cambio.sh deshacer        deja la base y los enlaces como estaban
#   layer/energia/cambio/cambio.sh registrar       corre los dos actos y guarda el resultado
#                                                  para la app (resultado.json, en esta carpeta)
#
# En este dominio los mapeos leen las tablas de enlaces de Rastro (esquema energia), que arma
# linking/energia/links.sql: el arreglo es una línea de ese archivo y volver a armar los enlaces.
# Se corre desde cualquier carpeta del repo. Siempre terminar con "deshacer".
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LINKS="$ROOT/linking/energia/links.sql"
ORIGINAL="       sum(p.prod_pet) AS petroleo_m3, sum(p.prod_gas) AS gas_mm3"
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
sql() { compose exec -T postgres psql -U rastro -v ON_ERROR_STOP=1 -q -c "$1"; }

# Cambia la línea de los enlaces que suma el petróleo de cada pozo
set_line() {
  python3 - "$LINKS" "$1" <<'PY'
import re, sys
path, new = sys.argv[1:]
text = open(path).read()
line = re.search(r"       sum\(p\.[^\n]*\) AS petroleo_m3, sum\(p\.prod_gas\) AS gas_mm3", text).group(0)
open(path, "w").write(text.replace(line, new))
PY
}

relink() {
  echo "Volviendo a armar los enlaces de Rastro..."
  compose run --rm -T energia-linker >/dev/null 2>&1 && echo "Enlaces listos." \
    || echo "Los enlaces no se pudieron armar (es lo esperado si la fuente cambió y el enlace no)."
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
    "$0" renombrar && relink && "$0" probar renombrar
    "$0" arreglar renombrar && "$0" probar renombrar-arreglado
    "$0" deshacer
    "$0" valores && relink && "$0" probar valores
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
    echo "Enlaces cambiados (una línea):"
    grep -n "AS petroleo_m3" "$LINKS" || true
    relink ;;
  deshacer)
    if [ -n "$(has_column petroleo)" ]; then sql "ALTER TABLE capitulo4.produccion RENAME COLUMN petroleo TO prod_pet"; fi
    # Si el petróleo de 2025 suma más de 100 millones, está en barriles: vuelve a m³
    sql "UPDATE capitulo4.produccion SET prod_pet = prod_pet / 6.2898 WHERE (SELECT sum(prod_pet) FROM capitulo4.produccion) > 100000000"
    set_line "$ORIGINAL"
    relink
    echo "Todo como estaba." ;;
  *)
    sed -n '2,15p' "$0"; exit 1 ;;
esac
