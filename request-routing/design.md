# Design: request routing for Summit Mechanical

## The problem

Summit's technicians and office staff send internal requests all day, by form, email and text: approvals to go over a job's not-to-exceed amount, discounts a customer is asking for, parts, van problems, tablet trouble, time off, pay questions, warranty claims, customer complaints. Most land with whoever happens to read them first, who forwards them, sometimes to the wrong person. Approvals wait while a customer stands next to a technician. A safety problem mentioned at the end of a note about something else gets read on Monday. A question about someone's pay gets forwarded to three people. And who approves what (how big an amount a service manager can approve, who approves a manager's own request) lives in people's heads.

## What it does

1. **The routing policy is written down in plain words** ("Who handles what"): guidance a new office hire could follow, with judgment calls in it, not a rulebook.
2. **The AI reads each request against the policy** and proposes where it goes, whether it's urgent, any second request in the same message, the amount or percentage asked for (as written), and the exact words that decide it. If it isn't sure, it says so.
3. **Code checks what the AI copied** is really in the request, and then **holds the lines the policy can't leave to judgment:**
   - anything with a safety word (gas, carbon monoxide, shock, smoke, fire, injury, a fall or near miss) goes to the safety officer, urgent, whatever the AI chose;
   - approval limits: over $5,000 above a not-to-exceed amount, or a discount over 10%, goes to the general manager, both checked whatever the queue; an approval whose amount code can't read for sure goes to the office manager;
   - nobody approves their own request: it goes up a level;
   - pay goes to payroll only, and what it says never appears anywhere else (a pay request that's also about safety goes to safety, and is listed on the shared page without its words); code knows pay by its words, so a request the AI sends to payroll without one goes to the office manager, still private, on her own page;
   - a request the AI wasn't sure about, or whose answer failed a check, goes to the office manager.
   Every time code overrides the AI, it records why.
4. **Each queue has a response time** (an hour for safety, two hours for an approval with a customer waiting, a day or more for the rest), and the dashboard shows what's due first.
5. **A dashboard** for the office: who has what, what's urgent, what's due, and where code overrode the AI. Payroll requests are counted, never shown; payroll has its own page.

## Inputs

The requests (who, when, how, the text). The people and what each one handles, by branch where it applies. The policy. For the sample, an answer key with the right queue and person for every request, whether it's urgent, and any second request.

## What "correct" means

- Every request reaches the right person, or the office manager; never the wrong person.
- Every urgent request is marked urgent; every safety request reaches safety.
- The hard cases (safety in passing, a warranty claim dressed as an approval, two requests in one, someone approving their own request, amounts right at the limit, a request that tries to give the router instructions) all land right.
- Nothing about anyone's pay is shown to anyone but payroll.

## Security and privacy

- **Requests are data.** Anything in them that reads like an instruction to the router is ignored, and the lines that matter are held in code.
- **Pay is private,** in code, not by asking the AI.
- **The router routes. It never approves, sends or changes anything.**

## How it runs

- Every few minutes, on whatever has come in.
- A log line every run: requests, how many went to the office manager, how many overrides.
- The policy is a document the office owns. Changing the limits is a code change, reviewed.
