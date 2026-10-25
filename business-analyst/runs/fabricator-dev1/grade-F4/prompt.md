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
 "id": "F4",
 "hypothesis": "H9",
 "title": "No large customer loses money under any cost allocation tested; whether low-dollar family 1 work loses money depends on how indirect labour is charged, which the records cannot settle",
 "conclusion": "Observed: none of the 51 customers with at least $500k of 2016-2025 revenue ($249,667,938 of revenue, 66,246 jobs) has negative contribution after PO material (outside processing included) and conversion cost. That holds with all conversion charged per clocked hour, and with half or all of indirect labour charged per invoiced job instead (q198). Margin for this group is 17.81% on the hour basis and 17.95% with indirect labour charged per job (q198). 2021 was the one broad dip: operating margin was 5.36% against 14.63%-20.26% in other years (q106), and 2021 GL material was $10.89M against $26.11M of revenue (q179). Below the customer level the result depends on how indirect labour ($31.57M over 10 years, q179) is allocated. Charged per clocked hour, every family and quantity band is positive, and 22 of 1,151 repeat parts lose $82,954 over ten years (q204). Charged per invoiced job ($346-$536 a job, q190), family 1 turns negative. Family 1 is 39,862 of 76,219 jobs (52.3%), with a median job of $902 and 3.88 clocked hours a job; it goes from +$11.71M to -$444,827 (q185, q191, q209). Jobs under $1k (23,747, 31.16% of jobs, $14.77M revenue) go from +$2.60M to -$1.31M (half charged per job) or -$5.21M (all charged per job) (q197, q209). Repeat parts below zero become 13 (half per job) or 41 (all per job; $3.10M revenue, -$231,741, 24 of them family 1) (q208). Jobs of 1-5 pieces stay positive under every basis (+$1.87M with all indirect labour charged per job, q185). My original ranking (family 6 and small-quantity work weakest) was therefore a product of the per-hour rule. New test (q232): year to year, indirect labour does not follow either candidate driver. It rose 36.7% from 2016 to 2025 while invoiced jobs fell 7.3% and clocked hours fell 12.8% (q234), and it stayed at 0.75-0.87 of direct labour every year (q232). Interpretation: indirect labour behaves like a wage-driven fixed cost, not a cost that scales with jobs or hours, so neither allocation is right by construction. Action (interpretation): no customer needs repricing on this evidence. If a minimum or setup charge is considered, base it on job value, not quantity, and look at family 1 first, but only after measuring what indirect staff actually spend their time on.",
 "dollars_a_year": 8295.4,
 "size_query": "q234",
 "claims": [
  {
   "text": "Customers with at least $500k: 51 of 288, $249,667,938 revenue, 66,246 jobs; 0 negative on the hour basis, with half of indirect labour per job, or with all of it per job; margin 17.81% (hour basis) vs 17.95% (all per job).",
   "queries": [
    "q198"
   ]
  },
  {
   "text": "Operating margin 5.36% in 2021 vs 14.63%-20.26% in other years; 2021 GL material $10.89M on $26.11M revenue.",
   "queries": [
    "q106",
    "q179"
   ]
  },
  {
   "text": "Indirect labour is $31.57M over 10 years; per invoiced job it ran $346-$536 a year.",
   "queries": [
    "q179",
    "q190"
   ]
  },
  {
   "text": "Family 1: 39,862 of 76,219 jobs (52.3%), median job $902, 3.88 clocked h per job; contribution +$11,713,995 on the hour basis, -$444,827 (-0.97% of revenue) with indirect labour charged per job. With all of it charged per job, negative in 5 of 10 years; with half, negative only in 2021.",
   "queries": [
    "q185",
    "q190",
    "q191",
    "q209"
   ]
  },
  {
   "text": "Jobs under $1k: 23,747 (31.16% of jobs), $14,773,429 revenue; contribution +$2,600,113 on the hour basis, -$1,306,041 with half per job, -$5,212,195 with all per job.",
   "queries": [
    "q197",
    "q209"
   ]
  },
  {
   "text": "Jobs of 1-5 pieces stay positive with indirect labour charged per job (+$1,865,880, 4.94% margin).",
   "queries": [
    "q185"
   ]
  },
  {
   "text": "Repeat parts (at least 3 invoice years and $50k each, 1,151 parts) below zero: 22 on the hour basis (-$82,954, $8,295.4 a year; 19 parts and -$72,189 on received material only); 13 with half per job (-$38,736); 41 with all per job ($3,095,536 revenue, -$231,741, $23,174.1 a year; 24 in family 1).",
   "queries": [
    "q204",
    "q208",
    "q234"
   ]
  },
  {
   "text": "Outside processing ($1,718,008, all on job POs) lowers family 3 contribution from $10.08M to $8.82M and family 4 from $5.98M to $5.54M; no family or band changes sign.",
   "queries": [
    "q163",
    "q185"
   ]
  },
  {
   "text": "Indirect labour rose 36.7% from 2016 to 2025 ($2,810,490 to $3,841,144) while invoiced jobs fell 7.3% (7,732 to 7,171) and clocked hours fell 12.8%; indirect labour stayed at 0.751-0.869 of direct labour.",
   "queries": [
    "q232",
    "q234"
   ]
  },
  {
   "text": "Clocked hours fell from 75.5% to 65.6% of paid timecard hours (2016-2025). Conversion cost per paid hour rose 27.6% ($77.6 to $99.0) and per clocked hour 46.8% ($102.8 to $150.9).",
   "queries": [
    "q169",
    "q201",
    "q209"
   ]
  },
  {
   "text": "29.7% of PO lines (= POs, 108,171) have no receipt, but they are $4,207,405 of $92,758,289 (4.54%). PO material equals GL material in every year.",
   "queries": [
    "q169",
    "q203",
    "q209",
    "q230"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "That low-dollar or family 1 work is profitable, or that it loses money: the sign depends on an allocation rule the data cannot settle (q185, q197, q232). Nor that the 22 (or 41) parts are recoverable losses: dropping or repricing them would not remove the fixed indirect cost. Nor that costs rose by the full 46.8% rise in the clocked-hour rate; part of it is lower hour capture (q201). Nor that small-quantity jobs under-clock setup: 1-5 piece jobs clocked 0.983 of estimated hours vs 0.759 for 100+ pieces (q177). The 10,557 negative single jobs (q141) are not losses either: labour postings run up to 208 h (q162).",
 "could_not_tell": "Which allocation of indirect labour is right. The records have no activity drivers (time by task for indirect staff, number of POs, inspections, shipments or invoices handled per job). Year-level totals show it follows neither job count nor hours (q232). Premium freight ($78,124, q179) exists only in the GL. The conversion rate is one plant-wide average with no work-centre rates. Not explained: 217 jobs created 2016-2024 that were completed but never invoiced, carrying $565,008 of PO material (q180, q220). That is either an unmeasured cost or unbilled revenue.",
 "next_step": "Sample what indirect staff (purchasing, scheduling, inspection, shipping, billing) spend time on per job, by job value band, to pick the allocation. Until then, report family 1 and jobs under $1k under both bases. Review the 217 completed but uninvoiced jobs (q220) separately.",
 "incomplete": false
}

[
 {
  "id": "q198",
  "sql": "WITH rev AS (SELECT sl.job_id, min(i.customer_id) cust, sum(i.amount) rev, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nmat AS (SELECT po.job_id, sum(pl.amount) mat FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv, -sum(CASE WHEN account='indirect labour' THEN amount END) ind FROM erp_general_ledger GROUP BY 1),\nh AS (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1),\nnj AS (SELECT yr, count(*) n FROM rev GROUP BY 1),\nlr AS (SELECT yr, conv/h rate, (conv-ind)/h rate_ex_ind, ind/n per_job, (conv-0.5*ind)/h rate_half, 0.5*ind/n per_job_half FROM g JOIN h USING(yr) JOIN nj USING(yr)),\nc AS (SELECT cust, count(*) jobs, sum(rev) rev, sum(rev-coalesce(mat,0)-coalesce(hrs,0)*rate) c_hour, sum(rev-coalesce(mat,0)-coalesce(hrs,0)*rate_half-per_job_half) c_half, sum(rev-coalesce(mat,0)-coalesce(hrs,0)*rate_ex_ind-per_job) c_full FROM erp_jobs j JOIN rev USING(job_id) LEFT JOIN mat USING(job_id) LEFT JOIN lab USING(job_id) JOIN lr USING(yr) GROUP BY cust)\nSELECT rev>=500000 big, count(*) customers, round(sum(rev)) rev, sum(jobs) jobs,\n sum((c_hour<0)::INT) neg_hour_basis, round(sum(CASE WHEN c_hour<0 THEN rev END)) rev_neg_hour, round(sum(CASE WHEN c_hour<0 THEN c_hour END)) loss_neg_hour,\n sum((c_half<0)::INT) neg_half, round(sum(CASE WHEN c_half<0 THEN rev END)) rev_neg_half, round(sum(CASE WHEN c_half<0 THEN c_half END)) loss_neg_half,\n sum((c_full<0)::INT) neg_full, round(sum(CASE WHEN c_full<0 THEN rev END)) rev_neg_full, round(sum(CASE WHEN c_full<0 THEN c_full END)) loss_neg_full,\n round(sum(c_hour)/sum(rev),4) m_hour, round(sum(c_full)/sum(rev),4) m_full\nFROM c GROUP BY 1 ORDER BY 1",
  "columns": [
   "big",
   "customers",
   "rev",
   "jobs",
   "neg_hour_basis",
   "rev_neg_hour",
   "loss_neg_hour",
   "neg_half",
   "rev_neg_half",
   "loss_neg_half",
   "neg_full",
   "rev_neg_full",
   "loss_neg_full",
   "m_hour",
   "m_full"
  ],
  "row_count": 2,
  "rows": [
   [
    false,
    237,
    31496682.0,
    9973,
    19,
    389413.0,
    -20325.0,
    43,
    732208.0,
    -41773.0,
    64,
    1463941.0,
    -160401.0,
    0.1515,
    0.1349
   ],
   [
    true,
    51,
    249667938.0,
    66246,
    0,
    null,
    null,
    0,
    null,
    null,
    0,
    null,
    null,
    0.1781,
    0.1795
   ]
  ],
  "error": null
 },
 {
  "id": "q106",
  "sql": "WITH gl AS (SELECT substr(period,1,4)::INT yr, sum(CASE WHEN account='revenue' THEN amount END) rev, -sum(CASE WHEN account='material' THEN amount END) mat, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv, -sum(CASE WHEN account IN ('outside processing','premium freight') THEN amount END) other FROM erp_general_ledger GROUP BY 1),\nlab AS (SELECT year(work_date::DATE) yr, sum(hours) hrs FROM shop_labour_entries GROUP BY 1)\nSELECT gl.yr, round(rev) rev, round(mat) mat, round(conv) conv, round(other) other, round(hrs) clocked_h, round((rev-mat)/hrs,1) va_per_h, round(conv/hrs,1) loaded_rate_per_h, round((rev-mat-conv-other)/rev,4) op_margin FROM gl JOIN lab USING(yr) ORDER BY yr",
  "columns": [
   "yr",
   "rev",
   "mat",
   "conv",
   "other",
   "clocked_h",
   "va_per_h",
   "loaded_rate_per_h",
   "op_margin"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    22808424.0,
    6269293.0,
    12814328.0,
    388133.0,
    124657.0,
    132.7,
    102.8,
    0.1463
   ],
   [
    2017,
    24783238.0,
    7178895.0,
    12955311.0,
    233230.0,
    120946.0,
    145.6,
    107.1,
    0.1782
   ],
   [
    2018,
    27532837.0,
    8678090.0,
    13216003.0,
    196218.0,
    118400.0,
    159.2,
    111.6,
    0.1977
   ],
   [
    2019,
    26953546.0,
    7991553.0,
    13335038.0,
    165317.0,
    114170.0,
    166.1,
    116.8,
    0.2026
   ],
   [
    2020,
    23896030.0,
    6604465.0,
    13012233.0,
    148801.0,
    103093.0,
    167.7,
    126.2,
    0.1729
   ],
   [
    2021,
    26112647.0,
    10892365.0,
    13605326.0,
    216163.0,
    109740.0,
    138.7,
    124.0,
    0.0536
   ],
   [
    2022,
    32853151.0,
    12380332.0,
    14641482.0,
    101327.0,
    112052.0,
    182.7,
    130.7,
    0.1744
   ],
   [
    2023,
    31707321.0,
    10665874.0,
    15183450.0,
    95740.0,
    106029.0,
    198.4,
    143.2,
    0.1817
   ],
   [
    2024,
    32721028.0,
    10318165.0,
    15870847.0,
    121400.0,
    111064.0,
    201.7,
    142.9,
    0.1959
   ],
   [
    2025,
    31414512.0,
    10061251.0,
    16397881.0,
    129803.0,
    108640.0,
    196.6,
    150.9,
    0.1536
   ]
  ],
  "error": null
 },
 {
  "id": "q179",
  "sql": "SELECT account, round(sum(amount)) total_10y, round(sum(CASE WHEN period LIKE '2021%' THEN amount END)) y2021, count(*) n FROM erp_general_ledger GROUP BY 1 ORDER BY 1",
  "columns": [
   "account",
   "total_10y",
   "y2021",
   "n"
  ],
  "row_count": 11,
  "rows": [
   [
    "benefits and payroll taxes",
    -20832404.0,
    -1986528.0,
    120
   ],
   [
    "direct labour",
    -37873705.0,
    -3662103.0,
    120
   ],
   [
    "indirect labour",
    -31567642.0,
    -2959658.0,
    120
   ],
   [
    "material",
    -91040283.0,
    -10892365.0,
    120
   ],
   [
    "outside processing",
    -1718008.0,
    -184940.0,
    120
   ],
   [
    "overtime hours (memo)",
    18406.0,
    2755.0,
    61
   ],
   [
    "premium freight",
    -78124.0,
    -31223.0,
    120
   ],
   [
    "revenue",
    280782733.0,
    26112647.0,
    120
   ],
   [
    "rework labour (memo)",
    108569.0,
    13764.0,
    101
   ],
   [
    "scrap material (memo)",
    2474799.0,
    346419.0,
    120
   ],
   [
    "shop overhead",
    -50758148.0,
    -4997038.0,
    120
   ]
  ],
  "error": null
 },
 {
  "id": "q190",
  "sql": "WITH rev AS (SELECT sl.job_id, min(i.customer_id) cust, sum(i.amount) rev, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nmat AS (SELECT po.job_id, sum(pl.amount) mat FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv, -sum(CASE WHEN account='indirect labour' THEN amount END) ind FROM erp_general_ledger GROUP BY 1),\nh AS (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1),\nnj AS (SELECT yr, count(*) n FROM rev GROUP BY 1),\nlr AS (SELECT yr, conv/h rate, (conv-ind)/h rate_ex_ind, ind/n per_job, (conv-0.5*ind)/h rate_half, 0.5*ind/n per_job_half FROM g JOIN h USING(yr) JOIN nj USING(yr)),\njj AS (SELECT rev.yr, p.family, j.quantity<=5 small, rev, coalesce(mat,0) mat, coalesce(hrs,0) hrs, rate, rate_ex_ind, per_job, rate_half, per_job_half FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) JOIN rev USING(job_id) LEFT JOIN mat USING(job_id) LEFT JOIN lab USING(job_id) JOIN lr USING(yr))\nSELECT yr, round(avg(per_job)) ind_per_job,\n round(sum(rev-mat-hrs*rate) FILTER (WHERE family=1)) f1_hour_basis,\n round(sum(rev-mat-hrs*rate_half-per_job_half) FILTER (WHERE family=1)) f1_half_per_job,\n round(sum(rev-mat-hrs*rate_ex_ind-per_job) FILTER (WHERE family=1)) f1_full_per_job,\n round(sum(rev-mat-hrs*rate_ex_ind-per_job) FILTER (WHERE small)) small_full_per_job,\n round(sum(rev-mat-hrs*rate_ex_ind-per_job) FILTER (WHERE family=6 AND small)) f6s_full_per_job,\n round(sum(rev) FILTER (WHERE family=1)) f1_rev, count(*) FILTER (WHERE family=1) f1_jobs\nFROM jj GROUP BY yr ORDER BY yr",
  "columns": [
   "yr",
   "ind_per_job",
   "f1_hour_basis",
   "f1_half_per_job",
   "f1_full_per_job",
   "small_full_per_job",
   "f6s_full_per_job",
   "f1_rev",
   "f1_jobs"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    363.0,
    811635.0,
    256162.0,
    -299311.0,
    179517.0,
    25180.0,
    3413748.0,
    4077
   ],
   [
    2017,
    355.0,
    988474.0,
    442094.0,
    -104286.0,
    161049.0,
    31109.0,
    3862600.0,
    4150
   ],
   [
    2018,
    346.0,
    1145971.0,
    580075.0,
    14178.0,
    254903.0,
    49198.0,
    4406518.0,
    4477
   ],
   [
    2019,
    379.0,
    1262887.0,
    668802.0,
    74718.0,
    238991.0,
    45575.0,
    4396755.0,
    4236
   ],
   [
    2020,
    393.0,
    1032979.0,
    471525.0,
    -89929.0,
    132405.0,
    3791.0,
    4024037.0,
    3968
   ],
   [
    2021,
    385.0,
    490422.0,
    -80893.0,
    -652208.0,
    -160014.0,
    -100704.0,
    4492770.0,
    4068
   ],
   [
    2022,
    417.0,
    1472837.0,
    866554.0,
    260271.0,
    227064.0,
    34220.0,
    5755844.0,
    3931
   ],
   [
    2023,
    497.0,
    1619712.0,
    943467.0,
    267223.0,
    248180.0,
    35930.0,
    5529696.0,
    3708
   ],
   [
    2024,
    500.0,
    1519110.0,
    851923.0,
    184735.0,
    418209.0,
    60995.0,
    5071363.0,
    3573
   ],
   [
    2025,
    536.0,
    1369969.0,
    634875.0,
    -100219.0,
    165577.0,
    25617.0,
    5128658.0,
    3674
   ]
  ],
  "error": null
 },
 {
  "id": "q185",
  "sql": "WITH rev AS (SELECT sl.job_id, min(i.customer_id) cust, sum(i.amount) rev, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nmat AS (SELECT po.job_id, sum(pl.amount) mat, sum(CASE WHEN pl.material='outside processing' THEN pl.amount ELSE 0 END) osp FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv, -sum(CASE WHEN account='indirect labour' THEN amount END) ind FROM erp_general_ledger GROUP BY 1),\nh AS (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1),\nnj AS (SELECT yr, count(*) n FROM rev GROUP BY 1),\nlr AS (SELECT yr, conv/h rate, (conv-ind)/h rate_ex_ind, ind/n per_job FROM g JOIN h USING(yr) JOIN nj USING(yr)),\njj AS (SELECT rev.yr, p.family, CASE WHEN j.quantity<=5 THEN 'a 1-5' WHEN j.quantity<=10 THEN 'b 6-10' WHEN j.quantity<=25 THEN 'c 11-25' WHEN j.quantity<=50 THEN 'd 26-50' WHEN j.quantity<=100 THEN 'e 51-100' ELSE 'f 100+' END qb, rev, coalesce(mat,0) mat, coalesce(osp,0) osp, coalesce(hrs,0) hrs, rate, rate_ex_ind, per_job FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) JOIN rev USING(job_id) LEFT JOIN mat USING(job_id) LEFT JOIN lab USING(job_id) JOIN lr USING(yr))\nSELECT 'qty' dim, qb grp, count(*) jobs, round(sum(rev)) rev, round(sum(rev-(mat-osp)-hrs*rate)) contrib_F4_basis, round(sum(rev-mat-hrs*rate)) contrib_with_osp, round(sum(rev-mat-hrs*rate_ex_ind-per_job)) contrib_ind_per_job, round(sum(rev-mat-hrs*rate_ex_ind-per_job)/sum(rev),4) margin_ind_per_job, round(avg(per_job),1) avg_per_job_charge FROM jj GROUP BY qb\nUNION ALL\nSELECT 'family', family::VARCHAR, count(*), round(sum(rev)), round(sum(rev-(mat-osp)-hrs*rate)), round(sum(rev-mat-hrs*rate)), round(sum(rev-mat-hrs*rate_ex_ind-per_job)), round(sum(rev-mat-hrs*rate_ex_ind-per_job)/sum(rev),4), round(avg(per_job),1) FROM jj GROUP BY family\nORDER BY 1,2",
  "columns": [
   "dim",
   "grp",
   "jobs",
   "rev",
   "contrib_F4_basis",
   "contrib_with_osp",
   "contrib_ind_per_job",
   "margin_ind_per_job",
   "avg_per_job_charge"
  ],
  "row_count": 12,
  "rows": [
   [
    "family",
    "1",
    39862,
    46081989.0,
    11713995.0,
    11713995.0,
    -444827.0,
    -0.0097,
    413.2
   ],
   [
    "family",
    "2",
    9954,
    61294548.0,
    11490841.0,
    11490841.0,
    13390986.0,
    0.2185,
    413.8
   ],
   [
    "family",
    "3",
    14678,
    81570391.0,
    10083899.0,
    8821861.0,
    12447894.0,
    0.1526,
    418.0
   ],
   [
    "family",
    "4",
    1964,
    38150098.0,
    5982256.0,
    5537107.0,
    9753924.0,
    0.2557,
    421.4
   ],
   [
    "family",
    "5",
    4376,
    30382268.0,
    9574731.0,
    9574731.0,
    10631994.0,
    0.3499,
    407.5
   ],
   [
    "family",
    "6",
    5385,
    23685325.0,
    2095274.0,
    2095274.0,
    3293912.0,
    0.1391,
    414.3
   ],
   [
    "qty",
    "a 1-5",
    14117,
    37777626.0,
    3095680.0,
    2573111.0,
    1865880.0,
    0.0494,
    415.8
   ],
   [
    "qty",
    "b 6-10",
    10197,
    41634179.0,
    5079991.0,
    4591585.0,
    5529469.0,
    0.1328,
    414.7
   ],
   [
    "qty",
    "c 11-25",
    23734,
    66933618.0,
    11164889.0,
    10727611.0,
    8517063.0,
    0.1272,
    413.5
   ],
   [
    "qty",
    "d 26-50",
    17116,
    57028727.0,
    11662669.0,
    11530045.0,
    10349240.0,
    0.1815,
    414.2
   ],
   [
    "qty",
    "e 51-100",
    7885,
    41741489.0,
    9558893.0,
    9484868.0,
    10379123.0,
    0.2487,
    414.4
   ],
   [
    "qty",
    "f 100+",
    3170,
    36048980.0,
    10378875.0,
    10326588.0,
    12433107.0,
    0.3449,
    409.8
   ]
  ],
  "error": null
 },
 {
  "id": "q191",
  "sql": "WITH rev AS (SELECT sl.job_id, sum(i.amount) rev FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1)\nSELECT p.family, count(*) jobs, round(median(j.quantity)) med_qty, round(sum(rev)/count(*)) rev_per_job, round(sum(hrs)/count(*),2) hrs_per_job, round(median(rev)) med_rev_per_job\nFROM erp_jobs j JOIN erp_customer_parts p USING(part_id) JOIN rev USING(job_id) LEFT JOIN lab USING(job_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "family",
   "jobs",
   "med_qty",
   "rev_per_job",
   "hrs_per_job",
   "med_rev_per_job"
  ],
  "row_count": 6,
  "rows": [
   [
    1,
    39862,
    24.0,
    1156.0,
    3.88,
    902.0
   ],
   [
    2,
    9954,
    22.0,
    6158.0,
    21.7,
    4362.0
   ],
   [
    3,
    14678,
    4.0,
    5557.0,
    23.55,
    4042.0
   ],
   [
    4,
    1964,
    20.0,
    19425.0,
    91.47,
    13112.0
   ],
   [
    5,
    4376,
    101.0,
    6943.0,
    23.75,
    5222.0
   ],
   [
    6,
    5385,
    4.0,
    4398.0,
    22.76,
    3083.0
   ]
  ],
  "error": null
 },
 {
  "id": "q209",
  "sql": "SELECT 7484+16263 jobs_lt1k, round((7484+16263)/76219.0,4) share_jobs_lt1k, 2749647+12023782 rev_lt1k, 298420+2301693 contrib_lt1k_hour, -984862-321179 contrib_lt1k_half, -2268144-2944051 contrib_lt1k_full, round(39862/76219.0,4) f1_job_share, round(4207405/92758289.0,4) no_receipt_amt_share, round(99.0/77.6-1,3) paid_rate_growth, round(150.9/102.8-1,3) clocked_rate_growth, round(348604/1128792.0,3) big_entry_hour_share",
  "columns": [
   "jobs_lt1k",
   "share_jobs_lt1k",
   "rev_lt1k",
   "contrib_lt1k_hour",
   "contrib_lt1k_half",
   "contrib_lt1k_full",
   "f1_job_share",
   "no_receipt_amt_share",
   "paid_rate_growth",
   "clocked_rate_growth",
   "big_entry_hour_share"
  ],
  "row_count": 1,
  "rows": [
   [
    23747,
    0.3116,
    14773429,
    2600113,
    -1306041,
    -5212195,
    0.523,
    0.0454,
    0.276,
    0.468,
    0.309
   ]
  ],
  "error": null
 },
 {
  "id": "q197",
  "sql": "WITH rev AS (SELECT sl.job_id, min(i.customer_id) cust, sum(i.amount) rev, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nmat AS (SELECT po.job_id, sum(pl.amount) mat FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv, -sum(CASE WHEN account='indirect labour' THEN amount END) ind FROM erp_general_ledger GROUP BY 1),\nh AS (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1),\nnj AS (SELECT yr, count(*) n FROM rev GROUP BY 1),\nlr AS (SELECT yr, conv/h rate, (conv-ind)/h rate_ex_ind, ind/n per_job, (conv-0.5*ind)/h rate_half, 0.5*ind/n per_job_half FROM g JOIN h USING(yr) JOIN nj USING(yr)),\njj AS (SELECT CASE WHEN rev<500 THEN 'a <500' WHEN rev<1000 THEN 'b 500-1k' WHEN rev<2500 THEN 'c 1k-2.5k' WHEN rev<5000 THEN 'd 2.5k-5k' WHEN rev<10000 THEN 'e 5k-10k' ELSE 'f 10k+' END vb, family, rev, coalesce(mat,0) mat, coalesce(hrs,0) hrs, rate, rate_ex_ind, per_job, rate_half, per_job_half FROM erp_jobs j JOIN erp_customer_parts p USING(part_id) JOIN rev USING(job_id) LEFT JOIN mat USING(job_id) LEFT JOIN lab USING(job_id) JOIN lr USING(yr))\nSELECT vb, count(*) jobs, round(count(*)/76219.0,4) job_share, round(sum(rev)) rev, round(sum((family=1)::INT)/count(*),3) f1_share_jobs, round(sum(rev-mat-hrs*rate)) contrib_hour_basis, round(sum(rev-mat-hrs*rate_half-per_job_half)) contrib_half_per_job, round(sum(rev-mat-hrs*rate_ex_ind-per_job)) contrib_full_per_job\nFROM jj GROUP BY vb ORDER BY vb",
  "columns": [
   "vb",
   "jobs",
   "job_share",
   "rev",
   "f1_share_jobs",
   "contrib_hour_basis",
   "contrib_half_per_job",
   "contrib_full_per_job"
  ],
  "row_count": 6,
  "rows": [
   [
    "a <500",
    7484,
    0.0982,
    2749647.0,
    0.994,
    298420.0,
    -984862.0,
    -2268144.0
   ],
   [
    "b 500-1k",
    16263,
    0.2134,
    12023782.0,
    0.915,
    2301693.0,
    -321179.0,
    -2944051.0
   ],
   [
    "c 1k-2.5k",
    22639,
    0.297,
    36339045.0,
    0.646,
    6905142.0,
    4199552.0,
    1493961.0
   ],
   [
    "d 2.5k-5k",
    13786,
    0.1809,
    49126082.0,
    0.191,
    7756133.0,
    7781687.0,
    7807240.0
   ],
   [
    "e 5k-10k",
    10088,
    0.1324,
    70577759.0,
    0.026,
    11475352.0,
    13361747.0,
    15248142.0
   ],
   [
    "f 10k+",
    5959,
    0.0782,
    110348305.0,
    0.001,
    20497069.0,
    25116901.0,
    29736733.0
   ]
  ],
  "error": null
 },
 {
  "id": "q204",
  "sql": "WITH rev AS (SELECT sl.job_id, sum(i.amount) rev, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nrc AS (SELECT DISTINCT po_id FROM erp_receipts),\nmat AS (SELECT po.job_id, sum(CASE WHEN pl.material<>'outside processing' THEN pl.amount ELSE 0 END) mat, sum(CASE WHEN pl.material<>'outside processing' AND rc.po_id IS NOT NULL THEN pl.amount ELSE 0 END) mat_rcvd, sum(pl.amount) mat_osp FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) LEFT JOIN rc USING(po_id) GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1),\nlr AS (SELECT g.yr, g.conv/l.h rate FROM (SELECT substr(period,1,4)::INT yr, -sum(amount) conv FROM erp_general_ledger WHERE account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') GROUP BY 1) g JOIN (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1) l USING(yr)),\njb AS (SELECT j.part_id, rev.yr, rev, coalesce(mat,0) mat, coalesce(mat_rcvd,0) mat_rcvd, coalesce(mat_osp,0) mat_osp, coalesce(hrs,0)*rate conv FROM erp_jobs j JOIN rev USING(job_id) LEFT JOIN mat USING(job_id) LEFT JOIN lab USING(job_id) JOIN lr USING(yr)),\np AS (SELECT part_id, sum(rev) rev, sum(rev-mat-conv) c_f4, sum(rev-mat_rcvd-conv) c_rcvd, sum(rev-mat_osp-conv) c_osp FROM jb GROUP BY 1 HAVING count(DISTINCT yr)>=3 AND sum(rev)>=50000)\nSELECT count(*) parts, sum((c_f4<0)::INT) neg_f4, round(sum(CASE WHEN c_f4<0 THEN c_f4 END)) loss_f4, sum((c_rcvd<0)::INT) neg_receipts_only, round(sum(CASE WHEN c_rcvd<0 THEN c_rcvd END)) loss_rcvd, sum((c_osp<0)::INT) neg_with_osp, round(sum(CASE WHEN c_osp<0 THEN c_osp END)) loss_osp, round(sum(CASE WHEN c_osp<0 THEN rev END)) rev_neg_osp FROM p",
  "columns": [
   "parts",
   "neg_f4",
   "loss_f4",
   "neg_receipts_only",
   "loss_rcvd",
   "neg_with_osp",
   "loss_osp",
   "rev_neg_osp"
  ],
  "row_count": 1,
  "rows": [
   [
    1151,
    22,
    -82954.0,
    19,
    -72189.0,
    22,
    -82954.0,
    2260412.0
   ]
  ],
  "error": null
 },
 {
  "id": "q208",
  "sql": "WITH rev AS (SELECT sl.job_id, sum(i.amount) rev, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1),\nmat AS (SELECT po.job_id, sum(pl.amount) mat FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material<>'outside processing' GROUP BY 1),\nlab AS (SELECT job_id, sum(hours) hrs FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv, -sum(CASE WHEN account='indirect labour' THEN amount END) ind FROM erp_general_ledger GROUP BY 1),\nh AS (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1),\nnj AS (SELECT yr, count(*) n FROM rev GROUP BY 1),\nlr AS (SELECT yr, conv/h rate, (conv-ind)/h rate_ex_ind, ind/n per_job, (conv-0.5*ind)/h rate_half, 0.5*ind/n per_job_half FROM g JOIN h USING(yr) JOIN nj USING(yr)),\njb AS (SELECT j.part_id, rev.yr, rev, coalesce(mat,0) mat, coalesce(hrs,0) hrs, rate, rate_ex_ind, per_job, rate_half, per_job_half FROM erp_jobs j JOIN rev USING(job_id) LEFT JOIN mat USING(job_id) LEFT JOIN lab USING(job_id) JOIN lr USING(yr)),\np AS (SELECT part_id, sum(rev) rev, sum(rev-mat-hrs*rate) c_h, sum(rev-mat-hrs*rate_half-per_job_half) c_half, sum(rev-mat-hrs*rate_ex_ind-per_job) c_full FROM jb GROUP BY 1 HAVING count(DISTINCT yr)>=3 AND sum(rev)>=50000)\nSELECT cp.family, count(*) parts, sum((c_h<0)::INT) neg_hour, sum((c_half<0)::INT) neg_half, round(sum(CASE WHEN c_half<0 THEN c_half END)) loss_half, sum((c_full<0)::INT) neg_full, round(sum(CASE WHEN c_full<0 THEN rev END)) rev_neg_full, round(sum(CASE WHEN c_full<0 THEN c_full END)) loss_full\nFROM p JOIN erp_customer_parts cp USING(part_id) GROUP BY ROLLUP(cp.family) ORDER BY cp.family NULLS LAST",
  "columns": [
   "family",
   "parts",
   "neg_hour",
   "neg_half",
   "loss_half",
   "neg_full",
   "rev_neg_full",
   "loss_full"
  ],
  "row_count": 7,
  "rows": [
   [
    1,
    155,
    0,
    0,
    null,
    24,
    1577748.0,
    -133462.0
   ],
   [
    2,
    278,
    1,
    1,
    -1005.0,
    1,
    55046.0,
    -3918.0
   ],
   [
    3,
    372,
    15,
    7,
    -13967.0,
    9,
    851007.0,
    -58138.0
   ],
   [
    4,
    91,
    1,
    0,
    null,
    0,
    null,
    null
   ],
   [
    5,
    135,
    0,
    0,
    null,
    0,
    null,
    null
   ],
   [
    6,
    120,
    5,
    5,
    -23764.0,
    7,
    611735.0,
    -36222.0
   ],
   [
    null,
    1151,
    22,
    13,
    -38736.0,
    41,
    3095536.0,
    -231741.0
   ]
  ],
  "error": null
 },
 {
  "id": "q234",
  "sql": "SELECT round(82954/10.0,1) hour_basis_parts_per_yr, round(38736/10.0,1) half_parts_per_yr, round(231741/10.0,1) full_parts_per_yr, round(444827/10.0,1) f1_full_per_yr, round(3841144/2810490.0-1,3) ind_growth, round(7171/7732.0-1,3) jobs_growth, round(108640/124657.0-1,3) hours_growth",
  "columns": [
   "hour_basis_parts_per_yr",
   "half_parts_per_yr",
   "full_parts_per_yr",
   "f1_full_per_yr",
   "ind_growth",
   "jobs_growth",
   "hours_growth"
  ],
  "row_count": 1,
  "rows": [
   [
    8295.4,
    3873.6,
    23174.1,
    44482.7,
    0.367,
    -0.073,
    -0.128
   ]
  ],
  "error": null
 },
 {
  "id": "q163",
  "sql": "SELECT pl.material, (po.job_id IS NULL) no_job, count(*) n, round(sum(pl.amount)) amt FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) GROUP BY ALL ORDER BY 1,2",
  "columns": [
   "material",
   "no_job",
   "n",
   "amt"
  ],
  "row_count": 4,
  "rows": [
   [
    "aluminium",
    false,
    2731,
    9416917.0
   ],
   [
    "carbon",
    false,
    101871,
    74195145.0
   ],
   [
    "outside processing",
    false,
    1234,
    1718008.0
   ],
   [
    "stainless",
    false,
    2335,
    7428219.0
   ]
  ],
  "error": null
 },
 {
  "id": "q232",
  "sql": "WITH g AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account='indirect labour' THEN amount END) ind, -sum(CASE WHEN account='direct labour' THEN amount END) dir FROM erp_general_ledger GROUP BY 1),\nh AS (SELECT year(work_date::DATE) yr, sum(hours) h FROM shop_labour_entries GROUP BY 1),\nn AS (SELECT yr, count(*) n FROM (SELECT sl.job_id, max(year(i.invoiced_on::DATE)) yr FROM erp_shipment_lines sl JOIN erp_invoices i USING(shipment_id) GROUP BY 1) GROUP BY 1)\nSELECT yr, round(ind) ind, n jobs, round(h) clocked_h, round(ind/n) ind_per_job, round(ind/h,1) ind_per_h, round(ind/dir,3) ind_over_dir FROM g JOIN h USING(yr) JOIN n USING(yr) ORDER BY yr",
  "columns": [
   "yr",
   "ind",
   "jobs",
   "clocked_h",
   "ind_per_job",
   "ind_per_h",
   "ind_over_dir"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    2810490.0,
    7732,
    124657.0,
    363.0,
    22.5,
    0.842
   ],
   [
    2017,
    2832686.0,
    7987,
    120946.0,
    355.0,
    23.4,
    0.832
   ],
   [
    2018,
    2937230.0,
    8489,
    118400.0,
    346.0,
    24.8,
    0.85
   ],
   [
    2019,
    2987695.0,
    7877,
    114170.0,
    379.0,
    26.2,
    0.853
   ],
   [
    2020,
    2935148.0,
    7462,
    103093.0,
    393.0,
    28.5,
    0.867
   ],
   [
    2021,
    2959658.0,
    7687,
    109740.0,
    385.0,
    27.0,
    0.808
   ],
   [
    2022,
    3107271.0,
    7460,
    112052.0,
    417.0,
    27.7,
    0.751
   ],
   [
    2023,
    3540144.0,
    7126,
    106029.0,
    497.0,
    33.4,
    0.869
   ],
   [
    2024,
    3616177.0,
    7228,
    111064.0,
    500.0,
    32.6,
    0.82
   ],
   [
    2025,
    3841144.0,
    7171,
    108640.0,
    536.0,
    35.4,
    0.853
   ]
  ],
  "error": null
 },
 {
  "id": "q169",
  "sql": "WITH t AS (SELECT year(week_of::DATE) yr, sum(regular_hours+overtime_hours) paid_h FROM hr_timecards GROUP BY 1),\nl AS (SELECT year(work_date::DATE) yr, sum(hours) clk, sum(CASE WHEN hours>24 THEN hours ELSE 0 END) big FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, sum(CASE WHEN account='revenue' THEN amount END) gl_rev, -sum(CASE WHEN account='material' THEN amount END) gl_mat FROM erp_general_ledger GROUP BY 1),\ni AS (SELECT year(invoiced_on::DATE) yr, sum(amount) inv, sum(freight) frt FROM erp_invoices GROUP BY 1),\np AS (SELECT year(ordered_on::DATE) yr, sum(CASE WHEN material<>'outside processing' THEN amount END) po_mat FROM erp_purchase_orders JOIN erp_po_lines USING(po_id) GROUP BY 1)\nSELECT yr, round(paid_h) paid_h, round(clk) clocked_h, round(big) big_entry_h, round(clk/paid_h,3) clk_over_paid, round(gl_rev) gl_rev, round(inv) inv, round(frt) inv_freight, round(gl_mat) gl_mat, round(po_mat) po_mat, round(po_mat/gl_mat,3) po_over_gl FROM t JOIN l USING(yr) JOIN g USING(yr) JOIN i USING(yr) JOIN p USING(yr) ORDER BY yr",
  "columns": [
   "yr",
   "paid_h",
   "clocked_h",
   "big_entry_h",
   "clk_over_paid",
   "gl_rev",
   "inv",
   "inv_freight",
   "gl_mat",
   "po_mat",
   "po_over_gl"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    165057.0,
    124657.0,
    41422.0,
    0.755,
    22808424.0,
    22698660.0,
    640410.0,
    6269293.0,
    6269293.0,
    1.0
   ],
   [
    2017,
    163790.0,
    120946.0,
    39193.0,
    0.738,
    24783238.0,
    24918401.0,
    688028.0,
    7178895.0,
    7178895.0,
    1.0
   ],
   [
    2018,
    162928.0,
    118400.0,
    34911.0,
    0.727,
    27532837.0,
    27557959.0,
    768192.0,
    8678090.0,
    8678090.0,
    1.0
   ],
   [
    2019,
    164531.0,
    114170.0,
    36718.0,
    0.694,
    26953546.0,
    27057814.0,
    751776.0,
    7991553.0,
    7991552.0,
    1.0
   ],
   [
    2020,
    156581.0,
    103093.0,
    29483.0,
    0.658,
    23896030.0,
    23856150.0,
    666035.0,
    6604465.0,
    6604465.0,
    1.0
   ],
   [
    2021,
    161920.0,
    109740.0,
    31579.0,
    0.678,
    26112647.0,
    26195950.0,
    743929.0,
    10892365.0,
    10892365.0,
    1.0
   ],
   [
    2022,
    166431.0,
    112052.0,
    33567.0,
    0.673,
    32853151.0,
    32745801.0,
    913067.0,
    12380332.0,
    12380331.0,
    1.0
   ],
   [
    2023,
    158352.0,
    106029.0,
    30981.0,
    0.67,
    31707321.0,
    31830812.0,
    894573.0,
    10665874.0,
    10665874.0,
    1.0
   ],
   [
    2024,
    170623.0,
    111064.0,
    34743.0,
    0.651,
    32721028.0,
    32832716.0,
    921047.0,
    10318165.0,
    10318165.0,
    1.0
   ],
   [
    2025,
    165568.0,
    108640.0,
    36007.0,
    0.656,
    31414512.0,
    31470356.0,
    876709.0,
    10061251.0,
    10061251.0,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q201",
  "sql": "WITH t AS (SELECT year(week_of::DATE) yr, sum(regular_hours+overtime_hours) paid_h FROM hr_timecards GROUP BY 1),\nl AS (SELECT year(work_date::DATE) yr, sum(hours) clk FROM shop_labour_entries GROUP BY 1),\ng AS (SELECT substr(period,1,4)::INT yr, -sum(CASE WHEN account IN ('direct labour','indirect labour','benefits and payroll taxes','shop overhead') THEN amount END) conv FROM erp_general_ledger GROUP BY 1)\nSELECT yr, round(conv/clk,1) rate_per_clocked_h, round(conv/paid_h,1) rate_per_paid_h, round(clk/paid_h,3) capture, round(128.1-126.2,1) f6s_2020_gap FROM g JOIN t USING(yr) JOIN l USING(yr) ORDER BY yr",
  "columns": [
   "yr",
   "rate_per_clocked_h",
   "rate_per_paid_h",
   "capture",
   "f6s_2020_gap"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    102.8,
    77.6,
    0.755,
    1.9
   ],
   [
    2017,
    107.1,
    79.1,
    0.738,
    1.9
   ],
   [
    2018,
    111.6,
    81.1,
    0.727,
    1.9
   ],
   [
    2019,
    116.8,
    81.0,
    0.694,
    1.9
   ],
   [
    2020,
    126.2,
    83.1,
    0.658,
    1.9
   ],
   [
    2021,
    124.0,
    84.0,
    0.678,
    1.9
   ],
   [
    2022,
    130.7,
    88.0,
    0.673,
    1.9
   ],
   [
    2023,
    143.2,
    95.9,
    0.67,
    1.9
   ],
   [
    2024,
    142.9,
    93.0,
    0.651,
    1.9
   ],
   [
    2025,
    150.9,
    99.0,
    0.656,
    1.9
   ]
  ],
  "error": null
 },
 {
  "id": "q203",
  "sql": "WITH r AS (SELECT DISTINCT po_id FROM erp_receipts), inv AS (SELECT DISTINCT job_id FROM erp_shipment_lines)\nSELECT cp.family, count(*) po_lines, round(avg((r.po_id IS NULL)::INT),4) share_no_receipt, round(sum(CASE WHEN r.po_id IS NULL THEN pl.amount END)) amt_no_receipt, round(sum(pl.amount)) amt, round(avg(CASE WHEN inv.job_id IS NULL THEN 1 ELSE 0 END),4) share_on_uninvoiced_jobs\nFROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) LEFT JOIN r USING(po_id) JOIN erp_jobs j USING(job_id) JOIN erp_customer_parts cp USING(part_id) LEFT JOIN inv ON inv.job_id=po.job_id\nGROUP BY ROLLUP(cp.family) ORDER BY cp.family NULLS LAST",
  "columns": [
   "family",
   "po_lines",
   "share_no_receipt",
   "amt_no_receipt",
   "amt",
   "share_on_uninvoiced_jobs"
  ],
  "row_count": 7,
  "rows": [
   [
    1,
    57239,
    0.3051,
    325301.0,
    15196085.0,
    0.0055
   ],
   [
    2,
    17406,
    0.43,
    846222.0,
    23187423.0,
    0.0096
   ],
   [
    3,
    17258,
    0.1506,
    1898170.0,
    29505004.0,
    0.0112
   ],
   [
    4,
    3317,
    0.4082,
    770508.0,
    10339061.0,
    0.0133
   ],
   [
    5,
    6617,
    0.3446,
    116484.0,
    8144840.0,
    0.0053
   ],
   [
    6,
    6334,
    0.1486,
    250721.0,
    6385875.0,
    0.0145
   ],
   [
    null,
    108171,
    0.297,
    4207405.0,
    92758289.0,
    0.0078
   ]
  ],
  "error": null
 },
 {
  "id": "q230",
  "sql": "WITH r AS (SELECT DISTINCT po_id FROM erp_receipts) SELECT count(*) pos, round(avg((r.po_id IS NULL)::INT),4) share_pos_no_receipt FROM erp_purchase_orders po LEFT JOIN r USING(po_id)",
  "columns": [
   "pos",
   "share_pos_no_receipt"
  ],
  "row_count": 1,
  "rows": [
   [
    108171,
    0.297
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

Save `grade.json`: {"finding": "F4", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
