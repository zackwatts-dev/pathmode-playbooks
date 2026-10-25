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
 "id": "F1",
 "hypothesis": "H1",
 "title": "Narrowed: Wendlow absorbed the 2021 carbon-steel jump on repeat parts, about $1.09M a year over 2021-2022; prices have more than covered material since 2023, so no material gap remains to requote",
 "conclusion": "Observed: on the same carbon parts at their 2020 shipped quantities, the price index in 2021 was 1.0007 while material per unit was 1.5475 times 2020, so margin over material fell $2,077,947 across 1,686 parts (q176). The rise in material per unit on those parts came from $/lb, not weight: the pounds index stayed between 0.997 and 1.0087 (q176), and carbon cost $0.3123/lb in 2020, $0.4857 in 2021 and $0.5959 in 2022 (q173). Prices reset in 2022 (index 1.2271), and margin over material on the matched parts was about even that year (+$166,479). It was above 2020 from 2023 on: +$1,526,003 in 2023, +$1,312,006 in 2024 and +$949,945 in 2025 (q176). The result holds when 2019 is the base year instead: -$1,358,121 in 2021, then +$958,869 to +$1,364,746 a year in 2023-2025 (q215). Across all carbon order jobs, steel cost added versus 2020 $/lb exceeded the estimated price gain by $2,913,379 in 2021. Prices gained $733,298 more than steel cost in 2022, which leaves a net shortfall of $1,090,041 a year over 2021-2022 (q188, q213). Interpretation: repeat-part prices lagged steel by about a year. Material's share of price (about 0.29-0.31 in 2024-2025 against about 0.25 in 2020; q173, q176) stays higher because prices passed steel through dollar for dollar, not because cost is going unrecovered. My earlier $972,905-a-year ongoing gap was produced by measuring material against a fixed share, and I retract it. Action: a steel-indexed price clause, or a surcharge line recorded on repeat POs, so that the next steel spike reaches prices within a quarter rather than a year.",
 "dollars_a_year": 1090041.0,
 "size_query": "q213",
 "claims": [
  {
   "text": "Matched carbon parts at 2020 quantities: in 2021, price index 1.0007 and material index 1.5475, margin over material -$2,077,947 (1,686 parts). In 2022, price 1.2271, material 1.9243, +$166,479 (1,305 parts). In 2023-2025, +$1,526,003, +$1,312,006 and +$949,945 (1,012, 804 and 643 parts).",
   "queries": [
    "q176"
   ]
  },
  {
   "text": "With 2019 as the base instead of 2020, the pattern is the same: -$1,358,121 in 2021 (1,322 parts, price index 0.9986, material 1.3929), +$439,532 in 2022, and +$958,869 to +$1,364,746 a year in 2023-2025. The 2020 baseline is not driving the sign.",
   "queries": [
    "q215"
   ]
  },
  {
   "text": "On matched parts, material per unit rose because of $/lb, not pounds: pounds index 0.997-1.0087 over 2020-2025. Carbon $/lb was 0.3123 (2020), 0.4857 (2021), 0.5959 (2022), 0.5158 (2023), 0.4793 (2024) and 0.4706 (2025). Shipped quantity equalled job quantity in every year (ratio 1.0).",
   "queries": [
    "q173",
    "q176"
   ]
  },
  {
   "text": "Repeat-part prices against each part's last 2020 price: median 1.0 in 2021 (59.7% of 6,210 lines unchanged), 1.3588 in 2022 (12.4% of 4,746 unchanged).",
   "queries": [
    "q128"
   ]
  },
  {
   "text": "All carbon order jobs (estimate that applies the matched-part price index to all jobs): steel cost added versus 2020 was $3,132,703 in 2021 and $5,135,591 in 2022. Against estimated price gains of $219,324 and $5,868,889, the net shortfall was $2,913,379 in 2021 and the net gain $733,298 in 2022, for $1,090,041 a year over 2021-2022. In 2024-2025 prices exceed steel cost added by $3,814,537 a year.",
   "queries": [
    "q188",
    "q213"
   ]
  },
  {
   "text": "Invoices priced above the PO price appear in high-steel years: 790 in 2021 and 1,793 in 2022, against 28 in 2024 and 2 in 2025. Some of them trace to quote lines with the surcharge flag set (91 in 2021, 212 in 2022). Freight is recorded separately and is not the uplift.",
   "queries": [
    "q183",
    "q184"
   ]
  },
  {
   "text": "Carbon material share by first-ship year was 0.2373-0.2788 in 2016-2020, 0.3792 in 2021, 0.3714 in 2022 and 0.2898-0.2927 in 2024-2025. Because a dollar-for-dollar pass-through raises the share, the share is not a measure of unrecovered cost.",
   "queries": [
    "q173"
   ]
  },
  {
   "text": "The 2021-2022 squeeze was not concentrated in one segment or customer: carbon share rose in all five segments, and the top 10 customers held 0.6356 of the excess against 0.6523 of revenue.",
   "queries": [
    "q140",
    "q149"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "This measures margin over material only. Labour, outside processing and overhead are not in it. The hours-weighted pay rate rose by a factor of 1.2328 from 2020 to 2025 (q193, q195), so the over-recovery on material since 2023 does not show that total margin is back to 2020 levels. The all-jobs figure (q188, q213) applies the price index of the surviving matched parts to all carbon work, which is an assumption. The matched set shrinks from 2,395 parts to 643 (q176). It does not show that steel caused the price changes (they coincide in time only), or that the invoice uplift is a steel surcharge, although the surcharge flag matches some of it (q184).",
 "could_not_tell": "Why prices were held through 2021 (contract, blanket PO, or a choice to keep volume). Whether parts that dropped out after the 2022 reset were lost because of the reset. Labour hours and overhead per job, which would show whether total contribution has recovered. What the invoice uplift on untraced repeat orders is.",
 "next_step": "Do not run a requote campaign on carbon repeat parts on material grounds; the records show no current material gap. Put a steel index clause or a recorded surcharge line on repeat POs so that recovery lag can be measured next time. Test whether the post-2022 price level covers labour as well, using shop labour hours per unit on matched parts. Correct the map: outside-processing PO lines carry $1,718,008 of amount (q101), not $0.",
 "incomplete": false
}

[
 {
  "id": "q176",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat, sum(pl.pounds) lbs FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity) q, sum(sl.quantity*l.unit_price) po_val, sum(i.amount) inv FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_invoices i USING(shipment_id) GROUP BY sl.job_id),\nb AS (SELECT j.part_id, substr(fs,1,4)::int yr, q, mat, lbs, po_val, inv FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) WHERE j.kind='order'),\npp AS (SELECT part_id, yr, sum(q) q, sum(mat)/sum(q) mpu, sum(lbs)/sum(q) lpu, sum(po_val)/sum(q) ppu, sum(inv)/sum(q) ipu FROM b GROUP BY 1,2),\nbase AS (SELECT * FROM pp WHERE yr=2020)\nSELECT p.yr, count(*) parts, round(sum(base.q*base.ppu)) rev2020_basis,\n round(sum(base.q*p.ppu)/sum(base.q*base.ppu),4) price_idx,\n round(sum(base.q*p.mpu)/sum(base.q*base.mpu),4) mat_idx,\n round(sum(base.q*p.lpu)/sum(base.q*base.lpu),4) lbs_idx,\n round(sum(base.q*(p.mpu-base.mpu))) d_mat_at2020qty,\n round(sum(base.q*(p.ipu-base.ppu))) d_inv_at2020qty,\n round(sum(base.q*(p.ipu-base.ppu)) - sum(base.q*(p.mpu-base.mpu))) d_margin_over_mat,\n round(sum(base.q*p.mpu)/sum(base.q*p.ppu),4) share_now, round(sum(base.q*base.mpu)/sum(base.q*base.ppu),4) share_2020\nFROM pp p JOIN base USING(part_id) WHERE p.yr>=2020 GROUP BY p.yr ORDER BY p.yr",
  "columns": [
   "yr",
   "parts",
   "rev2020_basis",
   "price_idx",
   "mat_idx",
   "lbs_idx",
   "d_mat_at2020qty",
   "d_inv_at2020qty",
   "d_margin_over_mat",
   "share_now",
   "share_2020"
  ],
  "row_count": 6,
  "rows": [
   [
    2020,
    2395,
    21167262.0,
    1.0,
    1.0,
    1.0,
    0.0,
    16651.0,
    16651.0,
    0.2458,
    0.2458
   ],
   [
    2021,
    1686,
    16164397.0,
    1.0007,
    1.5475,
    1.0028,
    2176113.0,
    98165.0,
    -2077947.0,
    0.3802,
    0.2459
   ],
   [
    2022,
    1305,
    12506898.0,
    1.2271,
    1.9243,
    0.997,
    2871195.0,
    3037675.0,
    166479.0,
    0.3895,
    0.2484
   ],
   [
    2023,
    1012,
    9305698.0,
    1.3285,
    1.6633,
    1.0026,
    1551666.0,
    3077669.0,
    1526003.0,
    0.3147,
    0.2514
   ],
   [
    2024,
    804,
    7597404.0,
    1.3094,
    1.5348,
    0.9954,
    1041685.0,
    2353691.0,
    1312006.0,
    0.3005,
    0.2564
   ],
   [
    2025,
    643,
    5917223.0,
    1.2969,
    1.5206,
    1.0087,
    807077.0,
    1757022.0,
    949945.0,
    0.3072,
    0.262
   ]
  ],
  "error": null
 },
 {
  "id": "q215",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity) q, sum(sl.quantity*l.unit_price) po_val, sum(i.amount) inv FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_invoices i USING(shipment_id) GROUP BY sl.job_id),\nb AS (SELECT j.part_id, substr(fs,1,4)::int yr, q, mat, po_val, inv FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) WHERE j.kind='order'),\npp AS (SELECT part_id, yr, sum(q) q, sum(mat)/sum(q) mpu, sum(po_val)/sum(q) ppu, sum(inv)/sum(q) ipu FROM b GROUP BY 1,2),\nbase AS (SELECT * FROM pp WHERE yr=2019)\nSELECT p.yr, count(*) parts, round(sum(base.q*p.ppu)/sum(base.q*base.ppu),4) price_idx, round(sum(base.q*p.mpu)/sum(base.q*base.mpu),4) mat_idx,\n round(sum(base.q*(p.ipu-base.ipu)) - sum(base.q*(p.mpu-base.mpu))) d_margin_over_mat_vs2019\nFROM pp p JOIN base USING(part_id) WHERE p.yr>=2019 GROUP BY p.yr ORDER BY p.yr",
  "columns": [
   "yr",
   "parts",
   "price_idx",
   "mat_idx",
   "d_margin_over_mat_vs2019"
  ],
  "row_count": 7,
  "rows": [
   [
    2019,
    2391,
    1.0,
    1.0,
    0.0
   ],
   [
    2020,
    1627,
    1.0014,
    0.8998,
    430372.0
   ],
   [
    2021,
    1322,
    0.9986,
    1.3929,
    -1358121.0
   ],
   [
    2022,
    1033,
    1.2232,
    1.7368,
    439532.0
   ],
   [
    2023,
    769,
    1.3215,
    1.5041,
    1364746.0
   ],
   [
    2024,
    619,
    1.3079,
    1.3664,
    1262803.0
   ],
   [
    2025,
    485,
    1.2922,
    1.348,
    958869.0
   ]
  ],
  "error": null
 },
 {
  "id": "q173",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat, sum(pl.pounds) lbs FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity) q, sum(sl.quantity*l.unit_price) po_val, sum(i.amount) inv FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_invoices i USING(shipment_id) GROUP BY sl.job_id),\nb AS (SELECT j.part_id, substr(fs,1,4)::int yr, j.quantity jq, q, mat, lbs, po_val, inv FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) WHERE j.kind='order')\nSELECT yr, count(*) jobs, round(sum(po_val)/sum(q),2) price_per_unit_shipped, round(sum(mat)/sum(q),2) mat_per_unit, round(sum(lbs)/sum(jq),3) lbs_per_job_unit, round(sum(lbs)/sum(q),3) lbs_per_shipped_unit, round(sum(mat)/sum(lbs),4) usd_lb, round(sum(q)::double/sum(jq),4) shipped_over_jobqty, round(sum(mat)/sum(po_val),4) share\nFROM b GROUP BY yr ORDER BY yr",
  "columns": [
   "yr",
   "jobs",
   "price_per_unit_shipped",
   "mat_per_unit",
   "lbs_per_job_unit",
   "lbs_per_shipped_unit",
   "usd_lb",
   "shipped_over_jobqty",
   "share"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    6967,
    92.76,
    22.01,
    78.666,
    78.666,
    0.2798,
    1.0,
    0.2373
   ],
   [
    2017,
    7581,
    97.91,
    24.93,
    81.25,
    81.25,
    0.3068,
    1.0,
    0.2546
   ],
   [
    2018,
    8105,
    104.32,
    29.08,
    83.764,
    83.764,
    0.3472,
    1.0,
    0.2788
   ],
   [
    2019,
    7515,
    110.35,
    29.1,
    83.31,
    83.31,
    0.3492,
    1.0,
    0.2637
   ],
   [
    2020,
    7187,
    106.98,
    26.3,
    84.218,
    84.218,
    0.3123,
    1.0,
    0.2458
   ],
   [
    2021,
    7404,
    112.22,
    42.56,
    87.629,
    87.629,
    0.4857,
    1.0,
    0.3792
   ],
   [
    2022,
    7141,
    140.81,
    52.3,
    87.76,
    87.76,
    0.5959,
    1.0,
    0.3714
   ],
   [
    2023,
    6820,
    150.79,
    46.41,
    89.974,
    89.974,
    0.5158,
    1.0,
    0.3078
   ],
   [
    2024,
    6884,
    154.69,
    44.82,
    93.522,
    93.522,
    0.4793,
    1.0,
    0.2898
   ],
   [
    2025,
    6872,
    152.45,
    44.63,
    94.82,
    94.82,
    0.4706,
    1.0,
    0.2927
   ]
  ],
  "error": null
 },
 {
  "id": "q128",
  "sql": "WITH p AS (SELECT substr(po.ordered_on,1,4) yr, sum(pl.amount)/sum(pl.pounds) ppl, count(*) n FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY 1),\nl AS (SELECT l.part_id, substr(o.order_date,1,4) yr, o.order_date, l.line_id, l.unit_price FROM erp_so_lines l JOIN erp_sales_orders o USING(order_id)),\nref AS (SELECT part_id, arg_max(unit_price, order_date || lpad(line_id::varchar,8,'0')) p2020 FROM l WHERE yr='2020' GROUP BY part_id),\nidx AS (SELECT yr, median(unit_price/p2020) med_ratio, avg(unit_price/p2020) avg_ratio, count(*) n_lines, avg(CASE WHEN abs(unit_price-p2020)<0.005 THEN 1.0 ELSE 0 END) share_unchanged FROM l JOIN ref USING(part_id) WHERE yr>='2020' GROUP BY yr),\nf AS (SELECT substr(month,1,4) yr, avg(value) v FROM external_fred_monthly WHERE series=(SELECT min(series) FROM external_fred_monthly WHERE lower(label) LIKE '%steel%') GROUP BY 1)\nSELECT p.yr, round(p.ppl,4) carbon_ppl, p.n, round(f.v,1) fred_steel, round(idx.med_ratio,4) med_price_vs2020, round(idx.avg_ratio,4) avg_price_vs2020, round(idx.share_unchanged,4) share_unchanged, idx.n_lines\nFROM p LEFT JOIN f USING(yr) LEFT JOIN idx USING(yr) ORDER BY p.yr",
  "columns": [
   "yr",
   "carbon_ppl",
   "n",
   "fred_steel",
   "med_price_vs2020",
   "avg_price_vs2020",
   "share_unchanged",
   "n_lines"
  ],
  "row_count": 10,
  "rows": [
   [
    "2016",
    0.2802,
    10138,
    167.8,
    null,
    null,
    null,
    null
   ],
   [
    "2017",
    0.3087,
    10865,
    187.4,
    null,
    null,
    null,
    null
   ],
   [
    "2018",
    0.3512,
    11098,
    211.1,
    null,
    null,
    null,
    null
   ],
   [
    "2019",
    0.3455,
    10817,
    204.1,
    null,
    null,
    null,
    null
   ],
   [
    "2020",
    0.3131,
    10064,
    184.5,
    1.0,
    1.009,
    0.7502,
    7527
   ],
   [
    "2021",
    0.508,
    10420,
    350.9,
    1.0,
    1.0282,
    0.5971,
    6210
   ],
   [
    "2022",
    0.5907,
    9907,
    381.5,
    1.3588,
    1.3382,
    0.1241,
    4746
   ],
   [
    "2023",
    0.514,
    9623,
    319.6,
    1.3652,
    1.3676,
    0.0264,
    3566
   ],
   [
    "2024",
    0.4765,
    9455,
    291.4,
    1.3303,
    1.3333,
    0.0115,
    2861
   ],
   [
    "2025",
    0.4735,
    9484,
    298.4,
    1.3246,
    1.3326,
    0.0019,
    2099
   ]
  ],
  "error": null
 },
 {
  "id": "q188",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat, sum(pl.pounds) lbs FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity*l.unit_price) po_val, sum(i.amount) inv FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_invoices i USING(shipment_id) GROUP BY sl.job_id),\ny AS (SELECT substr(fs,1,4)::int yr, sum(mat) mat, sum(lbs) lbs, sum(po_val) pv, sum(inv) inv FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) WHERE j.kind='order' GROUP BY 1),\nidx(yr, pidx) AS (VALUES (2021,1.0007),(2022,1.2271),(2023,1.3285),(2024,1.3094),(2025,1.2969)),\nc AS (SELECT yr, lbs*(mat/lbs - 0.3123) steel_cost, pv*(1-1/pidx) + (inv-pv) price_gain FROM y JOIN idx USING(yr))\nSELECT yr, round(steel_cost) steel_cost_vs2020, round(price_gain) price_gain_est, round(price_gain-steel_cost) net\nFROM c UNION ALL\nSELECT 9999, round(sum(steel_cost) FILTER (WHERE yr IN (2024,2025))/2), round(sum(price_gain) FILTER (WHERE yr IN (2024,2025))/2), round(sum(price_gain-steel_cost) FILTER (WHERE yr IN (2024,2025))/2) FROM c\nUNION ALL SELECT 2122, round(sum(steel_cost) FILTER (WHERE yr IN (2021,2022))), round(sum(price_gain) FILTER (WHERE yr IN (2021,2022))), round(sum(price_gain-steel_cost) FILTER (WHERE yr IN (2021,2022))) FROM c\nORDER BY 1",
  "columns": [
   "yr",
   "steel_cost_vs2020",
   "price_gain_est",
   "net"
  ],
  "row_count": 7,
  "rows": [
   [
    2021,
    3132703.0,
    219324.0,
    -2913379.0
   ],
   [
    2022,
    5135591.0,
    5868889.0,
    733298.0
   ],
   [
    2023,
    3422761.0,
    7004960.0,
    3582199.0
   ],
   [
    2024,
    2936801.0,
    6880023.0,
    3943222.0
   ],
   [
    2025,
    2782326.0,
    6468179.0,
    3685853.0
   ],
   [
    2122,
    8268294.0,
    6088213.0,
    -2180081.0
   ],
   [
    9999,
    2859564.0,
    6674101.0,
    3814537.0
   ]
  ],
  "error": null
 },
 {
  "id": "q213",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat, sum(pl.pounds) lbs FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity*l.unit_price) po_val, sum(i.amount) inv FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_invoices i USING(shipment_id) GROUP BY sl.job_id),\ny AS (SELECT substr(fs,1,4)::int yr, sum(mat) mat, sum(lbs) lbs, sum(po_val) pv, sum(inv) inv FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) WHERE j.kind='order' GROUP BY 1),\nidx(yr, pidx) AS (VALUES (2021,1.0007),(2022,1.2271),(2023,1.3285),(2024,1.3094),(2025,1.2969)),\nc AS (SELECT yr, lbs*(mat/lbs - 0.3123) steel_cost, pv*(1-1/pidx) + (inv-pv) price_gain FROM y JOIN idx USING(yr))\nSELECT 'all_jobs_2021_2022_shortfall_per_yr' metric, round(sum(steel_cost-price_gain)/2) val FROM c WHERE yr IN (2021,2022)\nUNION ALL SELECT 'all_jobs_2021_shortfall', round(sum(steel_cost-price_gain)) FROM c WHERE yr=2021\nUNION ALL SELECT 'all_jobs_2022_net_gain', round(sum(price_gain-steel_cost)) FROM c WHERE yr=2022\nUNION ALL SELECT 'all_jobs_2024_2025_net_gain_per_yr', round(sum(price_gain-steel_cost)/2) FROM c WHERE yr IN (2024,2025)\nORDER BY 1",
  "columns": [
   "metric",
   "val"
  ],
  "row_count": 4,
  "rows": [
   [
    "all_jobs_2021_2022_shortfall_per_yr",
    1090041.0
   ],
   [
    "all_jobs_2021_shortfall",
    2913379.0
   ],
   [
    "all_jobs_2022_net_gain",
    733298.0
   ],
   [
    "all_jobs_2024_2025_net_gain_per_yr",
    3814537.0
   ]
  ],
  "error": null
 },
 {
  "id": "q183",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat, sum(pl.pounds) lbs FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity*l.unit_price) po_val, sum(i.amount) inv, sum(i.freight) fr, sum(s.freight) sfr FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_invoices i USING(shipment_id) GROUP BY sl.job_id),\nb AS (SELECT substr(fs,1,4)::int yr, mat, lbs, po_val, inv, fr, sfr FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) WHERE j.kind='order'),\ny AS (SELECT yr, sum(mat) mat, sum(lbs) lbs, sum(po_val) pv, sum(inv) inv, sum(fr) fr, sum(sfr) sfr FROM b GROUP BY yr),\nr AS (SELECT mat/lbs p20 FROM y WHERE yr=2020)\nSELECT yr, round(mat/lbs,4) usd_lb, round(lbs*(mat/lbs - p20)) steel_price_cost_vs2020, round(mat - 0.2572*pv) q152_style_excess, round(inv-pv) uplift, round(fr) inv_freight, round(sfr) ship_freight\nFROM y, r ORDER BY yr",
  "columns": [
   "yr",
   "usd_lb",
   "steel_price_cost_vs2020",
   "q152_style_excess",
   "uplift",
   "inv_freight",
   "ship_freight"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    0.2798,
    -511765.0,
    -370212.0,
    -5.0,
    525313.0,
    525313.0
   ],
   [
    2017,
    0.3068,
    -98248.0,
    -56707.0,
    -23.0,
    596017.0,
    596017.0
   ],
   [
    2018,
    0.3472,
    665713.0,
    512352.0,
    39715.0,
    662927.0,
    662927.0
   ],
   [
    2019,
    0.3492,
    660754.0,
    152799.0,
    108952.0,
    661987.0,
    661987.0
   ],
   [
    2020,
    0.3123,
    0.0,
    -240641.0,
    16651.0,
    592233.0,
    592233.0
   ],
   [
    2021,
    0.4857,
    3133394.0,
    2823912.0,
    203137.0,
    657317.0,
    657317.0
   ],
   [
    2022,
    0.5959,
    5136283.0,
    3318186.0,
    492529.0,
    817940.0,
    817940.0
   ],
   [
    2023,
    0.5158,
    3423403.0,
    1425510.0,
    34488.0,
    799704.0,
    799704.0
   ],
   [
    2024,
    0.4793,
    2937473.0,
    947132.0,
    5983.0,
    817644.0,
    817644.0
   ],
   [
    2025,
    0.4706,
    2782998.0,
    1003522.0,
    131.0,
    785322.0,
    785322.0
   ]
  ],
  "error": null
 },
 {
  "id": "q184",
  "sql": "SELECT substr(s.shipped_on,1,4) yr, count(*) n, sum(CASE WHEN i.amount > sl.quantity*l.unit_price*1.005 THEN 1 ELSE 0 END) n_up, sum(CASE WHEN i.amount < sl.quantity*l.unit_price*0.995 THEN 1 ELSE 0 END) n_down,\n round(median(CASE WHEN i.amount > sl.quantity*l.unit_price*1.005 THEN i.amount/(sl.quantity*l.unit_price)-1 END),4) med_up_pct,\n sum(CASE WHEN q.surcharge=1 THEN 1 ELSE 0 END) quoted_surcharge, sum(CASE WHEN q.surcharge=1 AND i.amount > sl.quantity*l.unit_price*1.005 THEN 1 ELSE 0 END) surcharge_and_up\nFROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_sales_orders o USING(order_id) JOIN erp_invoices i USING(shipment_id)\nLEFT JOIN (SELECT ql.quote_id, ql.part_id, max(ql.surcharge) surcharge FROM erp_quote_lines ql GROUP BY 1,2) q ON q.quote_id=o.quote_id AND q.part_id=l.part_id\nGROUP BY 1 ORDER BY 1",
  "columns": [
   "yr",
   "n",
   "n_up",
   "n_down",
   "med_up_pct",
   "quoted_surcharge",
   "surcharge_and_up"
  ],
  "row_count": 10,
  "rows": [
   [
    "2016",
    7947,
    0,
    0,
    null,
    0,
    0
   ],
   [
    "2017",
    8034,
    0,
    0,
    null,
    0,
    0
   ],
   [
    "2018",
    8561,
    536,
    0,
    0.0232,
    237,
    107
   ],
   [
    "2019",
    7916,
    1488,
    0,
    0.0191,
    490,
    203
   ],
   [
    "2020",
    7521,
    287,
    0,
    0.0146,
    0,
    0
   ],
   [
    "2021",
    7953,
    790,
    0,
    0.07,
    176,
    91
   ],
   [
    "2022",
    7502,
    1793,
    0,
    0.0389,
    442,
    212
   ],
   [
    "2023",
    7174,
    191,
    0,
    0.0319,
    0,
    0
   ],
   [
    "2024",
    7254,
    28,
    0,
    0.0368,
    0,
    0
   ],
   [
    "2025",
    7215,
    2,
    0,
    0.1082,
    0,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q140",
  "sql": "WITH mat AS (SELECT po.job_id, sum(pl.amount) mat FROM erp_purchase_orders po JOIN erp_po_lines pl USING(po_id) WHERE pl.material='carbon' GROUP BY po.job_id),\nshp AS (SELECT sl.job_id, min(s.shipped_on) fs, sum(sl.quantity*l.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) GROUP BY sl.job_id),\nb AS (SELECT o.customer_id, c.segment, substr(fs,1,4) yr, mat, po_val FROM mat JOIN erp_jobs j USING(job_id) JOIN shp USING(job_id) JOIN erp_so_lines l USING(line_id) JOIN erp_sales_orders o USING(order_id) JOIN erp_customers c ON c.customer_id=o.customer_id WHERE j.kind='order'),\nseg AS (SELECT segment, round(sum(CASE WHEN yr BETWEEN '2016' AND '2020' THEN mat END)/sum(CASE WHEN yr BETWEEN '2016' AND '2020' THEN po_val END),4) s1620,\n  round(sum(CASE WHEN yr IN ('2021','2022') THEN mat END)/sum(CASE WHEN yr IN ('2021','2022') THEN po_val END),4) s2122,\n  round(sum(CASE WHEN yr IN ('2024','2025') THEN mat END)/sum(CASE WHEN yr IN ('2024','2025') THEN po_val END),4) s2425,\n  round(sum(CASE WHEN yr IN ('2021','2022') THEN mat-0.2572*po_val END)) ex2122 FROM b GROUP BY 1),\ncust AS (SELECT customer_id, sum(mat-0.2572*po_val) ex FROM b WHERE yr IN ('2021','2022') GROUP BY 1),\ntop AS (SELECT round(sum(ex) FILTER (WHERE rk<=10)/sum(ex),4) top10_share, count(*) n_cust, sum(CASE WHEN ex>0 THEN 1 ELSE 0 END) n_pos FROM (SELECT ex, row_number() OVER (ORDER BY ex DESC, customer_id) rk FROM cust))\nSELECT s.*, t.* FROM seg s, top t ORDER BY segment",
  "columns": [
   "segment",
   "s1620",
   "s2122",
   "s2425",
   "ex2122",
   "top10_share",
   "n_cust",
   "n_pos"
  ],
  "row_count": 5,
  "rows": [
   [
    "ag",
    0.2631,
    0.3793,
    0.2885,
    1312038.0,
    0.6356,
    205,
    181
   ],
   [
    "contractor",
    0.2501,
    0.3878,
    0.2924,
    557335.0,
    0.6356,
    205,
    181
   ],
   [
    "food",
    0.2604,
    0.3653,
    0.2985,
    1331592.0,
    0.6356,
    205,
    181
   ],
   [
    "hvac",
    0.2569,
    0.3908,
    0.3028,
    874361.0,
    0.6356,
    205,
    181
   ],
   [
    "machinery",
    0.254,
    0.37,
    0.2838,
    2066772.0,
    0.6356,
    205,
    181
   ]
  ],
  "error": null
 },
 {
  "id": "q149",
  "sql": "WITH r AS (SELECT o.customer_id, sum(sl.quantity*l.unit_price) v FROM erp_shipment_lines sl JOIN erp_shipments s USING(shipment_id) JOIN erp_so_lines l USING(line_id) JOIN erp_sales_orders o USING(order_id) WHERE substr(s.shipped_on,1,4) IN ('2021','2022') GROUP BY 1)\nSELECT round(sum(v) FILTER (WHERE rk<=10)/sum(v),4) top10_rev_share, count(*) n FROM (SELECT v, row_number() OVER (ORDER BY v DESC, customer_id) rk FROM r)",
  "columns": [
   "top10_rev_share",
   "n"
  ],
  "row_count": 1,
  "rows": [
   [
    0.6523,
    207
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

Save `grade.json`: {"finding": "F1", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
