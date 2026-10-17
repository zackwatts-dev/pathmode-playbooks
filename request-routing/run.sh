#!/bin/sh
# Every few minutes: route whatever has come in. Settings from the environment:
#   OPENAI_API_KEY, PLAYBOOK_PROVIDER=openai, PLAYBOOK_MODEL  the AI model that reads each request against the policy
#   REQUESTS  requests.csv (new requests), people.csv and policy.md
#   OUT       dashboard.html for the office; payroll.html must be readable by payroll only, safety.html by the
#             safety officer only, office-manager.html by the office manager only
set -eu
python3 "$(dirname "$0")/request_routing.py" --data "$REQUESTS" --out "$OUT"
