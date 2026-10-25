## This stage: investigate one hypothesis

The map of the records:

{map}

The hypothesis:

{hypothesis}

BEFORE your first query, save `prediction.json`: how you will test it, what would support it, what would weaken it, and what you expect to see and how strongly. {{"test": "...", "support": "...", "weaken": "...", "expect": "..."}} Code checks that it was saved before your first query.

Then query. Don't stop at the first result; follow what you find:
- concentration: a few customers, products, periods or people, or spread evenly? A pattern that survives breaking down is a different fact from one that doesn't;
- time: the whole period, or part of it?
- segments: does the total hide two groups moving differently?
- counts: every rate needs its denominator; a 40% rate on five orders is not a finding;
- the money: what it costs a year, computed from the records, and what part of it could be recovered or avoided.

Be suspicious of what arrives easily: a pattern can be a fact about how a system records things rather than about the business. Keep dead ends; write them in `notes.md` as you go (your working notes; nobody else in this run reads them).

Then save `finding.json`. Every number in title, conclusion and claims must come from the queries that claim cites (title and conclusion: from any query the finding cites). dollars_a_year must equal a value in the result of size_query, so compute it as a query; leave both null if it can't be sized.
{{"id": "{finding_id}", "hypothesis": "{hypothesis_id}", "title": "a heading that states the conclusion",
 "conclusion": "one dense paragraph a manager can act on alone, with the numbers",
 "dollars_a_year": 123456.0, "size_query": "q17",
 "claims": [{{"text": "one supporting fact, with its numbers and denominators", "queries": ["q12", "q13"]}}],
 "confidence": "high | medium | low", "not_evidence_of": "what a reader might over-read", "could_not_tell": "what the records couldn't answer",
 "next_step": "what to check or change next", "dead_ends": ["what you tested that didn't hold"], "incomplete": false}}
When you save finding.json, code runs the report's checks on it and tells you anything it would hold back (a number no query produced, a query that doesn't re-run the same, a size that isn't a query's value). Fix each and save again.
If the hypothesis doesn't hold, say so in the finding: that is a result. Then title and conclusion say it doesn't hold, and dollars_a_year is null.
