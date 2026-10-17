# Request routing

Sends each internal request (approvals, parts, vans, time off, pay questions, safety problems, customer complaints) to the right person, first time, by a policy written in plain words. The AI uses judgment; code holds the lines that can't be left to judgment.

The full playbook, worked through at Summit Mechanical with a value calculator, the design, the plan an AI wrote from it, and a map of the built system: **https://pathmode.com/playbooks/request-routing/**

## What it does

- **The policy is a plain-words document** (`sample-data/policy.md`): who handles what, with judgment calls in it.
- **The AI reads each request against it** and proposes where it goes, whether it's urgent, any second request in the same message, the amount or percentage asked for, and the exact words that decide it. If it isn't sure, it says so.
- **Code checks what it copied, and holds the lines:**
  - safety words (gas, carbon monoxide, shock, smoke, fire, injury, a fall or near miss) always go to safety, urgent. The words, and a few phrases that only look like them ("gas card", "fire station"), are in `sample-data/line-words.txt`, next to the policy; changing them is a reviewed change, like the code;
  - approvals over $5,000 above a not-to-exceed amount, or discounts over 10%, go to the general manager. Code reads every amount and percentage in the request itself (ranges at their upper end, "US$6,200", "5.7k", "$1.2M") and applies the limit to the largest, not just to the one the AI picked, and checks both limits whatever the queue: an NTE request that also asks for 25% off goes to the general manager. An over-limit amount in a request the AI put in another queue still goes to the general manager (or to the office manager, if it isn't clear it's an approval). An approval with an amount code can't read for sure (in words, a rate per month, several amounts that may add up) goes to the office manager, with the reason;
  - nobody approves their own request: it goes up to the general manager, and the general manager's own go to the owner if `people.csv` names one (Queue `owner`), otherwise to the office manager to find someone else;
  - pay is private: the words of a request that mentions pay are never on the shared page or in the shared files, and it goes to payroll, or to the office manager to check. One that's also about safety goes to safety and is still listed under Urgent on the shared page, without its words (the safety officer has them on `safety.html`). No money limit applies to a pay request, so its amounts aren't repeated. A request the AI sends to payroll has to contain a pay word, or it goes to the office manager, still private: "send it to payroll" in a request can't hide it in payroll. The office manager sees the private requests she has to route on her own page, `office-manager.html`;
  - anything unsure, or whose answer fails a check, goes to the office manager.
  Every override is recorded. An answer from the AI that isn't the shape asked for goes to the office manager too, and `people.csv` is checked before anything is routed: every queue needs someone holding it.
- **Response times per queue,** and a dashboard of who has what and what's due first. Payroll has its own page, and so does the safety officer, for safety reports that also mention pay.

## What it doesn't do

Approve, send, forward or change anything.

## Try it

```sh
# Replay a recorded run: a real model's routing (Claude Sonnet 5.5), free
python3 request-routing/request_routing.py --sample --replay request-routing/sample-data/recorded-run.json

# The offline stand-in: no model, so everything but safety goes to the office manager
python3 request-routing/request_routing.py --sample --dry-run
```

## Before you run this on your own data

- **Safety words are a floor, not a full list.** `line-words.txt` catches the common ways of saying it (gas, CO alarm, sparking, smoking, burning, fell, cut himself, slipped off a ladder); other phrasings ("he's dizzy in the boiler room", "the unit is glowing") rest on the AI's reading. Add your trade's words, and check a phrase you add as an exception can't hide a hazard. If the AI is down, only the words send a request to safety; everything else goes to the office manager.
- **Who sent it is only the From field.** A shared tablet, or someone forwarding a manager's request, defeats "nobody approves their own". Give each person their own login before relying on it.
- **Amounts code can't read go to a person, not through.** Amounts in words ("four thousand"), rates ("$4,500/mo"), multiples and several amounts that may add up send an approval to the office manager; code doesn't do the sum. A discount asked for in dollars ("$600 off") has no percentage to check, so it goes to the office manager too.
- **Both limits read the request's own words.** A dollar amount counts against the NTE limit in a discount request only when the request says "NTE" or "not-to-exceed"; a percentage counts against the discount limit in an NTE request only when it says "off" or "discount".
- **Privacy fails safe, so the office manager sees more.** A request is private if it has a pay word or the AI calls it payroll. One the AI calls payroll with no pay word in it (a family matter, or "send it to payroll" planted in a request) goes to the office manager, private, on `office-manager.html`, for her to route by hand. Add your own words to `[private]` so real ones reach payroll directly.
- **The limits, queues and response times are Summit's,** in code (`NTE_LIMIT`, `DISCOUNT_LIMIT`, `QUEUES`, `RESPOND_HOURS`). Each queue has one holder: no deputies, no cover for someone on leave, and payroll staff's own pay questions stay with payroll.
- **The pages are files.** `payroll.html`, `safety.html` and `office-manager.html` must be readable only by payroll, the safety officer and the office manager; the script doesn't control who opens them. Every request, pay questions included, goes to the AI provider.
- **One request per line of `requests.csv`, in English,** and at most one second request in the same message is noticed.

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
| `sample-data/` | The requests, people, policy, the safety and pay words, answer key and recorded run. |
