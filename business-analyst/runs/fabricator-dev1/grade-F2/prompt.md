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
 "id": "F2",
 "hypothesis": "H5",
 "title": "Scrap is not concentrated in fixable parts, families, first runs or people once volume and routing are allowed for; the one robust pattern is a first-year learning curve (about 1.8x the tenured rate), worth roughly $18,900 a year at cost",
 "conclusion": "The hypothesis does not hold in its testable form. Observed: the top 10% of parts carry 69.4% of 'dimension out of tolerance' (DOT) plus 'operator error' (OE) scrap value ($4,716,749, 2016-2025, 4,986 of 7,725 parts with order jobs). But the top 10% of parts by sales value already carry 62.11% of it (q109), and part x work-centre combinations scrap in proportion to throughput (58.65% of scrap vs 57.75% of throughput, q159). Part differences after routing are weak and do not repeat: half-period correlation 0.0409 (258 parts, q153); odd/even job split correlation -0.0249 on pieces and 0.1144 on scrap events (516 parts), event overdispersion chi2/df 1.255 (445 parts) (q218). Parts in the top quintile on even jobs (event O/E 1.429) ran at 1.017x events and 0.965x pieces on odd jobs (q219). So there is a weak real part signal in event counts, but nothing that can be found ahead of time and fixed. Family differences disappear once routing is allowed for (0.946-1.033, q154). First runs are not worse: for parts created 2017+, first runs run at 0.984x (DOT+OE, 4,800 jobs) against 1.007x for run 4 onward (q222). Employee differences are work-centre mix (correlation within work centre -0.1682, 56 employees, q151). What holds is tenure. First-year staff scrap 1.804x a work-centre x year baseline set by staff with a year or more (7,940 vs 4,402 pieces, 900,795 pieces worked, q260, q262). The ratio stays about the same within part x work centre x job-size band (1.827x, q214) and within work centre x month x overtime (1.811x, q217). It also holds within the same people: 47 hires who stayed 3+ years ran at 1.787x in year 1, 1.001x in years 2-3 and 0.968x from year 4 (q212). So it is a learning curve, not selection. The excess is 3,538 pieces over 10 years, 353.8 a year (q262). At cost (GL scrap-material memo ratio 0.327 plus rework labour at the GL memo rate) that is about $18,914 a year (q225). At selling price it is at most $54,971 a year (q168), an upper bound, not a recoverable cost. Interpretation: the reason codes, entered at the machine, cannot say what kind of defect new hires make. On ops worked only by first-year staff, OE runs at 5.94x the tenured rate and DOT at 0.509x (q210), which suggests the label depends on who is reporting. Action: give new hires first-piece checks and paired setups, and judge them on total scrap per piece against a work-centre baseline, not on operator-error counts. The gain is modest.",
 "dollars_a_year": 18914.0,
 "size_query": "q225",
 "claims": [
  {
   "text": "Top 10% of the 7,725 parts with order jobs carry 69.4% of DOT+OE scrap value ($4,716,749, 2016-2025), but the top 10% by sales value already carry 62.11%. The concentration follows volume and value.",
   "queries": [
    "q109"
   ]
  },
  {
   "text": "Of 23,406 part x work-centre combinations (9,076 with any DOT+OE scrap), the top 10% by throughput hold 58.65% of scrap vs 57.75% of throughput. Scrap is proportional; the 78.22% top-decile share by scrap value reflects zero-heavy data.",
   "queries": [
    "q159"
   ]
  },
  {
   "text": "Part-level scrap persists only weakly after routing. Half-period correlation 0.0409 (258 parts); odd/even job correlation -0.0249 on pieces and 0.1144 on events (516 parts); event overdispersion chi2/df 1.255 (445 parts). The top even-job quintile (O/E 1.429) runs at 1.017x events and 0.965x pieces on odd jobs.",
   "queries": [
    "q153",
    "q218",
    "q219"
   ]
  },
  {
   "text": "Family scrap is explained by routing (O/E 0.946-1.033). For parts created 2017+, first runs are at 0.984x (DOT+OE, 4,800 jobs) and 0.974x (all reasons), against 1.007x and 0.984x for run 4 onward.",
   "queries": [
    "q154",
    "q222"
   ]
  },
  {
   "text": "Employee scrap rates correlate 0.8751 across halves raw (49 employees), but -0.1682 within work-centre mix (56 employees).",
   "queries": [
    "q143",
    "q151"
   ]
  },
  {
   "text": "First-year staff: 7,940 scrap pieces against 4,402 expected at the tenured work-centre x year rate (1.804x, 900,795 pieces, 2016-2025). 1.827x within part x work centre x job-size band; 1.811x within work centre x month x overtime. Tenured overtime entries carry no scrap (0.0 vs 0.00424 regular).",
   "queries": [
    "q260",
    "q262",
    "q214",
    "q217"
   ]
  },
  {
   "text": "Within the same people: 47 hires who stayed 3+ years ran at 1.787x in year 1, 1.001x in years 2-3 and 0.968x from year 4. 51 who stayed 1-3 years went from 1.798x to 1.05x. 23 who left within a year ran at 2.094x (685 vs 327 pieces). Learning, not survivorship.",
   "queries": [
    "q212"
   ]
  },
  {
   "text": "The pattern holds in every year 2016-2025 (1.477-2.519x), and 110 of 112 first-year hires are above expected (median 1.783x).",
   "queries": [
    "q156",
    "q158"
   ]
  },
  {
   "text": "On ops worked only by first-year staff (865,968 pieces), OE runs at 5.94x the tenured rate (4,704 vs 792) and DOT at 0.509x (1,356 vs 2,663); DOT+OE combined at 1.754x (6,060 vs 3,455). Interpretation: the label appears to depend on tenure, so the codes cannot separate defect types.",
   "queries": [
    "q210",
    "q225"
   ]
  },
  {
   "text": "1,186 ops (7,474 of 46,931 scrap-report pieces) have scrap reports but no rework entry, mostly wrong revision (2,061 pieces). First-year staff did 12.61% of original pieces there, against 9.68% on scrap-free ops, so leaving them out does not inflate the tenure effect.",
   "queries": [
    "q205",
    "q207",
    "q227"
   ]
  },
  {
   "text": "Excess 3,538 pieces over 10 years (353.8 a year). Cost basis: the GL scrap-material memo is 0.327 of all scrap-report value at selling price ($2,474,799 / $7,568,632), giving $17,974 a year in material. Adding 685 rework hours over 10 years at $13.73 per hour ($940 a year) gives $18,914 a year. At selling price the upper bound is $54,971 a year.",
   "queries": [
    "q223",
    "q224",
    "q225",
    "q262",
    "q168"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that any individual new hire is a problem: the effect is broad (110 of 112) and fades within the same people. Not evidence that out-of-tolerance scrap is a process issue separate from operator experience, or that operator error is the new-hire defect type: the reason codes look like tenure-dependent labels. Not evidence of where defects originate (scrap is booked where found). Not evidence that $54,971 a year is recoverable: it is a selling-price upper bound, and onboarding could at most close the gap to the tenured rate. The high top-decile shares (69.4%, 78.22%) are not evidence of fixable hot spots.",
 "could_not_tell": "What defect types new hires actually make (reason codes are entered at the machine and appear to depend on who enters them; an independent inspector classification would be needed). Where out-of-tolerance defects originate (no cause-operation coding). Whether new hires are supervised differently. Lost capacity and late-remake cost of scrap. Wrong-revision, paint and weld scrap without rework entries (7,474 pieces) is largely outside the labour-based analysis.",
 "next_step": "Trial structured onboarding (first-piece verification, paired setups) for new hires and track each hire's total scrap per piece over their first 12 months against the tenured work-centre baseline (expected about 1.8x falling to about 1.0x). Have inspection, not the operator, assign the reason code on a sample of scrap reports to test whether DOT vs OE labelling depends on tenure. Add cause-operation coding to scrap reports.",
 "incomplete": false
}

[
 {
  "id": "q109",
  "sql": "WITH prod AS (\n SELECT j.part_id, sum(j.quantity) pcs, sum(j.quantity*l.unit_price) val\n FROM erp_jobs j JOIN erp_so_lines l ON l.line_id=j.line_id WHERE j.kind='order' GROUP BY 1),\nsc AS (\n SELECT j.part_id, sum(s.quantity) spcs, sum(s.quantity*l.unit_price) sval\n FROM shop_scrap_reports s JOIN erp_jobs j USING(job_id) JOIN erp_so_lines l ON l.line_id=j.line_id\n WHERE s.reason_code IN ('dimension out of tolerance','operator error') GROUP BY 1),\na AS (SELECT p.part_id, p.pcs, p.val, coalesce(sc.spcs,0) spcs, coalesce(sc.sval,0) sval FROM prod p LEFT JOIN sc USING(part_id)),\nr AS (SELECT *, row_number() OVER (ORDER BY sval DESC, part_id) rs, row_number() OVER (ORDER BY val DESC, part_id) rv, count(*) OVER () n FROM a)\nSELECT max(n) parts_with_jobs, sum(CASE WHEN sval>0 THEN 1 ELSE 0 END) parts_with_scrap,\n round(sum(CASE WHEN rs<=n*0.1 THEN sval END)/sum(sval),4) top10_scrap_share_of_scrap,\n round(sum(CASE WHEN rs<=n*0.1 THEN val END)/sum(val),4) top10scrap_parts_share_of_prodval,\n round(sum(CASE WHEN rv<=n*0.1 THEN val END)/sum(val),4) top10_prodval_share_of_prodval,\n round(sum(CASE WHEN rv<=n*0.1 THEN sval END)/sum(sval),4) top10prod_parts_share_of_scrap,\n round(sum(sval),0) scrap_val, round(sum(val),0) prod_val\nFROM r",
  "columns": [
   "parts_with_jobs",
   "parts_with_scrap",
   "top10_scrap_share_of_scrap",
   "top10scrap_parts_share_of_prodval",
   "top10_prodval_share_of_prodval",
   "top10prod_parts_share_of_scrap",
   "scrap_val",
   "prod_val"
  ],
  "row_count": 1,
  "rows": [
   [
    7725,
    4986,
    0.694,
    0.5167,
    0.5872,
    0.6211,
    4716749.0,
    281293085.0
   ]
  ],
  "error": null
 },
 {
  "id": "q159",
  "sql": "WITH sc AS (SELECT op_id, sum(quantity) s FROM shop_scrap_reports WHERE reason_code IN ('dimension out of tolerance','operator error') GROUP BY 1),\no AS (SELECT j.part_id, o.work_centre, sum(j.quantity*l.unit_price) pv, sum(coalesce(sc.s,0)*l.unit_price) sv\n FROM erp_job_operations o JOIN erp_jobs j USING(job_id) JOIN erp_so_lines l ON l.line_id=j.line_id LEFT JOIN sc USING(op_id)\n WHERE j.kind='order' AND o.work_centre<>'inspect' GROUP BY 1,2),\nr AS (SELECT *, row_number() OVER (ORDER BY sv DESC, part_id, work_centre) rs, row_number() OVER (ORDER BY pv DESC, part_id, work_centre) rp, count(*) OVER () n FROM o)\nSELECT max(n) combos, sum(CASE WHEN sv>0 THEN 1 ELSE 0 END) with_scrap,\n round(sum(CASE WHEN rs<=n*0.1 THEN sv END)/sum(sv),4) top10_scrap_share, round(sum(CASE WHEN rs<=n*0.1 THEN pv END)/sum(pv),4) their_throughput_share,\n round(sum(CASE WHEN rp<=n*0.1 THEN sv END)/sum(sv),4) top10_by_throughput_scrap_share, round(sum(CASE WHEN rp<=n*0.1 THEN pv END)/sum(pv),4) top10_throughput_share\nFROM r",
  "columns": [
   "combos",
   "with_scrap",
   "top10_scrap_share",
   "their_throughput_share",
   "top10_by_throughput_scrap_share",
   "top10_throughput_share"
  ],
  "row_count": 1,
  "rows": [
   [
    23406,
    9076,
    0.7822,
    0.4538,
    0.5865,
    0.5775
   ]
  ],
  "error": null
 },
 {
  "id": "q153",
  "sql": "WITH sc AS (SELECT op_id, sum(quantity) s FROM shop_scrap_reports WHERE reason_code IN ('dimension out of tolerance','operator error') GROUP BY 1),\no AS (SELECT j.part_id, o.work_centre, CASE WHEN year(CAST(j.released_on AS DATE))<=2020 THEN 1 ELSE 2 END hf, j.quantity q, coalesce(sc.s,0) s\n FROM erp_job_operations o JOIN erp_jobs j USING(job_id) LEFT JOIN sc USING(op_id) WHERE j.kind='order' AND j.released_on IS NOT NULL),\nwc AS (SELECT work_centre, hf, sum(s)/sum(q) wr FROM o GROUP BY 1,2),\nph AS (SELECT part_id, hf, sum(s) s, sum(q*wr) e FROM o JOIN wc USING(work_centre,hf) GROUP BY 1,2),\nw AS (SELECT a.part_id, a.s/a.e oe1, b.s/b.e oe2, a.s s1, b.s s2, a.e e1, b.e e2 FROM ph a JOIN ph b ON a.part_id=b.part_id AND a.hf=1 AND b.hf=2 WHERE a.e>=5 AND b.e>=5)\nSELECT count(*) n_parts, round(corr(oe1,oe2),4) corr_oe, \n round(sum(CASE WHEN oe1>=2 THEN s2 END)/sum(CASE WHEN oe1>=2 THEN e2 END),3) h2_oe_of_h1_high, count(*) FILTER (WHERE oe1>=2) n_high,\n round(sum(CASE WHEN oe1<0.5 THEN s2 END)/sum(CASE WHEN oe1<0.5 THEN e2 END),3) h2_oe_of_h1_low, count(*) FILTER (WHERE oe1<0.5) n_low,\n round(sum(CASE WHEN oe1>=2 THEN s2-e2 END),0) h2_excess_pcs_high\nFROM w",
  "columns": [
   "n_parts",
   "corr_oe",
   "h2_oe_of_h1_high",
   "n_high",
   "h2_oe_of_h1_low",
   "n_low",
   "h2_excess_pcs_high"
  ],
  "row_count": 1,
  "rows": [
   [
    258,
    0.0409,
    0.985,
    8,
    0.949,
    22,
    -2.0
   ]
  ],
  "error": null
 },
 {
  "id": "q218",
  "sql": "WITH sc AS (SELECT op_id, sum(quantity) s, count(*) ev FROM shop_scrap_reports WHERE reason_code IN ('dimension out of tolerance','operator error') GROUP BY 1),\no AS (SELECT j.part_id, j.job_id, o.work_centre, CASE WHEN year(CAST(j.released_on AS DATE))<=2020 THEN 1 ELSE 2 END hf, j.quantity q, coalesce(sc.s,0) s, coalesce(sc.ev,0) ev\n FROM erp_job_operations o JOIN erp_jobs j USING(job_id) LEFT JOIN sc USING(op_id) WHERE j.kind='order' AND j.released_on IS NOT NULL),\nwc AS (SELECT work_centre, sum(s)/sum(q) wr, sum(ev)/sum(q) wev FROM o GROUP BY 1),\nx AS (SELECT o.*, q*wr e, q*wev eev, CASE WHEN job_id%2=0 THEN 1 ELSE 2 END par FROM o JOIN wc USING(work_centre)),\nsp AS (SELECT part_id, par, sum(s) s, sum(e) e, sum(ev) ev, sum(eev) eev FROM x GROUP BY 1,2),\nw AS (SELECT a.part_id, a.s/a.e o1, b.s/b.e o2, a.ev/a.eev v1, b.ev/b.eev v2, a.e e1, b.e e2 FROM sp a JOIN sp b ON a.part_id=b.part_id AND a.par=1 AND b.par=2),\nph AS (SELECT part_id, sum(ev) ev, sum(eev) eev FROM x GROUP BY 1 HAVING sum(eev)>=10)\nSELECT 'oddeven_e>=5' k, count(*) n, round(corr(o1,o2),4) c_pcs, round(corr(v1,v2),4) c_events FROM w WHERE e1>=5 AND e2>=5\nUNION ALL SELECT 'oddeven_e>=20', count(*), round(corr(o1,o2),4), round(corr(v1,v2),4) FROM w WHERE e1>=20 AND e2>=20\nUNION ALL SELECT 'events_dispersion_chi2_over_df(parts eev>=10)', count(*), round(sum((ev-eev)^2/eev)/(count(*)-1),3), NULL FROM ph\nORDER BY 1",
  "columns": [
   "k",
   "n",
   "c_pcs",
   "c_events"
  ],
  "row_count": 3,
  "rows": [
   [
    "events_dispersion_chi2_over_df(parts eev>=10)",
    445,
    1.255,
    null
   ],
   [
    "oddeven_e>=20",
    43,
    -0.1519,
    0.2374
   ],
   [
    "oddeven_e>=5",
    516,
    -0.0249,
    0.1144
   ]
  ],
  "error": null
 },
 {
  "id": "q219",
  "sql": "WITH sc AS (SELECT op_id, sum(quantity) s, count(*) ev FROM shop_scrap_reports WHERE reason_code IN ('dimension out of tolerance','operator error') GROUP BY 1),\no AS (SELECT j.part_id, j.job_id, o.work_centre, j.quantity q, coalesce(sc.s,0) s, coalesce(sc.ev,0) ev\n FROM erp_job_operations o JOIN erp_jobs j USING(job_id) LEFT JOIN sc USING(op_id) WHERE j.kind='order' AND j.released_on IS NOT NULL),\nwc AS (SELECT work_centre, sum(s)/sum(q) wr, sum(ev)/sum(q) wev FROM o GROUP BY 1),\nx AS (SELECT o.*, q*wr e, q*wev eev, CASE WHEN job_id%2=0 THEN 1 ELSE 2 END par FROM o JOIN wc USING(work_centre)),\nsp AS (SELECT part_id, par, sum(s) s, sum(e) e, sum(ev) ev, sum(eev) eev FROM x GROUP BY 1,2),\nw AS (SELECT a.part_id, a.ev/a.eev v1, b.ev b_ev, b.eev b_eev, b.s b_s, b.e b_e FROM sp a JOIN sp b ON a.part_id=b.part_id AND a.par=1 AND b.par=2 WHERE a.eev>=5 AND b.eev>=5),\nr AS (SELECT *, ntile(5) OVER (ORDER BY v1, part_id) qn FROM w)\nSELECT qn, count(*) parts, round(avg(v1),3) mean_oe_events_even, round(sum(b_ev)/sum(b_eev),3) odd_oe_events, round(sum(b_s)/sum(b_e),3) odd_oe_pcs, round(sum(b_ev-b_eev),0) odd_excess_events FROM r GROUP BY 1 ORDER BY 1",
  "columns": [
   "qn",
   "parts",
   "mean_oe_events_even",
   "odd_oe_events",
   "odd_oe_pcs",
   "odd_excess_events"
  ],
  "row_count": 5,
  "rows": [
   [
    1,
    67,
    0.506,
    0.825,
    1.068,
    -140.0
   ],
   [
    2,
    67,
    0.747,
    0.88,
    1.116,
    -100.0
   ],
   [
    3,
    67,
    0.899,
    0.931,
    0.971,
    -52.0
   ],
   [
    4,
    66,
    1.092,
    0.993,
    1.01,
    -5.0
   ],
   [
    5,
    66,
    1.429,
    1.017,
    0.965,
    11.0
   ]
  ],
  "error": null
 },
 {
  "id": "q154",
  "sql": "WITH sc AS (SELECT op_id, sum(quantity) s FROM shop_scrap_reports WHERE reason_code IN ('dimension out of tolerance','operator error') GROUP BY 1),\no AS (SELECT p.family, o.work_centre, j.quantity q, coalesce(sc.s,0) s\n FROM erp_job_operations o JOIN erp_jobs j USING(job_id) JOIN erp_customer_parts p ON p.part_id=j.part_id LEFT JOIN sc USING(op_id) WHERE j.kind='order'),\nwc AS (SELECT work_centre, sum(s)/sum(q) wr FROM o GROUP BY 1)\nSELECT family, sum(s) scrap_pcs, round(sum(q*wr),0) expected_pcs, round(sum(s)/sum(q*wr),3) o_e FROM o JOIN wc USING(work_centre) GROUP BY 1 ORDER BY 1",
  "columns": [
   "family",
   "scrap_pcs",
   "expected_pcs",
   "o_e"
  ],
  "row_count": 6,
  "rows": [
   [
    1,
    16175,
    15827.0,
    1.022
   ],
   [
    2,
    6718,
    7104.0,
    0.946
   ],
   [
    3,
    1054,
    1064.0,
    0.99
   ],
   [
    4,
    1111,
    1145.0,
    0.97
   ],
   [
    5,
    3710,
    3592.0,
    1.033
   ],
   [
    6,
    655,
    691.0,
    0.948
   ]
  ],
  "error": null
 },
 {
  "id": "q222",
  "sql": "WITH sc AS (SELECT op_id, sum(quantity) FILTER (WHERE reason_code IN ('dimension out of tolerance','operator error')) s, sum(quantity) sall FROM shop_scrap_reports GROUP BY 1),\njb AS (SELECT j.job_id, j.part_id, j.quantity, CAST(p.created_on AS DATE) pc, row_number() OVER (PARTITION BY j.part_id ORDER BY j.released_on, j.job_id) runno\n FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) WHERE j.kind='order' AND j.released_on IS NOT NULL),\no AS (SELECT jb.*, o.work_centre, coalesce(sc.s,0) s, coalesce(sc.sall,0) sall FROM jb JOIN erp_job_operations o USING(job_id) LEFT JOIN sc USING(op_id)),\nwc AS (SELECT work_centre, sum(s)/sum(quantity) wr, sum(sall)/sum(quantity) wra FROM o GROUP BY 1)\nSELECT CASE WHEN pc>=DATE '2017-01-01' THEN 'part created 2017+' ELSE 'part created pre-2017' END cohort,\n CASE WHEN runno=1 THEN '1 first' WHEN runno<=3 THEN '2 run2-3' ELSE '3 run4+' END run,\n count(DISTINCT job_id) jobs, sum(s) dot_oe, round(sum(s)/sum(quantity*wr),3) oe_dotoe, sum(sall) all_reasons, round(sum(sall)/sum(quantity*wra),3) oe_all\nFROM o JOIN wc USING(work_centre) GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "cohort",
   "run",
   "jobs",
   "dot_oe",
   "oe_dotoe",
   "all_reasons",
   "oe_all"
  ],
  "row_count": 6,
  "rows": [
   [
    "part created 2017+",
    "1 first",
    4800,
    1731,
    0.984,
    2713,
    0.974
   ],
   [
    "part created 2017+",
    "2 run2-3",
    7644,
    2898,
    1.009,
    4888,
    1.074
   ],
   [
    "part created 2017+",
    "3 run4+",
    27687,
    10557,
    1.007,
    16359,
    0.984
   ],
   [
    "part created pre-2017",
    "1 first",
    2916,
    942,
    0.863,
    1563,
    0.9
   ],
   [
    "part created pre-2017",
    "2 run2-3",
    5009,
    1807,
    0.932,
    2980,
    0.967
   ],
   [
    "part created pre-2017",
    "3 run4+",
    28263,
    11488,
    1.018,
    18241,
    1.016
   ]
  ],
  "error": null
 },
 {
  "id": "q143",
  "sql": "WITH le AS (\n SELECT e.employee_id, year(CAST(e.work_date AS DATE)) yr, e.qty_good, e.qty_scrap, l.unit_price\n FROM shop_labour_entries e JOIN erp_jobs j ON j.job_id=e.job_id JOIN erp_so_lines l ON l.line_id=j.line_id),\nemp AS (SELECT employee_id, sum(qty_good+qty_scrap) pcs, sum(qty_scrap) s, sum(qty_scrap*unit_price) sval, sum((qty_good+qty_scrap)*unit_price) pval FROM le GROUP BY 1),\nr AS (SELECT *, row_number() OVER (ORDER BY sval DESC, employee_id) rs, row_number() OVER (ORDER BY pval DESC, employee_id) rp, count(*) OVER () n FROM emp WHERE pcs>0),\nh AS (SELECT employee_id, CASE WHEN yr<=2020 THEN 1 ELSE 2 END hf, sum(qty_good+qty_scrap) p, sum(qty_scrap) s FROM le GROUP BY 1,2),\nw AS (SELECT a.employee_id, a.s/a.p r1, b.s/b.p r2 FROM h a JOIN h b ON a.employee_id=b.employee_id AND a.hf=1 AND b.hf=2 WHERE a.p>=5000 AND b.p>=5000)\nSELECT max(n) employees, round(sum(CASE WHEN rs<=n*0.1 THEN sval END)/sum(sval),4) top10_share_scrapval,\n round(sum(CASE WHEN rs<=n*0.1 THEN pval END)/sum(pval),4) same_emps_share_prodval,\n round(sum(CASE WHEN rp<=n*0.1 THEN sval END)/sum(sval),4) top10prod_emps_share_scrapval,\n round(sum(s)/sum(pcs),5) overall_rate,\n round(quantile_cont(s/pcs,0.1) FILTER (WHERE pcs>=10000),5) p10_rate_10k, round(quantile_cont(s/pcs,0.9) FILTER (WHERE pcs>=10000),5) p90_rate_10k,\n count(*) FILTER (WHERE pcs>=10000) n10k,\n (SELECT count(*) FROM w) both_halves, (SELECT round(corr(r1,r2),4) FROM w) corr_halves\nFROM r",
  "columns": [
   "employees",
   "top10_share_scrapval",
   "same_emps_share_prodval",
   "top10prod_emps_share_scrapval",
   "overall_rate",
   "p10_rate_10k",
   "p90_rate_10k",
   "n10k",
   "both_halves",
   "corr_halves"
  ],
  "row_count": 1,
  "rows": [
   [
    208,
    0.3868,
    0.33,
    0.2672,
    0.00459,
    0.0026,
    0.01021,
    111,
    49,
    0.8751
   ]
  ],
  "error": null
 },
 {
  "id": "q151",
  "sql": "WITH le AS (\n SELECT e.employee_id, o.work_centre, CASE WHEN year(CAST(e.work_date AS DATE))<=2020 THEN 1 ELSE 2 END hf, e.qty_good+e.qty_scrap p, e.qty_scrap s\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id),\nwc AS (SELECT work_centre, hf, CASE WHEN sum(p)>0 THEN sum(s)/sum(p) ELSE 0 END wr FROM le GROUP BY 1,2),\neh AS (SELECT le.employee_id, le.hf, sum(le.p) p, sum(le.s) s, sum(le.p*wc.wr) e FROM le JOIN wc USING(work_centre,hf) GROUP BY 1,2),\nw AS (SELECT a.employee_id, a.s/a.e oe1, b.s/b.e oe2 FROM eh a JOIN eh b ON a.employee_id=b.employee_id AND a.hf=1 AND b.hf=2 WHERE a.e>=20 AND b.e>=20),\nal AS (SELECT employee_id, sum(p) p, sum(s) s, sum(e) e FROM eh GROUP BY 1 HAVING sum(e)>=50)\nSELECT (SELECT count(*) FROM w) n_both, (SELECT round(corr(oe1,oe2),4) FROM w) corr_oe_halves,\n count(*) n_emp, round(quantile_cont(s/e,0.1),3) p10_oe, round(quantile_cont(s/e,0.5),3) p50_oe, round(quantile_cont(s/e,0.9),3) p90_oe, round(max(s/e),3) max_oe,\n sum(CASE WHEN s/e>=1.5 THEN 1 ELSE 0 END) n_oe_ge_1_5, round(sum(CASE WHEN s/e>=1.5 THEN s-e ELSE 0 END),0) excess_pcs_ge1_5,\n round(sum(CASE WHEN s>e THEN s-e ELSE 0 END),0) excess_all_above1, sum(s) scrap_these, round(sum(e),0) exp_these\nFROM al",
  "columns": [
   "n_both",
   "corr_oe_halves",
   "n_emp",
   "p10_oe",
   "p50_oe",
   "p90_oe",
   "max_oe",
   "n_oe_ge_1_5",
   "excess_pcs_ge1_5",
   "excess_all_above1",
   "scrap_these",
   "exp_these"
  ],
  "row_count": 1,
  "rows": [
   [
    56,
    -0.1682,
    121,
    0.838,
    0.971,
    1.243,
    2.119,
    4,
    297.0,
    1626.0,
    33932,
    34455.0
   ]
  ],
  "error": null
 },
 {
  "id": "q260",
  "sql": "WITH le AS (\n SELECT o.work_centre, year(CAST(e.work_date AS DATE)) yr, e.qty_good+e.qty_scrap p, e.qty_scrap s,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) ten\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id),\nb1 AS (SELECT work_centre, sum(s)/sum(p) r FROM le WHERE ten>=365 GROUP BY 1),\nb2 AS (SELECT work_centre, yr, sum(s)/sum(p) r FROM le WHERE ten>=365 GROUP BY 1,2),\nb3 AS (SELECT work_centre, sum(s)/sum(p) r FROM le WHERE ten>=1095 GROUP BY 1)\nSELECT sum(s) first_year_scrap, sum(p) first_year_pcs,\n round(sum(p*b1.r),0) exp_wc_tenured1y, round(sum(p*b2.r),0) exp_wc_year_tenured1y, round(sum(p*b3.r),0) exp_wc_tenured3y\nFROM le JOIN b1 USING(work_centre) JOIN b2 USING(work_centre,yr) JOIN b3 USING(work_centre) WHERE ten<365 AND ten>=0",
  "columns": [
   "first_year_scrap",
   "first_year_pcs",
   "exp_wc_tenured1y",
   "exp_wc_year_tenured1y",
   "exp_wc_tenured3y"
  ],
  "row_count": 1,
  "rows": [
   [
    7940,
    900795,
    4375.0,
    4402.0,
    4344.0
   ]
  ],
  "error": null
 },
 {
  "id": "q262",
  "sql": "SELECT 7940-4402 excess_pcs_10y, round((7940-4402)/10.0,1) excess_pcs_per_yr, round(7940/4402.0,3) o_e_wc_year, round(18914.0/247480.0,4) cost_excess_share_of_gl_scrap_memo, round(3538.0/46931,4) excess_share_all_scrap_pcs",
  "columns": [
   "excess_pcs_10y",
   "excess_pcs_per_yr",
   "o_e_wc_year",
   "cost_excess_share_of_gl_scrap_memo",
   "excess_share_all_scrap_pcs"
  ],
  "row_count": 1,
  "rows": [
   [
    3538,
    353.8,
    1.804,
    0.0764,
    0.0754
   ]
  ],
  "error": null
 },
 {
  "id": "q214",
  "sql": "WITH le AS (\n SELECT j.part_id, o.work_centre, j.quantity jq, e.qty_good+e.qty_scrap p, e.qty_scrap s,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 nb\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id\n JOIN erp_jobs j ON j.job_id=e.job_id),\nb AS (SELECT *, CASE WHEN jq<10 THEN 1 WHEN jq<25 THEN 2 WHEN jq<50 THEN 3 WHEN jq<100 THEN 4 ELSE 5 END qb FROM le),\npw AS (SELECT part_id, work_centre, qb, sum(s)/sum(p) r FROM b WHERE NOT nb GROUP BY 1,2,3 HAVING sum(p)>=500)\nSELECT 'by_band' k, qb, nb, sum(p) pcs, sum(s) scrap, round(sum(s)*1.0/sum(p),5) rate, NULL o_e FROM b GROUP BY 2,3\nUNION ALL\nSELECT 'part_wc_band', NULL, nb, sum(p), sum(s), NULL, round(sum(s)/sum(p*r),3) FROM b JOIN pw USING(part_id,work_centre,qb) GROUP BY 3\nORDER BY 1,2,3",
  "columns": [
   "k",
   "qb",
   "nb",
   "pcs",
   "scrap",
   "rate",
   "o_e"
  ],
  "row_count": 12,
  "rows": [
   [
    "by_band",
    1,
    false,
    402686,
    1682,
    0.00418,
    null
   ],
   [
    "by_band",
    1,
    true,
    54098,
    417,
    0.00771,
    null
   ],
   [
    "by_band",
    2,
    false,
    1472377,
    6224,
    0.00423,
    null
   ],
   [
    "by_band",
    2,
    true,
    192829,
    1729,
    0.00897,
    null
   ],
   [
    "by_band",
    3,
    false,
    2171895,
    9078,
    0.00418,
    null
   ],
   [
    "by_band",
    3,
    true,
    282506,
    2503,
    0.00886,
    null
   ],
   [
    "by_band",
    4,
    false,
    1737921,
    7207,
    0.00415,
    null
   ],
   [
    "by_band",
    4,
    true,
    229156,
    2121,
    0.00926,
    null
   ],
   [
    "by_band",
    5,
    false,
    1240514,
    4231,
    0.00341,
    null
   ],
   [
    "by_band",
    5,
    true,
    142206,
    1170,
    0.00823,
    null
   ],
   [
    "part_wc_band",
    null,
    false,
    2780629,
    10632,
    null,
    1.0
   ],
   [
    "part_wc_band",
    null,
    true,
    327589,
    2793,
    null,
    1.827
   ]
  ],
  "error": null
 },
 {
  "id": "q217",
  "sql": "WITH le AS (\n SELECT o.work_centre, strftime(CAST(e.work_date AS DATE),'%Y-%m') ym, e.overtime ot, e.qty_good+e.qty_scrap p, e.qty_scrap s,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 nb\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id),\nbase AS (SELECT work_centre, ym, ot, sum(s)/sum(p) r FROM le WHERE NOT nb GROUP BY 1,2,3 HAVING sum(p)>0)\nSELECT nb, sum(p) pcs, sum(s) scrap, round(sum(p*r),0) exp, round(sum(s)/sum(p*r),3) o_e,\n round(avg(ot),4) ot_share_entries,\n (SELECT round(sum(s) FILTER (WHERE ot=1)*1.0/sum(p) FILTER (WHERE ot=1),5) FROM le WHERE NOT nb) tenured_ot_rate,\n (SELECT round(sum(s) FILTER (WHERE ot=0)*1.0/sum(p) FILTER (WHERE ot=0),5) FROM le WHERE NOT nb) tenured_reg_rate\nFROM le JOIN base USING(work_centre,ym,ot) GROUP BY 1 ORDER BY 1",
  "columns": [
   "nb",
   "pcs",
   "scrap",
   "exp",
   "o_e",
   "ot_share_entries",
   "tenured_ot_rate",
   "tenured_reg_rate"
  ],
  "row_count": 2,
  "rows": [
   [
    false,
    7025393,
    28422,
    28422.0,
    1.0,
    0.0502,
    0.0,
    0.00424
   ],
   [
    true,
    900795,
    7940,
    4384.0,
    1.811,
    0.0707,
    0.0,
    0.00424
   ]
  ],
  "error": null
 },
 {
  "id": "q212",
  "sql": "WITH le AS (\n SELECT e.employee_id, o.work_centre, e.qty_good+e.qty_scrap p, e.qty_scrap s,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) ten,\n  CAST(h.hired_on AS DATE) hired, CAST(h.terminated_on AS DATE) term\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id),\nwc AS (SELECT work_centre, sum(s)/sum(p) wr FROM le WHERE ten>=365 GROUP BY 1),\nx AS (SELECT le.*, p*wr ex,\n  CASE WHEN term IS NOT NULL AND date_diff('day',hired,term)<365 THEN 'a left <1y'\n       WHEN date_diff('day',hired,coalesce(term,DATE '2025-12-31'))>=1095 AND hired>=DATE '2016-01-01' THEN 'c stayed 3y+ (hired in window)'\n       WHEN hired>=DATE '2016-01-01' THEN 'b stayed 1-3y' ELSE 'd hired pre-2016' END grp,\n  CASE WHEN ten<365 THEN 'y1' WHEN ten<1095 THEN 'y2-3' ELSE 'y4+' END tb\n FROM le JOIN wc USING(work_centre))\nSELECT grp, tb, count(DISTINCT employee_id) emps, sum(p) pcs, sum(s) scrap, round(sum(ex),0) exp, round(sum(s)/sum(ex),3) o_e\nFROM x GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "grp",
   "tb",
   "emps",
   "pcs",
   "scrap",
   "exp",
   "o_e"
  ],
  "row_count": 8,
  "rows": [
   [
    "a left <1y",
    "y1",
    23,
    57184,
    685,
    327.0,
    2.094
   ],
   [
    "b stayed 1-3y",
    "y1",
    51,
    425253,
    3516,
    1956.0,
    1.798
   ],
   [
    "b stayed 1-3y",
    "y2-3",
    44,
    413547,
    2040,
    1942.0,
    1.05
   ],
   [
    "c stayed 3y+ (hired in window)",
    "y1",
    47,
    418358,
    3739,
    2092.0,
    1.787
   ],
   [
    "c stayed 3y+ (hired in window)",
    "y2-3",
    47,
    824359,
    4078,
    4073.0,
    1.001
   ],
   [
    "c stayed 3y+ (hired in window)",
    "y4+",
    47,
    905961,
    4078,
    4214.0,
    0.968
   ],
   [
    "d hired pre-2016",
    "y2-3",
    12,
    107787,
    557,
    532.0,
    1.047
   ],
   [
    "d hired pre-2016",
    "y4+",
    87,
    4773739,
    17669,
    17661.0,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q156",
  "sql": "WITH le AS (\n SELECT o.work_centre, e.qty_good+e.qty_scrap p, e.qty_scrap s, l.unit_price up, year(CAST(e.work_date AS DATE)) yr,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 newbie\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id\n JOIN erp_jobs j ON j.job_id=e.job_id JOIN erp_so_lines l ON l.line_id=j.line_id),\nwc AS (SELECT work_centre, yr, CASE WHEN sum(p)>0 THEN sum(s)/sum(p) ELSE 0 END wr FROM le WHERE NOT newbie GROUP BY 1,2)\nSELECT yr, sum(CASE WHEN newbie THEN p END) new_pcs, sum(CASE WHEN newbie THEN s END) new_scrap, round(sum(CASE WHEN newbie THEN p*wr END),0) new_exp_at_tenured,\n round(sum(CASE WHEN newbie THEN s END)/sum(CASE WHEN newbie THEN p*wr END),3) new_o_e,\n round(sum(CASE WHEN newbie THEN (s - p*wr)*up END),0) excess_val, round(sum(s*up),0) all_scrap_val, sum(s) all_scrap_pcs\nFROM le LEFT JOIN wc USING(work_centre,yr) GROUP BY ROLLUP(yr) ORDER BY yr NULLS LAST",
  "columns": [
   "yr",
   "new_pcs",
   "new_scrap",
   "new_exp_at_tenured",
   "new_o_e",
   "excess_val",
   "all_scrap_val",
   "all_scrap_pcs"
  ],
  "row_count": 11,
  "rows": [
   [
    2016,
    30109,
    281,
    112.0,
    2.519,
    18833.0,
    441100.0,
    3422
   ],
   [
    2017,
    122682,
    1209,
    632.0,
    1.914,
    70535.0,
    545519.0,
    4165
   ],
   [
    2018,
    107276,
    1179,
    720.0,
    1.638,
    37383.0,
    551715.0,
    4138
   ],
   [
    2019,
    123161,
    827,
    439.0,
    1.885,
    65053.0,
    590952.0,
    3822
   ],
   [
    2020,
    96551,
    520,
    352.0,
    1.477,
    34307.0,
    479208.0,
    3416
   ],
   [
    2021,
    189453,
    1316,
    642.0,
    2.049,
    86381.0,
    573495.0,
    3951
   ],
   [
    2022,
    62988,
    625,
    398.0,
    1.571,
    56295.0,
    621733.0,
    3479
   ],
   [
    2023,
    64926,
    676,
    328.0,
    2.06,
    79237.0,
    706643.0,
    3436
   ],
   [
    2024,
    68576,
    708,
    472.0,
    1.501,
    57741.0,
    630373.0,
    3213
   ],
   [
    2025,
    35073,
    599,
    308.0,
    1.945,
    43947.0,
    647235.0,
    3320
   ],
   [
    null,
    900795,
    7940,
    4402.0,
    1.804,
    549713.0,
    5787974.0,
    36362
   ]
  ],
  "error": null
 },
 {
  "id": "q158",
  "sql": "WITH le AS (\n SELECT e.employee_id, o.work_centre, e.qty_good+e.qty_scrap p, e.qty_scrap s,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 newbie\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id),\nwc AS (SELECT work_centre, CASE WHEN sum(p)>0 THEN sum(s)/sum(p) ELSE 0 END wr FROM le WHERE NOT newbie GROUP BY 1),\nne AS (SELECT employee_id, sum(s) s, sum(p*wr) e FROM le JOIN wc USING(work_centre) WHERE newbie GROUP BY 1 HAVING sum(p*wr)>=5)\nSELECT count(*) new_hires, sum(CASE WHEN s>e THEN 1 ELSE 0 END) above_expected, round(quantile_cont(s/e,0.5),3) median_oe, round(quantile_cont(s/e,0.25),3) p25, round(quantile_cont(s/e,0.75),3) p75,\n round(sum(CASE WHEN rk<=ceil(n*0.1) THEN s-e END)/sum(s-e),4) top10pct_share_of_excess\nFROM (SELECT *, row_number() OVER (ORDER BY s-e DESC, employee_id) rk, count(*) OVER () n FROM ne)",
  "columns": [
   "new_hires",
   "above_expected",
   "median_oe",
   "p25",
   "p75",
   "top10pct_share_of_excess"
  ],
  "row_count": 1,
  "rows": [
   [
    112,
    110,
    1.783,
    1.563,
    1.982,
    0.4714
   ]
  ],
  "error": null
 },
 {
  "id": "q210",
  "sql": "WITH le AS (\n SELECT e.op_id, o.work_centre, e.qty_good+e.qty_scrap p,\n  date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 nb\n FROM shop_labour_entries e JOIN erp_job_operations o ON o.op_id=e.op_id JOIN hr_employees h ON h.employee_id=e.employee_id),\nop AS (SELECT op_id, work_centre, sum(p) p, max(nb::int) anynew, min(nb::int) allnew FROM le GROUP BY 1,2),\ncls AS (SELECT op_id, work_centre, p, CASE WHEN allnew=1 THEN 'new_only' WHEN anynew=0 THEN 'tenured_only' ELSE 'mixed' END c FROM op),\nsr AS (SELECT op_id, reason_code, sum(quantity) q FROM shop_scrap_reports GROUP BY 1,2),\nrc AS (SELECT DISTINCT reason_code FROM shop_scrap_reports),\ngrid AS (SELECT c, work_centre, sum(p) p FROM cls GROUP BY 1,2),\nsc AS (SELECT cls.c, cls.work_centre, sr.reason_code, sum(sr.q) q FROM cls JOIN sr USING(op_id) GROUP BY 1,2,3),\nten AS (SELECT g.work_centre, rc.reason_code, coalesce(s.q,0)*1.0/g.p r FROM grid g CROSS JOIN rc LEFT JOIN sc s ON s.c=g.c AND s.work_centre=g.work_centre AND s.reason_code=rc.reason_code WHERE g.c='tenured_only')\nSELECT g.c, rc.reason_code, sum(coalesce(s.q,0)) scrap, round(sum(g.p*t.r),0) exp_at_tenured, round(sum(coalesce(s.q,0))/nullif(sum(g.p*t.r),0),3) o_e, sum(g.p) pcs\nFROM grid g CROSS JOIN rc LEFT JOIN sc s ON s.c=g.c AND s.work_centre=g.work_centre AND s.reason_code=rc.reason_code\nJOIN ten t ON t.work_centre=g.work_centre AND t.reason_code=rc.reason_code\nWHERE g.c<>'tenured_only' GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "c",
   "reason_code",
   "scrap",
   "exp_at_tenured",
   "o_e",
   "pcs"
  ],
  "row_count": 16,
  "rows": [
   [
    "mixed",
    "dimension out of tolerance",
    166,
    263.0,
    0.632,
    69197
   ],
   [
    "mixed",
    "first article",
    0,
    2.0,
    0.0,
    69197
   ],
   [
    "mixed",
    "material",
    90,
    70.0,
    1.285,
    69197
   ],
   [
    "mixed",
    "operator error",
    243,
    85.0,
    2.847,
    69197
   ],
   [
    "mixed",
    "other",
    76,
    71.0,
    1.069,
    69197
   ],
   [
    "mixed",
    "paint or finish",
    3,
    15.0,
    0.203,
    69197
   ],
   [
    "mixed",
    "weld defect",
    0,
    18.0,
    0.0,
    69197
   ],
   [
    "mixed",
    "wrong revision",
    34,
    35.0,
    0.979,
    69197
   ],
   [
    "new_only",
    "dimension out of tolerance",
    1356,
    2663.0,
    0.509,
    865968
   ],
   [
    "new_only",
    "first article",
    4,
    7.0,
    0.587,
    865968
   ],
   [
    "new_only",
    "material",
    1145,
    762.0,
    1.502,
    865968
   ],
   [
    "new_only",
    "operator error",
    4704,
    792.0,
    5.94,
    865968
   ],
   [
    "new_only",
    "other",
    1113,
    723.0,
    1.54,
    865968
   ],
   [
    "new_only",
    "paint or finish",
    122,
    143.0,
    0.852,
    865968
   ],
   [
    "new_only",
    "weld defect",
    253,
    149.0,
    1.702,
    865968
   ],
   [
    "new_only",
    "wrong revision",
    497,
    402.0,
    1.235,
    865968
   ]
  ],
  "error": null
 },
 {
  "id": "q225",
  "sql": "SELECT round(54971.0*2474799.0/7568632.0,0) excess_yr_material_basis_corrected,\n round(2474799.0/7568632.0,4) ratio_corrected, round(2474799.0/5787974.0,4) ratio_used,\n 7940-4402 excess_pcs_10y, round((7940-4402)*0.1935,0) excess_rework_hours_10y,\n round(108569.0/(6371+1536),2) rework_memo_per_rework_hour,\n round((7940-4402)*0.1935*108569.0/(6371+1536)/10,0) excess_rework_labour_per_yr,\n round(54971.0*2474799.0/7568632.0 + (7940-4402)*0.1935*108569.0/(6371+1536)/10,0) excess_cost_per_yr,\n round(2474799.0/10,0) gl_scrap_memo_per_yr,\n round(1356.0+4704,0) newonly_dotoe, round(2663.0+792,0) newonly_dotoe_exp, round((1356.0+4704)/(2663+792),3) newonly_dotoe_oe",
  "columns": [
   "excess_yr_material_basis_corrected",
   "ratio_corrected",
   "ratio_used",
   "excess_pcs_10y",
   "excess_rework_hours_10y",
   "rework_memo_per_rework_hour",
   "excess_rework_labour_per_yr",
   "excess_cost_per_yr",
   "gl_scrap_memo_per_yr",
   "newonly_dotoe",
   "newonly_dotoe_exp",
   "newonly_dotoe_oe"
  ],
  "row_count": 1,
  "rows": [
   [
    17974.0,
    0.327,
    0.4276,
    3538,
    685.0,
    13.73,
    940.0,
    18914.0,
    247480.0,
    6060.0,
    3455.0,
    1.754
   ]
  ],
  "error": null
 },
 {
  "id": "q205",
  "sql": "WITH sr AS (SELECT op_id, sum(quantity) q, count(*) n FROM shop_scrap_reports GROUP BY 1),\nlr AS (SELECT op_id, sum(qty_scrap) q FROM shop_labour_entries WHERE rework=1 GROUP BY 1)\nSELECT count(*) FILTER (WHERE sr.op_id IS NOT NULL AND lr.op_id IS NOT NULL) both_ops,\n count(*) FILTER (WHERE sr.op_id IS NOT NULL AND lr.op_id IS NULL) sr_only_ops,\n count(*) FILTER (WHERE sr.op_id IS NULL AND lr.op_id IS NOT NULL) lr_only_ops,\n sum(sr.q) sr_pcs, sum(lr.q) lr_pcs,\n sum(CASE WHEN sr.op_id IS NOT NULL AND lr.op_id IS NOT NULL AND sr.q=lr.q THEN 1 ELSE 0 END) equal_qty_ops,\n sum(CASE WHEN sr.op_id IS NOT NULL AND lr.op_id IS NULL THEN sr.q ELSE 0 END) sr_only_pcs\nFROM sr FULL OUTER JOIN lr USING(op_id)",
  "columns": [
   "both_ops",
   "sr_only_ops",
   "lr_only_ops",
   "sr_pcs",
   "lr_pcs",
   "equal_qty_ops",
   "sr_only_pcs"
  ],
  "row_count": 1,
  "rows": [
   [
    29420,
    1186,
    0,
    46931,
    36362,
    29224,
    7474
   ]
  ],
  "error": null
 },
 {
  "id": "q207",
  "sql": "WITH lr AS (SELECT DISTINCT op_id FROM shop_labour_entries WHERE rework=1)\nSELECT s.reason_code, count(*) FILTER (WHERE lr.op_id IS NULL) n_no_rework, sum(CASE WHEN lr.op_id IS NULL THEN s.quantity ELSE 0 END) pcs_no_rework,\n count(*) FILTER (WHERE lr.op_id IS NOT NULL) n_rework, sum(CASE WHEN lr.op_id IS NOT NULL THEN s.quantity ELSE 0 END) pcs_rework\nFROM shop_scrap_reports s LEFT JOIN lr USING(op_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "reason_code",
   "n_no_rework",
   "pcs_no_rework",
   "n_rework",
   "pcs_rework"
  ],
  "row_count": 8,
  "rows": [
   [
    "dimension out of tolerance",
    197,
    662,
    15249,
    18736
   ],
   [
    "first article",
    0,
    0,
    34,
    68
   ],
   [
    "material",
    178,
    1115,
    3924,
    5153
   ],
   [
    "operator error",
    156,
    1157,
    6401,
    8977
   ],
   [
    "other",
    144,
    937,
    3923,
    5087
   ],
   [
    "paint or finish",
    199,
    698,
    29,
    271
   ],
   [
    "weld defect",
    194,
    844,
    37,
    374
   ],
   [
    "wrong revision",
    118,
    2061,
    19,
    791
   ]
  ],
  "error": null
 },
 {
  "id": "q227",
  "sql": "WITH lr AS (SELECT DISTINCT op_id FROM shop_labour_entries WHERE rework=1),\nsro AS (SELECT op_id, sum(quantity) q FROM shop_scrap_reports GROUP BY 1),\nle AS (SELECT e.op_id, e.qty_good+e.qty_scrap p, date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 nb FROM shop_labour_entries e JOIN hr_employees h USING(employee_id) WHERE e.rework=0)\nSELECT CASE WHEN sro.op_id IS NULL THEN 'no scrap report' WHEN lr.op_id IS NULL THEN 'scrap report, no rework entry' ELSE 'scrap report + rework' END grp,\n count(DISTINCT le.op_id) ops, sum(p) pcs, round(sum(CASE WHEN nb THEN p ELSE 0 END)*1.0/sum(p),4) new_share_pcs, sum(DISTINCT 0) z\nFROM le LEFT JOIN sro USING(op_id) LEFT JOIN lr USING(op_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "grp",
   "ops",
   "pcs",
   "new_share_pcs",
   "z"
  ],
  "row_count": 3,
  "rows": [
   [
    "no scrap report",
    278486,
    6383725,
    0.0968,
    0
   ],
   [
    "scrap report + rework",
    29420,
    1480380,
    0.1834,
    0
   ],
   [
    "scrap report, no rework entry",
    1186,
    25721,
    0.1261,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q223",
  "sql": "WITH srv AS (SELECT sum(s.quantity*l.unit_price) v, sum(s.quantity) q FROM shop_scrap_reports s JOIN erp_jobs j USING(job_id) JOIN erp_so_lines l ON l.line_id=j.line_id),\ngl AS (SELECT account, sum(amount) a, min(period) p0, max(period) p1 FROM erp_general_ledger WHERE account ILIKE '%memo%' OR account ILIKE '%rework%' OR account ILIKE '%scrap%' GROUP BY 1)\nSELECT gl.account, round(gl.a,0) total, gl.p0, gl.p1, round(srv.v,0) all_scrap_reports_val_sp, srv.q all_scrap_pcs, round(gl.a/srv.v,4) ratio_to_all_scrap_val FROM gl, srv ORDER BY 1",
  "columns": [
   "account",
   "total",
   "p0",
   "p1",
   "all_scrap_reports_val_sp",
   "all_scrap_pcs",
   "ratio_to_all_scrap_val"
  ],
  "row_count": 3,
  "rows": [
   [
    "overtime hours (memo)",
    18406.0,
    "2016-01",
    "2024-08",
    7568632.0,
    46931,
    0.0024
   ],
   [
    "rework labour (memo)",
    108569.0,
    "2016-01",
    "2025-11",
    7568632.0,
    46931,
    0.0143
   ],
   [
    "scrap material (memo)",
    2474799.0,
    "2016-01",
    "2025-12",
    7568632.0,
    46931,
    0.327
   ]
  ],
  "error": null
 },
 {
  "id": "q224",
  "sql": "WITH le AS (\n SELECT e.rework, e.hours, e.qty_scrap, date_diff('day', CAST(h.hired_on AS DATE), CAST(e.work_date AS DATE)) < 365 nb, year(CAST(e.work_date AS DATE)) yr\n FROM shop_labour_entries e JOIN hr_employees h USING(employee_id))\nSELECT nb, round(sum(hours) FILTER (WHERE rework=1),0) rework_hours, round(sum(hours),0) all_hours, sum(qty_scrap) scrap_pcs, min(yr)||'-'||max(yr) yrs,\n round(sum(hours) FILTER (WHERE rework=1)/sum(qty_scrap),4) rework_hrs_per_scrap_pc\nFROM le GROUP BY 1 ORDER BY 1",
  "columns": [
   "nb",
   "rework_hours",
   "all_hours",
   "scrap_pcs",
   "yrs",
   "rework_hrs_per_scrap_pc"
  ],
  "row_count": 2,
  "rows": [
   [
    false,
    6371.0,
    993445.0,
    28422,
    "2016-2025",
    0.2242
   ],
   [
    true,
    1536.0,
    135347.0,
    7940,
    "2016-2025",
    0.1935
   ]
  ],
  "error": null
 },
 {
  "id": "q168",
  "sql": "SELECT round(549713.0/10,0) excess_per_yr_selling_price, round(549713.0/5787974.0,4) excess_share_of_labour_scrap_val,\n round(2474799.0/5787974.0,4) gl_memo_to_labour_scrap_val, round(549713.0/10*2474799.0/5787974.0,0) excess_per_yr_material_basis_approx,\n round(4716749.0/10,0) dot_oe_val_per_yr, round(7940.0/36362,4) new_share_scrap_pcs, round(900795.0/(SELECT sum(qty_good+qty_scrap) FROM shop_labour_entries),4) new_share_pcs",
  "columns": [
   "excess_per_yr_selling_price",
   "excess_share_of_labour_scrap_val",
   "gl_memo_to_labour_scrap_val",
   "excess_per_yr_material_basis_approx",
   "dot_oe_val_per_yr",
   "new_share_scrap_pcs",
   "new_share_pcs"
  ],
  "row_count": 1,
  "rows": [
   [
    54971.0,
    0.095,
    0.4276,
    23504.0,
    471675.0,
    0.2184,
    0.1136
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

Save `grade.json`: {"finding": "F2", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
