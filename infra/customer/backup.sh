#!/usr/bin/env bash
# A backup of a Rastro installation (docs/customer-deployment.md, section 2.2), from the repository root:
#
#   infra/customer/backup.sh [folder]        # default: backups/<date-time>/
#
# It keeps what cannot be rebuilt from the repository:
# - database.dump: the whole database (pg_dump, custom format): the loaded sources, the links, the load records
# - state.tar.gz: what people change while using Rastro: the reviewed corrections and their confirmations (linking/),
#   the question approvals (layer/*/lifecycle.json, layer/*/requirements/), mappings edited in the app (mappings/)
#   and the experiment logs (docs/experiments/)
# - env.enc: .env, encrypted with RASTRO_BACKUP_PASSPHRASE; without it, .env is not saved (it holds the passwords)
# - SHA256SUMS: to check the files before restoring (restore.sh does)
#
# RASTRO_ENV_FILE=<file> uses another env file.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${RASTRO_ENV_FILE:-$ROOT/.env}"
set -a; source "$ENV_FILE"; set +a
OUT="${1:-$ROOT/backups/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUT" && chmod 700 "$OUT"
compose() { docker compose --env-file "$ENV_FILE" -f "$ROOT/infra/docker-compose.yml" "$@"; }

echo "1. Database → $OUT/database.dump"
compose exec -T postgres pg_dump -U "${PG_USER:-rastro}" -d "${PG_DB:-rastro}" -Fc > "$OUT/database.dump"

echo "2. What people changed → state.tar.gz"
cd "$ROOT"
STATE=(linking mappings)
for path in layer/*/lifecycle.json layer/*/requirements docs/experiments; do [ -e "$path" ] && STATE+=("$path"); done
tar -czf "$OUT/state.tar.gz" "${STATE[@]}"

echo "3. .env"
if [ -n "${RASTRO_BACKUP_PASSPHRASE:-}" ]; then
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "$ENV_FILE" -out "$OUT/env.enc" -pass env:RASTRO_BACKUP_PASSPHRASE
  echo "  saved, encrypted (decrypt: openssl enc -d -aes-256-cbc -pbkdf2 -in env.enc -out .env)"
else
  echo "  not saved: set RASTRO_BACKUP_PASSPHRASE to keep it, encrypted"
fi

(cd "$OUT" && for f in *; do [ "$f" = SHA256SUMS ] || echo "$(openssl dgst -sha256 -r "$f" | cut -d' ' -f1)  $f"; done > SHA256SUMS)
echo "Backup ready: $OUT ($(du -sh "$OUT" | cut -f1)). Keep it off this machine. Check it: infra/customer/restore.sh $OUT --check"
