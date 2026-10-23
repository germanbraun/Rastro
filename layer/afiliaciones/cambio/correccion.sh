#!/usr/bin/env bash
# One correction, every result: ROR adds the official name of the Garrahan hospital as an alias (a new row in ror.name,
# as its next release would). Measures every saved evaluation query (B, D, C) and cq1-cq3 before, right after the
# source change, and after rebuilding the links; then the guard puts everything back exactly. Approved plan:
# docs/experiments/research-affiliations/change-test-proposal.md. Result: correccion.json.
#
#   layer/afiliaciones/cambio/correccion.sh registrar
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

# All mutations run under the snapshot guard; never overwrite pre-existing edits.
if [ -z "${RASTRO_CHANGE_GUARD:-}" ]; then
  case "${1:-}" in
    registrar) exec python3 "$ROOT/layer/change_guard.py" run correccion afiliaciones ;;
    *) echo "Use registrar (guarded); recover with python3 layer/change_guard.py recover"; exit 1 ;;
  esac
fi
compose() { docker compose -f "$ROOT/infra/docker-compose.yml" "$@"; }
medir() { compose run --rm -T layer-eval python /layer/afiliaciones/cambio/medir.py "$1" 2>/dev/null </dev/null; }
now() { date -u +%s; }

medir antes
t0=$(now)
compose exec -T postgres psql -X -U "${PG_USER:-rastro}" -d "${PG_DB:-rastro}" -v ON_ERROR_STOP=1 -q -c \
  "INSERT INTO ror.name (id, value, types, lang) VALUES ('https://ror.org/051mda743', 'Hospital de Pediatría Prof. Dr. Juan P. Garrahan', 'alias', 'es')"
t1=$(now)
medir fuente
t2=$(now)
compose run --rm afiliaciones-linker >/dev/null
compose restart ontop-afiliaciones >/dev/null
for _ in $(seq 90); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' "$(compose ps -aq ontop-afiliaciones)")" = "healthy" ] && break
  sleep 2
done
t3=$(now)
medir despues
python3 "$ROOT/layer/afiliaciones/cambio/correccion.py" "$((t1 - t0))" "$((t3 - t2))"
