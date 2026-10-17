# Request routing

Sends each internal request (approvals, parts, vans, time off, pay questions, safety problems, customer complaints) to the right person, first time, by a policy written in plain words. The AI uses judgment; code holds the lines that can't be left to judgment.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/request-routing/**

## What it does

- **The policy is a plain-words document** (`sample-data/policy.md`): who handles what, with judgment calls in it.
- **The AI reads each request against it** and proposes where it goes, whether it's urgent, any second request in the same message, the amount or percentage asked for, and the exact words that decide it. If it isn't sure, it says so.
- **Code checks what it copied, and holds the lines:**
  - safety words (gas, carbon monoxide, shock, smoke, fire, injury, a fall or near miss) always go to safety, urgent;
  - approvals over $5,000 above a not-to-exceed amount, or discounts over 10%, go to the general manager;
  - nobody approves their own request;
  - pay is private: a request that mentions pay is never shown on the shared page, and goes to payroll, or to the office manager to check;
  - anything unsure, or whose answer fails a check, goes to the office manager.
  Every override is recorded.
- **Response times per queue,** and a dashboard of who has what and what's due first. Payroll has its own page.

## What it doesn't do

Approve, send, forward or change anything.

## Try it

```sh
# Replay a recorded run: a real model's routing (Claude Sonnet 5.5), free
python3 request-routing/request_routing.py --sample --replay request-routing/sample-data/recorded-run.json

# The offline stand-in: no model, so everything but safety goes to the office manager
python3 request-routing/request_routing.py --sample --dry-run
```

## The sample: a week of Summit's requests

From the Summit simulation (`pathmode-corpus/simulation/scripts/playbook_routing.py`): 93 requests from the week of September 22, 2025, by the simulation's real technicians, about real customers and work orders. Seventeen are planted hard cases: safety mentioned in passing, a warranty claim dressed as an approval, a complaint about both the work and the bill, two requests in one message, managers asking to approve their own requests, amounts right at the limit, and a request that tries to give the router instructions. The office staff and the policy are fictional.

The answer key has the right queue and person for every request, whether it's urgent, and any second request.

## Files

| File | What |
|---|---|
| `request_routing.py` | The AI's reading, the checks, the lines code holds, and response times. |
| `routing_page.py` | The office's dashboard and payroll's. |
| `design.md` | The design, in plain words. |
| `plan.md` | The build plan an AI wrote from the design, unedited. |
| `run.sh` | The run every few minutes. |
| `sample-data/` | The requests, people, policy, answer key and recorded run. |
