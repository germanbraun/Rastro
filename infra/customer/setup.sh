#!/usr/bin/env bash
# The customer setup's database users: creates rastro_readonly and gives every domain's SQL reader the password of
# .env (roles.sql). Run it after starting postgres and before the rest (Ontop logs in as rastro_readonly), and
# again after loading a domain, which creates its readers.
#
#   infra/customer/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${RASTRO_ENV_FILE:-$ROOT/.env}"   # another file only to try the setup without touching .env
set -a; source "$ENV_FILE"; set +a
: "${RASTRO_READONLY_PASSWORD:?set RASTRO_READONLY_PASSWORD in .env}"
: "${RASTRO_READER_PASSWORD:?set RASTRO_READER_PASSWORD in .env}"

# The readers each domain names in layer/dominios.yaml («readers: {B: …, D: …}»)
READERS="$(grep -o 'readers: {B: [a-z_]*, D: [a-z_]*}' "$ROOT/layer/dominios.yaml" \
           | sed -E 's/readers: \{B: ([a-z_]*), D: ([a-z_]*)\}/\1,\2/' | paste -sd, -)"

docker compose --env-file "$ENV_FILE" -f "$ROOT/infra/docker-compose.yml" exec -T postgres \
  psql -U "${PG_USER:-rastro}" -d "${PG_DB:-rastro}" -v ON_ERROR_STOP=1 -q \
       -v readonly_password="$RASTRO_READONLY_PASSWORD" -v reader_password="$RASTRO_READER_PASSWORD" \
       -v readers="$READERS" < "$ROOT/infra/customer/roles.sql"
echo "Database users ready: rastro_readonly, and the readers that exist of: $READERS"
