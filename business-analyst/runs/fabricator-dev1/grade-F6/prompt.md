You grade one finding from an AI analyst against the answer key of a simulated business. The analyst never saw the key. You have the `query` tool on a read-only database holding the simulation's truth tables (schema `truth`) and the same warehouse the analyst queried.

The answer key:

{
 "business": "Wendlow Fabrication & Machine (simulated job shop), 2016-2025, run 9",
 "source": "pathmode-corpus simulations/fabricator/grading/truth-summary.md, BUILD.md (runs 8 and 9) and the truth database (schema truth in the grader's database)",
 "problems": [
  {
   "id": "P1",
   "name": "Slow quotes losing work",
   "mechanism": "Quotes sent late win far less often (within 2 working days about 34%, 5+ days about 18%). Since runs 8-9 the delay comes mostly from how requests are handled: the quotes inbox is read and keyed twice a week, and about 40% of new requests are missing a revision, quantity or drawing, found only when an estimator opens the request to price it, after which it waits for the buyer's answer. The two estimator vacancies (2021-04, 2024-03) add to it.",
   "shows_in": "rfqs (received_on, entered_on), quotes (sent dates, outcomes), the mail log",
   "truth": "about 237 new requests a year (20%) lost because the quote came after the buyer decided (2023-25)",
   "dollars_a_year": null
  },
  {
   "id": "P2",
   "name": "Estimates that drift on some families",
   "mechanism": "Welding on families 3 and 4 runs about 1.03-1.07x the shop standard and about 1.2-1.4x each estimator's estimate; precision machining (family 5) runs under. The re-quotes copy the old estimates forward.",
   "shows_in": "quote line estimated hours by work centre against labour clock-ins by job and operation",
   "truth": "weld true/estimated about 1.22-1.44 on families 3-4 for every estimator; family 5 about 0.86-0.96",
   "dollars_a_year": null
  },
  {
   "id": "P3",
   "name": "Due dates promised without a capacity check",
   "mechanism": "Due dates are promised from a standard lead time; when the bottleneck work centre (laser and brake in 2016 and 2019-21, weld from 2022) is loaded, lines go late.",
   "shows_in": "sales order promised dates against shipments, and labour by work centre",
   "truth": "on time 78% (welding lines) in 2016 and 76-83% in 2021, against 93-99% in other years",
   "dollars_a_year": null
  },
  {
   "id": "P4",
   "name": "Material increases eaten between quote and purchase",
   "mechanism": "Steel bought after the quote at higher prices; repeat orders keep the old price; the surcharge clause recovers little.",
   "shows_in": "quote material cost against purchase-order cost by order, with the steel price index",
   "truth": "$3,029,316 of material over quote in 2021 (by year bought), $769,433 in 2018; 2019-20 and 2023-24 under",
   "dollars_a_year": null
  },
  {
   "id": "P5",
   "name": "Engineering changes that don't reach the floor",
   "mechanism": "A revision arrives by email that names no job, after the traveller is printed, or while engineering is behind; the job is built to the old revision; some escape to the customer as returns.",
   "shows_in": "drawing revisions, ECOs and the jobs logged against them, scrap reports, inspections, returns",
   "truth": "305 jobs built to an old revision (170 email named no job, 91 traveller already printed, 44 engineering behind); 81 escaped to the customer",
   "dollars_a_year": null
  },
  {
   "id": "P6",
   "name": "Know-how in one or two people",
   "mechanism": "The senior CAM programmer left in 2022 (programs and first articles suffer: first-article failures roughly doubled); the senior estimator's departure in 2024 slowed quotes.",
   "shows_in": "CAM programs by author, inspections (first articles), quote turnaround by period",
   "truth": "senior programmer wrote 64-108 programs a year through 2021, 59 in 2022, none after",
   "dollars_a_year": null
  }
 ]
}

