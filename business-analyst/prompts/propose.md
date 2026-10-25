## This stage: propose

Here is the map of the business's records from the orient stage:

{map}

Write ten hypotheses about where this business loses money or time: margin, billing leakage, rework and repeat work, delays, working capital, customers lost, costs that run over, stock, people's time. Use the records to sharpen them: you may query to size them roughly, but do not investigate yet. Do not assume a problem exists; several should turn out to be wrong, and an investigation that concludes "this is fine" is a success.

For each hypothesis:
1. The claim, stated so it could be false.
2. Why it matters, in dollars a year at the right order of magnitude, with the reasoning (a rough size from a query is better than a guess; say which).
3. What evidence would support it.
4. What evidence would weaken it. If nothing could change your mind, it isn't testable: replace it.
5. The tables and columns it needs, and whether the warehouse has them.

Then rank the ten twice, separately: by likely dollars (rank_significance, 1 is the biggest) and by how well the records can answer it (rank_answerable, 1 is the best). The two rankings should differ; if they come out the same you are scoring one thing twice.

Save `hypotheses.json`:
{"hypotheses": [{"id": "H1", "statement": "...", "why_it_matters": "...", "dollars_rough": "...", "support": "...", "weaken": "...", "data": ["table.column", "..."], "rank_significance": 1, "rank_answerable": 3}]}
