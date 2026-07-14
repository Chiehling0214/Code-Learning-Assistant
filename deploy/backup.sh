#!/usr/bin/env bash
# Nightly Postgres backup for the production VM.
#
# Dumps the codepath database from the running compose stack into ./backups,
# keeps the last 7 dumps, and (optionally) copies to a GCS bucket when
# BACKUP_GCS_BUCKET is set and gsutil is available.
#
# Install as a cron job (run `crontab -e` on the VM):
#   0 3 * * * cd /opt/codepath && ./deploy/backup.sh >> backups/backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p backups

STAMP="$(date +%Y%m%d-%H%M%S)"
FILE="backups/codepath-${STAMP}.sql.gz"

docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-codepath}" "${POSTGRES_DB:-codepath}" | gzip > "${FILE}"
echo "backup written: ${FILE} ($(du -h "${FILE}" | cut -f1))"

# Keep the 7 most recent dumps.
ls -1t backups/codepath-*.sql.gz | tail -n +8 | xargs -r rm --

# Optional off-VM copy.
if [ -n "${BACKUP_GCS_BUCKET:-}" ] && command -v gsutil >/dev/null 2>&1; then
  gsutil cp "${FILE}" "gs://${BACKUP_GCS_BUCKET}/"
  echo "uploaded to gs://${BACKUP_GCS_BUCKET}/"
fi

# Restore (manual):
#   gunzip -c backups/codepath-YYYYMMDD-HHMMSS.sql.gz | \
#     docker compose -f docker-compose.prod.yml exec -T postgres \
#       psql -U codepath -d codepath
