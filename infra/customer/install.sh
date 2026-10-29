#!/usr/bin/env bash
# The customer setup in one command (docs/customer-deployment.md, section 2.2), from the repository root:
#
#   infra/customer/install.sh <domain> [<domain> ...]      # for example: infra/customer/install.sh energia
#
# 1. Fills in .env what the customer setup needs and is missing, never changing a value already there: the database
#    owner's password (only for a new database), the read-only and reader passwords, and a login whose password is
#    shown once (only its hash is kept).
# 2. Starts Postgres, creates the read-only users (setup.sh), starts each domain's Ontop, the app and the login proxy.
# 3. Runs check.py, which says whether every point took effect.
#
# RASTRO_ENV_FILE=<file> uses another env file (to try it without touching .env).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${RASTRO_ENV_FILE:-$ROOT/.env}"
[ $# -gt 0 ] || { echo "Usage: infra/customer/install.sh <domain> [<domain> ...]"; exit 1; }
compose() { docker compose --env-file "$ENV_FILE" -f "$ROOT/infra/docker-compose.yml" \
                           -f "$ROOT/infra/docker-compose.customer.yml" "$@"; }
secret() { openssl rand -hex 16; }
value() { grep -E "^$1=" "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d "'\""; }
add() {   # adds KEY=VALUE only when the key is missing or empty
  if [ -z "$(value "$1")" ]; then
    grep -vE "^$1=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
    printf "%s=%s\n" "$1" "$2" >> "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"
    echo "  $1 set"
  fi
}

# Each domain's Ontop service, from its registry entry (method.ontop.service)
SERVICES=()
for domain in "$@"; do
  service="$(awk -v d="$domain:" '$1 == d {found=1} found && /ontop: \{service:/ {print $3; exit}' \
             "$ROOT/layer/dominios.yaml" | tr -d ',')"
  [ -n "$service" ] || { echo "«$domain» has no Ontop service in layer/dominios.yaml"; exit 1; }
  SERVICES+=("$service")
done

echo "1. $ENV_FILE"
[ -f "$ENV_FILE" ] || cp "$ROOT/.env.example" "$ENV_FILE"
chmod 600 "$ENV_FILE"
if ! docker volume inspect rastro_pgdata >/dev/null 2>&1; then
  if [ "$(value PG_PASSWORD)" = "rastro" ]; then   # the demo default is replaced before the database exists
    sed -i.bak '/^PG_PASSWORD=/d' "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  fi
  add PG_PASSWORD "$(secret)"   # a new database takes it when it is created
elif [ -z "$(value PG_PASSWORD)" ] || [ "$(value PG_PASSWORD)" = "rastro" ]; then
  echo "  ! The database already exists with the demo password; check.py will flag it. Change it with"
  echo "    ALTER ROLE <PG_USER> PASSWORD '...' and then PG_PASSWORD in $ENV_FILE."
fi
add RASTRO_READONLY_PASSWORD "$(secret)"
add RASTRO_READER_PASSWORD "$(secret)"
add RASTRO_LOGIN_USER rastro
LOGIN=""
if [ -z "$(value RASTRO_LOGIN_HASH)" ]; then
  LOGIN="$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-20)"
  add RASTRO_LOGIN_HASH "'$(docker run --rm caddy:2.8.4 caddy hash-password --plaintext "$LOGIN")'"
fi

echo "2. Services: postgres, ${SERVICES[*]}, app, proxy"
compose up -d --wait postgres >/dev/null
RASTRO_ENV_FILE="$ENV_FILE" "$ROOT/infra/customer/setup.sh"
compose up -d --wait postgres "${SERVICES[@]}" app proxy >/dev/null

echo "3. Check"
RASTRO_ENV_FILE="$ENV_FILE" RASTRO_LOGIN_PASSWORD="$LOGIN" python3 "$ROOT/infra/customer/check.py" || true
if [ -n "$LOGIN" ]; then
  echo
  host="$(value RASTRO_HOST || true)"; port="$(value RASTRO_HTTPS_PORT || true)"
  echo "Login: https://${host:-localhost}:${port:-8443}"
  echo "  user $(value RASTRO_LOGIN_USER), password $LOGIN"
  echo "  Shown only now: keep it in the customer's password manager; .env keeps only its hash."
fi
