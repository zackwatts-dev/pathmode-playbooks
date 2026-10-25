# H2 notes

- q398: price-to-list by year x category. Parts 0.8467->0.8379, refrigeration 0.8464->0.8379, supplies 0.8465->0.8373 (no markdown lines in these categories). Equipment overall 0.839->0.764 but non-markdown equipment only 0.8406->0.8281. So non-equipment does fall, ~0.9 pt; H1 markdowns are the bulk.
- q402: price = round(list*(1-disc)*(1-md),2) exactly on only 546,426 of 2,719,712 lines; ratio min 0.85 max 1.72 -> there is per-line noise. q403: median ratio ~0.991 every year, flat -> pricing formula stable over time; line-weighted discount rises 0.1415->0.1518.
- q404: DEAD END for "new accounts at higher discount": cohort avg discount 0.1355-0.1458, pre-2016 0.1412. New cohorts not higher.
- q407: line-weighted discount rises inside pre-2016 customers (0.1414->0.1565), and inside new cohort (0.1452 in 2016 tiny n, 0.1372 2019 -> 0.1473 2025). Since discount is fixed per customer, this is mix.
- q410/q415: low-discount customers stop buying faster: <10% tier 292/1000 active-2016 still active 2025 (0.292) vs >=20% 352/733 (0.4802). Lines per active customer similar across tiers.
- q413: DEAD END for repricing: 1,346 customers active in 2016 and 2025, non-markdown PTL 0.8319 -> 0.8323, median change +0.0005; 9 drop >2pt, 13 rise >2pt. Same customer pays same share of list. (Caveat: snapshot discount could be retroactively applied by system; can't rule out.)
- q417/q418: 2025 non-markdown list $140.5M; shortfall vs 2016 PTL $1,398,673.63; customer-discount-mix part $1,428,556.45; residual rate -$29,882.82.
- q419: tiers do not differ on credit limit/terms; >=20% tier onboarded slightly earlier on avg.
- q420: discount mix rises in 11 of 12 branches; Toledo 0.142->0.1402.
