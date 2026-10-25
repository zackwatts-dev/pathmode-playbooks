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
 "id": "F2",
 "hypothesis": "H3",
 "title": "Hartwell paid about $317K a year in vendor bill lines above PO value (2016-2025). Only about $85K a year of that is provably qty never received (stock POs). About $150K is special-order qty with no receipt record, and about $82K is unit cost that can't be judged.",
 "conclusion": "Holds with changes. Observed: over 2016-2025, 13,949 bills paid in full carried line value above their PO, 3,166,564.74 in total. That is 316,656.47 a year, or 0.2956% of 1,071,302,610.84 PO value on paid-in-full bills (q231, q126). Every year is between 272,768.64 (2023) and 429,671.84 (2016) (q231). This is a gross figure. All 1,234 vendor credits trace to vendor-return movements once they are matched on vendor_id, so no credit offsets it. My earlier 273,967.29 floor came from a join error and is withdrawn (q166, q169). The excess has three parts with different evidence. (a) Qty billed above PO on stock POs: 847,795.65 (84,779.56 a year). Every billed stock line has a WMS receipt equal to PO qty, so the billed extra was demonstrably not received (q164, q231). (b) Qty billed above PO on special-order POs: 1,498,042.39 (149,804.24 a year). Special orders have no WMS receipt at all (121,364 paid-in-full lines, 0 with a receipt), so receipt can't be checked. Indirectly, on all 1,228 of 1,290 qty-over lines that match exactly one customer sales line, the customer was shipped the PO qty and never the billed qty. That is consistent with non-delivery but doesn't prove it (q164, q193). (c) Unit cost above PO on lines without qty-over: 820,726.70 (82,072.67 a year). Whether this was owed can't be judged: PO cost equals the product master cost on every line and never changed for any of 1,096 SKUs in ten years, so the PO isn't an independent price reference (q171, q183, q231). Interpretation: AP paid exactly PO value, excluding freight, on about 30% of bills that differed from the PO for any reason, including freight-only bills (0.3008), and on 0 of 322,260 bills that matched. That looks like a pay-to-PO rule applied to a fraction of variance bills, not a three-way match (q197, q202). Action: hold any bill line whose qty exceeds the receipt (or, for special orders, the customer shipment) or whose unit cost exceeds the PO. Claim (a) against receipts first. Claim (b) with vendor proof of delivery. Start with 2024-2025: 658,006.40 in total, of which (a) is 157,039.15.",
 "dollars_a_year": 316656.47,
 "size_query": "q231",
 "claims": [
  {
   "text": "Bills reconcile: all 368,154 bills equal line value plus freight, and paid-in-full bills were paid that amount. Bill lines join to PO lines on po_id+sku. No line bills less qty or less unit cost than the PO. Paid-in-full excess is 3,166,564.74 on 1,071,302,610.84 of PO value (0.2956%), 2016-2025.",
   "queries": [
    "q154",
    "q231"
   ]
  },
  {
   "text": "Excess is a level, not a spike: 272,768.64 (2023) to 429,671.84 (2016) a year. Without each year's top 10 lines, every year stays at 250,088.62 or more. The largest single line is 3,219.00.",
   "queries": [
    "q231",
    "q205"
   ]
  },
  {
   "text": "Stock-PO qty-over (proven unreceived): every billed stock line has a receipt equal to PO qty (446,852 of 446,852 paid-in-full lines). Qty-over excess on stock POs is 847,795.65, or 84,779.56 a year; 157,039.15 of it falls in 2024-2025.",
   "queries": [
    "q164",
    "q231",
    "q234"
   ]
  },
  {
   "text": "Special-order qty-over (not provable from receipts): 121,364 paid-in-full special-order lines have no WMS receipt. Their qty-over excess is 1,498,042.39 (149,804.24 a year). Of 1,290 qty-over lines, 1,228 (0.9519) match exactly one special sales line. On all 1,228 the customer was shipped the PO qty, and on 0 was the customer shipped the billed qty or more. The other 62 match several sales lines and are ambiguous.",
   "queries": [
    "q164",
    "q193",
    "q231",
    "q234"
   ]
  },
  {
   "text": "Unit-cost excess without qty-over is 820,726.70 (82,072.67 a year). PO unit cost never varies for any of 1,096 SKUs and equals the product master cost on all 568,216 paid-in-full lines, so whether these costs were owed can't be tested. After the first overpriced line for a vendor-SKU, later lines are overpriced at 0.0249, the same as the base share. This argues against a general price increase, but it is weak evidence given the static PO prices.",
   "queries": [
    "q231",
    "q171",
    "q183",
    "q110"
   ]
  },
  {
   "text": "Vendor credits don't offset the excess: all 1,234 credits (all from OEM vendors 1-4) match a return_vendor movement on vendor_id+sku+qty within 60 days. The earlier 'unmatched 426,891.88' came from joining return ref_id (a vendor id) to PO ids.",
   "queries": [
    "q160",
    "q166",
    "q169"
   ]
  },
  {
   "text": "Short-pay pattern: all 12,026 short-paid bills were paid exactly PO value, with freight excluded. The short-pay share is 0.3008 on freight-only variance bills (6,115 of 20,329), 0.2986 on line-excess bills without freight (5,566 of 18,639), 0.2826 with both (345 of 1,221), and 0.0 on 322,260 matching bills. The caught share of overbilled bills is 0.2755-0.3122 in every year (overall 0.2976, 5,911 of 19,860).",
   "queries": [
    "q197",
    "q202",
    "q126"
   ]
  }
 ],
 "confidence": "high for the amount paid above PO and for the stock-PO qty-over part; medium for special-order qty-over; low for whether the unit-cost part was owed",
 "not_evidence_of": "Not evidence that any vendor or any AP staff member acted in bad faith. The pattern is uniform across 44 vendors and ten years, and its very regular structure (narrow ratio band, mostly +1 unit, flat rates, PO prices that never change) may partly reflect how the records were produced. Not evidence that special-order units were never delivered, since no receipt record exists for special orders. Not evidence that the higher unit costs were wrong: there are no price lists or contracts. Not evidence that purchasing costs are generally inflated (0.2956% of PO value). Not evidence that AP's short-pays were correct: some withheld freight may have been owed.",
 "could_not_tell": "Whether special-order units above PO qty were delivered (needs vendor proof of delivery or a special-order receiving record). Whether the higher unit costs were contractually valid (needs vendor price lists or contracts; PO cost is a fixed master price). What freight was owed (no freight terms). How AP picked the bills it short-paid (no approval or dispute history). Whether any excess was disputed or credited outside these tables. The vendor dispute window, which decides how much of 2016-2023 is recoverable.",
 "next_step": "Put a match hold on bill lines where qty exceeds the receipt (stock) or the customer shipment (special), or where unit cost exceeds the PO. Pull the paid-in-full stock-PO qty-over lines and claim them against receipts, starting with 2024-2025 (157,039.15). Ask OEM vendors for proof of delivery on special-order qty-over lines. Get vendor price agreements before pursuing unit-cost differences. Ask AP how short-pay bills are chosen and whether freight withheld on freight-only bills was owed. Separately, review the 963 paid second bills on duplicate-billed POs (2,732,286.38, q172).",
 "incomplete": false
}

