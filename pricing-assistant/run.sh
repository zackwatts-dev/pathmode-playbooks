#!/bin/sh
# Price the day's repair requests: one quote draft each, for a person to send.
# Run it hourly, or when a diagnosis comes in. Settings come from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model
#   DATA   the folder with the price book, tasks, guidance and today's repair requests
#   OUT    where the drafts and dashboard go: only the estimating team can open it
#   REPLIES  optional: a CSV of customers' replies to replacement quotes (Quote, From, Message, Offer).
#            Each gets one checked draft reply for an estimator to send. Never with --autonomous, which is
#            only for the simulated buyers.
set -eu
if [ -n "${REPLIES:-}" ]; then
    python3 "$(dirname "$0")/pricing_assistant.py" --data "$DATA" --out "$OUT" --replies "$REPLIES"
else
    python3 "$(dirname "$0")/pricing_assistant.py" --data "$DATA" --out "$OUT"
fi
