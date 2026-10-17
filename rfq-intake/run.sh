#!/bin/sh
# One scheduled run: copy new email out of quotes@, then sort it and rebuild the dashboard.
# Schedule it every 15 minutes (cron, or a timer job in your cloud). Settings come from the environment:
#   MS_TENANT_ID, MS_CLIENT_ID, MS_CLIENT_SECRET  the read-only mailbox app (see graph_mailbox.py)
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model
#   MAILBOX     the mailbox address, e.g. quotes@yourcompany.com
#   WORK        a folder on this server, e.g. /srv/quote-intake
#   RECORDS     the folder your field-service system exports customers, sites, equipment and contacts to
#   OUT         where the dashboard and lists go: somewhere only the estimating team can open
set -eu
here=$(dirname "$0")
python3 "$here/graph_mailbox.py" --mailbox "$MAILBOX" --to "$WORK/mail"
python3 "$here/rfq_intake.py" --mailbox "$WORK/mail" --records "$RECORDS" --remember --out "$OUT"
