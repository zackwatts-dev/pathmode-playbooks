# Design: a spec check before each bid goes out, for Halden Mechanical

## The problem

We're a commercial mechanical subcontractor in Columbus, about 150 people and $45-55 million a year, and we win most of our work as the low bid to a general contractor. Each bid is priced in two or three weeks from the drawings and a project manual: the Division 00 and 01 sections that bind every trade, plus Divisions 22 and 23, often 25,000 words or more. Four estimators bid about 330 jobs a year.

Somewhere in those pages are requirements that cost real money beyond the base scope:
- an independent testing and balancing agency;
- commissioning support;
- an extended warranty;
- night or phased work in an occupied building;
- prevailing wage, or a bond;
- a named equipment manufacturer with no substitutions;
- controls under our contract;
- BIM coordination;
- temporary heat;
- upgraded insulation.

An estimator who misses one doesn't find out on bid day. The bid is a little lower, so it's a little more likely to win. Once we've won, work that was in the spec can't be recovered by change order, so it comes out of the margin. We find out at buyout, a month after award, or in the field. By then the price was set long ago.

The labor has the same problem in a quieter form. Each estimator has habits, and our job cost shows them: one estimator's plumbing hours have run about a tenth light for years. Nobody compares a new estimate with how that estimator's last forty jobs actually came out.

## What it does

**When an estimate is marked ready**, and again when an addendum is issued after that, before the bid is due:
1. **Gathers the bid** (code), from the exports as they stand at that moment:
   - the project manual's sections and every addendum issued so far, as text;
   - the estimate by cost code, its labor rate and its alternates;
   - the project's facts (building type, new or renovation, public owner, county, square feet).
