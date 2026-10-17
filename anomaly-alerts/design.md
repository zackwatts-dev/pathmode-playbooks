# Design: anomaly alerts for Summit Mechanical

## The problem

Money and time leak out of Summit's operation in ways nobody sees until month-end, if ever: parts used on a job that never reach the invoice, invoices quietly written down to the customer's not-to-exceed (NTE) amount, increases approved in a customer's portal but never recorded, visits with no hours logged. The records that would show it sit in three systems: field service, accounting, and the customers' portals. About 5,500 jobs close every month, and nobody can reconcile them all by hand.

## What it does

Once a week (in the sample, for September 2025), for every completed job:
1. **Rules** reconcile the records across systems, and flag the problems we already know about:
   - parts recorded on the job that aren't on the invoice;
   - an invoice credited to stay under the NTE;
   - an NTE increase approved in the portal but not in our job;
   - a visit with no hours logged.
2. **Baselines** compare each technician with their branch peers, using robust statistics (median and MAD), on repeat visits and missing hours.
3. **A machine-learning model** (an Isolation Forest) looks across each technician's combination of habits (parts recorded after invoicing, paperwork lag, missing hours, repeat visits, hours and parts per visit) and flags the least typical. This finds patterns nobody wrote a rule for.
4. **Within an alert budget** (12 flags per owner per week), an AI model investigates each flag. Code gathers the records behind it, read-only. The AI explains what happened, the likely cause and the next step, citing the records. It can't change, rank or dismiss a flag.
5. **Code checks every explanation:** the records it cites must exist, and every number in it must come from those records. An explanation that fails goes to a person.
6. Each owner (the controller, the service manager) gets a digest draft. A dashboard shows everything.

The AI is not the detector. Language models are worse at finding anomalies in numbers than simple statistics and classic machine learning, so they only explain.

## Inputs

Exports from the field-service system (jobs, visits, time entries, parts used, technician notes, technicians), accounting (invoices and lines), and the customer portals (NTE and increase requests), as CSV. Plus an answer key: which jobs and technicians really had a problem.

## What "correct" means

- The answer key defines it, per problem type: how many real problems each check caught, and how many of its flags were real.
- For the investigated flags: how many were real, and how many explanations passed their checks.
- A missed problem costs money; a false flag costs a manager's time. The budget caps the second.
- Technician flags are signals for a manager to look into, never conclusions about a person.
- Every rule, baseline and model has a test that runs without calling the AI.

## Security and privacy

- **Read-only:** it reads exports and writes reports. It changes nothing in any system.
- **The AI sees only the records behind one flag at a time.** It has no tools and can't query anything itself.
- **Notes are data:** instructions in a technician's note are ignored, and everything is escaped on the dashboard.
- **Technician signals go to the service manager only.**
- **Pinned packages:** scikit-learn and its dependencies, by exact version and hash.

## How it runs

- Weekly, on a server Summit controls, after the nightly exports.
- At most 12 investigations per owner per run; every flag is still listed.
- Each run adds a line to a log. If the flag count jumps or drops sharply, someone looks.
- Owners mark each flag real or not; those decisions tune the thresholds and the budget.
- Re-run the answer key after any change, including a new model version.
