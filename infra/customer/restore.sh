#!/usr/bin/env bash
# Restores a backup made by backup.sh, from the repository root:
#
#   infra/customer/restore.sh <folder> --check    # restores into a temporary database, compares it and drops it;
#                                                 # nothing in use is touched
#   infra/customer/restore.sh <folder>            # replaces the database and the state files with the backup
#
# Both check the files against SHA256SUMS first. The real restore asks to type the folder's name, stops the services
# that read the database while it runs, and starts them again. .env is not restored: decrypt env.enc by hand.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${RASTRO_ENV_FILE:-$ROOT/.env}"
set -a; source "$ENV_FILE"; set +a
BACKUP="${1:?Usage: infra/customer/restore.sh <folder> [--check]}"
MODE="${2:-}"
compose() { docker compose --env-file "$ENV_FILE" -f "$ROOT/infra/docker-compose.yml" "$@"; }
psql_() { compose exec -T postgres psql -U "${PG_USER:-rastro}" -v ON_ERROR_STOP=1 -qAt "$@"; }

echo "1. Files"
(cd "$BACKUP" && while read -r sum file; do
  [ "$(openssl dgst -sha256 -r "$file" | cut -d' ' -f1)" = "$sum" ] || { echo "  $file does not match its checksum"; exit 1; }
done < SHA256SUMS)
echo "  they match SHA256SUMS"

tables() { psql_ -d "$1" -c "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema')"; }
loads() { psql_ -d "$1" -c "SELECT count(*) FROM rastro_meta.load_run"; }

if [ "$MODE" = "--check" ]; then
  CHECK="rastro_check_$(date +%s)"
  echo "2. Restoring into a temporary database, $CHECK"
  psql_ -d "${PG_DB:-rastro}" -c "CREATE DATABASE $CHECK"
  trap 'psql_ -d "${PG_DB:-rastro}" -c "DROP DATABASE IF EXISTS $CHECK" >/dev/null' EXIT
  compose exec -T postgres pg_restore -U "${PG_USER:-rastro}" -d "$CHECK" --no-owner < "$BACKUP/database.dump"
  echo "3. Compared with the database in use (it may have changed since the backup)"
  echo "  tables: backup $(tables "$CHECK"), in use $(tables "${PG_DB:-rastro}")"
  echo "  load records: backup $(loads "$CHECK"), in use $(loads "${PG_DB:-rastro}")"
  echo "  state files: $(tar -tzf "$BACKUP/state.tar.gz" | grep -vc '/$')"
  echo "The backup restores. The temporary database is dropped."
  exit 0
fi

echo "2. This replaces the database «${PG_DB:-rastro}» and the state files (linking/, mappings/, approvals, logs)"
echo "   with the backup in $BACKUP."
read -r -p "   Type the folder's name ($(basename "$BACKUP")) to continue: " answer
[ "$answer" = "$(basename "$BACKUP")" ] || { echo "Nothing was changed."; exit 1; }
READERS="$(compose ps --services --status running | grep -E '^(app|ontop.*|proxy)$' || true)"
[ -z "$READERS" ] || compose stop $READERS >/dev/null
compose exec -T postgres pg_restore -U "${PG_USER:-rastro}" -d "${PG_DB:-rastro}" --clean --if-exists --no-owner \
  < "$BACKUP/database.dump"
tar -xzf "$BACKUP/state.tar.gz" -C "$ROOT"
[ -z "$READERS" ] || compose start $READERS >/dev/null
echo "Restored. Then: infra/customer/setup.sh (users and passwords) and python3 infra/customer/check.py."
