# Design: morning anomaly briefs for Ironbark Tavern & Grill

## The problem

We run twelve restaurants and about $45 million of sales a year, on margins where a point of food or labor cost is most of a store's profit. Money leaks out in a dozen small ways:
- the kitchen uses more than the recipes say (heavy portions, over-prep, waste);
- the bar pours more than it rings;
- servers void or discount checks after the guest paid cash;
- managers comp friends or come up short on the deposit;
- a delivery is short, or invoiced above the price list;
- crews clock in early and out late, and the schedule runs over the labor guide.

The records that would show each of these are in different systems: the point of sale, the inventory counts and recipes, the invoices and price lists, the timeclock and schedule. Today we see them together once a period, when the P&L closes two or three weeks after the period ends. By then a leak has run for six weeks, mixed in with the weather, the promotion and the night the cooler died, and our budgets, built from last year, already include last year's leaks.

## What it does

**Every morning**, for each store and for the group, after the overnight exports:
1. **Builds the day's picture** (code), from the exports:
   - the register, by employee over the last 28 days: voids after the check printed on cash checks, employee-meal and manager discounts on guest checks, comps by who approved them, the share of checks paid in cash;
   - each closing manager's cash over/short, over the last 28 days;
   - each invoice line against that month's price list;
   - each shift's punches against the schedule, edited punches by who edited them, and hours over the labor guide.

   **Every Monday**, after the Sunday counts, it adds the kitchen and the bar: each store's actual usage (last count, plus what was delivered, less this count) against its theoretical usage (product mix times recipes), in dollars, by item, category and vendor.
2. **Finds what's unusual** (code and machine learning, no AI model):
   - **Rules** for what's exact: an invoice price over the list, a punch edited to add hours, whole-check comps a manager approved (the office's party package excepted).
   - **Baselines:** each employee's rate (after-print cash voids, guest-check discounts, as a share of their sales) against the group's typical rate, and each store's kitchen and bar gap against the group's median gap that week and against its own last eight weeks. A flag needs a rate well above typical in absolute terms, a material amount and enough occurrences, not just an unusual score.
   - **An attribution model:** which bartender's shifts explain a bar's extra usage (a regression of each week's bar gap on each bartender's hours over twelve weeks).
   - A one-week jump that reverses the next week (a miscount) isn't flagged unless it's large.
   - Each flag is built only from what was known that morning.
3. **Reads the records, and the log where it can explain** (AI). For each new flag, or one whose dollars a week have grown by half since it was last read, code gathers the records behind it as of that morning. For a store-level flag (the kitchen, the bar, the store's hours), it adds the store's log entries for the same days, with people's names taken out. An AI model (OpenAI's API) says whether the log explains it (the walk-in failed, a catering order went out, a snowstorm), quoting the entry. For every flag it writes a short plain-English explanation and a next step for the general manager, citing the records. An employee's pattern, a vendor's prices or a closer's cash are never "explained" by the log.
4. **Checks the AI's answer** (code):
   - a quoted log entry must be one it was given, its words found in that entry, the entry describing an event of a kind that could account for the flag, and not addressed to an AI;
   - it must cite at least one record, every record it cites must exist, and every amount it uses must be one of those records' amounts;
   - it may not accuse, name anyone, state a cause as fact, or suggest discipline;
   - an answer that fails any check goes to a person with the flag, unexplained.
5. **Writes the briefs:**
   - **each general manager:** their store's flags, money first, each with its evidence, the AI's explanation and next step;
   - **the director of operations:** the group view, every store's flags ranked by dollars a week, and what the log explained away;
   - **the controller:** vendor overcharges and cash shortages.

Employee flags are a pattern worth a conversation, never a conclusion. The tool never contacts anyone, changes a record or disciplines anyone.

## Inputs

Nightly CSV exports:
- **point of sale:** stores, employees with POS ids, menu items and prices, adjustments (every void, comp and discount, with who rang and approved it), sales by employee and day, product mix by week, cash deposits;
- **back office:** inventory items, recipes, Sunday counts, the waste log;
- **purchasing:** vendors, monthly price lists, invoices and their lines, credits;
- **labor:** the schedule and the punches;
- **the managers' log;**
- the period ledger and budgets, and the weather.

**The answer key** (sample only): every problem that was running, who or what it involved, when it started, when the current way of working stopped it, its loss by week; and every honest odd day (benign event), and whether the manager logged it.

## What "correct" means

- **The answer key defines it.** A flag matches a problem when it names the same store (or vendor), the same kind of leak, and the same person where there is one, while the problem was running. Each flag counts for one problem at most, a flag that coincides with an honest event of a kind that explains it counts for none, and a flag the log "explained" doesn't count as found.
- **What we measure:**
  - problems flagged, and the losses from each problem's first flag on;
  - how much sooner: days from the problem's start (or the window's start) to the first flag, against when the current way of working stopped it;
  - **money saved:** each problem's losses from a week after its first flag (time to act) to the day the current way of working stopped it, or the end of the window;
  - false alarms: flags matching no problem, per store per week (a manager's time);
  - honest odd days: how many benign events were flagged, and how many of those the log explained.
- **Mistakes aren't equal.** An accusation, or a flag the log "explains" with words that aren't in the log, is the worst: it costs trust with the staff. A missed problem costs money. A false alarm costs a manager's time, and the budget caps it.
- Every rule, baseline and model has a test that runs without calling the AI.

## Security and privacy

- **Read-only:** it reads exports and writes the briefs. It changes nothing in any system and can't send anything.
- **The AI sees only one flag at a time:** the records behind it and, for a store-level flag, that store's log entries for those days with names taken out. Employees appear by id. It has no tools.
- **The log is data, not instructions.** An entry that tells the AI to do something is ignored, and can never clear a flag.
- **Employee flags go to that store's GM and the director of operations only.** The controller's brief has vendors and cash, not servers.
- **Everything shown is escaped.** Credentials come from the environment.
- **Software:** Python, with pinned numpy and scikit-learn.

## How it runs

- **Daily,** on a server we control, after the overnight exports; the kitchen and bar on Mondays. Each run looks back 90 days to know which flags are already open, so only new or grown flags are read.
- **At most 6 AI reads per store per run, and 40 for the group;** every flag is still listed.
- **Nothing is silently dropped:** an export that's missing or late is named at the top of every brief.
- **Every run adds a line to a log:** when, which model, flags by kind, explained, sent to a person.
- **Managers mark each flag real or not;** those marks tune the thresholds.
- **After any change,** including a new model version, re-run the answer key before going live.
