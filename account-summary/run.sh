#!/bin/sh
# The first Monday after a quarter closes: every branch manager's briefing, and any requests waiting. Settings:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model that writes the briefings
#   EXPORTS   the quarter's exports (customers, sites, jobs, quotes, invoices, payments, emails), users.csv
#             and requests.csv
#   OUT       dashboard.html is the general manager's; dashboard-<user>.html must be readable by that person only
set -eu
python3 "$(dirname "$0")/account_summary.py" --data "$EXPORTS" --out "$OUT"
