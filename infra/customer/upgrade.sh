#!/usr/bin/env bash
# Upgrades a customer installation to the latest Rastro (docs/customer-deployment.md, section 2.2), from the
# repository root:
#
#   infra/customer/upgrade.sh <domain> [<domain> ...]            # for example: infra/customer/upgrade.sh energia
#   infra/customer/upgrade.sh --dry-run <domain> [<domain> ...]  # says what it would do, changes nothing
#   infra/customer/upgrade.sh --no-restart <domain> ...          # steps 1-3 only: restart later, in a maintenance window
#
# 1. A backup first (backup.sh), so there is always a way back.
# 2. What people changed while using Rastro (state.tar.gz's paths: linking/, mappings/, approvals, experiment logs)
#    is kept in a local commit; any other uncommitted change stops the upgrade.
# 3. git pull (a merge); a conflict stops it, with the backup to go back to.
# 4. Rebuilds the images, starts the services, the users (setup.sh), and checks: check.py and, for each domain,
#    check_domain.py (every section of the app as the read-only users).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${RASTRO_ENV_FILE:-$ROOT/.env}"
DRY="" NO_RESTART=""
[ "${1:-}" = "--dry-run" ] && { DRY=1; shift; }
[ "${1:-}" = "--no-restart" ] && { NO_RESTART=1; shift; }
[ $# -gt 0 ] || { echo "Usage: infra/customer/upgrade.sh [--dry-run] <domain> [<domain> ...]"; exit 1; }
compose() { docker compose --env-file "$ENV_FILE" -f "$ROOT/infra/docker-compose.yml" \
                           -f "$ROOT/infra/docker-compose.customer.yml" "$@"; }
step() { echo "$1"; [ -z "$DRY" ] || echo "   (dry run: not done)"; }
cd "$ROOT"

STATE=(linking mappings)
for path in layer/*/lifecycle.json layer/*/requirements docs/experiments; do [ -e "$path" ] && STATE+=("$path"); done
OTHER="$(git status --porcelain -- . $(printf ":(exclude)%s " "${STATE[@]}") | grep -v '^?? backups/' || true)"
if [ -n "$OTHER" ]; then
  echo "Uncommitted changes outside Rastro's state; commit or undo them first:"; echo "$OTHER"; exit 1
fi
SERVICES=()
for domain in "$@"; do
  service="$(awk -v d="$domain:" '$1 == d {found=1} found && /ontop: \{service:/ {print $3; exit}' \
             layer/dominios.yaml | tr -d ',')"
  [ -n "$service" ] || { echo "«$domain» has no Ontop service in layer/dominios.yaml"; exit 1; }
  SERVICES+=("$service")
done

BACKUP="$ROOT/backups/before-upgrade-$(date +%Y%m%d-%H%M%S)"
step "1. Backup → $BACKUP"
[ -n "$DRY" ] || RASTRO_ENV_FILE="$ENV_FILE" infra/customer/backup.sh "$BACKUP" >/dev/null

step "2. People's changes → a local commit"
if [ -z "$DRY" ] && [ -n "$(git status --porcelain -- "${STATE[@]}")" ]; then
  git add -- "${STATE[@]}"
  git commit -q -m "Rastro state before the upgrade of $(date +%Y-%m-%d): confirmations, approvals, edited mappings"
fi

step "3. git pull: $(git rev-parse --short HEAD) → the latest of $(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo 'its upstream')"
if [ -z "$DRY" ] && ! git pull --no-rebase --no-edit -q; then
  git merge --abort 2>/dev/null || true
  echo "The new version conflicts with this installation's changes; nothing was upgraded."
  echo "Resolve it with the Rastro team. The backup is in $BACKUP."; exit 1
fi

step "4. Images, services (postgres, ${SERVICES[*]}, app, proxy), users and checks"
[ -n "$DRY" ] && exit 0
if [ -n "$NO_RESTART" ]; then
  echo "   Not restarted (--no-restart). When ready: infra/customer/upgrade.sh $* (nothing new to pull, it restarts)"
  exit 0
fi
compose build -q
compose up -d --wait postgres >/dev/null
RASTRO_ENV_FILE="$ENV_FILE" infra/customer/setup.sh >/dev/null
compose up -d --wait postgres "${SERVICES[@]}" app proxy >/dev/null
FAILED=""
RASTRO_ENV_FILE="$ENV_FILE" python3 infra/customer/check.py | tail -1 || FAILED=1
for domain in "$@"; do
  compose exec -T -w /app app python /app/check_domain.py "$domain" 2>&1 | grep "view:" || FAILED=1
done
if [ -n "$FAILED" ]; then
  echo "A check failed after the upgrade. To go back: git reset --hard ORIG_HEAD, then"
  echo "infra/customer/restore.sh $BACKUP and infra/customer/install.sh $*"; exit 1
fi
echo "Upgraded to $(git rev-parse --short HEAD); every check passed. Backup kept in $BACKUP."
