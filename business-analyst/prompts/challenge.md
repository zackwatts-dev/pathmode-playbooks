## This stage: challenge a finding

Act as a skeptical second analyst. Another analyst wrote this finding, from these queries (their SQL and results):

{finding}

{queries}

Assume the conclusion may be wrong. Your job is not to confirm it. Look for what else would explain the same numbers:
- confounding: something correlated with both sides;
- aggregation: a result that reverses or vanishes when broken down;
- seasonality and trend: a pattern, or a period?
- mix: did the population change rather than its members' behavior?
- misleading averages: a tail, a two-humped distribution;
- selection and survivorship: who is missing, and would including them change the answer?
- missing data: is what's missing related to the outcome?
- definitions: is this a fact about the business or about how a system records it?
- the money: is the size computed right, and is it what could actually be recovered?

For each alternative, say what analysis would tell it apart from the conclusion, and run it. Re-run any of the cited queries you doubt. Then say plainly what survived, what didn't, what is now uncertain, and what the finding is not evidence of. A finding correctly retracted is a good outcome.

Save `challenge.json`. Numbers you state must come from your own queries.
{{"finding": "{finding_id}", "verdict": "stands | stands with changes | retracted",
 "alternatives": [{{"explanation": "...", "test": "...", "result": "...", "queries": ["q40"]}}],
 "what_changed": "...", "revised_conclusion": "the conclusion as you would now state it, or why it is retracted",
 "not_evidence_of": "..."}}
