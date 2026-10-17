#!/bin/sh
# One weekly run: check the jobs completed in the last 45 days (most are invoiced days after they're done, so
# a week-only window would check them too early), investigate the flags not reported before, rebuild the dashboards.
# Schedule it after the nightly exports (cron, or a timer job). Settings come from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model that explains flags
#   EXPORTS   the folder the systems export to (jobs, visits, time entries, parts, notes, invoices, portal)
#             (with recipients.csv: Owner,To, the address each owner's digest draft is written to)
#   OUT       where the dashboards, digests and flag-history.csv go. Each owner's files are named for them
#             (-service-manager); give each owner access to their own (see README)
set -eu
here=$(dirname "$0")
start=$(date -d "last monday -7 days" +%F)
end=$(date -d "last sunday" +%F)
python3 "$here/anomaly_alerts.py" --data "$EXPORTS" --start "$start" --end "$end" --lookback 45 --out "$OUT"
