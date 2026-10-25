# H5 working notes

- q104: scrap reports by reason valued at SO price (10 yrs). DOT $3,080,744 / 19,398 pcs; operator error $1,636,005 / 10,134 pcs.
- q109 parts (7,725 with order jobs, 4,986 with DOT+OE scrap): top 10% by scrap value = 69.4% of scrap value, but those parts are 51.67% of production value; top 10% by production value already carry 62.11% of scrap. Pareto mostly follows volume/value.
- q159 part x work centre (23,406 combos, 9,076 with any scrap): top 10% = 78.22% of scrap value vs 45.38% of throughput. But 61% of combos have zero scrap, so lumpiness produces concentration on its own. Top 10% by throughput: 58.65% of scrap vs 57.75% of throughput, i.e. proportional.
- q116: raw per-part rate corr between halves 0.2741 (488 parts, >=200 pcs in each half). q153: after routing expectation, corr 0.0409 (258 parts); parts high (O/E>=2) in 2016-20 run at 0.985 in 2021-25 (n=8). DEAD END: no persistent bad parts.
- q121/q154: family rates 0.68%-2.37% raw, but O/E vs work-centre routing 0.946-1.033. DEAD END: family is just routing.
- q121 first run 0.01232 vs run 4+ 0.01344. DEAD END: first runs are not worse.
- q125 work centre DOT+OE rate per piece through: brake 0.00835, weld 0.00648 ... laser 0.00242. But scrap is booked where it's found (q46 orient), so this can't say where it was caused.
- q133: labour qty_scrap only on rework=1 rows (29,420 rows, 36,362 pcs, qty_good 0). q138: the rework employee always also did original work on that op (29,420/29,420).
- q143 employee raw rate corr across halves 0.8751 (49 emps), but q151 after work-centre mix corr -0.1682 (56 emps), O/E p10-p90 0.838-1.243. DEAD END: individual employee differences = work-centre mix.
- q155 tenure: <90d O/E 2.238, 90-364d 1.397, 1-3y 0.916, 3y+ 0.899. q157 holds within part x work centre: 1.852. q156 every year 1.477-2.519. q158 110 of 112 first-year hires above expected, median 1.783: broad learning curve, not a few people.
- q171 first-year ops hold 53.09% of operator-error pieces but 7.17% of DOT pieces (op basis).
- Sizing q168: excess $549,713 over 10y = $54,971/yr at selling price (9.5% of labour scrap value); ~$23,504/yr at material-cost basis via GL memo ratio 0.4276 (approximate).
- Data concern: none addressed to AI found.
