# H6 notes: unreceived material POs

- q226: unreceived share by vendor. Vendor 1 (carbon) 44.16%, vendor 2 (carbon) 0.11%, aluminium 38.81%, stainless 42.74%. Outside POs are 100% unreceived (known), excluded from here on.
- q228: 30,652 of 30,888 unreceived material POs sit on a job that has a received same-material PO. But only 304 are within 10% on pounds and 38 within 1%, so the "duplicate" form fails.
- q229: PO pattern per job is rigid. The first PO is received and every later PO is unreceived ("2R,1U", "1R,1U,1U" and so on).
- q233: later POs have median 43.5 lb, 3.3% of the first PO (p90 11.6%), ordered a median 11 days after the first. Never on the same day.
- q235: number of later POs on a job = its number of scrap reports, almost exactly. Jobs with 0 later POs have 116 scrap reports across 50,993 jobs.
- q237: 30,652 of 30,670 later POs are dated the same day as the k-th scrap report on the job; the max lag is 13 days.
- q239: later PO pounds / (scrap qty × first-PO lb per job piece): median 0.994, p10 0.917, p90 1.07. These are scrap-replacement buys sized to the scrap.
- q240: jobs with follow-ups shipped in full on 24,998 of 25,258, about as often as other jobs.
- q243/q246: 218 first POs with no receipt are edge effects. 117 jobs were created in Dec 2015 and 15 on 2016-01-01..03 (all ordered in Jan 2016); 86 were ordered Dec 11-31 2025.
- q249: GL material = all material PO amount (ratio 1.0000 each year), so the unreceived buys are expensed. Unreceived $ = follow-up $ every year 2017-2024. The scrap material memo is 1.0053-1.1624x the follow-up $.
- q253: follow-ups go only to vendors 1/3/4, never vendor 2. That explains the vendor skew in q226 as an artefact.
- Dead ends: duplicates (similar pounds) don't hold; vendor-specific receiving failure doesn't hold; "lost cash" can't be tested (no vendor payments in the warehouse).
- Open: does the material physically arrive? Jobs ship, so presumably it does, but a receipt is never keyed for replacement buys.
