#!/bin/sh
# One scheduled run: copy new email out of quotes@, then sort it, plan the queue and rebuild the dashboard.
# Schedule it every 15 minutes (cron, or a timer job on a server you control). Settings come from the environment:
#   MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET  the read-only mailbox app (see graph_mailbox.py)
#   ANTHROPIC_API_KEY   the AI model (Claude); PLAYBOOK_MODEL to pin a different Claude model
#   MAILBOX   the mailbox address, e.g. quotes@yourcompany.com
#   WORK      a folder on this server, e.g. /srv/quote-intake
#   RECORDS   the folder the ERP exports customers, contacts, customer-parts and open-rfqs to each night, with
#             estimator-hours.csv, which a person keeps current. Read only.
#   OUT       where the dashboard and lists go: a folder only estimating and sales can open
# Deleting saved email, dashboards and recorded answers after 90 days is a separate job: this one never deletes.
set -eu
here=$(dirname "$0")
python3 "$here/graph_mailbox.py" --mailbox "$MAILBOX" --to "$WORK/mail"
python3 "$here/rfq_intake.py" --mailbox "$WORK/mail" --records "$RECORDS" --remember --out "$OUT"