[
 {
  "id": "q154",
  "sql": "WITH bl AS (SELECT bill_id, sum(qty*unit_cost) lv FROM finance_vendor_bill_lines GROUP BY 1)\nSELECT count(*) bills, sum(CASE WHEN abs(b.amount-(bl.lv+b.freight))<0.01 THEN 1 ELSE 0 END) amt_eq_lines_plus_freight,\nsum(CASE WHEN abs(b.amount-bl.lv)<0.01 THEN 1 ELSE 0 END) amt_eq_lines,\nsum(CASE WHEN bl.bill_id IS NULL THEN 1 ELSE 0 END) no_lines,\nround(sum(b.freight),2) freight, round(sum(b.amount),2) amount\nFROM finance_vendor_bills b LEFT JOIN bl USING(bill_id)",
  "columns": [
   "bills",
   "amt_eq_lines_plus_freight",
   "amt_eq_lines",
   "no_lines",
   "freight",
   "amount"
  ],
  "row_count": 1,
  "rows": [
   [
    368154,
    368154,
    346268,
    0,
    3007927.95,
    1133578191.26
   ]
  ],
  "error": null
 },
 {
  "id": "q231",
  "sql": "WITH x AS (SELECT po.purpose, d.year, (l.qty>p.qty) qo, l.qty*l.unit_cost-p.qty*p.unit_cost diff, p.qty*p.unit_cost pv\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id)\nJOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku JOIN erp_purchase_orders po ON po.po_id=b.po_id\nJOIN dim_date d ON d.day=b.day\nJOIN finance_vendor_payments vp ON vp.bill_id=b.bill_id AND abs(vp.amount-b.amount)<0.01)\nSELECT year,\n round(sum(diff) FILTER (WHERE diff>0.005),2) excess,\n round(sum(diff) FILTER (WHERE diff>0.005 AND qo AND purpose='stock'),2) a_stock_qty,\n round(sum(diff) FILTER (WHERE diff>0.005 AND qo AND purpose='special'),2) b_special_qty,\n round(sum(diff) FILTER (WHERE diff>0.005 AND NOT qo),2) c_cost_only,\n round(sum(pv),2) po_value,\n round(sum(diff) FILTER (WHERE diff>0.005)/10,2) excess_per_yr_10,\n round(sum(diff) FILTER (WHERE diff>0.005 AND qo AND purpose='stock')/10,2) a_per_yr_10,\n round(sum(diff) FILTER (WHERE diff>0.005 AND qo AND purpose='special')/10,2) b_per_yr_10,\n round(sum(diff) FILTER (WHERE diff>0.005 AND NOT qo)/10,2) c_per_yr_10,\n round(100*sum(diff) FILTER (WHERE diff>0.005)/sum(pv),4) excess_pct_of_po\nFROM x GROUP BY ROLLUP(year) ORDER BY year NULLS LAST",
  "columns": [
   "year",
   "excess",
   "a_stock_qty",
   "b_special_qty",
   "c_cost_only",
   "po_value",
   "excess_per_yr_10",
   "a_per_yr_10",
   "b_per_yr_10",
   "c_per_yr_10",
   "excess_pct_of_po"
  ],
  "row_count": 11,
  "rows": [
   [
    2016,
    429671.84,
    68996.33,
    277687.47,
    82988.04,
    106211654.45,
    42967.18,
    6899.63,
    27768.75,
    8298.8,
    0.4045
   ],
   [
    2017,
    314474.76,
    78248.92,
    150713.85,
    85511.98,
    109617889.23,
    31447.48,
    7824.89,
    15071.38,
    8551.2,
    0.2869
   ],
   [
    2018,
    328219.59,
    80438.76,
    154947.91,
    92832.92,
    123934774.84,
    32821.96,
    8043.88,
    15494.79,
    9283.29,
    0.2648
   ],
   [
    2019,
    307838.46,
    108059.07,
    119605.86,
    80173.53,
    114069673.55,
    30783.85,
    10805.91,
    11960.59,
    8017.35,
    0.2699
   ],
   [
    2020,
    294787.57,
    84219.66,
    130286.14,
    80281.77,
    111316112.67,
    29478.76,
    8421.97,
    13028.61,
    8028.18,
    0.2648
   ],
   [
    2021,
    285324.78,
    80298.9,
    115902.47,
    89123.41,
    113391993.45,
    28532.48,
    8029.89,
    11590.25,
    8912.34,
    0.2516
   ],
   [
    2022,
    275472.71,
    99914.74,
    93331.14,
    82226.83,
    111458566.21,
    27547.27,
    9991.47,
    9333.11,
    8222.68,
    0.2472
   ],
   [
    2023,
    272768.64,
    90580.11,
    113494.47,
    68694.06,
    89483133.57,
    27276.86,
    9058.01,
    11349.45,
    6869.41,
    0.3048
   ],
   [
    2024,
    333959.25,
    89723.67,
    168139.99,
    76095.59,
    97272694.47,
    33395.93,
    8972.37,
    16814.0,
    7609.56,
    0.3433
   ],
   [
    2025,
    324047.15,
    67315.48,
    173933.1,
    82798.57,
    94546118.4,
    32404.71,
    6731.55,
    17393.31,
    8279.86,
    0.3427
   ],
   [
    null,
    3166564.74,
    847795.65,
    1498042.39,
    820726.7,
    1071302610.84,
    316656.47,
    84779.56,
    149804.24,
    82072.67,
    0.2956
   ]
  ],
  "error": null
 },
 {
  "id": "q205",
  "sql": "WITH x AS (SELECT d.year, l.qty*l.unit_cost-p.qty*p.unit_cost diff\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id)\nJOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku JOIN dim_date d ON d.day=b.day\nJOIN finance_vendor_payments vp ON vp.bill_id=b.bill_id AND abs(vp.amount-b.amount)<0.01 WHERE l.qty*l.unit_cost-p.qty*p.unit_cost>0.005),\nr AS (SELECT *, row_number() OVER (PARTITION BY year ORDER BY diff DESC) rk FROM x)\nSELECT year, count(*) n, round(sum(diff),2) excess, round(sum(diff) FILTER (WHERE rk<=10),2) top10_lines, round(sum(diff) FILTER (WHERE rk>10),2) excl_top10, round(max(diff),2) max_line, round(median(diff),2) med\nFROM r GROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "n",
   "excess",
   "top10_lines",
   "excl_top10",
   "max_line",
   "med"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    1570,
    429671.84,
    21702.3,
    407969.53,
    2505.02,
    65.32
   ],
   [
    2017,
    1431,
    314474.76,
    20781.05,
    293693.7,
    2625.69,
    62.73
   ],
   [
    2018,
    1436,
    328219.59,
    21138.44,
    307081.15,
    2673.96,
    62.65
   ],
   [
    2019,
    1374,
    307838.46,
    20713.76,
    287124.7,
    3219.0,
    61.76
   ],
   [
    2020,
    1388,
    294787.57,
    22377.23,
    272410.34,
    2908.47,
    57.76
   ],
   [
    2021,
    1337,
    285324.78,
    19165.29,
    266159.49,
    2495.23,
    63.91
   ],
   [
    2022,
    1380,
    275472.71,
    20203.2,
    255269.51,
    2772.94,
    56.1
   ],
   [
    2023,
    1248,
    272768.64,
    22680.02,
    250088.62,
    2673.96,
    57.21
   ],
   [
    2024,
    1411,
    333959.25,
    22671.11,
    311288.14,
    2772.94,
    60.28
   ],
   [
    2025,
    1400,
    324047.15,
    20979.49,
    303067.66,
    2308.93,
    63.45
   ]
  ],
  "error": null
 },
 {
  "id": "q164",
  "sql": "WITH rq AS (SELECT ref_id po_id, sku, sum(qty_delta) rq FROM wms_inventory_transactions WHERE reason='receipt' GROUP BY 1,2),\nx AS (SELECT po.purpose, l.qty bq, p.qty pq, rq.rq, l.unit_cost bc, p.unit_cost pc, l.qty*l.unit_cost-p.qty*p.unit_cost diff,\n CASE WHEN vp.bill_id IS NULL THEN 'unpaid' WHEN abs(vp.amount-b.amount)<0.01 THEN 'full' ELSE 'short' END pay\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id)\nJOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku\nJOIN erp_purchase_orders po ON po.po_id=b.po_id\nLEFT JOIN rq ON rq.po_id=b.po_id AND rq.sku=l.sku\nLEFT JOIN finance_vendor_payments vp ON vp.bill_id=b.bill_id)\nSELECT purpose, pay, count(*) lines, sum((rq IS NULL)::int) no_receipt, sum((rq=pq)::int) rec_eq_po, sum((rq<pq)::int) rec_lt_po, sum((rq>pq)::int) rec_gt_po,\nsum((bq>pq)::int) qty_over, sum((bq>pq AND rq IS NULL)::int) qty_over_no_rec, sum((bq>pq AND rq>=bq)::int) qty_over_but_received,\nround(sum(CASE WHEN diff>0.005 AND bq>pq THEN diff ELSE 0 END),2) qty_excess,\nround(sum(CASE WHEN diff>0.005 AND bq>pq AND rq IS NULL THEN diff ELSE 0 END),2) qty_excess_no_rec\nFROM x GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "purpose",
   "pay",
   "lines",
   "no_receipt",
   "rec_eq_po",
   "rec_lt_po",
   "rec_gt_po",
   "qty_over",
   "qty_over_no_rec",
   "qty_over_but_received",
   "qty_excess",
   "qty_excess_no_rec"
  ],
  "row_count": 6,
  "rows": [
   [
    "special",
    "full",
    121364,
    121364,
    null,
    null,
    null,
    1290,
    1290,
    0,
    1498042.39,
    1498042.39
   ],
   [
    "special",
    "short",
    4116,
    4116,
    null,
    null,
    null,
    584,
    584,
    0,
    683542.37,
    683542.37
   ],
   [
    "special",
    "unpaid",
    1946,
    1946,
    null,
    null,
    null,
    26,
    26,
    0,
    28555.03,
    28555.03
   ],
   [
    "stock",
    "full",
    446852,
    0,
    446852,
    0,
    0,
    2479,
    0,
    0,
    847795.65,
    0.0
   ],
   [
    "stock",
    "short",
    15162,
    0,
    15162,
    0,
    0,
    1111,
    0,
    0,
    346762.58,
    0.0
   ],
   [
    "stock",
    "unpaid",
    8349,
    0,
    8349,
    0,
    0,
    52,
    0,
    0,
    24630.31,
    0.0
   ]
  ],
  "error": null
 },
 {
  "id": "q234",
  "sql": "SELECT round(89723.67+67315.48,2) a_2024_25, round(168139.99+173933.10,2) b_2024_25, round(76095.59+82798.57,2) c_2024_25, round((89723.67+67315.48)/2,2) a_2024_25_yr, round((333959.25+324047.15)/2,2) all_2024_25_yr, round(1228.0/1290,4) uniq_share",
  "columns": [
   "a_2024_25",
   "b_2024_25",
   "c_2024_25",
   "a_2024_25_yr",
   "all_2024_25_yr",
   "uniq_share"
  ],
  "row_count": 1,
  "rows": [
   [
    157039.15,
    342073.09,
    158894.16,
    78519.58,
    329003.2,
    0.9519
   ]
  ],
  "error": null
 },
 {
  "id": "q193",
  "sql": "WITH sp AS (SELECT po.po_id, po.day, po.branch, p.sku, p.qty FROM erp_purchase_orders po JOIN erp_purchase_order_lines p USING(po_id) WHERE po.purpose='special'),\nsl AS (SELECT o.day, o.branch, l.sku, l.qty_ordered, l.qty_shipped FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) WHERE l.fulfilment='special'),\nm AS (SELECT sp.po_id, sp.sku, sp.qty pq, count(*) n, max(sl.qty_shipped) sh, sum(sl.qty_shipped) shs FROM sp JOIN sl ON sl.day=sp.day AND sl.branch=sp.branch AND sl.sku=sp.sku GROUP BY 1,2,3),\nx AS (SELECT m.*, l.qty bq, l.qty*l.unit_cost-m.pq*l.unit_cost qty_part FROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id) JOIN m ON m.po_id=b.po_id AND m.sku=l.sku\n JOIN finance_vendor_payments vp ON vp.bill_id=b.bill_id AND abs(vp.amount-b.amount)<0.01 WHERE l.qty>m.pq)\nSELECT count(*) qty_over_lines, sum((n=1)::int) unique_match, sum((n=1 AND sh=pq)::int) cust_shipped_eq_po, sum((n=1 AND sh>=bq)::int) cust_shipped_ge_bill,\n sum((n>1 AND shs>=bq)::int) multi_sum_ge_bill\nFROM x",
  "columns": [
   "qty_over_lines",
   "unique_match",
   "cust_shipped_eq_po",
   "cust_shipped_ge_bill",
   "multi_sum_ge_bill"
  ],
  "row_count": 1,
  "rows": [
   [
    1290,
    1228,
    1228,
    0,
    62
   ]
  ],
  "error": null
 },
 {
  "id": "q171",
  "sql": "WITH x AS (SELECT b.bill_id, l.sku, l.qty bq, p.qty pq, l.unit_cost bc, p.unit_cost pc, pr.unit_cost prc, l.qty*l.unit_cost-p.qty*p.unit_cost diff\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id)\nJOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku JOIN erp_products pr ON pr.sku=l.sku\nJOIN finance_vendor_payments vp ON vp.bill_id=b.bill_id AND abs(vp.amount-b.amount)<0.01)\nSELECT count(*) FILTER (WHERE bq>pq) qty_over, count(*) FILTER (WHERE bq>pq AND bq-pq=1) over_by_1,\n round(median((bq-pq)/pq) FILTER (WHERE bq>pq),4) med_qty_ratio_over, count(*) FILTER (WHERE bq>pq AND bc>pc+1e-6) both_over,\n count(*) FILTER (WHERE abs(pc-prc)<1e-6) po_eq_product_cost, count(*) lines,\n count(*) FILTER (WHERE bc>pc+1e-6 AND abs(bc-prc)<1e-6) overcost_eq_product_cost\nFROM x",
  "columns": [
   "qty_over",
   "over_by_1",
   "med_qty_ratio_over",
   "both_over",
   "po_eq_product_cost",
   "lines",
   "overcost_eq_product_cost"
  ],
  "row_count": 1,
  "rows": [
   [
    3769,
    3249,
    0.25,
    119,
    568216,
    568216,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q183",
  "sql": "SELECT count(*) skus, sum((n_cost>1)::int) skus_po_cost_varies, (SELECT count(DISTINCT fulfilment) FROM erp_sales_order_lines) nf, (SELECT string_agg(fulfilment||':'||n, ', ') FROM (SELECT fulfilment, count(*) n FROM erp_sales_order_lines GROUP BY 1)) fulf\nFROM (SELECT sku, count(DISTINCT round(unit_cost,4)) n_cost FROM erp_purchase_order_lines GROUP BY 1)",
  "columns": [
   "skus",
   "skus_po_cost_varies",
   "nf",
   "fulf"
  ],
  "row_count": 1,
  "rows": [
   [
    1096,
    0,
    4,
    "short:155280, transfer:122649, stock:2313827, special:127956"
   ]
  ],
  "error": null
 },
 {
  "id": "q110",
  "sql": "WITH x AS (\nSELECT b.vendor_id, l.sku, b.day, l.unit_cost/p.unit_cost r, (l.unit_cost>p.unit_cost+1e-6) co\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id)\nJOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku),\nf AS (SELECT vendor_id, sku, min(day) fd FROM x WHERE co GROUP BY 1,2),\ns AS (SELECT x.vendor_id, x.sku, count(*) n_after, sum(co::int) co_after,\n  count(DISTINCT round(r,4)) FILTER (WHERE co) distinct_ratios\n  FROM x JOIN f USING(vendor_id, sku) WHERE x.day>f.fd GROUP BY 1,2)\nSELECT count(*) vendor_skus_with_overprice, (SELECT count(DISTINCT vendor_id||'-'||sku) FROM x) all_vendor_skus,\n sum(n_after) lines_after_first, sum(co_after) overpriced_after_first, round(sum(co_after)/sum(n_after),4) share_after,\n (SELECT round(avg(co::int),4) FROM x) base_share,\n sum(CASE WHEN co_after>=0.9*n_after THEN 1 ELSE 0 END) skus_step_like,\n (SELECT round(quantile_cont(r,0.1),4)||' / '||round(quantile_cont(r,0.5),4)||' / '||round(quantile_cont(r,0.9),4) FROM x WHERE co) ratio_p10_p50_p90\nFROM s",
  "columns": [
   "vendor_skus_with_overprice",
   "all_vendor_skus",
   "lines_after_first",
   "overpriced_after_first",
   "share_after",
   "base_share",
   "skus_step_like",
   "ratio_p10_p50_p90"
  ],
  "row_count": 1,
  "rows": [
   [
    1082,
    1096,
    553751,
    13778,
    0.0249,
    0.0249,
    0,
    "1.0351 / 1.0548 / 1.0749"
   ]
  ],
  "error": null
 },
 {
  "id": "q160",
  "sql": "SELECT w.ref_id, count(*), min(w.day), max(w.day), (SELECT count(*) FROM erp_purchase_orders po WHERE po.po_id=w.ref_id) is_po, (SELECT count(*) FROM wms_receipts r WHERE r.receipt_id=w.ref_id) is_receipt FROM wms_inventory_transactions w WHERE reason='return_vendor' GROUP BY 1",
  "columns": [
   "ref_id",
   "count_star()",
   "min(w.\"day\")",
   "max(w.\"day\")",
   "is_po",
   "is_receipt"
  ],
  "row_count": 4,
  "rows": [
   [
    1,
    1012,
    105,
    2499,
    1,
    1
   ],
   [
    4,
    144,
    252,
    2499,
    1,
    1
   ],
   [
    2,
    135,
    252,
    2499,
    1,
    1
   ],
   [
    3,
    174,
    252,
    2520,
    1,
    1
   ]
  ],
  "error": null
 },
 {
  "id": "q166",
  "sql": "SELECT c.vendor_id, v.kind, count(*) n, round(sum(c.amount),2) amt, min(c.day), max(c.day),\n(SELECT count(*) FROM wms_inventory_transactions w WHERE w.reason='return_vendor' AND w.ref_id=c.vendor_id) rv_txns\nFROM finance_vendor_credits c JOIN erp_vendors v USING(vendor_id) GROUP BY 1,2 ORDER BY 1",
  "columns": [
   "vendor_id",
   "kind",
   "n",
   "amt",
   "min(c.\"day\")",
   "max(c.\"day\")",
   "rv_txns"
  ],
  "row_count": 4,
  "rows": [
   [
    1,
    "oem",
    844,
    1502714.62,
    130,
    2520,
    1012
   ],
   [
    2,
    "oem",
    113,
    123794.49,
    275,
    2520,
    135
   ],
   [
    3,
    "oem",
    148,
    171666.88,
    281,
    2520,
    174
   ],
   [
    4,
    "oem",
    129,
    131430.51,
    263,
    2520,
    144
   ]
  ],
  "error": null
 },
 {
  "id": "q169",
  "sql": "WITH rv AS (SELECT * FROM wms_inventory_transactions WHERE reason='return_vendor'),\nc AS (SELECT c.*, EXISTS (SELECT 1 FROM rv WHERE rv.ref_id=c.vendor_id AND rv.sku=c.sku AND abs(-rv.qty_delta-c.qty)<1e-6 AND c.day BETWEEN rv.day AND rv.day+60) m_fix,\n EXISTS (SELECT 1 FROM rv JOIN erp_purchase_orders po ON po.po_id=rv.ref_id WHERE po.vendor_id=c.vendor_id AND rv.sku=c.sku AND abs(-rv.qty_delta-c.qty)<1e-6 AND c.day BETWEEN rv.day AND rv.day+60) m_orig\n FROM finance_vendor_credits c)\nSELECT count(*) n, sum(m_fix::int) matched_fix, round(sum(CASE WHEN NOT m_fix THEN amount END),2) unmatched_fix_amt, sum(m_orig::int) matched_orig, round(sum(CASE WHEN NOT m_orig THEN amount END),2) unmatched_orig_amt,\n(SELECT string_agg(po_id||':v'||vendor_id, ',') FROM erp_purchase_orders WHERE po_id<=4) po1_4\nFROM c",
  "columns": [
   "n",
   "matched_fix",
   "unmatched_fix_amt",
   "matched_orig",
   "unmatched_orig_amt",
   "po1_4"
  ],
  "row_count": 1,
  "rows": [
   [
    1234,
    1234,
    null,
    844,
    426891.88,
    "1:v1,2:v1,3:v1,4:v1"
   ]
  ],
  "error": null
 },
 {
  "id": "q197",
  "sql": "WITH bl AS (SELECT b.bill_id, b.amount bamt, b.freight fr, sum(l.qty*l.unit_cost) lv, sum(p.qty*p.unit_cost) pv\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id) JOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku GROUP BY 1,2,3)\nSELECT count(*) short_bills, sum((abs(vp.amount-(pv+fr))<0.01)::int) paid_po_plus_freight, sum((abs(vp.amount-pv)<0.01)::int) paid_po_only,\n sum((lv-pv>0.005)::int) short_and_overbilled, sum((lv-pv<=0.005)::int) short_not_overbilled,\n round(sum(bamt-vp.amount),2) total_withheld, round(sum(lv-pv),2) total_line_excess\nFROM bl JOIN finance_vendor_payments vp USING(bill_id) WHERE abs(vp.amount-bamt)>=0.01",
  "columns": [
   "short_bills",
   "paid_po_plus_freight",
   "paid_po_only",
   "short_and_overbilled",
   "short_not_overbilled",
   "total_withheld",
   "total_line_excess"
  ],
  "row_count": 1,
  "rows": [
   [
    12026,
    5566,
    12026,
    5911,
    6115,
    2249435.22,
    1371706.45
   ]
  ],
  "error": null
 },
 {
  "id": "q202",
  "sql": "WITH bl AS (SELECT b.bill_id, b.amount bamt, b.freight fr, sum(l.qty*l.unit_cost) lv, sum(p.qty*p.unit_cost) pv\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id) JOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku GROUP BY 1,2,3),\ny AS (SELECT bl.*, abs(vp.amount-bamt)>=0.01 is_short, lv-pv>0.005 is_over, fr>0.005 hasfr FROM bl JOIN finance_vendor_payments vp USING(bill_id))\nSELECT is_over, hasfr, count(*) paid_bills, sum(is_short::int) short_paid, round(avg(is_short::int),4) short_share FROM y GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "is_over",
   "hasfr",
   "paid_bills",
   "short_paid",
   "short_share"
  ],
  "row_count": 4,
  "rows": [
   [
    false,
    false,
    322260,
    0,
    0.0
   ],
   [
    false,
    true,
    20329,
    6115,
    0.3008
   ],
   [
    true,
    false,
    18639,
    5566,
    0.2986
   ],
   [
    true,
    true,
    1221,
    345,
    0.2826
   ]
  ],
  "error": null
 },
 {
  "id": "q126",
  "sql": "WITH bl AS (\nSELECT b.bill_id, b.po_id, d.year, b.amount, sum(l.qty*l.unit_cost) lv, sum(p.qty*p.unit_cost) pv\nFROM finance_vendor_bill_lines l JOIN finance_vendor_bills b USING(bill_id)\nJOIN erp_purchase_order_lines p ON p.po_id=b.po_id AND p.sku=l.sku JOIN dim_date d ON d.day=b.day\nGROUP BY 1,2,3,4),\ndup AS (SELECT po_id FROM finance_vendor_bills GROUP BY 1 HAVING count(*)>1),\ny AS (SELECT bl.*, CASE WHEN abs(vp.amount-bl.amount)<0.01 THEN 'full' ELSE 'short' END pay, bl.po_id IN (SELECT po_id FROM dup) isdup\n FROM bl JOIN finance_vendor_payments vp USING(bill_id) WHERE lv-pv>0.005)\nSELECT year, count(*) FILTER (WHERE pay='full') full_bills, count(*) FILTER (WHERE pay='short') short_bills,\n round(count(*) FILTER (WHERE pay='short')/count(*),4) caught_share,\n count(*) FILTER (WHERE pay='full' AND isdup) full_on_dup_po\nFROM y GROUP BY ROLLUP(year) ORDER BY year NULLS LAST",
  "columns": [
   "year",
   "full_bills",
   "short_bills",
   "caught_share",
   "full_on_dup_po"
  ],
  "row_count": 11,
  "rows": [
   [
    2016,
    1570,
    657,
    0.295,
    17
   ],
   [
    2017,
    1428,
    543,
    0.2755,
    9
   ],
   [
    2018,
    1434,
    630,
    0.3052,
    10
   ],
   [
    2019,
    1368,
    590,
    0.3013,
    13
   ],
   [
    2020,
    1386,
    629,
    0.3122,
    14
   ],
   [
    2021,
    1337,
    601,
    0.3101,
    11
   ],
   [
    2022,
    1377,
    569,
    0.2924,
    7
   ],
   [
    2023,
    1244,
    522,
    0.2956,
    6
   ],
   [
    2024,
    1408,
    586,
    0.2939,
    11
   ],
   [
    2025,
    1397,
    584,
    0.2948,
    4
   ],
   [
    null,
    13949,
    5911,
    0.2976,
    102
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
