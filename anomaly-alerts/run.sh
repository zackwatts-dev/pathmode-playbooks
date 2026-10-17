#!/bin/sh
# One weekly run: flag last week's completed jobs, investigate the top flags, rebuild the dashboard.
# Schedule it after the nightly exports (cron, or a timer job). Settings come from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model that explains flags
#   EXPORTS   the folder the systems export to (jobs, visits, time entries, parts, notes, invoices, portal)
#   OUT       where the dashboard and digests go: only the controller and service manager can open it
set -eu
here=$(dirname "$0")
start=$(date -d "last monday -7 days" +%F)
end=$(date -d "last sunday" +%F)
python3 "$here/anomaly_alerts.py" --data "$EXPORTS" --start "$start" --end "$end" --out "$OUT"