The finding (its cited queries' SQL and results follow it):

{
 "id": "F6",
 "hypothesis": "H8",
 "title": "Mostly timing, not the person: quoter 115's lower new-quote hit rate is largely explained by quoting in months when estimators had just left. Matched by month, the gap is about 3 points, in line with a full-time estimator's. The bigger lever is estimating coverage and quote turnaround.",
 "conclusion": "Observed: quoter 115 is an engineer, not an estimator, and is still employed. Estimators 108 (retired 2024-03-01) and 109 (resigned 2021-04-15) and engineers 114 (resigned 2018-02-23) and 113 (resigned 2021-05-07) have left (q276). Half of 115's new quotes (217 of 430, 0.505) fall in 14 months in which they sent 9 or more. Most of those months come right after a departure: 2018-03 and 2018-05, Apr-Oct 2021, and Mar-Apr 2024. Three do not: 2019-12, 2022-12 and 2023-08 (q300, q320). In those 14 months the other quoters won 0.187 with an average turnaround of 8.13 days. In the 58 months with no 115 quotes they won 0.272 with 5.13 days (q299). Against peers' quotes from the same calendar month, 115's gap is -0.031 (n=430, customer-clustered SE 0.017, z about -1.8), against the -0.071 that customer x year gave (q290, q312, q320; reproduced in q334). By customer x quarter it is -0.030 (n=331) (q290). On the month-matched measure 115 sits near full-time estimator 109 (-0.038, n=2,675) and below 108 (+0.033, n=4,223); 108 minus 109 is 0.071 (q290, q320, q334). In 2021, a third of 115's quotes (0.335), 115 matched peers month for month: 0.125 against an expected 0.119 (q315, q320). A smaller residual remains outside 2021: -0.049 month-matched (n=286, SE 0.025). It rests partly on 2022, when 115 won 2 of 37 (q305, q315). Turnaround predicts winning even against quotes from the same month: +0.078 for quotes sent in 0-2 days and -0.092 for 8-30 days (about 2,190 quotes per quintile, q317). Interpretation: the gap I first attributed to estimator 115 mostly comes from when they quoted. They covered quoting in the months after estimators left, when the whole shop quoted slowly and won less. The more useful finding is about coverage. When estimating capacity drops, quoting falls to non-estimators and turnaround slips, and slower quotes go with fewer wins. Valued at month-matched peer rates, 115's shortfall is 13.2 wins, or $158,802 of quoted value over 7.61 years: $20,872 a year (q312). That is quoted revenue, not margin, and much of it accrued when no estimator was available to send those quotes.",
 "dollars_a_year": 20872.0,
 "size_query": "q312",
 "claims": [
  {
   "text": "Quoter roles from HR: 115 is an engineer and still employed. 108 (estimator) retired 2024-03-01, 109 (estimator) resigned 2021-04-15, 113 (engineer) resigned 2021-05-07, 114 (engineer) resigned 2018-02-23, 118 (sales) resigned 2022-04-20. Estimators 254 and 327 were hired 2021-09-21 and 2024-05-10.",
   "queries": [
    "q276"
   ]
  },
  {
   "text": "In 14 months 115 sent 9 or more new quotes. Those months hold 217 of 115's 430 new quotes (0.505). In them, other quoters won 0.187 with an average turnaround of 8.13 days. In the 58 months with no 115 quotes, others won 0.272 with 5.13 days, a gap of 0.085. Of the 14 months, 2018-03/05, 2021-04 to 2021-10 and 2024-03/04 follow departures; 2019-12, 2022-12 and 2023-08 do not.",
   "queries": [
    "q299",
    "q300",
    "q320"
   ]
  },
  {
   "text": "Peers matched by calendar month: 115 -0.031 (n=430, SE 0.019; customer-clustered SE 0.017 across 120 customers, z about -1.8). For comparison, customer x year gives -0.071 (n=389, clustered SE 0.022, z about -3.2) and customer x quarter -0.030 (n=331, SE 0.02).",
   "queries": [
    "q290",
    "q312",
    "q320",
    "q334"
   ]
  },
  {
   "text": "Month-matched gaps for other quoters: 108 +0.033 (n=4,223), 109 -0.038 (n=2,675), 254 -0.021 (n=2,196), 327 +0.027 (n=847). 108 minus 109 is 0.071. With month x turnaround band, 115 is -0.041 and 109 -0.030; with month x segment, 115 is -0.031 and 109 -0.040.",
   "queries": [
    "q290",
    "q305",
    "q320",
    "q334"
   ]
  },
  {
   "text": "115's month-matched gap by year: 2018 +0.024 (n=49), 2019 -0.076 (50), 2020 +0.101 (18), 2021 +0.006 (144; 0.125 vs expected 0.119), 2022 -0.215 (37, 2 wins), 2023 -0.045 (72), 2024 -0.062 (53), 2025 +0.163 (7).",
   "queries": [
    "q315"
   ]
  },
  {
   "text": "Excluding 2021: customer x year -0.071 (n=263, SE 0.025); year-month -0.049 (n=286, SE 0.025).",
   "queries": [
    "q305"
   ]
  },
  {
   "text": "Quote size doesn't explain the gap. Within customer x year cells, 115's quotes are smaller than peers' (log price -0.312, log hours -0.318, work centres -0.317, n=389), similar to 109 and 254. A customer x year x size-tercile cell leaves 115 at -0.062 (n=343).",
   "queries": [
    "q279",
    "q290"
   ]
  },
  {
   "text": "The status data look sound. Every won new quote has a sales order and no non-won quote does, for every quoter. 115's validity window averages 30.1 days, like everyone else's. No expired, lost or no-award quote from 108/109/115/254/327 had its part ordered within 365 days. Every RFQ has exactly one quote, and 115 has no null statuses.",
   "queries": [
    "q275",
    "q281",
    "q283",
    "q285",
    "q286"
   ]
  },
  {
   "text": "Turnaround against same-month quotes, by quintile (2,189-2,190 quotes each): 0-2 days +0.078, 2-4 days +0.041, 4-6 days +0.018, 6-8 days -0.045, 8-30 days -0.092. Raw hit rates are 0.342 to 0.131.",
   "queries": [
    "q317",
    "q250"
   ]
  },
  {
   "text": "Sizing at month-matched peer rates: 13.2 missing wins, $158,802 of quoted value over 7.61 years, $20,872 a year. Under customer x year it was 27.7 wins, $257,449, $33,837 a year.",
   "queries": [
    "q312"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that quoter 115 quotes badly or is at fault. They were an engineer covering quoting, mostly in months after estimators left, and their month-matched gap is in the same range as full-time estimator 109's. Not evidence that faster quoting causes wins: slow quotes may be harder or less wanted RFQs. The dollar figure is quoted revenue under an assumed peer win rate, not margin, and is largely not recoverable for months when no estimator was available. Departures and the low-win months coincide in time, but the records don't show that the departures caused the slowdown (2021 also had other conditions).",
 "could_not_tell": "Why quotes were lost: there is no loss reason or competitor price, and 'expired' means the buyer never replied. How RFQs are assigned between estimators and engineers, whether quotes were followed up, and whether 115 got the leftover or harder RFQs within a month. What drove the -0.049 residual outside 2021, which is about 2 SE and leans on 2022's 2 wins in 37. The standard errors don't account for uncertainty in the peer rates.",
 "next_step": "Treat estimating coverage as the issue. Track RFQ-to-quote turnaround and who sent each quote, month by month, and plan backfill or cross-training before an estimator leaves. Record an assignment reason and a loss reason when a quote's status is entered. If the remaining residual is worth checking, review a small sample of 115's 2022-2024 lost and expired new quotes next to same-month peer quotes for the same customer.",
 "incomplete": false
}

[
 {
  "id": "q276",
  "sql": "SELECT e.employee_id, e.role, e.hired_on, e.terminated_on, e.termination_reason FROM hr_employees e WHERE employee_id IN (SELECT DISTINCT estimator_id FROM erp_quotes) ORDER BY 1",
  "columns": [
   "employee_id",
   "role",
   "hired_on",
   "terminated_on",
   "termination_reason"
  ],
  "row_count": 9,
  "rows": [
   [
    108,
    "estimator",
    "1999-09-19",
    "2024-03-01",
    "retired"
   ],
   [
    109,
    "estimator",
    "2011-02-24",
    "2021-04-15",
    "resigned"
   ],
   [
    113,
    "engineer",
    "1999-09-19",
    "2021-05-07",
    "resigned"
   ],
   [
    114,
    "engineer",
    "2011-09-21",
    "2018-02-23",
    "resigned"
   ],
   [
    115,
    "engineer",
    "2008-10-15",
    null,
    null
   ],
   [
    118,
    "sales",
    "2009-01-22",
    "2022-04-20",
    "resigned"
   ],
   [
    182,
    "engineer",
    "2018-05-11",
    null,
    null
   ],
   [
    254,
    "estimator",
    "2021-09-21",
    null,
    null
   ],
   [
    327,
    "estimator",
    "2024-05-10",
    null,
    null
   ]
  ],
  "error": null
 },
 {
  "id": "q299",
  "sql": "WITH q AS (SELECT q.estimator_id e, substr(sent_on,1,7) ym, (status='won')::int w, date_diff('day', r.received_on::date, sent_on::date) tat FROM erp_quotes q JOIN erp_rfqs r USING(rfq_id) WHERE kind='new' AND status IS NOT NULL AND status<>''),\nm AS (SELECT ym, count(*) n, sum((e=115)::int) n115, avg(tat) tat, sum(w) FILTER (WHERE e<>115) w_oth FROM q GROUP BY 1),\nb AS (SELECT *, CASE WHEN n115=0 THEN '0 none' WHEN n115<=3 THEN '1 1-3' WHEN n115<=8 THEN '2 4-8' ELSE '3 9+' END band FROM m)\nSELECT band, count(*) n_months, sum(n) quotes, sum(n115) q115, round(sum(w_oth)/sum(n-n115),3) hit_others, round(sum(tat*n)/sum(n),2) avg_tat, round(avg(n),1) quotes_per_month FROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "band",
   "n_months",
   "quotes",
   "q115",
   "hit_others",
   "avg_tat",
   "quotes_per_month"
  ],
  "row_count": 4,
  "rows": [
   [
    "0 none",
    58,
    5070,
    0,
    0.272,
    5.13,
    87.4
   ],
   [
    "1 1-3",
    20,
    1851,
    44,
    0.268,
    5.13,
    92.6
   ],
   [
    "2 4-8",
    28,
    2665,
    169,
    0.244,
    5.6,
    95.2
   ],
   [
    "3 9+",
    14,
    1362,
    217,
    0.187,
    8.13,
    97.3
   ]
  ],
  "error": null
 },
 {
  "id": "q300",
  "sql": "WITH q AS (SELECT q.estimator_id e, substr(sent_on,1,7) ym, (status='won')::int w, date_diff('day', r.received_on::date, sent_on::date) tat FROM erp_quotes q JOIN erp_rfqs r USING(rfq_id) WHERE kind='new' AND status IS NOT NULL AND status<>'')\nSELECT ym, count(*) n, sum((e=115)::int) n115, round(avg(w) FILTER (WHERE e=115),3) hit115, round(avg(w) FILTER (WHERE e<>115),3) hit_oth, round(avg(tat),2) tat_all, round(avg(tat) FILTER (WHERE e=115),2) tat115 FROM q GROUP BY 1 HAVING sum((e=115)::int)>=9 ORDER BY 1",
  "columns": [
   "ym",
   "n",
   "n115",
   "hit115",
   "hit_oth",
   "tat_all",
   "tat115"
  ],
  "row_count": 14,
  "rows": [
   [
    "2018-03",
    105,
    9,
    0.222,
    0.24,
    5.77,
    4.89
   ],
   [
    "2018-05",
    124,
    10,
    0.3,
    0.246,
    5.65,
    4.7
   ],
   [
    "2019-12",
    108,
    10,
    0.2,
    0.235,
    7.12,
    5.0
   ],
   [
    "2021-04",
    86,
    13,
    0.0,
    0.096,
    8.1,
    6.46
   ],
   [
    "2021-05",
    68,
    14,
    0.214,
    0.037,
    11.79,
    11.43
   ],
   [
    "2021-06",
    87,
    21,
    0.0,
    0.121,
    15.8,
    15.57
   ],
   [
    "2021-07",
    101,
    26,
    0.231,
    0.093,
    11.78,
    12.15
   ],
   [
    "2021-08",
    99,
    31,
    0.032,
    0.103,
    10.84,
    10.39
   ],
   [
    "2021-09",
    106,
    19,
    0.158,
    0.138,
    12.36,
    13.68
   ],
   [
    "2021-10",
    93,
    10,
    0.3,
    0.193,
    5.99,
    6.7
   ],
   [
    "2022-12",
    98,
    11,
    0.0,
    0.253,
    5.12,
    3.91
   ],
   [
    "2023-08",
    124,
    11,
    0.091,
    0.23,
    5.59,
    5.45
   ],
   [
    "2024-03",
    91,
    21,
    0.19,
    0.243,
    4.75,
    4.62
   ],
   [
    "2024-04",
    72,
    11,
    0.273,
    0.262,
    5.18,
    4.55
   ]
  ],
  "error": null
 },
 {
  "id": "q320",
  "sql": "SELECT 0.033-(-0.038) gap_108_109_ym, -0.031/0.017 z115_ym_cluster, round(-0.071/0.022,1) z115_cy_cluster, round(217/430,3) share115_in_9plus_months, round(144/430,3) share115_2021, 0.272-0.187 others_hit_gap_none_vs_9plus",
  "columns": [
   "gap_108_109_ym",
   "z115_ym_cluster",
   "z115_cy_cluster",
   "share115_in_9plus_months",
   "share115_2021",
   "others_hit_gap_none_vs_9plus"
  ],
  "row_count": 1,
  "rows": [
   [
    0.071,
    -1.8235294117647058,
    -3.2,
    0.505,
    0.335,
    0.085
   ]
  ],
  "error": null
 },
 {
  "id": "q290",
  "sql": "WITH ql AS (SELECT quote_id, sum(unit_price*quantity) price FROM erp_quote_lines GROUP BY 1),\nq0 AS (SELECT quote_id, estimator_id e, customer_id c, substr(sent_on,1,4) y, substr(sent_on,1,7) ym, year(sent_on::date)*10+quarter(sent_on::date) yq, (status='won')::int w, price FROM erp_quotes JOIN ql USING(quote_id) WHERE kind='new' AND status IS NOT NULL AND status<>''),\nq AS (SELECT *, ntile(3) OVER (PARTITION BY y ORDER BY price, quote_id) sz FROM q0),\nk AS (SELECT 'cust_year_size' spec, c::varchar||'|'||y||'|'||sz key, e, w FROM q\n      UNION ALL SELECT 'year_month', ym, e, w FROM q\n      UNION ALL SELECT 'cust_quarter', c::varchar||'|'||yq::varchar, e, w FROM q),\ncell AS (SELECT spec,key,e,count(*) n,sum(w) w FROM k GROUP BY 1,2,3),\ntot AS (SELECT spec,key,sum(n) n,sum(w) w FROM cell GROUP BY 1,2),\nj AS (SELECT cell.*, tot.n-cell.n on_, tot.w-cell.w ow FROM cell JOIN tot USING(spec,key) WHERE tot.n>cell.n)\nSELECT spec, e, sum(n) n, round(sum(w)/sum(n),3) obs, round((sum(w)-sum(n*ow/on_))/sum(n),3) diff, round(sqrt(sum(n*(ow/on_)*(1-ow/on_)))/sum(n),3) se FROM j WHERE e IN (108,109,115,118,254,327) GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "spec",
   "e",
   "n",
   "obs",
   "diff",
   "se"
  ],
  "row_count": 18,
  "rows": [
   [
    "cust_quarter",
    108,
    3252,
    0.266,
    0.03,
    0.006
   ],
   [
    "cust_quarter",
    109,
    2102,
    0.247,
    -0.037,
    0.009
   ],
   [
    "cust_quarter",
    115,
    331,
    0.181,
    -0.03,
    0.02
   ],
   [
    "cust_quarter",
    118,
    95,
    0.158,
    0.017,
    0.03
   ],
   [
    "cust_quarter",
    254,
    1542,
    0.241,
    -0.026,
    0.01
   ],
   [
    "cust_quarter",
    327,
    585,
    0.304,
    0.055,
    0.015
   ],
   [
    "cust_year_size",
    108,
    3289,
    0.264,
    0.037,
    0.006
   ],
   [
    "cust_year_size",
    109,
    2118,
    0.245,
    -0.033,
    0.009
   ],
   [
    "cust_year_size",
    115,
    343,
    0.169,
    -0.062,
    0.02
   ],
   [
    "cust_year_size",
    118,
    100,
    0.16,
    -0.016,
    0.033
   ],
   [
    "cust_year_size",
    254,
    1609,
    0.24,
    -0.012,
    0.01
   ],
   [
    "cust_year_size",
    327,
    608,
    0.301,
    0.046,
    0.015
   ],
   [
    "year_month",
    108,
    4223,
    0.265,
    0.033,
    0.006
   ],
   [
    "year_month",
    109,
    2675,
    0.244,
    -0.038,
    0.009
   ],
   [
    "year_month",
    115,
    430,
    0.172,
    -0.031,
    0.019
   ],
   [
    "year_month",
    118,
    124,
    0.161,
    0.036,
    0.029
   ],
   [
    "year_month",
    254,
    2196,
    0.246,
    -0.021,
    0.009
   ],
   [
    "year_month",
    327,
    847,
    0.296,
    0.027,
    0.015
   ]
  ],
  "error": null
 },
 {
  "id": "q312",
  "sql": "WITH ql AS (SELECT quote_id, sum(unit_price*quantity) price FROM erp_quote_lines GROUP BY 1),\nq AS (SELECT quote_id, estimator_id e, customer_id c, substr(sent_on,1,4) y, substr(sent_on,1,7) ym, sent_on::date sd, (status='won')::int w, price FROM erp_quotes JOIN ql USING(quote_id) WHERE kind='new' AND status IS NOT NULL AND status<>''),\nk AS (SELECT 'cust_year' spec, c::varchar||'|'||y key, * FROM q UNION ALL SELECT 'year_month', ym, * FROM q),\ncell AS (SELECT spec,key,e,count(*) n,sum(w) w FROM k GROUP BY 1,2,3),\ntot AS (SELECT spec,key,sum(n) n,sum(w) w FROM cell GROUP BY 1,2),\np AS (SELECT k.spec, k.c, k.w, k.price, (tot.w-cell.w)/(tot.n-cell.n) pexp FROM k JOIN cell USING(spec,key,e) JOIN tot USING(spec,key) WHERE tot.n>cell.n AND k.e=115),\ncl AS (SELECT spec, c, sum(w-pexp) r FROM p GROUP BY 1,2),\nspan AS (SELECT date_diff('day', min(sd), max(sd))/365.25 yrs FROM q WHERE e=115)\nSELECT p.spec, count(*) n, round(avg(w-pexp),3) diff, round(sqrt((SELECT sum(r*r) FROM cl WHERE cl.spec=p.spec))/count(*),3) se_cluster_customer, (SELECT count(*) FROM cl WHERE cl.spec=p.spec) n_customers,\n round(sum(pexp-w),1) missing_wins, round(sum((pexp-w)*price),0) shortfall_value, round(sum((pexp-w)*price)/(SELECT yrs FROM span),0) per_year, round((SELECT yrs FROM span),2) yrs\nFROM p GROUP BY p.spec ORDER BY 1",
  "columns": [
   "spec",
   "n",
   "diff",
   "se_cluster_customer",
   "n_customers",
   "missing_wins",
   "shortfall_value",
   "per_year",
   "yrs"
  ],
  "row_count": 2,
  "rows": [
   [
    "cust_year",
    389,
    -0.071,
    0.022,
    92,
    27.7,
    257449.0,
    33837.0,
    7.61
   ],
   [
    "year_month",
    430,
    -0.031,
    0.017,
    120,
    13.2,
    158802.0,
    20872.0,
    7.61
   ]
  ],
  "error": null
 },
 {
  "id": "q334",
  "sql": "WITH q AS (SELECT estimator_id e, substr(sent_on,1,7) ym, (status='won')::int w FROM erp_quotes WHERE kind='new' AND status IS NOT NULL AND status<>''),\ncell AS (SELECT ym,e,count(*) n,sum(w) w FROM q GROUP BY 1,2),\ntot AS (SELECT ym,sum(n) n,sum(w) w FROM cell GROUP BY 1),\nj AS (SELECT cell.*, tot.n-cell.n on_, tot.w-cell.w ow FROM cell JOIN tot USING(ym) WHERE tot.n>cell.n)\nSELECT e, sum(n) n, round((sum(w)-sum(n*ow/on_))/sum(n),3) diff FROM j WHERE e IN (108,109,115,254,327) GROUP BY e ORDER BY e",
  "columns": [
   "e",
   "n",
   "diff"
  ],
  "row_count": 5,
  "rows": [
   [
    108,
    4223,
    0.033
   ],
   [
    109,
    2675,
    -0.038
   ],
   [
    115,
    430,
    -0.031
   ],
   [
    254,
    2196,
    -0.021
   ],
   [
    327,
    847,
    0.027
   ]
  ],
  "error": null
 },
 {
  "id": "q305",
  "sql": "WITH q0 AS (SELECT q.estimator_id e, q.customer_id c, cu.segment seg, substr(sent_on,1,4) y, substr(sent_on,1,7) ym, (status='won')::int w, date_diff('day', r.received_on::date, sent_on::date) tat FROM erp_quotes q JOIN erp_rfqs r USING(rfq_id) JOIN erp_customers cu ON cu.customer_id=q.customer_id WHERE kind='new' AND status IS NOT NULL AND status<>''),\nq AS (SELECT *, CASE WHEN tat<=4 THEN 1 WHEN tat<=8 THEN 2 ELSE 3 END tb FROM q0),\nk AS (SELECT 'ym_tat' spec, ym||'|'||tb key, e, w FROM q\n      UNION ALL SELECT 'ym_segment', ym||'|'||seg, e, w FROM q\n      UNION ALL SELECT 'cust_year_excl2021', c::varchar||'|'||y, e, w FROM q WHERE y<>'2021'\n      UNION ALL SELECT 'ym_excl2021', ym, e, w FROM q WHERE y<>'2021'),\ncell AS (SELECT spec,key,e,count(*) n,sum(w) w FROM k GROUP BY 1,2,3),\ntot AS (SELECT spec,key,sum(n) n,sum(w) w FROM cell GROUP BY 1,2),\nj AS (SELECT cell.*, tot.n-cell.n on_, tot.w-cell.w ow FROM cell JOIN tot USING(spec,key) WHERE tot.n>cell.n)\nSELECT spec, e, sum(n) n, round(sum(w)/sum(n),3) obs, round((sum(w)-sum(n*ow/on_))/sum(n),3) diff, round(sqrt(sum(n*(ow/on_)*(1-ow/on_)))/sum(n),3) se FROM j WHERE e IN (108,109,115,254,327) GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "spec",
   "e",
   "n",
   "obs",
   "diff",
   "se"
  ],
  "row_count": 20,
  "rows": [
   [
    "cust_year_excl2021",
    108,
    3321,
    0.276,
    0.032,
    0.007
   ],
   [
    "cust_year_excl2021",
    109,
    2260,
    0.246,
    -0.031,
    0.008
   ],
   [
    "cust_year_excl2021",
    115,
    263,
    0.19,
    -0.071,
    0.025
   ],
   [
    "cust_year_excl2021",
    254,
    1741,
    0.243,
    -0.017,
    0.009
   ],
   [
    "cust_year_excl2021",
    327,
    701,
    0.294,
    0.032,
    0.015
   ],
   [
    "ym_excl2021",
    108,
    3711,
    0.276,
    0.036,
    0.007
   ],
   [
    "ym_excl2021",
    109,
    2523,
    0.245,
    -0.036,
    0.009
   ],
   [
    "ym_excl2021",
    115,
    286,
    0.196,
    -0.049,
    0.025
   ],
   [
    "ym_excl2021",
    254,
    2076,
    0.249,
    -0.018,
    0.01
   ],
   [
    "ym_excl2021",
    327,
    847,
    0.296,
    0.027,
    0.015
   ],
   [
    "ym_segment",
    108,
    4223,
    0.265,
    0.035,
    0.006
   ],
   [
    "ym_segment",
    109,
    2675,
    0.244,
    -0.04,
    0.008
   ],
   [
    "ym_segment",
    115,
    430,
    0.172,
    -0.031,
    0.019
   ],
   [
    "ym_segment",
    254,
    2190,
    0.246,
    -0.021,
    0.009
   ],
   [
    "ym_segment",
    327,
    847,
    0.296,
    0.03,
    0.014
   ],
   [
    "ym_tat",
    108,
    4223,
    0.265,
    0.034,
    0.006
   ],
   [
    "ym_tat",
    109,
    2674,
    0.244,
    -0.03,
    0.008
   ],
   [
    "ym_tat",
    115,
    430,
    0.172,
    -0.041,
    0.019
   ],
   [
    "ym_tat",
    254,
    2190,
    0.246,
    -0.019,
    0.009
   ],
   [
    "ym_tat",
    327,
    847,
    0.296,
    0.029,
    0.015
   ]
  ],
  "error": null
 },
 {
  "id": "q315",
  "sql": "WITH q AS (SELECT estimator_id e, substr(sent_on,1,4) y, substr(sent_on,1,7) ym, (status='won')::int w FROM erp_quotes WHERE kind='new' AND status IS NOT NULL AND status<>''),\ncell AS (SELECT ym,e,count(*) n,sum(w) w FROM q GROUP BY 1,2),\ntot AS (SELECT ym,sum(n) n,sum(w) w FROM cell GROUP BY 1),\nj AS (SELECT cell.*, substr(cell.ym,1,4) y, tot.n-cell.n on_, tot.w-cell.w ow FROM cell JOIN tot USING(ym) WHERE tot.n>cell.n AND e=115)\nSELECT y, sum(n) n, sum(w) w, round(sum(w)/sum(n),3) obs, round(sum(n*ow/on_)/sum(n),3) expct, round((sum(w)-sum(n*ow/on_))/sum(n),3) diff FROM j GROUP BY y ORDER BY y",
  "columns": [
   "y",
   "n",
   "w",
   "obs",
   "expct",
   "diff"
  ],
  "row_count": 8,
  "rows": [
   [
    "2018",
    49,
    13,
    0.265,
    0.242,
    0.024
   ],
   [
    "2019",
    50,
    8,
    0.16,
    0.236,
    -0.076
   ],
   [
    "2020",
    18,
    7,
    0.389,
    0.288,
    0.101
   ],
   [
    "2021",
    144,
    18,
    0.125,
    0.119,
    0.006
   ],
   [
    "2022",
    37,
    2,
    0.054,
    0.269,
    -0.215
   ],
   [
    "2023",
    72,
    13,
    0.181,
    0.225,
    -0.045
   ],
   [
    "2024",
    53,
    10,
    0.189,
    0.25,
    -0.062
   ],
   [
    "2025",
    7,
    3,
    0.429,
    0.265,
    0.163
   ]
  ],
  "error": null
 },
 {
  "id": "q279",
  "sql": "WITH ql AS (SELECT quote_id, count(*) nl, sum(est_hours) hrs, sum(unit_price*quantity) price, sum(est_outside) outs, max(lead_weeks) lead FROM erp_quote_lines GROUP BY 1),\nlh AS (SELECT ql2.quote_id, count(DISTINCT h.work_centre) nwc FROM erp_quote_lines ql2 JOIN erp_quote_line_hours h USING(quote_line_id) GROUP BY 1),\nq AS (SELECT q.quote_id, estimator_id e, customer_id c, substr(sent_on,1,4) y, nl, ln(hrs+1) lh_, ln(price) lp, (outs>0)::int has_out, nwc FROM erp_quotes q JOIN ql USING(quote_id) LEFT JOIN lh USING(quote_id) WHERE kind='new' AND status IS NOT NULL AND status<>''),\ncy AS (SELECT c,y,count(*) n,sum(nl) s1,sum(lh_) s2,sum(lp) s3,sum(has_out) s4,sum(nwc) s5 FROM q GROUP BY 1,2),\nce AS (SELECT c,y,e,count(*) n,sum(nl) s1,sum(lh_) s2,sum(lp) s3,sum(has_out) s4,sum(nwc) s5 FROM q GROUP BY 1,2,3),\nd AS (SELECT q.e, nl-(cy.s1-ce.s1)/(cy.n-ce.n) d1, lh_-(cy.s2-ce.s2)/(cy.n-ce.n) d2, lp-(cy.s3-ce.s3)/(cy.n-ce.n) d3, has_out-(cy.s4-ce.s4)/(cy.n-ce.n) d4, nwc-(cy.s5-ce.s5)/(cy.n-ce.n) d5 FROM q JOIN cy USING(c,y) JOIN ce USING(c,y,e) WHERE cy.n>ce.n)\nSELECT e, count(*) n, round(avg(d1),3) rel_lines, round(avg(d2),3) rel_log_hrs, round(avg(d3),3) rel_log_price, round(avg(d4),3) rel_outside_share, round(avg(d5),3) rel_work_centres FROM d GROUP BY e ORDER BY e",
  "columns": [
   "e",
   "n",
   "rel_lines",
   "rel_log_hrs",
   "rel_log_price",
   "rel_outside_share",
   "rel_work_centres"
  ],
  "row_count": 9,
  "rows": [
   [
    108,
    3760,
    0.226,
    0.557,
    0.564,
    0.069,
    0.574
   ],
   [
    109,
    2401,
    -0.177,
    -0.434,
    -0.435,
    -0.05,
    -0.49
   ],
   [
    113,
    252,
    -0.145,
    -0.353,
    -0.391,
    -0.033,
    -0.3
   ],
   [
    114,
    78,
    -0.23,
    -0.226,
    -0.245,
    -0.032,
    -0.303
   ],
   [
    115,
    389,
    -0.133,
    -0.318,
    -0.312,
    -0.037,
    -0.317
   ],
   [
    118,
    114,
    -0.012,
    -0.171,
    -0.136,
    -0.022,
    -0.241
   ],
   [
    182,
    99,
    -0.245,
    -0.187,
    -0.157,
    0.013,
    -0.351
   ],
   [
    254,
    1851,
    -0.102,
    -0.315,
    -0.319,
    -0.041,
    -0.257
   ],
   [
    327,
    701,
    0.014,
    0.029,
    0.025,
    -0.006,
    0.053
   ]
  ],
  "error": null
 },
 {
  "id": "q275",
  "sql": "SELECT kind, coalesce(status,'<null>') status, count(*) n, count(*) FILTER (WHERE estimator_id=115) n115 FROM erp_quotes GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "kind",
   "status",
   "n",
   "n115"
  ],
  "row_count": 8,
  "rows": [
   [
    "new",
    "<null>",
    49,
    0
   ],
   [
    "new",
    "expired",
    5153,
    225
   ],
   [
    "new",
    "lost",
    2223,
    100
   ],
   [
    "new",
    "no award",
    808,
    31
   ],
   [
    "new",
    "won",
    2764,
    74
   ],
   [
    "requote",
    "<null>",
    21,
    0
   ],
   [
    "requote",
    "lost",
    602,
    37
   ],
   [
    "requote",
    "won",
    11818,
    575
   ]
  ],
  "error": null
 },
 {
  "id": "q281",
  "sql": "SELECT estimator_id e, kind, round(avg(date_diff('day', sent_on::date, valid_until::date)),1) avg_valid_days, min(date_diff('day', sent_on::date, valid_until::date)) mn, max(date_diff('day', sent_on::date, valid_until::date)) mx, round(avg(date_diff('day', sent_on::date, status_date::date)) FILTER (WHERE status='won'),1) days_to_win, count(*) n FROM erp_quotes WHERE status IS NOT NULL AND status<>'' GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "e",
   "kind",
   "avg_valid_days",
   "mn",
   "mx",
   "days_to_win",
   "n"
  ],
  "row_count": 18,
  "rows": [
   [
    108,
    "new",
    30.1,
    29,
    35,
    7.8,
    4223
   ],
   [
    108,
    "requote",
    30.0,
    29,
    35,
    2.5,
    3634
   ],
   [
    109,
    "new",
    30.3,
    29,
    36,
    7.1,
    2675
   ],
   [
    109,
    "requote",
    30.0,
    29,
    36,
    2.4,
    3307
   ],
   [
    113,
    "new",
    30.3,
    29,
    35,
    6.2,
    268
   ],
   [
    113,
    "requote",
    30.4,
    29,
    34,
    2.9,
    470
   ],
   [
    114,
    "new",
    30.2,
    29,
    33,
    8.8,
    79
   ],
   [
    114,
    "requote",
    30.1,
    29,
    33,
    2.7,
    204
   ],
   [
    115,
    "new",
    30.1,
    29,
    34,
    5.8,
    430
   ],
   [
    115,
    "requote",
    30.1,
    29,
    34,
    2.7,
    612
   ],
   [
    118,
    "new",
    29.7,
    29,
    33,
    6.9,
    124
   ],
   [
    118,
    "requote",
    29.4,
    29,
    33,
    2.3,
    105
   ],
   [
    182,
    "new",
    30.2,
    29,
    34,
    8.5,
    106
   ],
   [
    182,
    "requote",
    29.8,
    29,
    32,
    2.5,
    239
   ],
   [
    254,
    "new",
    30.1,
    1,
    36,
    7.6,
    2196
   ],
   [
    254,
    "requote",
    30.0,
    12,
    35,
    2.5,
    2671
   ],
   [
    327,
    "new",
    30.2,
    1,
    36,
    8.5,
    847
   ],
   [
    327,
    "requote",
    30.0,
    12,
    35,
    2.6,
    1178
   ]
  ],
  "error": null
 },
 {
  "id": "q283",
  "sql": "WITH so AS (SELECT quote_id, count(*) nso FROM erp_sales_orders WHERE quote_id IS NOT NULL GROUP BY 1)\nSELECT q.estimator_id e, q.status, count(*) n, round(avg((so.quote_id IS NOT NULL)::int),3) share_with_so FROM erp_quotes q LEFT JOIN so USING(quote_id) WHERE kind='new' AND status IS NOT NULL AND status<>'' GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "e",
   "status",
   "n",
   "share_with_so"
  ],
  "row_count": 36,
  "rows": [
   [
    108,
    "expired",
    2027,
    0.0
   ],
   [
    108,
    "lost",
    772,
    0.0
   ],
   [
    108,
    "no award",
    304,
    0.0
   ],
   [
    108,
    "won",
    1120,
    1.0
   ],
   [
    109,
    "expired",
    1276,
    0.0
   ],
   [
    109,
    "lost",
    548,
    0.0
   ],
   [
    109,
    "no award",
    199,
    0.0
   ],
   [
    109,
    "won",
    652,
    1.0
   ],
   [
    113,
    "expired",
    117,
    0.0
   ],
   [
    113,
    "lost",
    72,
    0.0
   ],
   [
    113,
    "no award",
    23,
    0.0
   ],
   [
    113,
    "won",
    56,
    1.0
   ],
   [
    114,
    "expired",
    30,
    0.0
   ],
   [
    114,
    "lost",
    17,
    0.0
   ],
   [
    114,
    "no award",
    5,
    0.0
   ],
   [
    114,
    "won",
    27,
    1.0
   ],
   [
    115,
    "expired",
    225,
    0.0
   ],
   [
    115,
    "lost",
    100,
    0.0
   ],
   [
    115,
    "no award",
    31,
    0.0
   ],
   [
    115,
    "won",
    74,
    1.0
   ],
   [
    118,
    "expired",
    83,
    0.0
   ],
   [
    118,
    "lost",
    14,
    0.0
   ],
   [
    118,
    "no award",
    7,
    0.0
   ],
   [
    118,
    "won",
    20,
    1.0
   ],
   [
    182,
    "expired",
    42,
    0.0
   ],
   [
    182,
    "lost",
    30,
    0.0
   ],
   [
    182,
    "no award",
    10,
    0.0
   ],
   [
    182,
    "won",
    24,
    1.0
   ],
   [
    254,
    "expired",
    992,
    0.0
   ],
   [
    254,
    "lost",
    510,
    0.0
   ],
   [
    254,
    "no award",
    154,
    0.0
   ],
   [
    254,
    "won",
    540,
    1.0
   ],
   [
    327,
    "expired",
    361,
    0.0
   ],
   [
    327,
    "lost",
    160,
    0.0
   ],
   [
    327,
    "no award",
    75,
    0.0
   ],
   [
    327,
    "won",
    251,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q285",
  "sql": "WITH r AS (SELECT rfq_id, count(*) nq, count(DISTINCT estimator_id) ne, sum((kind='new')::int) nnew, sum((kind='requote')::int) nre FROM erp_quotes GROUP BY 1)\nSELECT nq, ne, nnew, nre, count(*) rfqs FROM r GROUP BY ALL ORDER BY 5 DESC, 1,2,3,4 LIMIT 20",
  "columns": [
   "nq",
   "ne",
   "nnew",
   "nre",
   "rfqs"
  ],
  "row_count": 2,
  "rows": [
   [
    1,
    1,
    0,
    1,
    12441
   ],
   [
    1,
    1,
    1,
    0,
    10997
   ]
  ],
  "error": null
 },
 {
  "id": "q286",
  "sql": "WITH s AS (SELECT q.quote_id, q.customer_id, q.sent_on::date sd, q.status, q.estimator_id e, (SELECT count(*) FROM erp_quote_lines l WHERE l.quote_id=q.quote_id) nl FROM erp_quotes q WHERE kind='new' AND status IN ('expired','lost','no award')),\np AS (SELECT DISTINCT s.quote_id, s.e, s.status FROM s JOIN erp_quote_lines l1 ON l1.quote_id=s.quote_id JOIN erp_so_lines sl ON sl.part_id=l1.part_id JOIN erp_sales_orders so ON so.order_id=sl.order_id AND so.order_date::date > s.sd AND so.order_date::date <= s.sd + 365)\nSELECT s.e, s.status, count(*) n, count(p.quote_id) later_ordered_within_1y, round(count(p.quote_id)/count(*),3) share FROM s LEFT JOIN p USING(quote_id) WHERE s.e IN (108,109,115,254,327) GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "e",
   "status",
   "n",
   "later_ordered_within_1y",
   "share"
  ],
  "row_count": 15,
  "rows": [
   [
    108,
    "expired",
    2027,
    0,
    0.0
   ],
   [
    108,
    "lost",
    772,
    0,
    0.0
   ],
   [
    108,
    "no award",
    304,
    0,
    0.0
   ],
   [
    109,
    "expired",
    1276,
    0,
    0.0
   ],
   [
    109,
    "lost",
    548,
    0,
    0.0
   ],
   [
    109,
    "no award",
    199,
    0,
    0.0
   ],
   [
    115,
    "expired",
    225,
    0,
    0.0
   ],
   [
    115,
    "lost",
    100,
    0,
    0.0
   ],
   [
    115,
    "no award",
    31,
    0,
    0.0
   ],
   [
    254,
    "expired",
    992,
    0,
    0.0
   ],
   [
    254,
    "lost",
    510,
    0,
    0.0
   ],
   [
    254,
    "no award",
    154,
    0,
    0.0
   ],
   [
    327,
    "expired",
    361,
    0,
    0.0
   ],
   [
    327,
    "lost",
    160,
    0,
    0.0
   ],
   [
    327,
    "no award",
    75,
    0,
    0.0
   ]
  ],
  "error": null
 },
 {
  "id": "q317",
  "sql": "WITH q AS (SELECT q.quote_id, substr(sent_on,1,7) ym, (status='won')::int w, date_diff('day', r.received_on::date, sent_on::date) tat FROM erp_quotes q JOIN erp_rfqs r USING(rfq_id) WHERE kind='new' AND status IS NOT NULL AND status<>''),\nm AS (SELECT ym, count(*) n, sum(w) sw FROM q GROUP BY 1),\nd AS (SELECT q.*, w - (m.sw - w)/(m.n-1) dev, ntile(5) OVER (ORDER BY tat, quote_id) bt FROM q JOIN m USING(ym) WHERE m.n>1)\nSELECT bt, count(*) n, min(tat) lo, max(tat) hi, round(avg(w),3) hit_raw, round(avg(dev),3) hit_vs_same_month FROM d GROUP BY bt ORDER BY bt",
  "columns": [
   "bt",
   "n",
   "lo",
   "hi",
   "hit_raw",
   "hit_vs_same_month"
  ],
  "row_count": 5,
  "rows": [
   [
    1,
    2190,
    0,
    2,
    0.342,
    0.078
   ],
   [
    2,
    2190,
    2,
    4,
    0.304,
    0.041
   ],
   [
    3,
    2190,
    4,
    6,
    0.277,
    0.018
   ],
   [
    4,
    2189,
    6,
    8,
    0.208,
    -0.045
   ],
   [
    5,
    2189,
    8,
    30,
    0.131,
    -0.092
   ]
  ],
  "error": null
 },
 {
  "id": "q250",
  "sql": "WITH ql AS (SELECT quote_id, sum(unit_price*quantity) price, count(*) nl FROM erp_quote_lines GROUP BY 1),\nq AS (SELECT q.quote_id, q.estimator_id e, (status='won')::int w, date_diff('day', r.received_on::date, sent_on::date) tat, price, nl\n  FROM erp_quotes q JOIN ql USING(quote_id) JOIN erp_rfqs r USING(rfq_id) WHERE kind='new' AND status IS NOT NULL AND status<>''),\nb AS (SELECT *, ntile(5) OVER (ORDER BY tat, quote_id) bt, ntile(5) OVER (ORDER BY price, quote_id) bp FROM q)\nSELECT 'turnaround' k, bt b, count(*) n, min(tat) lo, max(tat) hi, round(avg(w),3) hit, round(avg((e=115)::int),3) share115 FROM b GROUP BY bt\nUNION ALL SELECT 'value', bp, count(*), round(min(price)), round(max(price)), round(avg(w),3), round(avg((e=115)::int),3) FROM b GROUP BY bp ORDER BY 1,2",
  "columns": [
   "k",
   "b",
   "n",
   "lo",
   "hi",
   "hit",
   "share115"
  ],
  "row_count": 10,
  "rows": [
   [
    "turnaround",
    1,
    2190,
    0.0,
    2.0,
    0.342,
    0.031
   ],
   [
    "turnaround",
    2,
    2190,
    2.0,
    4.0,
    0.304,
    0.038
   ],
   [
    "turnaround",
    3,
    2190,
    4.0,
    6.0,
    0.277,
    0.04
   ],
   [
    "turnaround",
    4,
    2189,
    6.0,
    8.0,
    0.208,
    0.025
   ],
   [
    "turnaround",
    5,
    2189,
    8.0,
    30.0,
    0.131,
    0.063
   ],
   [
    "value",
    1,
    2190,
    153.0,
    1810.0,
    0.268,
    0.053
   ],
   [
    "value",
    2,
    2190,
    1811.0,
    3862.0,
    0.266,
    0.046
   ],
   [
    "value",
    3,
    2190,
    3864.0,
    6667.0,
    0.257,
    0.036
   ],
   [
    "value",
    4,
    2189,
    6668.0,
    11863.0,
    0.231,
    0.031
   ],
   [
    "value",
    5,
    2189,
    11864.0,
    114480.0,
    0.241,
    0.031
   ]
  ],
  "error": null
 }
]

Decide:
- "full": it identifies a planted problem's mechanism (what happens and where it shows in the business) with evidence from the records;
- "partly": the right effect with a wrong or missing cause, or one part of a two-part problem;
- "true, not planted": it matches no planted problem, and the truth tables confirm it;
- "wrong": the truth contradicts it;
- "unverifiable": the truth tables can't settle it.
Query the truth to check the finding's main claim and its size. Every number you write must come from your own queries, cited.

Save `grade.json`: {"finding": "F6", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
