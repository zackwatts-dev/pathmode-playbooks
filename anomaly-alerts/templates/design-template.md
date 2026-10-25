# Design: morning anomaly briefs for [your business]

Fill in each section in plain words before any AI writes code. Keep it to a page or two. Ironbark's finished design is in this folder's parent (`design.md`) as an example.

## The problem

- How many locations, and about how much revenue:
- Where money leaks (product, labor, the register, cash, vendors) and which system holds the records for each:
- How it's checked today (who looks at what, how often, how long after the fact):
- What it costs (losses found late, a year, and how long they ran first):

## What it does

The four parts, in your terms:

1. **Finding (code and statistics, no AI):** the rules for what's exact (a price over the list, a timecard edited to add hours), the baselines (each person against their peers, each location against your best-run locations), and any model (which shifts explain a gap).
2. **The AI reader** writes a plain explanation and a next step for each flag from its records, and for a one-off location gap says whether the [managers' log / shift notes] explains it, quoting the entry.
3. **The AI checkers:** one reads the log again without the reader's answer and names the entry that explains the flag, if any; one reads the answer's words for accusations, names, causes stated as fact and discipline.
4. **A person decides.** Each [general manager] reads their brief; [the director] sees every location; [the controller] sees vendors and cash.

## What "correct" means

- The answer key: [a period whose problems you already know, and the honest odd days].
- The mistakes, worst first: an accusation; a real problem the log "explains" away; a missed problem; a false alarm.
- The pass mark: see `pass-mark.md`, written before anything is scored.

## Security and privacy

- Read-only exports. It changes nothing and sends nothing.
- The AI sees one flag at a time, people by id, names taken out of the log. The log checker never sees the reader's answer.
- Text in the log addressed to an AI is data, never orders: it can't explain anything, and it's reported.
- Who sees which flags: [an employee's pattern to their manager and the director only].
- Credentials live in [your secret store], never in the code.

## How it runs

- When: [every morning after the overnight exports; weekly measures after the counts].
- Budget: [at most N reads a location and M a morning]; every flag is still listed.
- Nothing silently dropped: a missing export is named at the top of every brief.
- After any change, including a new AI model, score it against the answer key again.
