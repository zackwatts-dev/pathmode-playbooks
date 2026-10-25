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
 "id": "F9",
 "hypothesis": "H2",
 "title": "From 2017 to 2025, paid time not clocked to jobs grew by about 10,361 to 14,085 h a year (about $255,110 to $349,162 at 2025 rates) as estimated work fell while paid hours held, mostly in lathe, mill and laser. It is spread across whole roles, not a few employees, and it is an opportunity value of fixed payroll, not a cost that grew.",
 "conclusion": "The hypothesis holds in a narrower form. Total paid hours barely moved from 2016 to 2025 (+511.3 h, q391), and annual clocked hours are labour on operations completed that year, with little truncation at the end of the series (q371, q372, q373, q375). The original 2016 baseline overstated the trend. During 2016, clocked hours per estimated hour fell from about 1.0 to about 0.81-0.88 (e.g. laser 0.992 in Jan-2016 to 0.811 in Dec-2016; q374), on the same parts with unchanged estimates (q389). 58.5% of the 2016-2025 fall in clocked hours comes from that ratio effect (q385, q391). Measured from 2017, the picture is cleaner: estimated work on completed operations fell (load effect -14,314 clocked-hour equivalents), while clocked hours per estimated hour held or rose slightly (ratio effect +2,342; shop-wide 0.883 in 2017, 0.903 in 2025; q383, q385). Unclocked paid time grew by 14,085 h (2017 vs 2025), or by 10,361 h a year comparing the 2017-19 and 2023-25 averages (q379, q395). Each role books only to its own work centre (q382). The rise moves the whole within-role distribution (q349). The largest pieces against 2017 are lathe (1.73 FTE-equivalents), mill (1.64) and laser (1.49) (q390). Interpretation: capacity did not follow a falling workload. In mill and lathe, load fell while paid hours were held (mill -104 h) or added (lathe +1,272 h). Laser lost load while paid hours rose 1,896 h, partly by deliberate backlog hiring (2 backlog requisitions, 2016-08-01 and 2021-01-25; q386). Priced at 2025 median rates, this is $255,110 a year on 3-year averages, of which mill plus lathe is $116,772 (q395). The 2017 baseline gives $349,162 (q379). It is an opportunity value of hours already paid: about 7.92 FTE spread across 8 roles, with none above 1.73 (q390). It becomes savings only by matching hours to load through attrition, cross-training or bringing in work. The 2016 step is a separate question: it could be real efficiency or labour no longer booked to jobs, and the records can't tell which.",
 "dollars_a_year": 255110.0,
 "size_query": "q395",
 "claims": [
  {
   "text": "Annual clocked hours are a sound measure. Between 96.5% (2016) and 98.0% (2025) of labour entries are dated on their operation's completion date, with 0 completion-year mismatches. Every operation completed 2016-2025 has labour, and open operations at the end of 2025 hold only 43.2 h of labour. Timecards cover 49-50 weeks a year.",
   "queries": [
    "q370",
    "q371",
    "q372",
    "q373",
    "q375"
   ]
  },
  {
   "text": "2016 is a transition year. Act/est fell within 2016 (laser 0.992 to 0.811, paint 1.02 to 0.878, brake 1.069 to 0.864, Jan to Dec), on identical parts whose estimates per piece were essentially unchanged by 2018 (median ratio 1.01-1.019, 409-941 parts per work centre), while clocked hours per piece fell (median 0.761-0.858). Of the 15,739 h fall in clocked hours 2016-2025, 9,209 h (58.5%) is this ratio effect.",
   "queries": [
    "q374",
    "q389",
    "q385",
    "q391"
   ]
  },
  {
   "text": "From 2017 the fall in clocked hours is a workload fall: load effect -14,314 h, ratio effect +2,342 h (shop-wide act/est 0.883 in 2017, 0.903 in 2025).",
   "queries": [
    "q385",
    "q383"
   ]
  },
  {
   "text": "Unclocked paid time grew by 14,085 h (2025 vs 2017) or 10,361 h a year (2023-25 vs 2017-19 averages). Against 2017: lathe +3,269 h (paid +1,272, clocked -1,997), mill +2,832 h (paid -104, clocked -2,936), laser +2,823 h (paid +1,896, clocked -927), brake +1,672 h, assembler +1,435 h, painter +1,303 h (paid only +213), welder +442 h, inspector +308 h.",
   "queries": [
    "q379",
    "q390"
   ]
  },
  {
   "text": "The shift is role-wide, not driven by a few people. For example, mill machinists' median unclocked share went 0.366 (2016, n=16) to 0.561 (2025, n=15), and laser operators' p10 went -0.118 to 0.188. Each role books 100% of its labour to its own work centre.",
   "queries": [
    "q349",
    "q382"
   ]
  },
  {
   "text": "Priced at 2025 median role rates: $255,110 a year on 3-year averages (mill $63,079, laser $63,772, lathe $53,693, mill plus lathe $116,772) and $349,162 on a 2017 baseline. That equals 7.92 FTE across 8 roles, at most 1.73 in any one role.",
   "queries": [
    "q395",
    "q379",
    "q390"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that any employee is idle or under-recording: whole roles move, and individual shares below zero in 2016 (q349) show that attributing hours to people is imperfect. Not evidence that a recording change happened in 2016, or that estimates were right; the 2016 drop could be genuine efficiency. Not a cost that grew: payroll changed by +511.3 h (q391), and the slack is under 2 FTE per role (q390). Not evidence of what the unclocked time was spent on.",
 "could_not_tell": "What the unclocked hours were spent on: there are no indirect clock codes. Whether the 2016 fall in clocked hours per piece was efficiency or a change in booking practice. Why lathe and inspector shares stay high in every year. Whether unclocked time rises in low-load weeks: work_date is effectively the completion date, so weekly load can't be measured reliably. Role changes over time: hr_employees holds only the current role. Benefits are excluded from the dollars.",
 "next_step": "Introduce indirect clock codes for mill, lathe and laser, and review staffing in those centres against estimated hours, using attrition (mill and lathe each had 18 replacement requisitions, q386) and cross-training rather than reductions. Ask the plant and accounting whether labour-booking practice changed during 2016 before treating that step as capacity.",
 "incomplete": false
}

[
 {
  "id": "q370",
  "sql": "SELECT CAST(substr(work_date,1,4) AS INT) yr, COUNT(*) n, ROUND(SUM(hours),1) h, SUM(CASE WHEN hours>40 THEN 1 ELSE 0 END) n_gt40, ROUND(SUM(CASE WHEN hours>40 THEN hours END),1) h_gt40, ROUND(MAX(hours),1) mx, ROUND(SUM(CASE WHEN rework=1 THEN hours END),1) rework_h, ROUND(SUM(CASE WHEN overtime=1 THEN hours END),1) ot_h FROM shop_labour_entries GROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "n",
   "h",
   "n_gt40",
   "h_gt40",
   "mx",
   "rework_h",
   "ot_h"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    41551,
    124657.1,
    382,
    25125.3,
    208.3,
    860.5,
    2868.8
   ],
   [
    2017,
    41414,
    120945.9,
    353,
    22250.7,
    155.4,
    867.7,
    1984.2
   ],
   [
    2018,
    39237,
    118399.8,
    316,
    19448.8,
    177.5,
    813.1,
    319.7
   ],
   [
    2019,
    36568,
    114169.9,
    344,
    21818.6,
    182.4,
    834.0,
    531.0
   ],
   [
    2020,
    36056,
    103093.5,
    266,
    15620.1,
    180.4,
    649.1,
    923.4
   ],
   [
    2021,
    37664,
    109740.4,
    267,
    16499.8,
    170.5,
    829.2,
    2754.5
   ],
   [
    2022,
    35552,
    112052.3,
    327,
    20042.9,
    174.9,
    750.7,
    5094.2
   ],
   [
    2023,
    33262,
    106029.2,
    283,
    17204.0,
    169.1,
    778.8,
    1640.0
   ],
   [
    2024,
    33566,
    111064.2,
    304,
    20003.0,
    193.2,
    768.0,
    2281.7
   ],
   [
    2025,
    32316,
    108639.5,
    336,
    21349.0,
    180.7,
    756.0,
    null
   ]
  ],
  "error": null
 },
 {
  "id": "q371",
  "sql": "WITH a AS (SELECT op_id, SUM(hours) act, MIN(work_date) first_d, MAX(work_date) last_d FROM shop_labour_entries GROUP BY 1)\nSELECT CAST(substr(o.completed_on,1,4) AS INT) yr, COUNT(*) n_ops, SUM(CASE WHEN a.op_id IS NULL THEN 1 ELSE 0 END) no_lab, ROUND(AVG(CASE WHEN a.op_id IS NULL THEN 1.0 ELSE 0 END),3) share_no_lab, ROUND(SUM(CASE WHEN a.op_id IS NULL THEN o.est_setup_hours+o.est_run_hours END),0) est_h_no_lab, SUM(CASE WHEN substr(a.last_d,1,4)<>substr(o.completed_on,1,4) THEN 1 ELSE 0 END) lab_other_yr\nFROM erp_job_operations o LEFT JOIN a USING(op_id) WHERE o.completed_on IS NOT NULL GROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "n_ops",
   "no_lab",
   "share_no_lab",
   "est_h_no_lab",
   "lab_other_yr"
  ],
  "row_count": 11,
  "rows": [
   [
    2015,
    656,
    656,
    1.0,
    3108.0,
    0
   ],
   [
    2016,
    31110,
    0,
    0.0,
    null,
    0
   ],
   [
    2017,
    32489,
    0,
    0.0,
    null,
    0
   ],
   [
    2018,
    34109,
    0,
    0.0,
    null,
    0
   ],
   [
    2019,
    31924,
    0,
    0.0,
    null,
    0
   ],
   [
    2020,
    30219,
    0,
    0.0,
    null,
    0
   ],
   [
    2021,
    31444,
    0,
    0.0,
    null,
    0
   ],
   [
    2022,
    30254,
    0,
    0.0,
    null,
    0
   ],
   [
    2023,
    29101,
    0,
    0.0,
    null,
    0
   ],
   [
    2024,
    29429,
    0,
    0.0,
    null,
    0
   ],
   [
    2025,
    29009,
    0,
    0.0,
    null,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q372",
  "sql": "SELECT CAST(substr(l.work_date,1,4) AS INT) yr, COUNT(*) n, ROUND(AVG(CASE WHEN l.work_date=o.completed_on THEN 1.0 ELSE 0 END),3) share_on_completion_date, ROUND(AVG(CASE WHEN o.completed_on IS NULL THEN 1.0 ELSE 0 END),4) share_open_op, ROUND(SUM(CASE WHEN o.completed_on IS NULL THEN l.hours END),1) h_open_op\nFROM shop_labour_entries l LEFT JOIN erp_job_operations o USING(op_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "n",
   "share_on_completion_date",
   "share_open_op",
   "h_open_op"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    41551,
    0.965,
    0.0,
    null
   ],
   [
    2017,
    41414,
    0.969,
    0.0,
    null
   ],
   [
    2018,
    39237,
    0.971,
    0.0,
    null
   ],
   [
    2019,
    36568,
    0.971,
    0.0,
    null
   ],
   [
    2020,
    36056,
    0.973,
    0.0,
    null
   ],
   [
    2021,
    37664,
    0.971,
    0.0,
    null
   ],
   [
    2022,
    35552,
    0.975,
    0.0,
    null
   ],
   [
    2023,
    33262,
    0.975,
    0.0,
    null
   ],
   [
    2024,
    33566,
    0.978,
    0.0,
    null
   ],
   [
    2025,
    32316,
    0.98,
    0.0001,
    43.2
   ]
  ],
  "error": null
 },
 {
  "id": "q373",
  "sql": "SELECT o.work_centre, COUNT(*) n_open, ROUND(SUM(o.est_setup_hours+o.est_run_hours),0) est_h_open, MIN(j.released_on) min_rel, MAX(j.released_on) max_rel FROM erp_job_operations o JOIN erp_jobs j USING(job_id) WHERE o.completed_on IS NULL GROUP BY 1 ORDER BY 1",
  "columns": [
   "work_centre",
   "n_open",
   "est_h_open",
   "min_rel",
   "max_rel"
  ],
  "row_count": 8,
  "rows": [
   [
    "assembly",
    75,
    645.0,
    "2025-12-09",
    "2025-12-31"
   ],
   [
    "brake",
    114,
    348.0,
    "2025-12-29",
    "2025-12-31"
   ],
   [
    "inspect",
    257,
    64.0,
    "2025-12-04",
    "2025-12-31"
   ],
   [
    "laser",
    95,
    178.0,
    null,
    null
   ],
   [
    "lathe",
    3,
    63.0,
    null,
    null
   ],
   [
    "mill",
    19,
    620.0,
    "2025-12-18",
    "2025-12-31"
   ],
   [
    "paint",
    163,
    439.0,
    "2025-12-04",
    "2025-12-31"
   ],
   [
    "weld",
    102,
    1423.0,
    "2025-12-11",
    "2025-12-31"
   ]
  ],
  "error": null
 },
 {
  "id": "q375",
  "sql": "SELECT CAST(substr(week_of,1,4) AS INT) yr, COUNT(DISTINCT week_of) n_weeks, MIN(week_of) first_wk, MAX(week_of) last_wk, COUNT(*) rows_, ROUND(SUM(regular_hours),0) reg, ROUND(SUM(overtime_hours),0) ot FROM hr_timecards GROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "n_weeks",
   "first_wk",
   "last_wk",
   "rows_",
   "reg",
   "ot"
  ],
  "row_count": 11,
  "rows": [
   [
    2015,
    1,
    "2015-12-28",
    "2015-12-28",
    87,
    3480.0,
    0.0
   ],
   [
    2016,
    49,
    "2016-01-04",
    "2016-12-26",
    4213,
    162192.0,
    2865.0
   ],
   [
    2017,
    49,
    "2017-01-02",
    "2017-12-29",
    4204,
    161816.0,
    1974.0
   ],
   [
    2018,
    49,
    "2018-01-08",
    "2018-12-28",
    4222,
    162608.0,
    320.0
   ],
   [
    2019,
    50,
    "2019-01-07",
    "2019-12-27",
    4265,
    164000.0,
    531.0
   ],
   [
    2020,
    50,
    "2020-01-06",
    "2020-12-23",
    4043,
    155656.0,
    925.0
   ],
   [
    2021,
    50,
    "2021-01-04",
    "2021-12-27",
    4130,
    159168.0,
    2752.0
   ],
   [
    2022,
    49,
    "2022-01-03",
    "2022-12-26",
    4190,
    161336.0,
    5095.0
   ],
   [
    2023,
    49,
    "2023-01-02",
    "2023-12-29",
    4064,
    156544.0,
    1808.0
   ],
   [
    2024,
    50,
    "2024-01-08",
    "2024-12-27",
    4373,
    168512.0,
    2111.0
   ],
   [
    2025,
    49,
    "2025-01-06",
    "2025-12-18",
    4296,
    165568.0,
    0.0
   ]
  ],
  "error": null
 },
 {
  "id": "q374",
  "sql": "WITH a AS (SELECT op_id, SUM(hours) act FROM shop_labour_entries GROUP BY 1)\nSELECT o.work_centre, substr(o.completed_on,1,7) ym, COUNT(*) n_ops, ROUND(SUM(a.act)/SUM(o.est_setup_hours+o.est_run_hours),3) act_over_est\nFROM erp_job_operations o JOIN a USING(op_id) WHERE substr(o.completed_on,1,7) IN ('2016-01','2016-02','2016-03','2016-06','2016-09','2016-12','2017-06') AND o.work_centre IN ('laser','paint','brake','mill')\nGROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "work_centre",
   "ym",
   "n_ops",
   "act_over_est"
  ],
  "row_count": 28,
  "rows": [
   [
    "brake",
    "2016-01",
    429,
    1.069
   ],
   [
    "brake",
    "2016-02",
    437,
    0.998
   ],
   [
    "brake",
    "2016-03",
    487,
    0.985
   ],
   [
    "brake",
    "2016-06",
    465,
    0.926
   ],
   [
    "brake",
    "2016-09",
    475,
    0.913
   ],
   [
    "brake",
    "2016-12",
    529,
    0.864
   ],
   [
    "brake",
    "2017-06",
    512,
    0.844
   ],
   [
    "laser",
    "2016-01",
    495,
    0.992
   ],
   [
    "laser",
    "2016-02",
    519,
    0.995
   ],
   [
    "laser",
    "2016-03",
    590,
    0.96
   ],
   [
    "laser",
    "2016-06",
    613,
    0.914
   ],
   [
    "laser",
    "2016-09",
    624,
    0.838
   ],
   [
    "laser",
    "2016-12",
    640,
    0.811
   ],
   [
    "laser",
    "2017-06",
    684,
    0.798
   ],
   [
    "mill",
    "2016-01",
    69,
    0.905
   ],
   [
    "mill",
    "2016-02",
    64,
    0.859
   ],
   [
    "mill",
    "2016-03",
    51,
    0.836
   ],
   [
    "mill",
    "2016-06",
    46,
    0.824
   ],
   [
    "mill",
    "2016-09",
    36,
    0.851
   ],
   [
    "mill",
    "2016-12",
    46,
    0.812
   ],
   [
    "mill",
    "2017-06",
    41,
    0.828
   ],
   [
    "paint",
    "2016-01",
    424,
    1.02
   ],
   [
    "paint",
    "2016-02",
    398,
    1.012
   ],
   [
    "paint",
    "2016-03",
    429,
    0.991
   ],
   [
    "paint",
    "2016-06",
    428,
    0.918
   ],
   [
    "paint",
    "2016-09",
    423,
    0.879
   ],
   [
    "paint",
    "2016-12",
    437,
    0.878
   ],
   [
    "paint",
    "2017-06",
    484,
    0.87
   ]
  ],
  "error": null
 },
 {
  "id": "q389",
  "sql": "WITH a AS (SELECT op_id, SUM(hours) act FROM shop_labour_entries GROUP BY 1),\nb AS (SELECT j.part_id, o.work_centre wc, CASE WHEN o.completed_on < '2016-07-01' THEN 'H1_2016' WHEN substr(o.completed_on,1,4)='2018' THEN 'Y2018' END per,\n (o.est_setup_hours+o.est_run_hours)/j.quantity est_pc, a.act/j.quantity act_pc\n FROM erp_job_operations o JOIN erp_jobs j USING(job_id) JOIN a USING(op_id) WHERE j.quantity>0 AND o.work_centre IN ('laser','paint','brake','weld')),\ng AS (SELECT part_id, wc, per, AVG(est_pc) e, AVG(act_pc) ac FROM b WHERE per IS NOT NULL GROUP BY 1,2,3),\nm AS (SELECT x.wc, x.part_id, x.e e16, x.ac a16, y.e e18, y.ac a18 FROM g x JOIN g y ON x.part_id=y.part_id AND x.wc=y.wc AND x.per='H1_2016' AND y.per='Y2018')\nSELECT wc, COUNT(*) n_parts, ROUND(median(e18/e16),3) med_est_ratio, ROUND(median(a18/a16),3) med_act_ratio FROM m GROUP BY 1 ORDER BY 1",
  "columns": [
   "wc",
   "n_parts",
   "med_est_ratio",
   "med_act_ratio"
  ],
  "row_count": 4,
  "rows": [
   [
    "brake",
    743,
    1.01,
    0.791
   ],
   [
    "laser",
    941,
    1.019,
    0.761
   ],
   [
    "paint",
    703,
    1.017,
    0.858
   ],
   [
    "weld",
    409,
    1.014,
    0.799
   ]
  ],
  "error": null
 },
 {
  "id": "q385",
  "sql": "WITH a AS (SELECT op_id, SUM(hours) act FROM shop_labour_entries GROUP BY 1),\ny AS (SELECT o.work_centre wc, CAST(substr(o.completed_on,1,4) AS INT) yr, SUM(o.est_setup_hours+o.est_run_hours) est, SUM(a.act) act FROM erp_job_operations o JOIN a USING(op_id) WHERE substr(o.completed_on,1,4) IN ('2016','2017','2025') GROUP BY 1,2),\np AS (SELECT wc, MAX(CASE WHEN yr=2016 THEN est END) e16, MAX(CASE WHEN yr=2016 THEN act END) a16, MAX(CASE WHEN yr=2017 THEN est END) e17, MAX(CASE WHEN yr=2017 THEN act END) a17, MAX(CASE WHEN yr=2025 THEN est END) e25, MAX(CASE WHEN yr=2025 THEN act END) a25 FROM y GROUP BY 1)\nSELECT COALESCE(wc,'ALL') wc, ROUND(SUM(a25)-SUM(a16),0) dclk16, ROUND((SUM(e25)-SUM(e16))*SUM(a16)/SUM(e16),0) load16, ROUND(SUM(e25)*(SUM(a25)/SUM(e25)-SUM(a16)/SUM(e16)),0) ratio16,\n ROUND(SUM(a25)-SUM(a17),0) dclk17, ROUND((SUM(e25)-SUM(e17))*SUM(a17)/SUM(e17),0) load17, ROUND(SUM(e25)*(SUM(a25)/SUM(e25)-SUM(a17)/SUM(e17)),0) ratio17\nFROM p GROUP BY ROLLUP(wc) ORDER BY wc NULLS LAST",
  "columns": [
   "wc",
   "dclk16",
   "load16",
   "ratio16",
   "dclk17",
   "load17",
   "ratio17"
  ],
  "row_count": 9,
  "rows": [
   [
    "ALL",
    -15739.0,
    -6530.0,
    -9209.0,
    -11972.0,
    -14314.0,
    2342.0
   ],
   [
    "assembly",
    -2134.0,
    -542.0,
    -1592.0,
    -1755.0,
    -1757.0,
    2.0
   ],
   [
    "brake",
    -2889.0,
    -408.0,
    -2481.0,
    -2455.0,
    -1605.0,
    -850.0
   ],
   [
    "inspect",
    -183.0,
    -179.0,
    -4.0,
    -236.0,
    -223.0,
    -14.0
   ],
   [
    "laser",
    -1210.0,
    192.0,
    -1402.0,
    -928.0,
    -1121.0,
    193.0
   ],
   [
    "lathe",
    -1713.0,
    -1585.0,
    -128.0,
    -1997.0,
    -2111.0,
    114.0
   ],
   [
    "mill",
    -4813.0,
    -5057.0,
    244.0,
    -2761.0,
    -3601.0,
    840.0
   ],
   [
    "paint",
    -866.0,
    148.0,
    -1013.0,
    -1081.0,
    -763.0,
    -319.0
   ],
   [
    "weld",
    -1931.0,
    2317.0,
    -4248.0,
    -759.0,
    -2289.0,
    1529.0
   ]
  ],
  "error": null
 },
 {
  "id": "q391",
  "sql": "SELECT ROUND(165568.0-165056.7,1) dpaid_16_25, ROUND(108639.5-124657.1,1) dclk_16_25, ROUND(56928.5-40399.6,1) dunclk_16_25, ROUND(9209.0/15739.0,3) ratio_share_of_clk_fall16, ROUND(405555.0-349162.0,0) usd_diff_base, ROUND(405555.0-255110.0,0) usd_diff_3avg",
  "columns": [
   "dpaid_16_25",
   "dclk_16_25",
   "dunclk_16_25",
   "ratio_share_of_clk_fall16",
   "usd_diff_base",
   "usd_diff_3avg"
  ],
  "row_count": 1,
  "rows": [
   [
    511.3,
    -16017.6,
    16528.9,
    0.585,
    56393.0,
    150445.0
   ]
  ],
  "error": null
 },
 {
  "id": "q383",
  "sql": "WITH a AS (SELECT op_id, SUM(hours) act FROM shop_labour_entries GROUP BY 1),\ny AS (SELECT CAST(substr(o.completed_on,1,4) AS INT) yr, SUM(o.est_setup_hours+o.est_run_hours) est, SUM(a.act) act FROM erp_job_operations o JOIN a USING(op_id) GROUP BY 1)\nSELECT yr, ROUND(est,0) est, ROUND(act,0) act, ROUND(act/est,3) ratio,\n ROUND((est - FIRST_VALUE(est) OVER (ORDER BY yr)) * FIRST_VALUE(act/est) OVER (ORDER BY yr),0) clk_change_from_load_vs2016,\n ROUND(est*(act/est - FIRST_VALUE(act/est) OVER (ORDER BY yr)),0) clk_change_from_ratio_vs2016\nFROM y ORDER BY yr",
  "columns": [
   "yr",
   "est",
   "act",
   "ratio",
   "clk_change_from_load_vs2016",
   "clk_change_from_ratio_vs2016"
  ],
  "row_count": 11,
  "rows": [
   [
    2016,
    127344.0,
    124654.0,
    0.979,
    0.0,
    0.0
   ],
   [
    2017,
    136881.0,
    120888.0,
    0.883,
    9336.0,
    -13102.0
   ],
   [
    2018,
    137922.0,
    118413.0,
    0.859,
    10355.0,
    -16596.0
   ],
   [
    2019,
    132719.0,
    114207.0,
    0.861,
    5261.0,
    -15708.0
   ],
   [
    2020,
    118369.0,
    103065.0,
    0.871,
    -8785.0,
    -12804.0
   ],
   [
    2021,
    125819.0,
    109771.0,
    0.872,
    -1492.0,
    -13391.0
   ],
   [
    2022,
    126687.0,
    112026.0,
    0.884,
    -643.0,
    -11985.0
   ],
   [
    2023,
    120609.0,
    106030.0,
    0.879,
    -6592.0,
    -12032.0
   ],
   [
    2024,
    124809.0,
    110779.0,
    0.888,
    -2482.0,
    -11393.0
   ],
   [
    2025,
    120673.0,
    108915.0,
    0.903,
    -6530.0,
    -9209.0
   ],
   [
    null,
    53.0,
    43.0,
    0.808,
    -124602.0,
    -9.0
   ]
  ],
  "error": null
 },
 {
  "id": "q379",
  "sql": "WITH tc AS (SELECT CAST(substr(week_of,1,4) AS INT) yr, employee_id, SUM(regular_hours+overtime_hours) paid, COUNT(*) wks FROM hr_timecards GROUP BY 1,2),\nlb AS (SELECT CAST(substr(work_date,1,4) AS INT) yr, employee_id, SUM(hours) clk FROM shop_labour_entries GROUP BY 1,2),\nr AS (SELECT e.role, tc.yr, SUM(paid) paid, SUM(COALESCE(clk,0)) clk, SUM(wks) wks FROM tc LEFT JOIN lb USING(yr,employee_id) JOIN hr_employees e USING(employee_id) WHERE tc.yr BETWEEN 2016 AND 2025 GROUP BY 1,2),\nrate AS (SELECT employee_id, arg_max(hourly, effective_on) hourly FROM hr_pay_rates WHERE effective_on <= '2025-12-31' GROUP BY 1),\nrr AS (SELECT e.role, median(rate.hourly) med_rate FROM rate JOIN hr_employees e USING(employee_id) WHERE employee_id IN (SELECT employee_id FROM tc WHERE yr=2025) GROUP BY 1),\nx AS (SELECT role,\n SUM(CASE WHEN yr=2025 THEN paid-clk END)-SUM(CASE WHEN yr=2016 THEN paid-clk END) d16,\n SUM(CASE WHEN yr=2025 THEN paid-clk END)-SUM(CASE WHEN yr=2017 THEN paid-clk END) d17,\n (SUM(CASE WHEN yr BETWEEN 2023 AND 2025 THEN paid-clk END)-SUM(CASE WHEN yr BETWEEN 2017 AND 2019 THEN paid-clk END))/3.0 d3avg,\n SUM(CASE WHEN yr=2017 THEN wks END) wks17, SUM(CASE WHEN yr=2025 THEN wks END) wks25,\n SUM(CASE WHEN yr=2016 THEN wks END) wks16\n FROM r GROUP BY 1)\nSELECT role, ROUND(d16,0) d16, ROUND(d17,0) d17, ROUND(d3avg,0) d3avg, wks16, wks17, wks25, ROUND(med_rate,2) rate,\n ROUND(d17*med_rate,0) usd17, ROUND(d3avg*med_rate,0) usd3avg,\n ROUND(SUM(d16) OVER(),0) t16, ROUND(SUM(d17) OVER(),0) t17, ROUND(SUM(d3avg) OVER(),0) t3,\n ROUND(SUM(d17*med_rate) OVER(),0) tusd17, ROUND(SUM(d3avg*med_rate) OVER(),0) tusd3\nFROM x JOIN rr USING(role) ORDER BY role",
  "columns": [
   "role",
   "d16",
   "d17",
   "d3avg",
   "wks16",
   "wks17",
   "wks25",
   "rate",
   "usd17",
   "usd3avg",
   "t16",
   "t17",
   "t3",
   "tusd17",
   "tusd3"
  ],
  "row_count": 8,
  "rows": [
   [
    "assembler",
    1742.0,
    1435.0,
    754.0,
    531,
    532,
    524,
    18.94,
    27181.0,
    14272.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "inspector",
    232.0,
    308.0,
    452.0,
    196,
    196,
    196,
    23.14,
    7134.0,
    10458.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "laser operator",
    3716.0,
    2823.0,
    2559.0,
    301,
    343,
    392,
    24.92,
    70350.0,
    63772.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "machinist lathe",
    2049.0,
    3269.0,
    1980.0,
    432,
    409,
    441,
    27.12,
    88645.0,
    53693.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "machinist mill",
    4762.0,
    2832.0,
    2295.0,
    672,
    675,
    672,
    27.48,
    77830.0,
    63079.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "painter",
    2629.0,
    1303.0,
    1452.0,
    268,
    307,
    340,
    22.23,
    28966.0,
    32278.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "press brake operator",
    1804.0,
    1672.0,
    1349.0,
    392,
    360,
    365,
    22.38,
    37428.0,
    30186.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ],
   [
    "welder",
    -404.0,
    442.0,
    -480.0,
    1421,
    1382,
    1366,
    26.32,
    11627.0,
    -12629.0,
    16529.0,
    14085.0,
    10361.0,
    349162.0,
    255110.0
   ]
  ],
  "error": null
 },
 {
  "id": "q390",
  "sql": "WITH tc AS (SELECT CAST(substr(week_of,1,4) AS INT) yr, employee_id, SUM(regular_hours+overtime_hours) paid FROM hr_timecards GROUP BY 1,2),\nlb AS (SELECT CAST(substr(work_date,1,4) AS INT) yr, employee_id, SUM(hours) clk FROM shop_labour_entries GROUP BY 1,2),\nr AS (SELECT e.role, tc.yr, SUM(paid) paid, SUM(COALESCE(clk,0)) clk, COUNT(*) n FROM tc LEFT JOIN lb USING(yr,employee_id) JOIN hr_employees e USING(employee_id) WHERE tc.yr IN (2017,2025) GROUP BY 1,2),\nx AS (SELECT role, SUM(CASE WHEN yr=2025 THEN paid-clk ELSE -(paid-clk) END) d17, SUM(CASE WHEN yr=2025 THEN paid ELSE -paid END) dpaid17, SUM(CASE WHEN yr=2025 THEN clk ELSE -clk END) dclk17, MAX(CASE WHEN yr=2025 THEN paid/n END) paid_per_head25 FROM r GROUP BY 1)\nSELECT role, ROUND(d17,0) d17, ROUND(dpaid17,0) dpaid17, ROUND(dclk17,0) dclk17, ROUND(paid_per_head25,0) paid_per_head25, ROUND(d17/paid_per_head25,2) fte_equiv, ROUND(SUM(d17/paid_per_head25) OVER (),2) fte_total FROM x ORDER BY d17 DESC",
  "columns": [
   "role",
   "d17",
   "dpaid17",
   "dclk17",
   "paid_per_head25",
   "fte_equiv",
   "fte_total"
  ],
  "row_count": 8,
  "rows": [
   [
    "machinist lathe",
    3269.0,
    1272.0,
    -1997.0,
    1886.0,
    1.73,
    7.92
   ],
   [
    "machinist mill",
    2832.0,
    -104.0,
    -2936.0,
    1723.0,
    1.64,
    7.92
   ],
   [
    "laser operator",
    2823.0,
    1896.0,
    -927.0,
    1890.0,
    1.49,
    7.92
   ],
   [
    "press brake operator",
    1672.0,
    -803.0,
    -2475.0,
    1562.0,
    1.07,
    7.92
   ],
   [
    "assembler",
    1435.0,
    -320.0,
    -1755.0,
    1681.0,
    0.85,
    7.92
   ],
   [
    "painter",
    1303.0,
    213.0,
    -1090.0,
    1869.0,
    0.7,
    7.92
   ],
   [
    "welder",
    442.0,
    -448.0,
    -890.0,
    1647.0,
    0.27,
    7.92
   ],
   [
    "inspector",
    308.0,
    72.0,
    -236.0,
    1904.0,
    0.16,
    7.92
   ]
  ],
  "error": null
 },
 {
  "id": "q349",
  "sql": "WITH tc AS (SELECT CAST(substr(week_of,1,4) AS INT) yr, employee_id, SUM(regular_hours) reg, SUM(overtime_hours) ot, COUNT(*) wks FROM hr_timecards GROUP BY 1,2),\nlb AS (SELECT CAST(substr(work_date,1,4) AS INT) yr, employee_id, SUM(hours) clk FROM shop_labour_entries GROUP BY 1,2)\nSELECT e.role, tc.yr, COUNT(*) n, ROUND(SUM(reg),0) reg, ROUND(SUM(ot),0) ot, ROUND(SUM(reg+ot)/SUM(wks),1) paid_per_wk,\nROUND(quantile_cont(1-COALESCE(clk,0)/(reg+ot),0.1),3) p10, ROUND(median(1-COALESCE(clk,0)/(reg+ot)),3) p50, ROUND(quantile_cont(1-COALESCE(clk,0)/(reg+ot),0.9),3) p90\nFROM tc LEFT JOIN lb USING(yr,employee_id) JOIN hr_employees e USING(employee_id)\nWHERE tc.yr IN (2016,2019,2022,2025) AND e.role NOT IN ('welder','inspector') GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "role",
   "yr",
   "n",
   "reg",
   "ot",
   "paid_per_wk",
   "p10",
   "p50",
   "p90"
  ],
  "row_count": 24,
  "rows": [
   [
    "assembler",
    2016,
    12,
    20488.0,
    81.0,
    38.7,
    0.215,
    0.404,
    0.523
   ],
   [
    "assembler",
    2019,
    11,
    21128.0,
    0.0,
    38.4,
    0.314,
    0.451,
    0.585
   ],
   [
    "assembler",
    2022,
    12,
    19864.0,
    0.0,
    38.6,
    0.365,
    0.464,
    0.553
   ],
   [
    "assembler",
    2025,
    12,
    20176.0,
    0.0,
    38.5,
    0.367,
    0.454,
    0.569
   ],
   [
    "laser operator",
    2016,
    8,
    11544.0,
    1072.0,
    41.9,
    -0.118,
    0.068,
    0.205
   ],
   [
    "laser operator",
    2019,
    9,
    12600.0,
    0.0,
    38.5,
    0.043,
    0.106,
    0.175
   ],
   [
    "laser operator",
    2022,
    9,
    14328.0,
    0.0,
    38.5,
    0.118,
    0.228,
    0.35
   ],
   [
    "laser operator",
    2025,
    8,
    15120.0,
    0.0,
    38.6,
    0.188,
    0.274,
    0.32
   ],
   [
    "machinist lathe",
    2016,
    10,
    16640.0,
    0.0,
    38.5,
    0.631,
    0.747,
    0.845
   ],
   [
    "machinist lathe",
    2019,
    12,
    15968.0,
    0.0,
    38.5,
    0.661,
    0.747,
    0.883
   ],
   [
    "machinist lathe",
    2022,
    10,
    16280.0,
    0.0,
    38.5,
    0.706,
    0.772,
    0.852
   ],
   [
    "machinist lathe",
    2025,
    9,
    16976.0,
    0.0,
    38.5,
    0.789,
    0.833,
    0.872
   ],
   [
    "machinist mill",
    2016,
    16,
    25912.0,
    106.0,
    38.7,
    0.212,
    0.366,
    0.492
   ],
   [
    "machinist mill",
    2019,
    16,
    26112.0,
    0.0,
    38.4,
    0.396,
    0.498,
    0.728
   ],
   [
    "machinist mill",
    2022,
    14,
    26112.0,
    0.0,
    38.5,
    0.476,
    0.561,
    0.765
   ],
   [
    "machinist mill",
    2025,
    15,
    25840.0,
    0.0,
    38.5,
    0.457,
    0.561,
    0.672
   ],
   [
    "painter",
    2016,
    8,
    10280.0,
    1038.0,
    42.2,
    -0.076,
    0.069,
    0.136
   ],
   [
    "painter",
    2019,
    9,
    12288.0,
    120.0,
    38.8,
    0.036,
    0.174,
    0.299
   ],
   [
    "painter",
    2022,
    7,
    12712.0,
    0.0,
    38.5,
    0.113,
    0.23,
    0.284
   ],
   [
    "painter",
    2025,
    7,
    13080.0,
    0.0,
    38.5,
    0.127,
    0.285,
    0.338
   ],
   [
    "press brake operator",
    2016,
    8,
    15040.0,
    120.0,
    38.7,
    -0.061,
    0.025,
    0.126
   ],
   [
    "press brake operator",
    2019,
    9,
    15040.0,
    0.0,
    38.5,
    -0.114,
    0.065,
    0.185
   ],
   [
    "press brake operator",
    2022,
    8,
    15056.0,
    0.0,
    38.4,
    -0.008,
    0.164,
    0.214
   ],
   [
    "press brake operator",
    2025,
    9,
    14056.0,
    0.0,
    38.5,
    0.073,
    0.198,
    0.224
   ]
  ],
  "error": null
 },
 {
  "id": "q382",
  "sql": "SELECT e.role, ROUND(SUM(CASE WHEN o.work_centre = CASE e.role WHEN 'assembler' THEN 'assembly' WHEN 'inspector' THEN 'inspect' WHEN 'laser operator' THEN 'laser' WHEN 'machinist lathe' THEN 'lathe' WHEN 'machinist mill' THEN 'mill' WHEN 'painter' THEN 'paint' WHEN 'press brake operator' THEN 'brake' WHEN 'welder' THEN 'weld' END THEN l.hours ELSE 0 END)/SUM(l.hours),4) own_wc_share, ROUND(SUM(l.hours),0) h, string_agg(DISTINCT o.work_centre, ',' ORDER BY o.work_centre) wcs\nFROM shop_labour_entries l JOIN erp_job_operations o USING(op_id) JOIN hr_employees e USING(employee_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "role",
   "own_wc_share",
   "h",
   "wcs"
  ],
  "row_count": 8,
  "rows": [
   [
    "assembler",
    1.0,
    115321.0,
    "assembly"
   ],
   [
    "inspector",
    1.0,
    20312.0,
    "inspect"
   ],
   [
    "laser operator",
    1.0,
    115439.0,
    "laser"
   ],
   [
    "machinist lathe",
    1.0,
    39204.0,
    "lathe"
   ],
   [
    "machinist mill",
    1.0,
    119667.0,
    "mill"
   ],
   [
    "painter",
    1.0,
    102132.0,
    "paint"
   ],
   [
    "press brake operator",
    1.0,
    133032.0,
    "brake"
   ],
   [
    "welder",
    1.0,
    483684.0,
    "weld"
   ]
  ],
  "error": null
 },
 {
  "id": "q395",
  "sql": "WITH tc AS (SELECT CAST(substr(week_of,1,4) AS INT) yr, employee_id, SUM(regular_hours+overtime_hours) paid, COUNT(*) wks FROM hr_timecards GROUP BY 1,2),\nlb AS (SELECT CAST(substr(work_date,1,4) AS INT) yr, employee_id, SUM(hours) clk FROM shop_labour_entries GROUP BY 1,2),\nr AS (SELECT e.role, tc.yr, SUM(paid) paid, SUM(COALESCE(clk,0)) clk FROM tc LEFT JOIN lb USING(yr,employee_id) JOIN hr_employees e USING(employee_id) WHERE tc.yr BETWEEN 2016 AND 2025 GROUP BY 1,2),\nrate AS (SELECT employee_id, arg_max(hourly, effective_on) hourly FROM hr_pay_rates WHERE effective_on <= '2025-12-31' GROUP BY 1),\nrr AS (SELECT e.role, median(rate.hourly) med_rate FROM rate JOIN hr_employees e USING(employee_id) WHERE employee_id IN (SELECT employee_id FROM tc WHERE yr=2025) GROUP BY 1),\nx AS (SELECT role,\n (SUM(CASE WHEN yr BETWEEN 2023 AND 2025 THEN paid-clk END)-SUM(CASE WHEN yr BETWEEN 2017 AND 2019 THEN paid-clk END))/3.0 d3avg,\n SUM(CASE WHEN yr=2025 THEN paid-clk END)-SUM(CASE WHEN yr=2017 THEN paid-clk END) d17\n FROM r GROUP BY 1)\nSELECT role, ROUND(d3avg,0) d3avg, ROUND(d3avg*med_rate,0) usd3avg, ROUND(d17*med_rate,0) usd17,\n ROUND(SUM(d3avg) OVER(),0) t3, ROUND(SUM(d3avg*med_rate) OVER(),0) tusd3, ROUND(SUM(d17*med_rate) OVER(),0) tusd17,\n ROUND(SUM(CASE WHEN role IN ('machinist mill','machinist lathe') THEN d3avg*med_rate END) OVER(),0) usd3_machining\nFROM x JOIN rr USING(role) ORDER BY role",
  "columns": [
   "role",
   "d3avg",
   "usd3avg",
   "usd17",
   "t3",
   "tusd3",
   "tusd17",
   "usd3_machining"
  ],
  "row_count": 8,
  "rows": [
   [
    "assembler",
    754.0,
    14272.0,
    27181.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "inspector",
    452.0,
    10458.0,
    7134.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "laser operator",
    2559.0,
    63772.0,
    70350.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "machinist lathe",
    1980.0,
    53693.0,
    88645.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "machinist mill",
    2295.0,
    63079.0,
    77830.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "painter",
    1452.0,
    32278.0,
    28966.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "press brake operator",
    1349.0,
    30186.0,
    37428.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
   ],
   [
    "welder",
    -480.0,
    -12629.0,
    11627.0,
    10361.0,
    255110.0,
    349162.0,
    116772.0
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

Save `grade.json`: {"finding": "F9", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
