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
 "id": "F8",
 "hypothesis": "H10",
 "title": "Late material is linked to about 2.8 times the late-shipment rate at the same planned slack, but it does not explain the 2016 and 2021 spikes. 2016 was a delay inside the plant. About four tenths of the 2021 excess came from vendor lead times that roughly doubled",
 "conclusion": "Observed: compared at the same promised year and the same planned slack (promise date minus the last PO due date, in weeks, capped at 6+), jobs with a receipt after the PO due date shipped late 0.3573 of the time against 0.1263 for other jobs. That is 2.83 times as often, with all 3,524 late-receipt order jobs matched (promised 2016-2025). It comes to about 814 extra late shipments over 10 years, or 81.4 a year (q366). My earlier figures of about ninefold and 111.9 a year did not control for slack and overstated the effect (q367). Late receipts cluster in tightly planned jobs. In non-spike years, 0.5129 of late-receipt jobs had 14 days or less of planned slack, against 0.1766 of other jobs (q367), and most of the effect sits in that band: 0.5471 (1,453 jobs) vs 0.0869 (10,234) (q364). Late-receipt jobs were flat across years and carried only 0.1486 (2016) and 0.177 (2021) of late shipments (q282). The spikes are periods, not seasons: no calendar month in other years averages above 0.0379 (q368). The two spikes differ. In 2016, slack at release was normal (0.1 of jobs with on-time material released with 14 days or less, the same as other years), yet jobs ran late far more often at every slack level. For example, with more than 35 days of slack the rate was 0.1842 against 0.0039 (q360, q362). In 2021, PO lead times (due minus ordered) roughly doubled: steel 5.6 calendar days against 3.2-3.7, aluminium 13.9 against 6.7-7.3, stainless 12.2 against 6.0-7.7 (q357). Release waits for the last receipt: release equals the last receipt date on 0.9953-1.0 of jobs, and none are released earlier (q352). So create-to-release rose to 9.1 days, against 5.5-6.2 in other years (q344), and 0.1921 of jobs with on-time material were released with 14 days or less of slack (q362). Under one ordering of a non-additive decomposition, about 0.394 of the 2021 excess among jobs with on-time material comes from that tighter slack mix and 0.606 from higher lateness at the same slack (q362, q367). In every year, every late shipment was on a job completed after its promise date (share 1.0, q344). So the delay at the same slack was before job completion, not between completion and shipping. Interpretation: 2016 was a post-release, pre-completion problem inside the plant. 2021 was partly that and partly a material-supply problem. Receipts were measured against PO due dates that had themselves been pushed out, so the late-receipt flag could not see it. For action: measure material timeliness against the job's need date as well as the PO due date. Protect slack on jobs planned with 14 days or less. Look at pre-completion flow in Sep-Dec 2016 and Mar-Oct 2021.",
 "dollars_a_year": null,
 "size_query": null,
 "claims": [
  {
   "text": "At the same year and planned-slack week, late-receipt jobs shipped late 0.3573 vs 0.1263 (ratio 2.83; 3,524 of 3,524 matched), about 814 extra late shipments over 10 years, 81.4 a year. This replaces the unadjusted 8.96x (0.3575/0.0399) and 111.9 a year, a difference of 30.5 a year.",
   "queries": [
    "q366",
    "q367"
   ]
  },
  {
   "text": "Late receipts concentrate in tightly planned jobs. In non-spike years, 0.5129 of late-receipt jobs vs 0.1766 of others had 14 days or less of planned slack. Within slack bands: 14 days or less, 0.5471 (1,453) vs 0.0869 (10,234); 15-21 days, 0.0984 (549) vs 0.0001 (15,752); 22-28 days, 0.0355 (451) vs 0.0004 (11,592); more than 28 days, 0.0026 (380) vs 0.0012 (20,359).",
   "queries": [
    "q364",
    "q367"
   ]
  },
  {
   "text": "The late rate rises with receipt delay: on time 0.0394 (71,812 jobs), 1-3 days late 0.2051 (390), 4-7 days 0.2736 (1,334), 8-14 days 0.4359 (1,661), more than 14 days 0.6475 (139). This gradient is not adjusted for planned slack.",
   "queries": [
    "q311"
   ]
  },
  {
   "text": "Late-receipt jobs are flat at 323-394 a year and carry only 0.1486 (2016) and 0.177 (2021) of late shipments, against 0.3769-0.6076 in other years. Monthly, they stay at 20-38 inside the spikes.",
   "queries": [
    "q282",
    "q308"
   ]
  },
  {
   "text": "The spikes are not seasonal. In non-spike years, no calendar month averages above 0.0379 and no single month-year exceeds 0.0799.",
   "queries": [
    "q368"
   ]
  },
  {
   "text": "2016: among jobs with on-time material, the share released with 14 days or less of slack was 0.1, the same as other years. Re-weighting 2016 to other years' slack mix leaves its late rate at 0.118 (actual 0.1152, other years 0.0159). At the same slack, 2016 was far worse: 15-21 days 0.0623 vs 0.0007; more than 35 days 0.1842 vs 0.0039.",
   "queries": [
    "q362",
    "q360"
   ]
  },
  {
   "text": "2021: PO lead rose to 5.6 days (steel), 13.9 (aluminium) and 12.2 (stainless), against 3.2-3.7, 6.7-7.3 and 6.0-7.7 in other years. Release equals the last receipt date on 0.9953-1.0 of jobs with receipts, and no job is released before its last receipt. Create-to-release was 9.1 days vs 5.5-6.2. Average slack at release was 23.8 days vs 26.4-27.6.",
   "queries": [
    "q357",
    "q352",
    "q344"
   ]
  },
  {
   "text": "Among jobs with on-time material in 2021, 0.1921 were released with 14 days or less of slack, against 0.1 elsewhere. Actual 2021 late rate 0.1593. With other years' slack mix it would have been 0.1028, against 0.0159 in other years. About 0.394 of the excess is slack mix and 0.606 is within-slack (one ordering of a non-additive decomposition).",
   "queries": [
    "q362",
    "q367"
   ]
  },
  {
   "text": "Across 120 months, the late rate of jobs with on-time material correlates 0.648 with create-to-release, 0.663 with PO lead and 0.493 with release-to-completion. Create-to-release and PO lead correlate 0.996 with each other, so they are effectively one signal.",
   "queries": [
    "q356"
   ]
  },
  {
   "text": "In every year, the share of late shipments on jobs completed after the promise date is 1.0, and completion to shipment averages 0.03-0.21 days. The lateness arises before job completion, not in shipping.",
   "queries": [
    "q344"
   ]
  },
  {
   "text": "Clocked labour in 2021 was 109,740 h, below 2017-2019 (114,170-120,946). The monthly late rate correlates 0.135 with clocked hours and 0.169 with overtime hours (120 months). Clocked hours are posting-dated. These were not re-tested by the challenger.",
   "queries": [
    "q302",
    "q298"
   ]
  },
  {
   "text": "The 2021 spike among jobs with on-time material is broad: 0.1547-0.1664 in all five segments, against 0.0137-0.0181 in non-spike years.",
   "queries": [
    "q325"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that late receipts cause late shipments. Even the slack-matched 81.4 a year is an association: rushed orders could produce both short PO due dates and late vendors. Not evidence that 2021 material supply was fine: 'on time' was measured against PO due dates that had lengthened. Not evidence of which work centre held jobs. Release-to-completion time is a weak measure of flow: it fell over the decade from 21.4 days (2016) to 8.6 (2025), and 2017 ran 18.4 days with a late rate of only 0.0307 (q344). Not evidence about vendors whose receipts are often unrecorded. The unreceived share is 0.4416 for vendor 1, 0.3881 for aluminium, 0.4274 for stainless and 1.0 for both outside processors (q338). Outside-processing jobs ran late 0.6602 (2016) and 0.6807 (2021) and can never carry a late-receipt flag (q341). Not evidence that capacity was adequate: clocked hours are posting-dated and measure neither skill nor queues.",
 "could_not_tell": "Which operation or work centre slowed jobs at the same slack in 2016 and 2021: operations carry only completion dates. Whether vendor lead times rose in 2021 because vendors quoted longer or because Wendlow set later due dates: POs record only ordered and due dates. Whether unreceived POs (flat at 0.2884-0.3115 a year, q337) were cancelled or received without a record. Jobs with an unreceived PO and no recorded late receipt ran late 0.0521, against 0.0331 for fully received jobs (q336), so some late material is probably hidden there. The 428 order jobs promised in 2016 with no PO (late 0.1262, q336) reflect PO data starting 2016-01-05 while releases start 2015-11-27 (q335). They slightly inflate early-2016 rates but not the Sep-Dec spike. No dollar figure is supported: direct cost is small and expedited freight is billed to customers (prior q76, q82, q98).",
 "next_step": "(1) For jobs with on-time material in Sep-Dec 2016 and Mar-Oct 2021, compare the gaps between successive operation completions with 2019 at the same slack at release, to find where elapsed time grew. (2) Add a need-date measure: last receipt against (promise date minus the estimated routing time), so that material delay is visible even when PO due dates move. (3) Ask purchasing whether the 2021 PO due dates reflected vendor quotes. (4) Close the receipt-recording gap for vendor 1, aluminium, stainless and the outside processors, so their timeliness can be measured. (5) Check the 2021 tenure signal (0.172 of hours worked by staff with under a year's tenure, q327) against timecard headcount. This is suggestive only.",
 "incomplete": false
}

[
 {
  "id": "q366",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nr1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt, max(po.due_on::DATE) last_due FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1),\nbase AS (SELECT year(l.promised_date::DATE) yr, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, rc.late_rcpt,\n  least(greatest(l.promised_date::DATE - rc.last_due,0)//7, 6) pb\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) JOIN rc USING(job_id) WHERE j.kind='order'),\nc AS (SELECT yr, pb, count(*) FILTER (WHERE late_rcpt=1) n1, sum(late) FILTER (WHERE late_rcpt=1) l1, avg(late) FILTER (WHERE late_rcpt=0) r0, count(*) FILTER (WHERE late_rcpt=0) n0 FROM base GROUP BY 1,2)\nSELECT sum(n1) lr_jobs, sum(n1) FILTER (WHERE n0>0) matched, round(sum(l1) FILTER (WHERE n0>0)*1.0/sum(n1) FILTER (WHERE n0>0),4) r_lr, round(sum(n1*r0) FILTER (WHERE n0>0)/sum(n1) FILTER (WHERE n0>0),4) r_ot_same_cell,\n round(sum(l1) FILTER (WHERE n0>0)*1.0/sum(n1*r0) FILTER (WHERE n0>0),2) ratio, round(sum(l1 - n1*r0) FILTER (WHERE n0>0)) excess_10y, round(sum(l1 - n1*r0) FILTER (WHERE n0>0)/10,1) excess_per_yr,\n round((SELECT avg(CASE WHEN pb<=1 THEN 1.0 ELSE 0 END) FROM base WHERE late_rcpt=1),4) lr_share_slack_lt14, round((SELECT avg(CASE WHEN pb<=1 THEN 1.0 ELSE 0 END) FROM base WHERE late_rcpt=0),4) ot_share_slack_lt14\nFROM c",
  "columns": [
   "lr_jobs",
   "matched",
   "r_lr",
   "r_ot_same_cell",
   "ratio",
   "excess_10y",
   "excess_per_yr",
   "lr_share_slack_lt14",
   "ot_share_slack_lt14"
  ],
  "row_count": 1,
  "rows": [
   [
    3524,
    3524,
    0.3573,
    0.1263,
    2.83,
    814.0,
    81.4,
    0.5082,
    0.1822
   ]
  ],
  "error": null
 },
 {
  "id": "q367",
  "sql": "SELECT round(0.3575/0.0399,2) orig_ratio, round((0.1593-0.1028)/(0.1593-0.0159),4) share_2021_excess_from_slack_mix, round((0.1028-0.0159)/(0.1593-0.0159),4) share_2021_excess_within_slack, round(111.9-81.4,1) diff_per_yr, round(1453.0/(1453+549+451+380),4) lr_share_le14_nonspike, round(10234.0/(10234+15752+11592+20359),4) ot_share_le14_nonspike",
  "columns": [
   "orig_ratio",
   "share_2021_excess_from_slack_mix",
   "share_2021_excess_within_slack",
   "diff_per_yr",
   "lr_share_le14_nonspike",
   "ot_share_le14_nonspike"
  ],
  "row_count": 1,
  "rows": [
   [
    8.96,
    0.394,
    0.606,
    30.5,
    0.5129,
    0.1766
   ]
  ],
  "error": null
 },
 {
  "id": "q364",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nr1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt, max(po.due_on::DATE) last_due FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1),\nbase AS (SELECT year(l.promised_date::DATE) yr, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, rc.late_rcpt, l.promised_date::DATE - rc.last_due planned_slack\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) JOIN rc USING(job_id) WHERE j.kind='order'),\nb AS (SELECT *, CASE WHEN planned_slack<=14 THEN 'a <=14' WHEN planned_slack<=21 THEN 'b 15-21' WHEN planned_slack<=28 THEN 'c 22-28' ELSE 'd >28' END pb FROM base WHERE yr NOT IN (2016,2021))\nSELECT pb, count(*) FILTER (WHERE late_rcpt=1) n_lr, round(avg(late) FILTER (WHERE late_rcpt=1),4) r_lr, count(*) FILTER (WHERE late_rcpt=0) n_ot, round(avg(late) FILTER (WHERE late_rcpt=0),4) r_ot\nFROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "pb",
   "n_lr",
   "r_lr",
   "n_ot",
   "r_ot"
  ],
  "row_count": 4,
  "rows": [
   [
    "a <=14",
    1453,
    0.5471,
    10234,
    0.0869
   ],
   [
    "b 15-21",
    549,
    0.0984,
    15752,
    0.0001
   ],
   [
    "c 22-28",
    451,
    0.0355,
    11592,
    0.0004
   ],
   [
    "d >28",
    380,
    0.0026,
    20359,
    0.0012
   ]
  ],
  "error": null
 },
 {
  "id": "q311",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nrc AS (SELECT po.job_id, max(r.received_on::DATE - po.due_on::DATE) d, max(r.received_on::DATE) last_rcpt FROM erp_purchase_orders po JOIN erp_receipts r USING(po_id) GROUP BY 1),\nbase AS (SELECT CASE WHEN rc.d<=0 THEN '0 on time' WHEN rc.d<=3 THEN '1: 1-3d' WHEN rc.d<=7 THEN '2: 4-7d' WHEN rc.d<=14 THEN '3: 8-14d' ELSE '4: >14d' END bucket,\n  CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, greatest(sh.last_ship - l.promised_date::DATE,0) days_late, l.promised_date::DATE - rc.last_rcpt slack_after_rcpt\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) JOIN rc USING(job_id) WHERE j.kind='order')\nSELECT bucket, count(*) jobs, round(avg(late),4) late_rate, round(avg(days_late) FILTER (WHERE late=1),1) avg_cal_days_late_if_late, round(median(slack_after_rcpt),1) med_cal_days_rcpt_to_promise\nFROM base GROUP BY 1 ORDER BY 1",
  "columns": [
   "bucket",
   "jobs",
   "late_rate",
   "avg_cal_days_late_if_late",
   "med_cal_days_rcpt_to_promise"
  ],
  "row_count": 5,
  "rows": [
   [
    "0 on time",
    71812,
    0.0394,
    5.8,
    27.0
   ],
   [
    "1: 1-3d",
    390,
    0.2051,
    6.8,
    14.0
   ],
   [
    "2: 4-7d",
    1334,
    0.2736,
    7.1,
    13.0
   ],
   [
    "3: 8-14d",
    1661,
    0.4359,
    9.5,
    8.0
   ],
   [
    "4: >14d",
    139,
    0.6475,
    11.6,
    2.0
   ]
  ],
  "error": null
 },
 {
  "id": "q282",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nrc AS (SELECT po.job_id, count(DISTINCT po.po_id) n_po, count(DISTINCT r.po_id) n_po_recv,\n  max(CASE WHEN r.received_on::DATE > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt,\n  max(r.received_on::DATE - po.due_on::DATE) max_rcpt_delay\n  FROM erp_purchase_orders po LEFT JOIN erp_receipts r USING(po_id) GROUP BY 1),\nbase AS (SELECT j.job_id, year(l.promised_date::DATE) yr, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late,\n  coalesce(rc.late_rcpt,0) late_rcpt\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) LEFT JOIN rc USING(job_id) WHERE j.kind='order')\nSELECT yr, count(*) jobs, sum(late) late, round(avg(late),4) late_rate, sum(late_rcpt) lr_jobs,\n round(avg(late) FILTER (WHERE late_rcpt=1),4) rate_lr, round(avg(late) FILTER (WHERE late_rcpt=0),4) rate_nolr,\n sum(late) FILTER (WHERE late_rcpt=1) late_from_lr, round(sum(late) FILTER (WHERE late_rcpt=1)*1.0/sum(late),4) share_late_from_lr\nFROM base GROUP BY yr ORDER BY yr",
  "columns": [
   "yr",
   "jobs",
   "late",
   "late_rate",
   "lr_jobs",
   "rate_lr",
   "rate_nolr",
   "late_from_lr",
   "share_late_from_lr"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    7609,
    989,
    0.13,
    338,
    0.4349,
    0.1158,
    147,
    0.1486
   ],
   [
    2017,
    7915,
    243,
    0.0307,
    392,
    0.3061,
    0.0163,
    120,
    0.4938
   ],
   [
    2018,
    8232,
    337,
    0.0409,
    381,
    0.3333,
    0.0267,
    127,
    0.3769
   ],
   [
    2019,
    7969,
    183,
    0.023,
    349,
    0.3095,
    0.0098,
    108,
    0.5902
   ],
   [
    2020,
    7546,
    236,
    0.0313,
    394,
    0.3122,
    0.0158,
    123,
    0.5212
   ],
   [
    2021,
    7535,
    1390,
    0.1845,
    353,
    0.6969,
    0.1593,
    246,
    0.177
   ],
   [
    2022,
    7373,
    213,
    0.0289,
    326,
    0.319,
    0.0155,
    104,
    0.4883
   ],
   [
    2023,
    7128,
    171,
    0.024,
    323,
    0.2724,
    0.0122,
    88,
    0.5146
   ],
   [
    2024,
    7144,
    158,
    0.0221,
    338,
    0.284,
    0.0091,
    96,
    0.6076
   ],
   [
    2025,
    7463,
    246,
    0.033,
    330,
    0.303,
    0.0205,
    100,
    0.4065
   ]
  ],
  "error": null
 },
 {
  "id": "q308",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r.received_on::DATE > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt FROM erp_purchase_orders po LEFT JOIN erp_receipts r USING(po_id) GROUP BY 1),\nbase AS (SELECT strftime(l.promised_date::DATE,'%Y-%m') ym, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, coalesce(rc.late_rcpt,0) late_rcpt\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) LEFT JOIN rc USING(job_id) WHERE j.kind='order' AND year(l.promised_date::DATE) IN (2016,2021)),\nlab AS (SELECT strftime(work_date::DATE,'%Y-%m') ym, round(sum(hours)) clocked_h FROM shop_labour_entries GROUP BY 1)\nSELECT ym, count(*) jobs, sum(late) late, round(avg(late),3) late_rate, sum(late_rcpt) lr_jobs, round(avg(late) FILTER (WHERE late_rcpt=0),3) late_rate_nolr, clocked_h\nFROM base JOIN lab USING(ym) GROUP BY ym, clocked_h ORDER BY ym",
  "columns": [
   "ym",
   "jobs",
   "late",
   "late_rate",
   "lr_jobs",
   "late_rate_nolr",
   "clocked_h"
  ],
  "row_count": 24,
  "rows": [
   [
    "2016-01",
    546,
    77,
    0.141,
    1,
    0.139,
    11782.0
   ],
   [
    "2016-02",
    548,
    17,
    0.031,
    20,
    0.015,
    9189.0
   ],
   [
    "2016-03",
    649,
    17,
    0.026,
    29,
    0.015,
    11471.0
   ],
   [
    "2016-04",
    689,
    35,
    0.051,
    34,
    0.035,
    10115.0
   ],
   [
    "2016-05",
    608,
    34,
    0.056,
    35,
    0.045,
    9501.0
   ],
   [
    "2016-06",
    661,
    56,
    0.085,
    33,
    0.068,
    10603.0
   ],
   [
    "2016-07",
    579,
    45,
    0.078,
    29,
    0.058,
    9976.0
   ],
   [
    "2016-08",
    719,
    82,
    0.114,
    38,
    0.091,
    11378.0
   ],
   [
    "2016-09",
    696,
    149,
    0.214,
    36,
    0.192,
    10625.0
   ],
   [
    "2016-10",
    642,
    232,
    0.361,
    30,
    0.353,
    10769.0
   ],
   [
    "2016-11",
    627,
    139,
    0.222,
    30,
    0.208,
    8555.0
   ],
   [
    "2016-12",
    645,
    106,
    0.164,
    23,
    0.154,
    10694.0
   ],
   [
    "2021-01",
    613,
    72,
    0.117,
    29,
    0.104,
    8810.0
   ],
   [
    "2021-02",
    587,
    75,
    0.128,
    20,
    0.115,
    8658.0
   ],
   [
    "2021-03",
    708,
    116,
    0.164,
    32,
    0.138,
    10076.0
   ],
   [
    "2021-04",
    685,
    169,
    0.247,
    30,
    0.224,
    9139.0
   ],
   [
    "2021-05",
    608,
    166,
    0.273,
    22,
    0.254,
    8871.0
   ],
   [
    "2021-06",
    646,
    152,
    0.235,
    33,
    0.204,
    10182.0
   ],
   [
    "2021-07",
    618,
    141,
    0.228,
    34,
    0.193,
    9667.0
   ],
   [
    "2021-08",
    657,
    125,
    0.19,
    32,
    0.158,
    8781.0
   ],
   [
    "2021-09",
    571,
    110,
    0.193,
    26,
    0.169,
    8499.0
   ],
   [
    "2021-10",
    617,
    108,
    0.175,
    25,
    0.147,
    9638.0
   ],
   [
    "2021-11",
    613,
    76,
    0.124,
    36,
    0.097,
    8418.0
   ],
   [
    "2021-12",
    612,
    80,
    0.131,
    34,
    0.099,
    9000.0
   ]
  ],
  "error": null
 },
 {
  "id": "q368",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nbase AS (SELECT year(l.promised_date::DATE) yr, month(l.promised_date::DATE) mo, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) WHERE j.kind='order')\nSELECT mo, count(*) FILTER (WHERE yr NOT IN (2016,2021)) n_other, round(avg(late) FILTER (WHERE yr NOT IN (2016,2021)),4) r_other, round(max(yr_rate) ,4) max_other_yr_rate\nFROM base JOIN (SELECT yr, mo, avg(late) yr_rate FROM base WHERE yr NOT IN (2016,2021) GROUP BY 1,2) USING(yr,mo) GROUP BY mo ORDER BY mo",
  "columns": [
   "mo",
   "n_other",
   "r_other",
   "max_other_yr_rate"
  ],
  "row_count": 12,
  "rows": [
   [
    1,
    5222,
    0.0379,
    0.0799
   ],
   [
    2,
    4847,
    0.0256,
    0.0524
   ],
   [
    3,
    5262,
    0.0213,
    0.0345
   ],
   [
    4,
    4999,
    0.0284,
    0.0523
   ],
   [
    5,
    5014,
    0.0347,
    0.0516
   ],
   [
    6,
    4980,
    0.0347,
    0.0591
   ],
   [
    7,
    4993,
    0.0296,
    0.0468
   ],
   [
    8,
    5368,
    0.0343,
    0.0614
   ],
   [
    9,
    4744,
    0.028,
    0.0495
   ],
   [
    10,
    5445,
    0.0239,
    0.039
   ],
   [
    11,
    4575,
    0.0262,
    0.0392
   ],
   [
    12,
    5321,
    0.028,
    0.0745
   ]
  ],
  "error": null
 },
 {
  "id": "q362",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nr1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1),\nbase AS (SELECT CASE WHEN year(l.promised_date::DATE)=2016 THEN '2016' WHEN year(l.promised_date::DATE)=2021 THEN '2021' ELSE 'other' END grp,\n  CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, l.promised_date::DATE - try_cast(j.released_on AS DATE) slack\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) JOIN rc USING(job_id) WHERE j.kind='order' AND rc.late_rcpt=0 AND try_cast(j.released_on AS DATE) IS NOT NULL),\nb AS (SELECT grp, late, CASE WHEN slack<=14 THEN 'a' WHEN slack<=21 THEN 'b' WHEN slack<=28 THEN 'c' WHEN slack<=35 THEN 'd' ELSE 'e' END sb FROM base),\nc AS (SELECT grp, sb, count(*) n, avg(late) r FROM b GROUP BY 1,2),\nt AS (SELECT grp, sum(n) tot FROM c GROUP BY 1),\nx AS (SELECT c.grp, c.sb, c.n, c.r, c.n*1.0/t.tot sh, o.r r_oth, o.n*1.0/ot.tot sh_oth\n  FROM c JOIN t USING(grp) JOIN c o ON o.sb=c.sb AND o.grp='other' JOIN t ot ON ot.grp='other')\nSELECT grp, sum(n) jobs, round(sum(n*r)) actual_late, round(sum(n*r)/sum(n),4) actual_rate,\n round(sum(sh*r_oth),4) rate_if_own_mix_other_rates, round(sum(sh_oth*r),4) rate_if_other_mix_own_rates, round(sum(sh_oth*r_oth),4) other_rate,\n round(sum(sh) FILTER (WHERE sb='a'),4) share_slack_le14\nFROM x WHERE grp IN ('2016','2021','other') GROUP BY 1 ORDER BY 1",
  "columns": [
   "grp",
   "jobs",
   "actual_late",
   "actual_rate",
   "rate_if_own_mix_other_rates",
   "rate_if_other_mix_own_rates",
   "other_rate",
   "share_slack_le14"
  ],
  "row_count": 3,
  "rows": [
   [
    "2016",
    6843,
    788.0,
    0.1152,
    0.0158,
    0.118,
    0.0159,
    0.1
   ],
   [
    "2021",
    7182,
    1144.0,
    0.1593,
    0.0289,
    0.1028,
    0.0159,
    0.1921
   ],
   [
    "other",
    57937,
    921.0,
    0.0159,
    0.0159,
    0.0159,
    0.0159,
    0.1
   ]
  ],
  "error": null
 },
 {
  "id": "q360",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nr1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1),\nbase AS (SELECT CASE WHEN year(l.promised_date::DATE)=2016 THEN '2016' WHEN year(l.promised_date::DATE)=2021 THEN '2021' ELSE 'other' END grp,\n  CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, l.promised_date::DATE - try_cast(j.released_on AS DATE) slack\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) JOIN rc USING(job_id) WHERE j.kind='order' AND rc.late_rcpt=0 AND try_cast(j.released_on AS DATE) IS NOT NULL),\nb AS (SELECT grp, late, CASE WHEN slack<=14 THEN 'a <=14' WHEN slack<=21 THEN 'b 15-21' WHEN slack<=28 THEN 'c 22-28' WHEN slack<=35 THEN 'd 29-35' ELSE 'e >35' END sb FROM base)\nSELECT sb, count(*) FILTER (WHERE grp='2016') n16, round(avg(late) FILTER (WHERE grp='2016'),4) r16, count(*) FILTER (WHERE grp='2021') n21, round(avg(late) FILTER (WHERE grp='2021'),4) r21,\n count(*) FILTER (WHERE grp='other') n_oth, round(avg(late) FILTER (WHERE grp='other'),4) r_oth\nFROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "sb",
   "n16",
   "r16",
   "n21",
   "r21",
   "n_oth",
   "r_oth"
  ],
  "row_count": 5,
  "rows": [
   [
    "a <=14",
    684,
    0.1725,
    1380,
    0.65,
    5795,
    0.1422
   ],
   [
    "b 15-21",
    1686,
    0.0623,
    1529,
    0.0281,
    13363,
    0.0007
   ],
   [
    "c 22-28",
    1517,
    0.0758,
    1260,
    0.0278,
    12532,
    0.0011
   ],
   [
    "d 29-35",
    1610,
    0.1255,
    1450,
    0.049,
    13292,
    0.0017
   ],
   [
    "e >35",
    1346,
    0.1842,
    1563,
    0.0627,
    12955,
    0.0039
   ]
  ],
  "error": null
 },
 {
  "id": "q357",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nr1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt, avg(po.due_on::DATE - po.ordered_on::DATE) po_lead\n  FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1)\nSELECT year(po.due_on::DATE) yr, v.kind, count(*) pos, round(avg(po.due_on::DATE - po.ordered_on::DATE),1) lead_cal, round(avg(po.ordered_on::DATE - j.created_on::DATE),1) ord_after_create\nFROM erp_purchase_orders po JOIN erp_vendors v USING(vendor_id) JOIN erp_jobs j USING(job_id)\nWHERE v.kind<>'outside' GROUP BY 1,2 ORDER BY 2,1",
  "columns": [
   "yr",
   "kind",
   "pos",
   "lead_cal",
   "ord_after_create"
  ],
  "row_count": 30,
  "rows": [
   [
    2016,
    "aluminium",
    257,
    7.1,
    11.0
   ],
   [
    2017,
    "aluminium",
    316,
    6.8,
    11.1
   ],
   [
    2018,
    "aluminium",
    337,
    7.3,
    11.2
   ],
   [
    2019,
    "aluminium",
    292,
    7.0,
    9.1
   ],
   [
    2020,
    "aluminium",
    229,
    7.1,
    9.6
   ],
   [
    2021,
    "aluminium",
    240,
    13.9,
    13.7
   ],
   [
    2022,
    "aluminium",
    256,
    7.2,
    8.1
   ],
   [
    2023,
    "aluminium",
    242,
    7.1,
    9.0
   ],
   [
    2024,
    "aluminium",
    306,
    6.7,
    7.9
   ],
   [
    2025,
    "aluminium",
    256,
    7.3,
    9.1
   ],
   [
    2016,
    "stainless",
    278,
    7.1,
    12.2
   ],
   [
    2017,
    "stainless",
    306,
    6.7,
    12.1
   ],
   [
    2018,
    "stainless",
    272,
    7.4,
    11.2
   ],
   [
    2019,
    "stainless",
    239,
    6.1,
    9.9
   ],
   [
    2020,
    "stainless",
    226,
    6.0,
    11.9
   ],
   [
    2021,
    "stainless",
    194,
    12.2,
    16.3
   ],
   [
    2022,
    "stainless",
    208,
    6.7,
    9.7
   ],
   [
    2023,
    "stainless",
    224,
    6.5,
    9.6
   ],
   [
    2024,
    "stainless",
    177,
    6.8,
    9.0
   ],
   [
    2025,
    "stainless",
    211,
    7.7,
    8.5
   ],
   [
    2016,
    "steel",
    10031,
    3.4,
    5.8
   ],
   [
    2017,
    "steel",
    10871,
    3.4,
    5.2
   ],
   [
    2018,
    "steel",
    11105,
    3.7,
    4.2
   ],
   [
    2019,
    "steel",
    10816,
    3.2,
    4.2
   ],
   [
    2020,
    "steel",
    10063,
    3.4,
    4.1
   ],
   [
    2021,
    "steel",
    10395,
    5.6,
    5.8
   ],
   [
    2022,
    "steel",
    9952,
    3.4,
    3.6
   ],
   [
    2023,
    "steel",
    9609,
    3.3,
    3.5
   ],
   [
    2024,
    "steel",
    9464,
    3.4,
    3.4
   ],
   [
    2025,
    "steel",
    9565,
    3.7,
    3.0
   ]
  ],
  "error": null
 },
 {
  "id": "q352",
  "sql": "WITH r1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt, max(r1.last_r) last_rcpt, count(r1.po_id) n_recv, count(*) n_po\n  FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1)\nSELECT late_rcpt, (n_recv<n_po) has_unrecv, count(*) jobs, count(last_rcpt) jobs_with_rcpt,\n round(avg(CASE WHEN try_cast(j.released_on AS DATE)=last_rcpt THEN 1.0 ELSE 0 END) FILTER (WHERE last_rcpt IS NOT NULL),4) share_release_eq_last_rcpt,\n round(avg(CASE WHEN try_cast(j.released_on AS DATE)<last_rcpt THEN 1.0 ELSE 0 END) FILTER (WHERE last_rcpt IS NOT NULL),4) share_release_before_rcpt\nFROM erp_jobs j JOIN rc USING(job_id) WHERE j.kind='order' GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "late_rcpt",
   "has_unrecv",
   "jobs",
   "jobs_with_rcpt",
   "share_release_eq_last_rcpt",
   "share_release_before_rcpt"
  ],
  "row_count": 4,
  "rows": [
   [
    0,
    false,
    47288,
    47288,
    0.9976,
    0.0
   ],
   [
    0,
    true,
    25146,
    24910,
    0.9953,
    0.0
   ],
   [
    1,
    false,
    2246,
    2246,
    1.0,
    0.0
   ],
   [
    1,
    true,
    1300,
    1300,
    1.0,
    0.0
   ]
  ],
  "error": null
 },
 {
  "id": "q344",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship, count(*) n_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nbase AS (SELECT year(l.promised_date::DATE) yr, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late,\n  j.created_on::DATE - so.order_date::DATE ord_to_create, try_cast(j.released_on AS DATE) - j.created_on::DATE create_to_rel,\n  try_cast(j.completed_on AS DATE) - try_cast(j.released_on AS DATE) rel_to_comp, sh.last_ship - try_cast(j.completed_on AS DATE) comp_to_ship,\n  l.promised_date::DATE - try_cast(j.released_on AS DATE) slack_at_release,\n  CASE WHEN try_cast(j.completed_on AS DATE) > l.promised_date::DATE THEN 1 ELSE 0 END comp_after_promise, sh.n_ship\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN erp_sales_orders so USING(order_id) JOIN sh USING(job_id) WHERE j.kind='order')\nSELECT yr, count(*) jobs, round(avg(late),4) late_rate, round(avg(ord_to_create),1) o2c, round(avg(create_to_rel),1) c2r, round(avg(rel_to_comp),1) r2c,\n round(median(rel_to_comp),1) med_r2c, round(quantile_cont(rel_to_comp,0.9),1) p90_r2c, round(avg(comp_to_ship),2) c2s, round(avg(slack_at_release),1) slack_rel,\n round(sum(comp_after_promise)*1.0/sum(late),4) late_share_comp_after_promise, round(avg(n_ship),3) ships_per_job\nFROM base GROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "jobs",
   "late_rate",
   "o2c",
   "c2r",
   "r2c",
   "med_r2c",
   "p90_r2c",
   "c2s",
   "slack_rel",
   "late_share_comp_after_promise",
   "ships_per_job"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    7609,
    0.13,
    0.0,
    5.6,
    21.4,
    20.0,
    38.0,
    0.14,
    26.4,
    1.0,
    1.024
   ],
   [
    2017,
    7915,
    0.0307,
    0.0,
    5.9,
    18.4,
    16.0,
    35.0,
    0.03,
    26.8,
    1.0,
    1.005
   ],
   [
    2018,
    8232,
    0.0409,
    0.0,
    6.2,
    13.9,
    11.0,
    28.0,
    0.05,
    26.6,
    1.0,
    1.009
   ],
   [
    2019,
    7969,
    0.023,
    0.0,
    5.5,
    13.9,
    11.0,
    29.0,
    0.03,
    27.4,
    1.0,
    1.005
   ],
   [
    2020,
    7546,
    0.0313,
    0.0,
    5.7,
    14.1,
    10.0,
    31.0,
    0.04,
    27.2,
    1.0,
    1.007
   ],
   [
    2021,
    7535,
    0.1845,
    0.0,
    9.1,
    17.2,
    13.0,
    36.0,
    0.21,
    23.8,
    1.0,
    1.036
   ],
   [
    2022,
    7373,
    0.0289,
    0.0,
    5.8,
    12.7,
    8.0,
    28.0,
    0.04,
    26.9,
    1.0,
    1.006
   ],
   [
    2023,
    7128,
    0.024,
    0.0,
    5.6,
    12.0,
    8.0,
    26.0,
    0.04,
    27.2,
    1.0,
    1.006
   ],
   [
    2024,
    7144,
    0.0221,
    0.0,
    5.6,
    12.4,
    8.0,
    27.0,
    0.03,
    27.6,
    1.0,
    1.005
   ],
   [
    2025,
    7463,
    0.033,
    0.0,
    6.0,
    8.6,
    7.0,
    15.0,
    0.04,
    26.9,
    1.0,
    1.008
   ]
  ],
  "error": null
 },
 {
  "id": "q356",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nr1 AS (SELECT po_id, max(received_on::DATE) last_r FROM erp_receipts GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r1.last_r > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt, avg(po.due_on::DATE - po.ordered_on::DATE) po_lead\n  FROM erp_purchase_orders po LEFT JOIN r1 USING(po_id) GROUP BY 1),\nbase AS (SELECT strftime(l.promised_date::DATE,'%Y-%m') ym, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late,\n  try_cast(j.released_on AS DATE) - j.created_on::DATE c2r, try_cast(j.completed_on AS DATE) - try_cast(j.released_on AS DATE) r2c, rc.po_lead\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) JOIN rc USING(job_id) WHERE j.kind='order' AND rc.late_rcpt=0 AND l.promised_date>='2016-01-01'),\nm AS (SELECT ym, avg(late) lr, avg(c2r) c2r, avg(r2c) r2c, avg(po_lead) po_lead, count(*) n FROM base GROUP BY 1)\nSELECT count(*) n_months, sum(n) jobs, round(corr(lr,c2r),3) r_c2r, round(corr(lr,r2c),3) r_r2c, round(corr(lr,po_lead),3) r_polead, round(corr(c2r,po_lead),3) r_c2r_polead, round(corr(c2r,r2c),3) r_c2r_r2c,\n round(corr(lr, c2r+r2c),3) r_total\nFROM m",
  "columns": [
   "n_months",
   "jobs",
   "r_c2r",
   "r_r2c",
   "r_polead",
   "r_c2r_polead",
   "r_c2r_r2c",
   "r_total"
  ],
  "row_count": 1,
  "rows": [
   [
    120,
    71962,
    0.648,
    0.493,
    0.663,
    0.996,
    0.058,
    0.623
   ]
  ],
  "error": null
 },
 {
  "id": "q302",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r.received_on::DATE > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt FROM erp_purchase_orders po LEFT JOIN erp_receipts r USING(po_id) GROUP BY 1),\nbase AS (SELECT year(l.promised_date::DATE) yr, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, coalesce(rc.late_rcpt,0) late_rcpt,\n  l.promised_date::DATE - so.order_date::DATE promise_days, j.completed_on::DATE - j.released_on::DATE shop_days, sh.last_ship - j.completed_on::DATE comp_to_ship\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN erp_sales_orders so USING(order_id) JOIN sh USING(job_id) LEFT JOIN rc USING(job_id) WHERE j.kind='order' AND l.promised_date>='2016-01-01'),\ny AS (SELECT yr, count(*) jobs, round(avg(late),4) late_rate, round(avg(promise_days),1) avg_promise_cal_days, round(avg(shop_days) FILTER (WHERE late_rcpt=0),1) shop_days_nolr, round(avg(comp_to_ship),2) comp_to_ship FROM base GROUP BY 1),\nlab AS (SELECT year(work_date::DATE) yr, round(sum(hours)) clocked_h, round(coalesce(sum(hours) FILTER (WHERE overtime=1),0)) ot_h, count(DISTINCT employee_id) emps FROM shop_labour_entries GROUP BY 1)\nSELECT * FROM y JOIN lab USING(yr) ORDER BY yr",
  "columns": [
   "yr",
   "jobs",
   "late_rate",
   "avg_promise_cal_days",
   "shop_days_nolr",
   "comp_to_ship",
   "clocked_h",
   "ot_h",
   "emps"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    7609,
    0.13,
    32.0,
    21.9,
    0.14,
    124657.0,
    2869.0,
    95
   ],
   [
    2017,
    7915,
    0.0307,
    32.6,
    18.9,
    0.03,
    120946.0,
    1984.0,
    98
   ],
   [
    2018,
    8232,
    0.0409,
    32.8,
    14.2,
    0.05,
    118400.0,
    320.0,
    97
   ],
   [
    2019,
    7969,
    0.023,
    32.9,
    14.2,
    0.03,
    114170.0,
    531.0,
    100
   ],
   [
    2020,
    7546,
    0.0313,
    32.9,
    14.3,
    0.04,
    103093.0,
    923.0,
    96
   ],
   [
    2021,
    7535,
    0.1845,
    32.8,
    17.6,
    0.21,
    109740.0,
    2755.0,
    99
   ],
   [
    2022,
    7373,
    0.0289,
    32.7,
    12.9,
    0.04,
    112052.0,
    5094.0,
    95
   ],
   [
    2023,
    7128,
    0.024,
    32.7,
    12.2,
    0.04,
    106029.0,
    1640.0,
    104
   ],
   [
    2024,
    7144,
    0.0221,
    33.3,
    12.7,
    0.03,
    111064.0,
    2282.0,
    94
   ],
   [
    2025,
    7463,
    0.033,
    32.9,
    8.7,
    0.04,
    108640.0,
    0.0,
    95
   ]
  ],
  "error": null
 },
 {
  "id": "q298",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r.received_on::DATE > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt\n  FROM erp_purchase_orders po LEFT JOIN erp_receipts r USING(po_id) GROUP BY 1),\nbase AS (SELECT strftime(l.promised_date::DATE,'%Y-%m') ym, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late, coalesce(rc.late_rcpt,0) late_rcpt\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN sh USING(job_id) LEFT JOIN rc USING(job_id) WHERE j.kind='order' AND l.promised_date >= '2016-01-01'),\nm AS (SELECT ym, count(*) jobs, avg(late) late_rate, avg(late_rcpt) lr_share, avg(late) FILTER (WHERE late_rcpt=0) late_rate_nolr FROM base GROUP BY 1),\nlab AS (SELECT strftime(work_date::DATE,'%Y-%m') ym, sum(hours) clocked_h, sum(hours) FILTER (WHERE overtime=1) ot_h FROM shop_labour_entries GROUP BY 1),\nt AS (SELECT m.*, lab.clocked_h, coalesce(lab.ot_h,0) ot_h FROM m JOIN lab USING(ym))\nSELECT count(*) n_months, round(corr(late_rate, lr_share),3) r_late_vs_lrshare, round(corr(late_rate, clocked_h),3) r_late_vs_clocked,\n round(corr(late_rate, ot_h),3) r_late_vs_ot, round(corr(late_rate_nolr, clocked_h),3) r_nolr_late_vs_clocked, min(ym) first_m, max(ym) last_m\nFROM t",
  "columns": [
   "n_months",
   "r_late_vs_lrshare",
   "r_late_vs_clocked",
   "r_late_vs_ot",
   "r_nolr_late_vs_clocked",
   "first_m",
   "last_m"
  ],
  "row_count": 1,
  "rows": [
   [
    120,
    -0.026,
    0.135,
    0.169,
    0.149,
    "2016-01",
    "2025-12"
   ]
  ],
  "error": null
 },
 {
  "id": "q325",
  "sql": "WITH sh AS (SELECT sl.job_id, max(s.shipped_on::DATE) last_ship FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nrc AS (SELECT po.job_id, max(CASE WHEN r.received_on::DATE > po.due_on::DATE THEN 1 ELSE 0 END) late_rcpt FROM erp_purchase_orders po LEFT JOIN erp_receipts r USING(po_id) GROUP BY 1),\nbase AS (SELECT year(l.promised_date::DATE) yr, c.segment, CASE WHEN sh.last_ship > l.promised_date::DATE THEN 1 ELSE 0 END late\n  FROM erp_jobs j JOIN erp_so_lines l USING(line_id) JOIN erp_sales_orders so USING(order_id) JOIN erp_customers c ON c.customer_id=so.customer_id JOIN sh USING(job_id) LEFT JOIN rc USING(job_id)\n  WHERE j.kind='order' AND l.promised_date>='2016-01-01' AND coalesce(rc.late_rcpt,0)=0)\nSELECT segment, count(*) FILTER (WHERE yr=2016) n16, round(avg(late) FILTER (WHERE yr=2016),4) r16, count(*) FILTER (WHERE yr=2021) n21, round(avg(late) FILTER (WHERE yr=2021),4) r21,\n count(*) FILTER (WHERE yr NOT IN (2016,2021)) n_other, round(avg(late) FILTER (WHERE yr NOT IN (2016,2021)),4) r_other\nFROM base GROUP BY 1 ORDER BY 1",
  "columns": [
   "segment",
   "n16",
   "r16",
   "n21",
   "r21",
   "n_other",
   "r_other"
  ],
  "row_count": 5,
  "rows": [
   [
    "ag",
    831,
    0.1143,
    1467,
    0.1547,
    10925,
    0.0137
   ],
   [
    "contractor",
    993,
    0.136,
    697,
    0.1664,
    6621,
    0.0174
   ],
   [
    "food",
    2127,
    0.1175,
    1815,
    0.162,
    14134,
    0.0171
   ],
   [
    "hvac",
    1376,
    0.117,
    1060,
    0.1613,
    8439,
    0.0181
   ],
   [
    "machinery",
    1944,
    0.1034,
    2143,
    0.1568,
    17818,
    0.0146
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

Save `grade.json`: {"finding": "F8", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
