## This stage: orient

Understand the business and its records. Do not recommend anything and do not investigate problems yet.

Read the documentation, then query the tables. Identify the business's operating cycles (how work arrives, gets done, gets billed and gets paid, and whatever else the records show). For each cycle: the tables that record it, the grain of each table stated explicitly (one row per what), the questions the data can answer, and the important questions it cannot answer, and why. Check what the documentation doesn't tell you: date ranges, row counts, how tables join, whether keys match across systems, what values a status or reason column actually takes, and anything that looks wrong, missing or suspicious (a sudden change, values that are too uniform, a column that never varies, records that don't agree between systems).

Save `map.json`:
{"cycles": [{"name": "...", "tables": [{"table": "...", "grain": "one row per ...", "answers": "...", "cannot_answer": "..."}]}],
 "joins": ["how the systems link, with the keys, and how well they match (cite queries)"],
 "concerns": ["each data concern, with the query ids that show it"],
 "cannot_answer": ["important questions these records can't answer, and what would be needed"],
 "queries": ["the ids of the queries behind this map"]}
