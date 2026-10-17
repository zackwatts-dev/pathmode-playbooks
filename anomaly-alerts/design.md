# Design: anomaly alerts for Summit Mechanical

## The problem

Money and time leak out of Summit's operation in ways nobody sees until month-end, if ever: parts used on a job that never reach the invoice, invoices quietly written down to the customer's not-to-exceed (NTE) amount, increases approved in a customer's portal but never recorded, visits with no hours logged. The records that would show it sit in three systems: field service, accounting, and the customers' portals. About 5,500 jobs close every month, and nobody can reconcile them all by hand.

## What it does

Once a week (in the sample, for September 2025), for every job completed in the last 45 days (a job is usually invoiced days after it's done, so each run looks back; flags already reported aren't sent again):
1. **Rules** reconcile the records across systems, and flag the problems we already know about:
   - parts recorded on the job that aren't on the invoice;
   - an invoice credited to stay under the NTE;
   - an NTE increase approved in the portal but not in our job;
   - a visit with no hours logged (a blank time entry, or no time entry at all).
2. **Baselines** compare each technician with their branch peers, using robust statistics (median and MAD), on repeat visits and missing hours. A flag also needs a material difference: at least three occurrences, and a rate well above peers in absolute terms, not just in robust units.
3. **A machine-learning model** (an Isolation Forest) looks across each technician's combination of habits over the 90 days ending on the run's end date (parts recorded after invoicing, paperwork lag, missing hours, repeat visits, hours and parts per visit) and flags those that are clearly unusual, with no quota: only above a threshold on how unusual they are, and only when a problem habit is material (well above typical, by enough, often enough). A month with nothing unusual flags nobody. This finds patterns nobody wrote a rule for. Paperwork lag needs the time each entry was made; in Summit's sample every time entry carries its visit's date, so it can't be seen there.
4. **Within an alert budget** (12 flags per owner per week; the most money first, technician patterns last), an AI model investigates each flag. Code gathers the records behind it, read-only. The AI explains what happened, the likely cause and the next step, citing the records. It can't change, rank or dismiss a flag.
5. **Code checks every explanation:** its shape first (a malformed answer goes to a person), then the records it cites or mentions must exist, every number in it must be one of those records' amounts or quantities (not the digits of an ID or a date), and it may not name a person or accuse or discipline anyone. An explanation that fails goes to a person.
6. Each owner (the controller, the service manager) gets their own dashboard, flag list and digest draft, with only their flags.

The AI is not the detector. Language models are worse at finding anomalies in numbers than simple statistics and classic machine learning, so they only explain.

## Inputs

Exports from the field-service system (jobs, visits, time entries, parts used, technician notes, technicians), accounting (invoices and lines), and the customer portals (NTE and increase requests), as CSV. Plus an answer key: which jobs and technicians really had a problem.

## What "correct" means

- The answer key defines it, per problem type: how many real problems each check caught, and how many of its flags were real.
- For the investigated flags: how many found the problem the answer key gives that job or technician, and how many explanations passed their checks.
- Say what the score can't show: where the answer key uses the rule's own definition (missing hours), the score checks the plumbing, not the rule; and problems no check looks for (callbacks) are reported as not checked.
- A missed problem costs money; a false flag costs a manager's time. The budget caps the second.
- Technician flags are a pattern worth a conversation, never conclusions about a person. They come last in each owner's list: money first.
- Every rule, baseline and model has a test that runs without calling the AI.

## Security and privacy

- **Read-only:** it reads exports and writes reports. It changes nothing in any system.
- **The AI sees only the records behind one flag at a time.** It has no tools and can't query anything itself.
- **Notes are data:** instructions in a technician's note are ignored, and everything is escaped on the dashboard.
- **Technician signals go to the service manager only.** The controller's flags are sent to the AI without technician IDs, and the shared summary has counts only.
- **Pinned packages:** scikit-learn and its dependencies, by exact version and hash.

## How it runs

- Weekly, on a server Summit controls, after the nightly exports.
- At most 12 investigations per owner per run; every flag is still listed.
- Each run adds a line to a log. If the flag count jumps or drops sharply, someone looks.
- Owners mark each flag real or not; those decisions tune the thresholds and the budget.
- Re-run the answer key after any change, including a new model version.
