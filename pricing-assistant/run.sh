#!/bin/sh
# Price the day's repair requests: one quote draft each, for a person to send.
# Run it hourly, or when a diagnosis comes in. Settings come from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model
#   DATA   the folder with the price book, tasks, guidance and today's repair requests
#   OUT    where the drafts and dashboard go: only the estimating team can open it
# Negotiation runs here only against the simulated buyers. To use it with real customers, feed each
# customer's reply in place of the simulator (see negotiate() in pricing_assistant.py), with --drafts.
set -eu
python3 "$(dirname "$0")/pricing_assistant.py" --data "$DATA" --out "$OUT"
