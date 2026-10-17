#!/bin/sh
# Quarterly: segment customers, re-test the predictions, and rebuild both dashboards. Settings from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model that names segments and explains the list
#   EXPORTS   two years of exports up to the quarter's end: customers, sites, agreements, jobs, quotes, invoices, payments
#   OUT       the team's files; OUT/billing (the named late-payment list and scores) must be readable by billing only
set -eu
cutoff=$(date -d "$(date +%Y-%m-01) -1 day" +%F)
python3 "$(dirname "$0")/customer_segments.py" --data "$EXPORTS" --cutoff "$cutoff" --out "$OUT"
