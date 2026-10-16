#!/usr/bin/env bash
# Carga en el esquema local `aact` los estudios de oncología de AACT.
#
# Oncología = estudios con algún término de condición bajo "Neoplasms" (MeSH C04),
# según browse_conditions de AACT, que ya incluye los ancestros de cada término.
#
# Origen, en este orden:
#   1. AACT_DUMP: ruta a un snapshot descargado de AACT (.zip o .dmp), se restaura
#      en una base temporal `aact_full` y se extrae desde ahí.
#   2. Base de AACT en la nube, con AACT_USER y AACT_PASSWORD (cuenta gratuita).
#
# Se corre con: docker compose run --rm aact-loader
set -euo pipefail

TABLES=(
  studies conditions browse_conditions interventions intervention_other_names
  browse_interventions design_groups design_group_interventions sponsors
  designs eligibilities calculated_values countries
)
ONCOLOGY="SELECT nct_id FROM ctgov.browse_conditions WHERE downcase_mesh_term = 'neoplasms'"

# Conexiones por parámetros y contraseña en PGPASSWORD: las URLs se rompen con
# caracteres como @ o $ en la contraseña, y los errores de psql las imprimen.
DST="host=postgres port=5432 dbname=${PG_DB} user=${PG_USER}"
dst()      { PGPASSWORD="$PG_PASSWORD" psql "$DST" "$@"; }
src()      { PGPASSWORD="$SRC_PASSWORD" psql "$SRC" "$@"; }
src_dump() { PGPASSWORD="$SRC_PASSWORD" pg_dump "$SRC" "$@"; }

if [[ -n "${AACT_DUMP:-}" ]]; then
  dump="/data/raw/${AACT_DUMP}"
  [[ -f "$dump" ]] || { echo "No existe $dump (AACT_DUMP es relativo a data/raw/)"; exit 1; }
  if [[ "$dump" == *.zip ]]; then
    tmp=$(mktemp -d)
    unzip -q -o "$dump" '*.dmp' -d "$tmp"
    dump=$(find "$tmp" -name '*.dmp' | head -1)
  fi
  echo "Restaurando $(basename "$dump") en aact_full (puede tardar varios minutos)..."
  dst -qc "DROP DATABASE IF EXISTS aact_full" -c "CREATE DATABASE aact_full"
  SRC="host=postgres port=5432 dbname=aact_full user=${PG_USER}"
  SRC_PASSWORD="$PG_PASSWORD"
  PGPASSWORD="$SRC_PASSWORD" pg_restore --no-owner --no-privileges --schema=ctgov -j 4 -d "$SRC" "$dump" || true
  VERSION="snapshot $(basename "$dump")"
elif [[ -n "${AACT_USER:-}" && -n "${AACT_PASSWORD:-}" ]]; then
  SRC="host=aact-db.ctti-clinicaltrials.org port=5432 dbname=aact user=${AACT_USER} sslmode=require"
  SRC_PASSWORD="$AACT_PASSWORD"
  VERSION="cloud $(date -u +%F)"
else
  echo "Falta el origen: definí AACT_USER y AACT_PASSWORD en .env, o AACT_DUMP con un snapshot en data/raw/."
  exit 1
fi

echo "Origen: ${VERSION}"
n_src=$(src -Atc "SELECT count(DISTINCT nct_id) FROM ($ONCOLOGY) o")
echo "Estudios de oncología en origen: ${n_src}"

# Esquema: mismas tablas que AACT, renombrando ctgov -> aact
echo "Creando esquema aact..."
dump_args=()
for t in "${TABLES[@]}"; do dump_args+=(-t "ctgov.$t"); done
src_dump --schema-only --no-owner --no-privileges "${dump_args[@]}" \
  | sed -e 's/\bctgov\./aact./g' -e '/^SET transaction_timeout/d' \
  > /tmp/aact-schema.sql
dst -q -v ON_ERROR_STOP=1 \
  -c "DROP SCHEMA IF EXISTS aact CASCADE" -c "CREATE SCHEMA aact" -f /tmp/aact-schema.sql

# Datos: studies primero, por las claves foráneas
for t in "${TABLES[@]}"; do
  printf "  %-28s" "$t"
  src -qc "\\copy (SELECT * FROM ctgov.$t WHERE nct_id IN ($ONCOLOGY)) TO STDOUT" \
    | dst -q -v ON_ERROR_STOP=1 -c "\\copy aact.$t FROM STDIN"
  n=$(dst -Atc "SELECT count(*) FROM aact.$t")
  dst -qc "INSERT INTO rastro_meta.load_run (source_id, version, table_name, row_count)
                   VALUES ('aact', '$VERSION', 'aact.$t', $n)"
  printf "%10s filas\n" "$n"
done

dst -qc "ANALYZE"
if [[ -n "${AACT_DUMP:-}" ]]; then dst -qc "DROP DATABASE aact_full"; fi

echo "Listo."
dst -c "SELECT * FROM rastro_meta.source_counts WHERE source_id = 'aact'"
