You grade one finding from an AI analyst against the answer key of a simulated business. The analyst never saw the key. You have the `query` tool on a read-only database holding the simulation's truth tables (schema `truth`) and the same warehouse the analyst queried.

The answer key:

{
 "business": "Hartwell Supply Co. (simulated HVAC/R distributor), 2016-2025",
 "source": "pathmode-corpus simulations/hartwell/grading/truth-summary.md and the truth database (schema truth in the grader's database)",
 "problems": [
  {
   "id": "P1",
   "name": "Order-entry errors that reach the customer",
   "mechanism": "Hand-keyed order lines (email, phone, counter) carry keying errors (wrong item, quantity or ship-to); about 80% are caught before shipping, the rest cause returns. EDI and web orders have none. The counter's return reason codes are random with respect to the cause.",
   "shows_in": "erp returns and credit memos against hand-keyed orders by channel",
   "truth": "6,447 errors reached the customer over ten years; 6,437 returns credited $3,281,327",
   "dollars_a_year": 328133
  },
  {
   "id": "P2",
   "name": "Pricing drift by rep",
   "mechanism": "Account managers give discounts beyond each customer's agreed discount; nine 'loose' reps give 2.5-5.3% extra on average.",
   "shows_in": "invoice or order line prices against list price and the customer's agreed discount, by rep",
   "truth": "$24.7M given beyond agreed discounts over the decade (1.69% of revenue), most of it by the nine loose reps",
   "dollars_a_year": 2470000
  },
  {
   "id": "P3",
   "name": "Shipments never billed",
   "mechanism": "A line dropped when the invoice was keyed, or a counter pickup never rung up.",
   "shows_in": "shipped lines (warehouse movements or order lines) with no invoice line",
   "truth": "4,989 lines, $2,845,459 over ten years",
   "dollars_a_year": 284546
  },
  {
   "id": "P4",
   "name": "Supplier bills that don't match the PO and the receipt",
   "mechanism": "Duplicate bills (vendor invoice number with an '-R' suffix, later date), quantities above received, prices above the PO, freight not on the PO; accounts payable catches about a third.",
   "shows_in": "vendor bills and lines against purchase orders and goods receipts",
   "truth": "$8,765,749 overpaid over ten years: duplicates $2.75M, freight $2.45M, quantity $2.44M, price $1.13M",
   "dollars_a_year": 876575
  },
  {
   "id": "P5",
   "name": "Repeat where's-my-order contacts",
   "mechanism": "Customers call or email about backorders (short lines), special-order waits and invoice questions; none is linked to its order in the CRM.",
   "shows_in": "crm service contacts, their notes and minutes, against orders with short lines or special orders",
   "truth": "212,047 contacts, 19,085 staff hours over ten years (backorder 102,707, invoice question 55,273, special order 54,067)",
   "dollars_a_year": null
  },
  {
   "id": "P6",
   "name": "Stock-outs alongside excess stock",
   "mechanism": "The buyer forecasts without a seasonal index (spring stock-outs recur) and ignores discontinued dates, so equipment retired by efficiency standards and the 2025 refrigerant change keeps being bought, then marked down; short lines go unfilled while other branches have stock.",
   "shows_in": "short order lines, transfers, stock movements, purchase orders and markdowns by product and branch",
   "truth": "186,712 lines short at the branch, 122,649 filled by transfer",
   "dollars_a_year": null
  },
  {
   "id": "P7",
   "name": "Customers who pay late, by habit",
   "mechanism": "Each customer has a payment habit: prompt, late (about 11 days past due) or slow (about 40 days).",
   "shows_in": "payments against invoice due dates, by customer",
   "truth": "4,168 prompt, 1,493 late, 364 slow customers",
   "dollars_a_year": null
  }
 ]
}

