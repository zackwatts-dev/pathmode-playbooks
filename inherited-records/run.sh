#!/bin/sh
# Once per batch of inherited records: read the tickets, match them to your records, and write the import files
# and the review list. Settings from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model that reads each ticket
#   RECORDS   rimview-tickets.csv, plus your summit-customers.csv, summit-sites.csv and summit-equipment.csv
#   OUT       merge/ (the import files), review.csv and dashboard.html; nothing is imported until review.csv is cleared
set -eu
python3 "$(dirname "$0")/inherited_records.py" --data "$RECORDS" --out "$OUT"
