## This stage: revise your finding after the challenge

You wrote this finding:

{finding}

Your working notes:

{notes}

A skeptical second analyst challenged it:

{challenge}

with these queries:

{queries}

Accept the challenge where it's right, and answer it with queries where it isn't. Don't defend the finding for its own sake; a narrower true finding beats a broad doubtful one. If the challenge retracted it and you disagree, you need new queries that answer the challenge's; without them the finding stays retracted.

When you save finding.json, code runs the report's checks on it and tells you anything it would hold back (a number no query produced, a query that doesn't re-run the same, a size that isn't a query's value). Fix each and save again.
Save `finding.json` in the same shape as before, with two more fields: "response_to_challenge" (what you accepted and what you answered, and how) and "accepted" (true or false). Every number must come from queries you or the challenger ran, cited by id; dollars_a_year must equal a value in size_query's result.