The finding (its cited queries' SQL and results follow it):

{
 "id": "F9",
 "hypothesis": "H2",
 "title": "H2 only partly holds: outside markdowns, price-to-list fell about 1 point because low-discount accounts in every cohort stop buying faster, not because accounts were repriced or new accounts signed at bigger discounts. That is $1.43M a year of price erosion on 2025 volume, not a sum retention would recover.",
 "conclusion": "Observed: non-markdown price-to-list fell from 0.8442 (2016) to 0.8343 (2025). It declined steadily every year, while the list-weighted price residual stayed flat at 0.98342-0.98387 (q456). Parts, refrigeration and supplies each fell by about 0.9 points (q398). Most of the equipment decline, 0.839 to 0.764, is H1 markdowns (q398). Continuing customers' list-weighted keep (1 - discount) barely moved, 0.8448 to 0.8433 across 1,346 customers (q436), and invoice prices match ERP prices exactly in both years (q446). The decline is a shift in the active customer mix toward higher-discount accounts. Accounts under 10% discount stop ordering faster than others. Of 2016-active accounts, 0.292 of the under-10% tier were still active in 2025, against 0.4802 of the 20%+ tier (q415). The gap holds within every size quartile (q440), every trade (q441) and every branch (q443), and among customers onboarded 2016-2020 (0.5022 vs 0.6483, q451). Lapses are spread evenly across the years (q445). On 2025 non-markdown list value of $140,533,485.01, the mix shift equals $1,428,556.44 of price erosion against the 2016 mix (q449, q462). Of that, $1,080,280.56 (0.7562) comes from 2025 entrants being more discounted per dollar than the 2016 accounts that exited. Interpretation: this happens because low-discount entrants also lapse faster, not because new accounts are signed at higher discounts (cohort averages q404; q451). The $1.43M is a counterfactual on fixed 2025 volume, not money that retention would recover. The larger cost of the churn is probably volume: non-markdown list value fell by $9,502,085.00 from 2016 to 2025 (q456, q462). Its value depends on margin, which the records cannot give. Interpretation: the lever is retention of standard-price accounts. A review of discount grants is not indicated.",
 "dollars_a_year": 1428556.44,
 "size_query": "q462",
 "claims": [
  {
   "text": "Price-to-list (shipped qty, list-weighted) falls 2016 to 2025 in categories with no markdown lines: parts 0.8467 to 0.8379, refrigeration 0.8464 to 0.8379, supplies 0.8465 to 0.8373. Non-markdown equipment falls 0.8406 to 0.8281, and total equipment falls 0.839 to 0.764 as markdown lines rise from 3,744 to 18,962.",
   "queries": [
    "q398"
   ]
  },
  {
   "text": "All non-markdown lines together: price-to-list 0.8442 (2016, 242,753 lines, $150,035,570.01 list) to 0.8343 (2025, 234,834 lines, $140,533,485.01 list). List-weighted keep falls every year, 0.8583 to 0.8479, with no step. The residual price/(list x keep) stays between 0.98342 and 0.98387 in every year.",
   "queries": [
    "q456"
   ]
  },
  {
   "text": "No repricing is visible in the records. Continuing customers (1,346, active in both 2016 and 2025) have keep 0.8448 vs 0.8433 and price-to-list 0.8308 vs 0.8287. Per customer, the median change is +0.0005. Finance invoice lines match ERP prices on all 246,052 matched 2016 lines and 252,359 matched 2025 lines, with 0 differences. In 2016, customers who later lapsed had the same residual as continuers (ptl/keep 0.8543/0.8683 vs 0.8308/0.8448).",
   "queries": [
    "q436",
    "q413",
    "q446"
   ]
  },
  {
   "text": "New accounts are not signed at higher discounts. Average discount_pct by onboarding cohort is 0.1355-0.1458 (271-320 customers per cohort), against 0.1412 for 3,154 pre-2016 customers. Discount is essentially unrelated to 2025 volume: correlation 0.0158 for post-2016 customers and 0.0133 for pre-2016 customers.",
   "queries": [
    "q404",
    "q450"
   ]
  },
  {
   "text": "Low-discount accounts lapse faster. Of the customers active in 2016, the share still ordering in 2025 is 292/1,000 (0.292) for discount under 10%, 337/849 (0.3969) for 10-15%, 368/782 (0.4706) for 15-20% and 352/733 (0.4802) for 20% or more. Lapses are spread across years. For the under-10% tier, last orders fall in 2016: 147, 2017: 123, 2018: 101, down to 2024: 43.",
   "queries": [
    "q415",
    "q445"
   ]
  },
  {
   "text": "The lapse gradient is not explained by size, trade or branch. Under-10% retention is 0.2763 / 0.291 / 0.3038 / 0.2983 across 2016 size quartiles, vs 0.4916 / 0.4056 / 0.5109 / 0.5132 for 20%+ (173-260 customers per cell). Within trades, under-10% vs 10%+ retention is commercial 0.2609 vs 0.4473, mixed 0.3296 vs 0.4606 and residential 0.2904 vs 0.4431. Under-10% retention is lower in all 12 branches.",
   "queries": [
    "q440",
    "q441",
    "q443"
   ]
  },
  {
   "text": "The same gradient appears among customers onboarded 2016-2020 who ever ordered. The share active in 2025 is 230/458 (0.5022) for under 10%, 0.5791 for 10-15%, 0.6762 for 15-20% and 212/327 (0.6483) for 20%+.",
   "queries": [
    "q451"
   ]
  },
  {
   "text": "Decomposition of the keep change 0.8583 to 0.8479 on 2025 non-markdown volume gives $1,428,556.44 in total. Of this, $1,080,280.56 (0.7562) is entrants (2,049 customers, keep 0.8526) replacing exiters (2,016 customers, keep 0.8683). $245,867.49 is the continuers' rising weight (0.4269 to 0.5025 of list), and $102,408.39 is continuers' own change. My original sizing (q418: $1,428,556.45 mix, -$29,882.82 residual rate) agrees to the cent.",
   "queries": [
    "q449",
    "q436",
    "q462",
    "q418"
   ]
  },
  {
   "text": "Volume context: non-markdown list value fell by $9,502,085.00 between 2016 and 2025. The 2016 exiters' list value exceeded the 2025 entrants' by $16,068,837.46. Continuers grew by $6,566,752.46.",
   "queries": [
    "q456",
    "q436",
    "q462"
   ]
  },
  {
   "text": "Quote data shows a modest pattern consistent with price sensitivity (2016-01-01 to 2025-12-29). The under-10% tier's quote loss rate is 0.2869, vs 0.275-0.2777 for other tiers. Price is the entered loss reason on 0.5488 of 32,443 lost quotes with a reason, vs 0.5076-0.5191 for other tiers. The only reasons recorded are price and job cancelled.",
   "queries": [
    "q452",
    "q453",
    "q454"
   ]
  },
  {
   "text": "The mix shift is broad. Line-weighted discount rose 2016 to 2025 in 11 of 12 branches. Toledo was flat (0.142 to 0.1402).",
   "queries": [
    "q420"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that reps or managers granted larger discounts, or that new accounts were signed at worse terms: continuers' rates are flat and onboarding discounts are flat. Not evidence that price caused low-discount accounts to leave: the quote loss-reason gap is small, reasons are rep-entered and quote-level, and there are no churn dates or reasons. Not evidence that $1.43M can be won back. It is erosion on fixed 2025 volume, and retention would add volume, not raise price on that volume. Not a margin measure, since cost is a static snapshot. Nothing here points at any individual.",
 "could_not_tell": "Whether discount_pct ever changed. Matching ERP and finance prices and a flat residual fit an unchanged discount, but only a discount change log could rule out history being restated in both systems. Why low-discount accounts stop ordering (competitor, closure, consolidation, price) is not recorded. What retained volume would be worth needs customer- or line-level margin with historical cost, which the records lack.",
 "next_step": "List lapsed under-10% accounts from all cohorts with their last order day, branch and account-manager rep_id, and have account managers ask whether the account closed, consolidated or moved, and whether price was a factor. Ask IT whether discount_pct changes are logged anywhere. Size the lost volume (not rate) once margin by product line can be estimated. Split the remaining equipment price decline under H1.",
 "incomplete": false
}

[
 {
  "id": "q398",
  "sql": "SELECT d.year, p.category,\n count(*) n_lines,\n sum(case when l.markdown_pct>0 then 1 else 0 end) n_md,\n round(sum(l.unit_price*l.qty_shipped)/sum(p.list_price*l.qty_shipped),4) ptl,\n round(sum(case when l.markdown_pct=0 then l.unit_price*l.qty_shipped end)/sum(case when l.markdown_pct=0 then p.list_price*l.qty_shipped end),4) ptl_nomd\nFROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku)\nWHERE l.qty_shipped>0\nGROUP BY 1,2 ORDER BY 2,1",
  "columns": [
   "year",
   "category",
   "n_lines",
   "n_md",
   "ptl",
   "ptl_nomd"
  ],
  "row_count": 40,
  "rows": [
   [
    2016,
    "equipment",
    41020,
    3744,
    0.839,
    0.8406
   ],
   [
    2017,
    "equipment",
    52560,
    4704,
    0.8318,
    0.8403
   ],
   [
    2018,
    "equipment",
    56557,
    5290,
    0.8273,
    0.8397
   ],
   [
    2019,
    "equipment",
    56220,
    5371,
    0.8253,
    0.839
   ],
   [
    2020,
    "equipment",
    56226,
    5281,
    0.8241,
    0.8372
   ],
   [
    2021,
    "equipment",
    58220,
    5489,
    0.8232,
    0.8361
   ],
   [
    2022,
    "equipment",
    56005,
    5473,
    0.8203,
    0.8347
   ],
   [
    2023,
    "equipment",
    45933,
    10836,
    0.8036,
    0.8312
   ],
   [
    2024,
    "equipment",
    49992,
    14007,
    0.7829,
    0.8305
   ],
   [
    2025,
    "equipment",
    49904,
    18962,
    0.764,
    0.8281
   ],
   [
    2016,
    "parts",
    95253,
    0,
    0.8467,
    0.8467
   ],
   [
    2017,
    "parts",
    91509,
    0,
    0.8457,
    0.8457
   ],
   [
    2018,
    "parts",
    107518,
    0,
    0.8444,
    0.8444
   ],
   [
    2019,
    "parts",
    102116,
    0,
    0.8456,
    0.8456
   ],
   [
    2020,
    "parts",
    94833,
    0,
    0.8455,
    0.8455
   ],
   [
    2021,
    "parts",
    93839,
    0,
    0.8436,
    0.8436
   ],
   [
    2022,
    "parts",
    98430,
    0,
    0.8413,
    0.8413
   ],
   [
    2023,
    "parts",
    83149,
    0,
    0.8415,
    0.8415
   ],
   [
    2024,
    "parts",
    83124,
    0,
    0.8381,
    0.8381
   ],
   [
    2025,
    "parts",
    94535,
    0,
    0.8379,
    0.8379
   ],
   [
    2016,
    "refrigeration",
    35042,
    0,
    0.8464,
    0.8464
   ],
   [
    2017,
    "refrigeration",
    33771,
    0,
    0.8461,
    0.8461
   ],
   [
    2018,
    "refrigeration",
    40206,
    0,
    0.8447,
    0.8447
   ],
   [
    2019,
    "refrigeration",
    38038,
    0,
    0.8447,
    0.8447
   ],
   [
    2020,
    "refrigeration",
    35374,
    0,
    0.8455,
    0.8455
   ],
   [
    2021,
    "refrigeration",
    34596,
    0,
    0.8441,
    0.8441
   ],
   [
    2022,
    "refrigeration",
    36263,
    0,
    0.842,
    0.842
   ],
   [
    2023,
    "refrigeration",
    30771,
    0,
    0.8402,
    0.8402
   ],
   [
    2024,
    "refrigeration",
    31200,
    0,
    0.8387,
    0.8387
   ],
   [
    2025,
    "refrigeration",
    35001,
    0,
    0.8379,
    0.8379
   ],
   [
    2016,
    "supplies",
    75182,
    0,
    0.8465,
    0.8465
   ],
   [
    2017,
    "supplies",
    72547,
    0,
    0.8455,
    0.8455
   ],
   [
    2018,
    "supplies",
    85395,
    0,
    0.8439,
    0.8439
   ],
   [
    2019,
    "supplies",
    81363,
    0,
    0.8442,
    0.8442
   ],
   [
    2020,
    "supplies",
    74668,
    0,
    0.845,
    0.845
   ],
   [
    2021,
    "supplies",
    73930,
    0,
    0.8435,
    0.8435
   ],
   [
    2022,
    "supplies",
    76987,
    0,
    0.8418,
    0.8418
   ],
   [
    2023,
    "supplies",
    66407,
    0,
    0.8412,
    0.8412
   ],
   [
    2024,
    "supplies",
    66392,
    0,
    0.839,
    0.839
   ],
   [
    2025,
    "supplies",
    74356,
    0,
    0.8373,
    0.8373
   ]
  ],
  "error": null
 },
 {
  "id": "q456",
  "sql": "WITH x AS (\n SELECT d.year, l.unit_price*l.qty_shipped rev, p.list_price*l.qty_shipped lst, (1-c.discount_pct) keep\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku) JOIN erp_customers c ON c.customer_id=o.customer_id\n WHERE l.qty_shipped>0 AND l.markdown_pct=0)\nSELECT year, count(*) n_lines, round(sum(lst),2) list_value, round(sum(lst*keep)/sum(lst),4) keep_w, round(sum(rev)/sum(lst*keep),5) resid, round(sum(rev)/sum(lst),4) ptl\nFROM x GROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "n_lines",
   "list_value",
   "keep_w",
   "resid",
   "ptl"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    242753,
    150035570.01,
    0.8583,
    0.98362,
    0.8442
   ],
   [
    2017,
    245683,
    165817014.71,
    0.8573,
    0.98345,
    0.8432
   ],
   [
    2018,
    284386,
    188712091.83,
    0.8564,
    0.98353,
    0.8423
   ],
   [
    2019,
    272366,
    182186951.76,
    0.8562,
    0.98378,
    0.8423
   ],
   [
    2020,
    255820,
    174956694.47,
    0.8554,
    0.98375,
    0.8415
   ],
   [
    2021,
    255096,
    178032284.88,
    0.854,
    0.98352,
    0.8399
   ],
   [
    2022,
    262212,
    177211276.91,
    0.8522,
    0.98358,
    0.8382
   ],
   [
    2023,
    215424,
    137686064.59,
    0.8509,
    0.98362,
    0.837
   ],
   [
    2024,
    216701,
    140640170.86,
    0.849,
    0.98342,
    0.8349
   ],
   [
    2025,
    234834,
    140533485.01,
    0.8479,
    0.98387,
    0.8343
   ]
  ],
  "error": null
 },
 {
  "id": "q436",
  "sql": "WITH x AS (\n SELECT d.year, o.customer_id, p.list_price*l.qty_shipped lst, l.unit_price*l.qty_shipped rev, (1-c.discount_pct) keep\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku) JOIN erp_customers c ON c.customer_id=o.customer_id\n WHERE l.qty_shipped>0 AND l.markdown_pct=0 AND d.year IN (2016,2025)),\ncy AS (SELECT customer_id, year, sum(lst) lst, sum(rev) rev, max(keep) keep FROM x GROUP BY 1,2),\ng AS (SELECT a.customer_id, a.year, a.lst, a.rev, a.keep,\n  CASE WHEN EXISTS (SELECT 1 FROM cy b WHERE b.customer_id=a.customer_id AND b.year<>a.year) THEN 'both' WHEN a.year=2016 THEN 'exited' ELSE 'entered' END grp FROM cy a)\nSELECT year, grp, count(*) n_cust, round(sum(lst),2) list_value, round(sum(lst*keep)/sum(lst),4) keep_w, round(sum(rev)/sum(lst),4) ptl, round(sum(lst)/count(*),0) list_per_cust\nFROM g GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "year",
   "grp",
   "n_cust",
   "list_value",
   "keep_w",
   "ptl",
   "list_per_cust"
  ],
  "row_count": 4,
  "rows": [
   [
    2016,
    "both",
    1346,
    64044415.18,
    0.8448,
    0.8308,
    47581.0
   ],
   [
    2016,
    "exited",
    2016,
    85991154.83,
    0.8683,
    0.8543,
    42654.0
   ],
   [
    2025,
    "both",
    1346,
    70611167.64,
    0.8433,
    0.8287,
    52460.0
   ],
   [
    2025,
    "entered",
    2049,
    69922317.37,
    0.8526,
    0.8398,
    34125.0
   ]
  ],
  "error": null
 },
 {
  "id": "q413",
  "sql": "WITH x AS (\n SELECT d.year, o.customer_id, l.unit_price*l.qty_shipped rev, p.list_price*l.qty_shipped lst\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku)\n WHERE l.markdown_pct=0 AND l.qty_shipped>0 AND d.year IN (2016,2025)),\nbc AS (SELECT customer_id FROM x GROUP BY 1 HAVING count(DISTINCT year)=2),\npc AS (SELECT customer_id, sum(case when year=2016 then rev end)/sum(case when year=2016 then lst end) p16, sum(case when year=2025 then rev end)/sum(case when year=2025 then lst end) p25 FROM x JOIN bc USING(customer_id) GROUP BY 1)\nSELECT count(*) n_cust, round(avg(p16),4) avg_ptl16, round(avg(p25),4) avg_ptl25, round(avg(p25-p16),4) avg_change, round(median(p25-p16),4) med_change,\n sum(case when p25-p16 < -0.02 then 1 else 0 end) n_drop_2pts, sum(case when p25-p16 > 0.02 then 1 else 0 end) n_rise_2pts\nFROM pc",
  "columns": [
   "n_cust",
   "avg_ptl16",
   "avg_ptl25",
   "avg_change",
   "med_change",
   "n_drop_2pts",
   "n_rise_2pts"
  ],
  "row_count": 1,
  "rows": [
   [
    1346,
    0.8319,
    0.8323,
    0.0004,
    0.0005,
    9,
    13
   ]
  ],
  "error": null
 },
 {
  "id": "q446",
  "sql": "SELECT d.year, count(*) n_matched,\n sum(CASE WHEN abs(f.unit_price-l.unit_price)>0.005 THEN 1 ELSE 0 END) n_price_diff,\n round(sum(f.unit_price*f.qty)/sum(l.unit_price*f.qty),5) fin_over_erp\nFROM finance_invoice_lines f JOIN erp_sales_order_lines l USING(line_id) JOIN erp_sales_orders o ON o.order_id=l.order_id JOIN dim_date d ON d.day=o.day\nWHERE d.year IN (2016,2025) GROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "n_matched",
   "n_price_diff",
   "fin_over_erp"
  ],
  "row_count": 2,
  "rows": [
   [
    2016,
    246052,
    0,
    1.0
   ],
   [
    2025,
    252359,
    0,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q404",
  "sql": "WITH c AS (SELECT customer_id, discount_pct, CASE WHEN onboarded_day<=0 THEN 'pre-2016' ELSE CAST((SELECT year FROM dim_date WHERE day=greatest(onboarded_day,1)) AS VARCHAR) END cohort FROM erp_customers)\nSELECT cohort, count(*) n_cust, round(avg(discount_pct),4) avg_disc, min(discount_pct) mn, max(discount_pct) mx\nFROM c GROUP BY 1 ORDER BY 1",
  "columns": [
   "cohort",
   "n_cust",
   "avg_disc",
   "mn",
   "mx"
  ],
  "row_count": 11,
  "rows": [
   [
    "2016",
    320,
    0.1403,
    0.0,
    0.3228
   ],
   [
    "2017",
    306,
    0.144,
    0.0,
    0.3386
   ],
   [
    "2018",
    283,
    0.1375,
    0.0,
    0.3023
   ],
   [
    "2019",
    294,
    0.1404,
    0.0,
    0.3691
   ],
   [
    "2020",
    304,
    0.143,
    0.0,
    0.3988
   ],
   [
    "2021",
    318,
    0.1355,
    0.0,
    0.3409
   ],
   [
    "2022",
    315,
    0.1398,
    0.0,
    0.42
   ],
   [
    "2023",
    271,
    0.1397,
    0.0,
    0.3919
   ],
   [
    "2024",
    298,
    0.1416,
    0.0,
    0.3505
   ],
   [
    "2025",
    293,
    0.1458,
    0.0,
    0.3367
   ],
   [
    "pre-2016",
    3154,
    0.1412,
    0.0,
    0.3789
   ]
  ],
  "error": null
 },
 {
  "id": "q450",
  "sql": "WITH x AS (\n SELECT o.customer_id, sum(p.list_price*l.qty_shipped) lst\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku)\n WHERE l.qty_shipped>0 AND l.markdown_pct=0 AND d.year=2025 GROUP BY 1)\nSELECT CASE WHEN c.onboarded_day<=0 THEN 'pre-2016' ELSE 'since-2016' END coh, count(*) n_cust,\n round(avg(c.discount_pct),4) avg_disc_unweighted, round(sum(c.discount_pct*x.lst)/sum(x.lst),4) avg_disc_list_weighted,\n round(corr(c.discount_pct, x.lst),4) corr_disc_volume\nFROM x JOIN erp_customers c USING(customer_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "coh",
   "n_cust",
   "avg_disc_unweighted",
   "avg_disc_list_weighted",
   "corr_disc_volume"
  ],
  "row_count": 2,
  "rows": [
   [
    "pre-2016",
    1254,
    0.1549,
    0.1568,
    0.0133
   ],
   [
    "since-2016",
    2141,
    0.1455,
    0.1478,
    0.0158
   ]
  ],
  "error": null
 },
 {
  "id": "q415",
  "sql": "WITH a AS (\n SELECT DISTINCT o.customer_id, d.year FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year IN (2016,2025)),\nc AS (SELECT customer_id, CASE WHEN discount_pct<0.10 THEN 'a <10%' WHEN discount_pct<0.15 THEN 'b 10-15%' WHEN discount_pct<0.20 THEN 'c 15-20%' ELSE 'd >=20%' END tier FROM erp_customers)\nSELECT tier, count(DISTINCT a16.customer_id) active_2016, count(DISTINCT a25.customer_id) still_active_2025, round(count(DISTINCT a25.customer_id)/count(DISTINCT a16.customer_id),4) retained_share\nFROM c JOIN a a16 ON a16.customer_id=c.customer_id AND a16.year=2016\nLEFT JOIN a a25 ON a25.customer_id=c.customer_id AND a25.year=2025\nGROUP BY 1 ORDER BY 1",
  "columns": [
   "tier",
   "active_2016",
   "still_active_2025",
   "retained_share"
  ],
  "row_count": 4,
  "rows": [
   [
    "a <10%",
    1000,
    292,
    0.292
   ],
   [
    "b 10-15%",
    849,
    337,
    0.3969
   ],
   [
    "c 15-20%",
    782,
    368,
    0.4706
   ],
   [
    "d >=20%",
    733,
    352,
    0.4802
   ]
  ],
  "error": null
 },
 {
  "id": "q445",
  "sql": "WITH a16 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2016),\nlast AS (SELECT o.customer_id, max(d.year) last_year FROM erp_sales_orders o JOIN dim_date d USING(day) GROUP BY 1),\nc AS (SELECT CASE WHEN discount_pct<0.10 THEN 'a <10%' WHEN discount_pct<0.15 THEN 'b 10-15%' WHEN discount_pct<0.20 THEN 'c 15-20%' ELSE 'd >=20%' END tier, last_year\n FROM a16 JOIN erp_customers cu USING(customer_id) JOIN last USING(customer_id))\nSELECT tier, last_year, count(*) n FROM c GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "tier",
   "last_year",
   "n"
  ],
  "row_count": 40,
  "rows": [
   [
    "a <10%",
    2016,
    147
   ],
   [
    "a <10%",
    2017,
    123
   ],
   [
    "a <10%",
    2018,
    101
   ],
   [
    "a <10%",
    2019,
    81
   ],
   [
    "a <10%",
    2020,
    66
   ],
   [
    "a <10%",
    2021,
    62
   ],
   [
    "a <10%",
    2022,
    43
   ],
   [
    "a <10%",
    2023,
    42
   ],
   [
    "a <10%",
    2024,
    43
   ],
   [
    "a <10%",
    2025,
    292
   ],
   [
    "b 10-15%",
    2016,
    116
   ],
   [
    "b 10-15%",
    2017,
    75
   ],
   [
    "b 10-15%",
    2018,
    66
   ],
   [
    "b 10-15%",
    2019,
    54
   ],
   [
    "b 10-15%",
    2020,
    49
   ],
   [
    "b 10-15%",
    2021,
    42
   ],
   [
    "b 10-15%",
    2022,
    36
   ],
   [
    "b 10-15%",
    2023,
    41
   ],
   [
    "b 10-15%",
    2024,
    33
   ],
   [
    "b 10-15%",
    2025,
    337
   ],
   [
    "c 15-20%",
    2016,
    93
   ],
   [
    "c 15-20%",
    2017,
    57
   ],
   [
    "c 15-20%",
    2018,
    56
   ],
   [
    "c 15-20%",
    2019,
    49
   ],
   [
    "c 15-20%",
    2020,
    38
   ],
   [
    "c 15-20%",
    2021,
    43
   ],
   [
    "c 15-20%",
    2022,
    26
   ],
   [
    "c 15-20%",
    2023,
    22
   ],
   [
    "c 15-20%",
    2024,
    30
   ],
   [
    "c 15-20%",
    2025,
    368
   ],
   [
    "d >=20%",
    2016,
    80
   ],
   [
    "d >=20%",
    2017,
    49
   ],
   [
    "d >=20%",
    2018,
    60
   ],
   [
    "d >=20%",
    2019,
    39
   ],
   [
    "d >=20%",
    2020,
    37
   ],
   [
    "d >=20%",
    2021,
    37
   ],
   [
    "d >=20%",
    2022,
    28
   ],
   [
    "d >=20%",
    2023,
    27
   ],
   [
    "d >=20%",
    2024,
    24
   ],
   [
    "d >=20%",
    2025,
    352
   ]
  ],
  "error": null
 },
 {
  "id": "q440",
  "sql": "WITH s AS (\n SELECT o.customer_id, sum(p.list_price*l.qty_shipped) lst16\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku)\n WHERE d.year=2016 AND l.qty_shipped>0 GROUP BY 1),\na25 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2025),\nc AS (SELECT s.customer_id, s.lst16, ntile(4) OVER (ORDER BY s.lst16, s.customer_id) size_q,\n  CASE WHEN discount_pct<0.10 THEN 'a <10%' WHEN discount_pct<0.15 THEN 'b 10-15%' WHEN discount_pct<0.20 THEN 'c 15-20%' ELSE 'd >=20%' END tier,\n  (a25.customer_id IS NOT NULL)::INT ret\n  FROM s JOIN erp_customers cu USING(customer_id) LEFT JOIN a25 USING(customer_id))\nSELECT size_q, tier, count(*) n, sum(ret) retained, round(avg(ret),4) ret_share, round(avg(lst16),0) avg_list16\nFROM c GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "size_q",
   "tier",
   "n",
   "retained",
   "ret_share",
   "avg_list16"
  ],
  "row_count": 16,
  "rows": [
   [
    1,
    "a <10%",
    257,
    71,
    0.2763,
    3752.0
   ],
   [
    1,
    "b 10-15%",
    232,
    74,
    0.319,
    3588.0
   ],
   [
    1,
    "c 15-20%",
    173,
    79,
    0.4566,
    3924.0
   ],
   [
    1,
    "d >=20%",
    179,
    88,
    0.4916,
    3486.0
   ],
   [
    2,
    "a <10%",
    244,
    71,
    0.291,
    13909.0
   ],
   [
    2,
    "b 10-15%",
    207,
    82,
    0.3961,
    13824.0
   ],
   [
    2,
    "c 15-20%",
    210,
    94,
    0.4476,
    14426.0
   ],
   [
    2,
    "d >=20%",
    180,
    73,
    0.4056,
    14104.0
   ],
   [
    3,
    "a <10%",
    260,
    79,
    0.3038,
    33962.0
   ],
   [
    3,
    "b 10-15%",
    200,
    84,
    0.42,
    32806.0
   ],
   [
    3,
    "c 15-20%",
    196,
    89,
    0.4541,
    32795.0
   ],
   [
    3,
    "d >=20%",
    184,
    94,
    0.5109,
    32275.0
   ],
   [
    4,
    "a <10%",
    238,
    71,
    0.2983,
    129362.0
   ],
   [
    4,
    "b 10-15%",
    210,
    97,
    0.4619,
    149724.0
   ],
   [
    4,
    "c 15-20%",
    203,
    106,
    0.5222,
    129901.0
   ],
   [
    4,
    "d >=20%",
    189,
    97,
    0.5132,
    129080.0
   ]
  ],
  "error": null
 },
 {
  "id": "q441",
  "sql": "WITH a16 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2016),\na25 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2025),\nc AS (SELECT cu.trade, CASE WHEN discount_pct<0.10 THEN 'lo <10%' ELSE 'hi >=10%' END tier, (a25.customer_id IS NOT NULL)::INT ret\n FROM a16 JOIN erp_customers cu USING(customer_id) LEFT JOIN a25 USING(customer_id))\nSELECT trade, tier, count(*) n, sum(ret) retained, round(avg(ret),4) ret_share FROM c GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "trade",
   "tier",
   "n",
   "retained",
   "ret_share"
  ],
  "row_count": 6,
  "rows": [
   [
    "commercial",
    "hi >=10%",
    474,
    212,
    0.4473
   ],
   [
    "commercial",
    "lo <10%",
    184,
    48,
    0.2609
   ],
   [
    "mixed",
    "hi >=10%",
    432,
    199,
    0.4606
   ],
   [
    "mixed",
    "lo <10%",
    179,
    59,
    0.3296
   ],
   [
    "residential",
    "hi >=10%",
    1458,
    646,
    0.4431
   ],
   [
    "residential",
    "lo <10%",
    637,
    185,
    0.2904
   ]
  ],
  "error": null
 },
 {
  "id": "q443",
  "sql": "WITH a16 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2016),\na25 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2025),\nc AS (SELECT cu.branch, CASE WHEN discount_pct<0.10 THEN 'lo' ELSE 'hi' END tier, (a25.customer_id IS NOT NULL)::INT ret\n FROM a16 JOIN erp_customers cu USING(customer_id) LEFT JOIN a25 USING(customer_id))\nSELECT branch, count(*) FILTER (WHERE tier='lo') n_lo, round(avg(ret) FILTER (WHERE tier='lo'),4) ret_lo,\n count(*) FILTER (WHERE tier='hi') n_hi, round(avg(ret) FILTER (WHERE tier='hi'),4) ret_hi\nFROM c GROUP BY 1 ORDER BY 1",
  "columns": [
   "branch",
   "n_lo",
   "ret_lo",
   "n_hi",
   "ret_hi"
  ],
  "row_count": 12,
  "rows": [
   [
    "Akron",
    48,
    0.3125,
    102,
    0.549
   ],
   [
    "Cincinnati",
    145,
    0.2897,
    305,
    0.4492
   ],
   [
    "Cleveland",
    121,
    0.2975,
    335,
    0.4149
   ],
   [
    "Columbus",
    125,
    0.288,
    295,
    0.4373
   ],
   [
    "Dayton",
    51,
    0.3529,
    121,
    0.4876
   ],
   [
    "Fort Wayne",
    33,
    0.2727,
    56,
    0.5714
   ],
   [
    "Indianapolis",
    101,
    0.2871,
    281,
    0.4021
   ],
   [
    "Lexington",
    34,
    0.3529,
    65,
    0.5077
   ],
   [
    "Louisville",
    75,
    0.2533,
    200,
    0.445
   ],
   [
    "Pittsburgh",
    151,
    0.2517,
    327,
    0.3976
   ],
   [
    "Toledo",
    35,
    0.3429,
    101,
    0.6139
   ],
   [
    "Troy",
    81,
    0.321,
    176,
    0.4432
   ]
  ],
  "error": null
 },
 {
  "id": "q451",
  "sql": "WITH a25 AS (SELECT DISTINCT o.customer_id FROM erp_sales_orders o JOIN dim_date d USING(day) WHERE d.year=2025),\nanyo AS (SELECT DISTINCT customer_id FROM erp_sales_orders),\nc AS (SELECT CASE WHEN discount_pct<0.10 THEN 'a <10%' WHEN discount_pct<0.15 THEN 'b 10-15%' WHEN discount_pct<0.20 THEN 'c 15-20%' ELSE 'd >=20%' END tier,\n  (a25.customer_id IS NOT NULL)::INT ret\n FROM erp_customers cu JOIN anyo USING(customer_id) LEFT JOIN a25 USING(customer_id) JOIN dim_date dd ON dd.day=cu.onboarded_day\n WHERE dd.year BETWEEN 2016 AND 2020)\nSELECT tier, count(*) n_ordered_ever, sum(ret) active_2025, round(avg(ret),4) share, (SELECT round(102408.39+1080280.56+245867.49,2)) decomposition_sum\nFROM c GROUP BY 1 ORDER BY 1",
  "columns": [
   "tier",
   "n_ordered_ever",
   "active_2025",
   "share",
   "decomposition_sum"
  ],
  "row_count": 4,
  "rows": [
   [
    "a <10%",
    458,
    230,
    0.5022,
    1428556.44
   ],
   [
    "b 10-15%",
    373,
    216,
    0.5791,
    1428556.44
   ],
   [
    "c 15-20%",
    349,
    236,
    0.6762,
    1428556.44
   ],
   [
    "d >=20%",
    327,
    212,
    0.6483,
    1428556.44
   ]
  ],
  "error": null
 },
 {
  "id": "q449",
  "sql": "WITH x AS (\n SELECT d.year, o.customer_id, p.list_price*l.qty_shipped lst, (1-c.discount_pct) keep\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku) JOIN erp_customers c ON c.customer_id=o.customer_id\n WHERE l.qty_shipped>0 AND l.markdown_pct=0 AND d.year IN (2016,2025)),\ncy AS (SELECT customer_id, year, sum(lst) lst, max(keep) keep FROM x GROUP BY 1,2),\ng AS (SELECT a.*, CASE WHEN count(*) OVER (PARTITION BY customer_id)=2 THEN 'both' WHEN year=2016 THEN 'exited' ELSE 'entered' END grp FROM cy a),\ns AS (SELECT year, grp, sum(lst) lst, sum(lst*keep)/sum(lst) k FROM g GROUP BY 1,2),\nt AS (SELECT\n (SELECT sum(lst*k)/sum(lst) FROM s WHERE year=2016) k16,\n (SELECT sum(lst*k)/sum(lst) FROM s WHERE year=2025) k25,\n (SELECT k FROM s WHERE year=2016 AND grp='both') kb16,\n (SELECT k FROM s WHERE year=2025 AND grp='both') kb25,\n (SELECT k FROM s WHERE year=2016 AND grp='exited') kx,\n (SELECT k FROM s WHERE year=2025 AND grp='entered') kn,\n (SELECT lst FROM s WHERE year=2016 AND grp='both')/(SELECT sum(lst) FROM s WHERE year=2016) wb16,\n (SELECT lst FROM s WHERE year=2025 AND grp='both')/(SELECT sum(lst) FROM s WHERE year=2025) wb25,\n (SELECT sum(lst) FROM s WHERE year=2025) lst25)\nSELECT round(k16,4) k16, round(k25,4) k25, round(k25-k16,4) total_change,\n round(wb25*(kb25-kb16),4) continuer_change,\n round((1-wb25)*(kn-kx),4) entrant_vs_exiter_gap,\n round((wb25-wb16)*(kb16-kx),4) weight_shift,\n round(wb16,4) wb16, round(wb25,4) wb25,\n round(lst25*wb25*(kb16-kb25)*0.98362255,2) continuer_dollars,\n round(lst25*(1-wb25)*(kx-kn)*0.98362255,2) replacement_dollars,\n round(lst25*(wb25-wb16)*(kx-kb16)*0.98362255,2) weight_dollars\nFROM t",
  "columns": [
   "k16",
   "k25",
   "total_change",
   "continuer_change",
   "entrant_vs_exiter_gap",
   "weight_shift",
   "wb16",
   "wb25",
   "continuer_dollars",
   "replacement_dollars",
   "weight_dollars"
  ],
  "row_count": 1,
  "rows": [
   [
    0.8583,
    0.8479,
    -0.0103,
    -0.0007,
    -0.0078,
    -0.0018,
    0.4269,
    0.5025,
    102408.39,
    1080280.56,
    245867.49
   ]
  ],
  "error": null
 },
 {
  "id": "q462",
  "sql": "SELECT round(150035570.01-140533485.01,2) nonmd_list_drop_16_25, round(85991154.83-69922317.37,2) exit_minus_entry_list, round(70611167.64-64044415.18,2) continuer_list_growth, round(102408.39+1080280.56+245867.49,2) decomposition_sum, round(1080280.56/1428556.44,4) replacement_share",
  "columns": [
   "nonmd_list_drop_16_25",
   "exit_minus_entry_list",
   "continuer_list_growth",
   "decomposition_sum",
   "replacement_share"
  ],
  "row_count": 1,
  "rows": [
   [
    9502085.0,
    16068837.46,
    6566752.46,
    1428556.44,
    0.7562
   ]
  ],
  "error": null
 },
 {
  "id": "q418",
  "sql": "WITH x AS (\n SELECT d.year, l.unit_price*l.qty_shipped rev, p.list_price*l.qty_shipped lst, (1-c.discount_pct) keep\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_products p USING(sku) JOIN erp_customers c ON c.customer_id=o.customer_id\n WHERE l.qty_shipped>0 AND l.markdown_pct=0 AND d.year IN (2016,2025)),\ny AS (SELECT year, sum(rev) rev, sum(lst) lst, sum(lst*keep)/sum(lst) keep_w, sum(rev)/sum(lst*keep) resid FROM x GROUP BY 1)\nSELECT a.keep_w keep16, b.keep_w keep25, a.resid resid16, b.resid resid25,\n round(b.lst*(a.keep_w-b.keep_w)*a.resid,2) customer_mix_dollars_2025,\n round(b.lst*b.keep_w*(a.resid-b.resid),2) residual_rate_dollars_2025,\n round(b.lst*(a.rev/a.lst - b.rev/b.lst),2) total_shortfall_2025\nFROM y a, y b WHERE a.year=2016 AND b.year=2025",
  "columns": [
   "keep16",
   "keep25",
   "resid16",
   "resid25",
   "customer_mix_dollars_2025",
   "residual_rate_dollars_2025",
   "total_shortfall_2025"
  ],
  "row_count": 1,
  "rows": [
   [
    0.8582789896028971,
    0.8479444981094445,
    0.9836225540476192,
    0.9838733233685002,
    1428556.45,
    -29882.82,
    1398673.63
   ]
  ],
  "error": null
 },
 {
  "id": "q452",
  "sql": "SELECT CASE WHEN c.discount_pct<0.10 THEN 'a <10%' WHEN c.discount_pct<0.15 THEN 'b 10-15%' WHEN c.discount_pct<0.20 THEN 'c 15-20%' ELSE 'd >=20%' END tier,\n count(*) n_quotes, round(avg((q.status='won')::INT),4) win_rate, round(avg((q.status='lost')::INT),4) loss_rate,\n count(*) FILTER (WHERE q.status='lost' AND q.loss_reason IS NOT NULL) n_lost_with_reason,\n round(avg((lower(q.loss_reason) LIKE '%price%')::INT) FILTER (WHERE q.status='lost' AND q.loss_reason IS NOT NULL),4) price_share_of_reasons,\n min(q.quote_date) first_q, max(q.quote_date) last_q\nFROM crm_quotes q JOIN erp_customers c USING(customer_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "tier",
   "n_quotes",
   "win_rate",
   "loss_rate",
   "n_lost_with_reason",
   "price_share_of_reasons",
   "first_q",
   "last_q"
  ],
  "row_count": 4,
  "rows": [
   [
    "a <10%",
    141039,
    0.4257,
    0.2869,
    32443,
    0.5488,
    "2016-01-01",
    "2025-12-29"
   ],
   [
    "b 10-15%",
    142851,
    0.4338,
    0.2751,
    31870,
    0.5191,
    "2016-01-01",
    "2025-12-29"
   ],
   [
    "c 15-20%",
    139557,
    0.4291,
    0.275,
    31159,
    0.5076,
    "2016-01-01",
    "2025-12-29"
   ],
   [
    "d >=20%",
    128504,
    0.4271,
    0.2777,
    29006,
    0.5085,
    "2016-01-01",
    "2025-12-29"
   ]
  ],
  "error": null
 },
 {
  "id": "q453",
  "sql": "SELECT loss_reason, count(*) n FROM crm_quotes WHERE status='lost' GROUP BY 1 ORDER BY 2 DESC, 1",
  "columns": [
   "loss_reason",
   "n"
  ],
  "row_count": 3,
  "rows": [
   [
    "price",
    64915
   ],
   [
    "job cancelled",
    59563
   ],
   [
    null,
    29340
   ]
  ],
  "error": null
 },
 {
  "id": "q454",
  "sql": "SELECT CASE WHEN c.discount_pct<0.10 THEN 'a <10%' WHEN c.discount_pct<0.15 THEN 'b 10-15%' WHEN c.discount_pct<0.20 THEN 'c 15-20%' ELSE 'd >=20%' END tier,\n count(*) FILTER (WHERE q.status='lost') n_lost,\n count(*) FILTER (WHERE q.status='lost' AND coalesce(q.loss_reason,'')<>'') n_lost_reason_filled,\n round(avg((q.loss_reason='price')::INT) FILTER (WHERE q.status='lost' AND coalesce(q.loss_reason,'')<>''),4) price_share_filled,\n round(avg((q.loss_reason='price')::INT) FILTER (WHERE q.status='lost'),4) price_share_all_lost\nFROM crm_quotes q JOIN erp_customers c USING(customer_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "tier",
   "n_lost",
   "n_lost_reason_filled",
   "price_share_filled",
   "price_share_all_lost"
  ],
  "row_count": 4,
  "rows": [
   [
    "a <10%",
    40463,
    32443,
    0.5488,
    0.5488
   ],
   [
    "b 10-15%",
    39292,
    31870,
    0.5191,
    0.5191
   ],
   [
    "c 15-20%",
    38373,
    31159,
    0.5076,
    0.5076
   ],
   [
    "d >=20%",
    35690,
    29006,
    0.5085,
    0.5085
   ]
  ],
  "error": null
 },
 {
  "id": "q420",
  "sql": "SELECT o.branch,\n round(avg(case when d.year=2016 then c.discount_pct end),4) disc16,\n round(avg(case when d.year=2025 then c.discount_pct end),4) disc25,\n count(case when d.year=2016 then 1 end) lines16, count(case when d.year=2025 then 1 end) lines25\nFROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day JOIN erp_customers c ON c.customer_id=o.customer_id\nWHERE d.year IN (2016,2025) GROUP BY 1 ORDER BY 1",
  "columns": [
   "branch",
   "disc16",
   "disc25",
   "lines16",
   "lines25"
  ],
  "row_count": 12,
  "rows": [
   [
    "Akron",
    0.1523,
    0.169,
    12373,
    12271
   ],
   [
    "Cincinnati",
    0.1406,
    0.1482,
    35308,
    33799
   ],
   [
    "Cleveland",
    0.1468,
    0.1484,
    38246,
    37211
   ],
   [
    "Columbus",
    0.1421,
    0.1546,
    34329,
    33482
   ],
   [
    "Dayton",
    0.156,
    0.1617,
    14064,
    13634
   ],
   [
    "Fort Wayne",
    0.1358,
    0.1565,
    7222,
    7398
   ],
   [
    "Indianapolis",
    0.1366,
    0.1575,
    32992,
    31770
   ],
   [
    "Lexington",
    0.1375,
    0.1546,
    8259,
    7821
   ],
   [
    "Louisville",
    0.1554,
    0.1604,
    20856,
    19917
   ],
   [
    "Pittsburgh",
    0.144,
    0.1502,
    41199,
    40405
   ],
   [
    "Toledo",
    0.142,
    0.1402,
    11750,
    10909
   ],
   [
    "Troy",
    0.1128,
    0.1334,
    23606,
    23214
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