2. **Reads the documents** (AI reader). An AI model (Claude, through Anthropic's API) reads the whole manual and the addenda. It lists every requirement of the kinds below that the documents put on the mechanical contractor, each with:
   - its kind, from a fixed list (in Inputs);
   - the section or addendum;
   - the words, quoted exactly;
   - its status: in the base bid, in an alternate, by others (the Owner's agent, another trade), doesn't apply (a condition the project doesn't meet), or deleted by an addendum;
   - its particulars (warranty years, the named manufacturer, insulation thickness, work hours).

   For an addendum issued after the first read, it reads the addendum against the earlier list and says what the addendum adds, changes or deletes.
3. **Checks the reading** (code, then the AI checker). Code accepts a requirement only when its quote is found word for word in the section or addendum it names, and its kind is on the list. Then a second, separate call to the model (the AI checker) gets each accepted requirement with only the sections and addenda it cites, not the whole manual, and is asked a different question: is this really a requirement of that kind on the mechanical contractor, what is its status by the documents' own words (base bid, alternate, by others, doesn't apply, deleted), and is that clear? Code compares the two. A requirement the checker says isn't one, a different kind or status, or one it finds unclear goes to the chief estimator with both answers, not into the gaps. Text addressed to an AI, found by the reader, the checker or a check in code, is reported and does nothing, and a part of the documents carrying it can't supply a "by others", "doesn't apply" or "deleted".
4. **Checks the estimate** (code). Each accepted base-bid requirement is priced when the estimate has a line on its cost code with an amount, or a line whose description names it. For three kinds the evidence is particular:
   - **prevailing wage:** a labor rate at the prevailing rate, or a prevailing wage line;
   - **a named manufacturer:** the equipment line names that manufacturer;
   - **upgraded insulation:** the insulation line names the thickness or jacket.

   Anything not priced is a **gap**. Work the estimate prices that is by others, doesn't apply or was deleted is **priced but not required**.
5. **Prices each gap** (code), from our own completed jobs before the bid date: the median cost of that kind of requirement as a share of the base cost on jobs of the same building type (or all types, when there are too few), with a range.
6. **Checks the labor** (code and statistics). For each system (ductwork, HVAC piping, plumbing, equipment), it takes this estimator's completed jobs and compares actual hours with estimated hours. Where that estimator's actuals have run over by a steady margin on enough jobs, it shows what this estimate's hours would be at that rate, in hours and dollars.
7. **Writes the review**, one page for the estimator and the chief estimator:
   - the gaps, largest first, each with the quote, the section and the cost to add;
   - what's priced but not required;
   - the labor flags;
   - anything sent to a person, and why.

The estimator decides. The tool changes nothing in the estimate and sends nothing.

## Inputs

Exports from estimating and document control, as CSV:
- **projects:** id, name, building type, new or renovation, square feet, public owner, county, delivery method, bid due date;
- **manual sections:** project, section number and title, full text;
- **addenda:** project, number, date issued, full text;
- **estimates:** estimator, date marked ready, labor rate, cost and bid, markup;
- **estimate lines:** cost code, description, hours and dollars by type;
- **alternates;**
- **cost codes.**

**Job history**, from job cost, for jobs completed before each bid's date: each job's project facts, estimator, budget by cost code, and actual hours and dollars by cost code.

**The kinds of requirement:**
- independent TAB agency;
- commissioning support;
- seismic restraints;
- extended warranty;
- named manufacturer, no substitutions;
- insulation upgrade;
- night, phased or occupied work;
- prevailing wage;
- payment and performance bond;
- BIM coordination;
- controls by the mechanical contractor;
- water treatment and flushing;
- temporary heat;
- IAQ flush-out;
- firestopping by the mechanical contractor.

**The answer key** (sample only):
- every requirement-like clause in each manual and addendum, with its kind, section, status, true cost and whether the estimate priced it;
- each bid's true base cost, every competitor's bid, and which bid the general contractor carried;
- each estimate's true labor hours by system.

## What "correct" means

- **The answer key defines it.** A gap matches a missed requirement when it names the same bid, kind and status (base bid). A "priced but not required" matches a clause the estimate priced that wasn't in the base bid.
- **What we measure:**
  - missed requirements found, by count and by true cost, on all bids and on the bids we won;
  - false gaps: a gap that matches nothing, per bid (an estimator's time);
  - **money:** each bid priced again with every gap added at the tool's cost, every labor flag at its rate, and everything priced but not required removed. That price is set against the same competitors' bids and the same general contractor's choice. The money is the change in the true margin across the year: jobs won at a better price, jobs lost that would have lost money, and jobs won that we lost by pricing work we didn't owe.
- **Mistakes aren't equal.** The worst is a requirement that isn't in the documents, because an estimator who trusts it prices work nobody asked for and loses the job. Next worst is calling something required that the documents give to others, or that an addendum deleted. A missed requirement costs margin. A false gap costs an estimator a few minutes.
- Every rule has a test that runs without calling the AI.

## Security and privacy

- **Read-only:** it reads exports and writes the review. It changes nothing in estimating or job cost and can't send anything.
- **The AI sees one bid's documents at a time,** and nothing from our estimate, job cost or other bids. It has no tools.
- **The documents are data, not instructions.** A line in a spec or addendum that tells the AI to do something is reported to the chief estimator, and can never remove a requirement or mark one priced.
- **Everything shown is escaped.** Credentials come from the environment.
- **Software:** Python, standard library and pinned numpy.

## How it runs

- **Every 30 minutes** during the working day, on a server we control, for estimates newly marked ready and addenda newly issued. A review is ready within the hour.
- **One AI read per bid, plus one for each later addendum, and a check of each read** (the checker sees only the sections and addenda the read cites). At most 80 calls a day; anything over that goes to a person.
- **Nothing is silently dropped:** a bid with a missing section list, or an addendum that can't be read, is named at the top of the review.
- **Every run adds a line to a log:** when, which model, bids read, requirements found, gaps, sent to a person.
- **Estimators mark each gap real or not;** those marks tune the rules.
- **After any change,** including a new model version, re-run the answer key before going live.
