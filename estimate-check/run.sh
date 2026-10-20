#!/bin/sh
# One evening run: check the quotes saved today but not yet sent, and rebuild the dashboard for the morning.
# Schedule it each weekday evening (cron, or a timer job on a server you control), for example:
#   30 18 * * 1-5 /srv/pathmode-playbooks/estimate-check/run.sh >> /srv/estimating/cron.log 2>&1
# Settings come from the environment:
#   ANTHROPIC_API_KEY, or PLAYBOOK_PROVIDER=openai OPENAI_API_KEY=... PLAYBOOK_MODEL=...   the AI model, for the notes
#                  (without a key it still runs, and code writes every note)
#   DATA  the folder your ERP and shop-floor exports land in: quotes-to-check.csv (today's unsent quotes, filtered
#         by the export), quote-hours.csv, job-history.csv, shop-rates.csv. Read only.
#   OUT   where the dashboard and lists go: a folder only the estimating team and the general manager can open
set -eu
python3 "$(dirname "$0")/estimate_check.py" --data "$DATA" --out "$OUT"
