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
 "id": "F5",
 "hypothesis": "H5",
 "title": "On hand-keyed orders a fixed share of shipped lines never reaches an invoice: about $285K a year at order price ($72K gross margin), worst at the counter, never billed later. The part still worth chasing is the recent tail of about $271K",
 "conclusion": "The hypothesis holds, with a narrower framing of the money. Observed: from 2016 to 2025 (ship days 1-2520), 4,985 of 2,563,485 shipped order lines (0.194%) have no invoice line (q286). By channel the rate is counter 1.124% (2,500/222,392), email 0.155% (1,850/1,195,113), phone 0.148% (635/429,969), and 0 of 461,656 EDI and 0 of 254,355 web lines (q286). The link between invoice lines and order lines is clean. Across all 2,558,500 invoice lines there are 0 null, orphan or duplicate line_ids, and 0 lines whose quantity, price, SKU or order differs from its order line (q255, q277). So the gap is real and not a linkage artefact. For all 4,751 non-special lines, the WMS sale quantity includes the uninvoiced line, so the goods left (q275). Nothing else covers these lines. There are no re-bills on other lines (q229), no consolidated or re-used-PO invoices (q280, q282), every payment ties to an invoice, and 0 of 1,388,665 invoices are overpaid (q260, q262). For the 3,655 lines whose order got an invoice within a day of shipment, all 4,009 such invoices have a header within 3 cents of their line sum, and in 0 cases does the gap equal the missing line. 3,956 were paid at header amount (q326, q329). Sizing for 2016-2024: 4,495 lines, 2,569,213.83 at order price. That is 285,468.20 a year (yearly range 252,827.81 to 348,493.66), 0.1948% of billed revenue, 213,944.60 a year at cost and 71,523.61 a year of gross margin (q324). Interpretation: drops look like a random per-line loss at a fixed rate per manual channel. Per-rep dispersion matches chance (q268), and dropped lines look like billed lines on value, markdown and price (q269), order size and line position (q259), and month, trade and terms (q272). This points to an order-to-invoice step on manually keyed orders, especially counter, not to people, customers or products. Recoverable money is the recent tail, not the cumulative total. In the last 252 operating days that is 490 lines worth 271,314.82 across 408 customers, of which 156 lines worth 90,763.66 fall in the last 85 days (q290). A small second leak: all 16 uninvoiced lines that were later returned (4,618.19) got credit memos, so customers were credited for goods never billed (q290, q291).",
 "dollars_a_year": 285468.2,
 "size_query": "q324",
 "claims": [
  {
   "text": "4,985 of 2,563,485 shipped lines in days 1-2520 (0.194%) have no invoice line. By channel: counter 1.124% (2,500/222,392), email 0.155% (1,850/1,195,113), phone 0.148% (635/429,969), EDI 0/461,656, web 0/254,355.",
   "queries": [
    "q286",
    "q232"
   ]
  },
  {
   "text": "The rate is flat by year (0.181-0.216%) and branch (0.166-0.219%), with no $0-price lines. 2025 in-window has 490 lines worth 271,314.82, in line with other years. A further 947 lines (932,590.69) ship after day 2520 and are excluded as end effects.",
   "queries": [
    "q232",
    "q224",
    "q226",
    "q290"
   ]
  },
  {
   "text": "The linkage is clean. Across 2,558,500 invoice lines: 0 null, orphan or duplicate line_ids, 0 invoices without an order or without lines, and 0 lines whose qty, price, SKU or order differs from the order line or that bill unshipped lines. The 1,303 lines where amount differs from qty x price net to -74.47 (ratio 0.9771-1.0185).",
   "queries": [
    "q255",
    "q277",
    "q257"
   ]
  },
  {
   "text": "The goods left. For all 4,751 non-special uninvoiced lines, the WMS sale qty equals the order's total shipped for the SKU including the uninvoiced line, in 0 cases the total excluding it. 4,529 moved on the ship day. The 234 special-order lines never touch WMS and cannot be confirmed this way.",
   "queries": [
    "q275",
    "q226"
   ]
  },
  {
   "text": "Not billed anywhere else. The 69 same-order-and-SKU matches are separate order lines billed only for their own qty. Of the 1,139 lines on orders with no invoice, 8 share a customer PO with another invoice, and all 9 matching invoices are other orders' invoices with no line for that SKU. 4 have a same-amount invoice within 60 days. All 1,366,817 payments (751,147 check, 615,670 ACH) tie to an existing invoice, and 0 of 1,388,665 invoices are overpaid.",
   "queries": [
    "q229",
    "q280",
    "q282",
    "q260",
    "q262"
   ]
  },
  {
   "text": "Re-verified: 3,655 lines sit on orders with an invoice within 1 day of shipment. All 4,009 of those invoices have a header within 3 cents of their line sum: 3,998 within 2 cents, and the other 11 differ by -0.02 to 0.03, never by the missing line's value. 3,956 were paid at header amount and 53 are unpaid.",
   "queries": [
    "q326",
    "q329"
   ]
  },
  {
   "text": "Random-looking drops. The per-rep chi-square is 36.5 (counter), 52.5 (email) and 53.8 (phone) across 48 reps each, with 0 reps beyond 3 SD. Counter uninvoiced vs invoiced: median value 235.64 vs 252.12, price-to-list 0.8361 vs 0.8363. Counter rate is 1.127%, 1.088% and 1.166% for 1, 2-3 and 4+ line orders, 0.975-1.212% by month, and 1.107-1.186% by trade.",
   "queries": [
    "q268",
    "q269",
    "q259",
    "q272"
   ]
  },
  {
   "text": "Cash at the counter is unlikely. Payments hold only check and ACH. Counter rate by terms is 1.054% at 0 days (244/23,156), 1.120% at 30 (1,824/162,907) and 1.189% at 45 (432/36,329), so cash-terms customers are not higher.",
   "queries": [
    "q260",
    "q272"
   ]
  },
  {
   "text": "Sizing for 2016-2024: 4,495 lines and 2,569,213.83 at order price, or 285,468.20 a year (range 252,827.81-348,493.66). That is 0.1948% of billed revenue, 213,944.60 a year at cost and 71,523.61 a year of gross margin. By channel per year: counter 137,555.05, email 109,830.29, phone 38,082.86.",
   "queries": [
    "q324",
    "q286"
   ]
  },
  {
   "text": "Recent tail and returns. Last 252 operating days: 490 lines, 271,314.82 net of returns, 408 customers. Last 85: 156 lines, 90,763.66. Over days 1-2520, 16 uninvoiced lines were returned (4,618.19), and all 16 got a matching credit memo.",
   "queries": [
    "q290",
    "q291"
   ]
  }
 ],
 "confidence": "high",
 "not_evidence_of": "Any person's fault or misconduct: rep-level counts match chance across all 48 inside reps (q268). Nor is it proof that the full 2,569,213.83 (2016-2024 at order price, q324) is lost cash. Collection through a system outside these tables can't be seen, though there is no cash method and no higher rate for cash-terms customers (q260, q272). The economic loss is the goods given away. At cost that is 213,944.60 a year, and the forgone margin is 71,523.61 a year (q324). The finding also does not show how much is still collectible, and it does not identify the mechanism.",
 "could_not_tell": "Whether any of these sales were collected outside the ERP and accounting tables (cash, manual invoices), because there is no POS or cash ledger. Why the line was dropped, because there is no invoicing or error log. How much of the recent tail is recoverable, which depends on customer terms and relationships. Whether the 234 special-order lines physically shipped, because special orders don't move through WMS.",
 "next_step": "Give accounting the 156 lines (90,763.66) shipped in the last 85 operating days and the 490 lines (271,314.82, 408 customers) from the last 252 (q290). Confirm none were billed outside the ERP, then back-bill where terms allow. Add a daily exception report of shipped lines with no invoice line, keyed on line_id, and block credit memos against lines that were never invoiced (q291). Trace a sample of counter orders end to end to find where lines drop between order entry and invoice generation.",
 "incomplete": false
}

[
 {
  "id": "q286",
  "sql": "WITH s AS (\n SELECT l.*, o.channel, o.customer_id, d.year, NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=l.ship_day\n WHERE l.qty_shipped>0 AND l.ship_day<=2520)\nSELECT channel, count(*) shipped, sum(uninv::int) un, round(100.0*sum(uninv::int)/count(*),3) pct,\n round(sum(CASE WHEN uninv AND year BETWEEN 2016 AND 2024 THEN qty_shipped*unit_price END),2) v_16_24,\n round(sum(CASE WHEN uninv AND year BETWEEN 2016 AND 2024 THEN qty_shipped*unit_price END)/9,2) v_per_yr,\n round(sum(CASE WHEN uninv AND year BETWEEN 2016 AND 2024 THEN qty_shipped*(unit_price-unit_cost) END)/9,2) margin_per_yr\nFROM s GROUP BY ROLLUP(channel) ORDER BY 1",
  "columns": [
   "channel",
   "shipped",
   "un",
   "pct",
   "v_16_24",
   "v_per_yr",
   "margin_per_yr"
  ],
  "row_count": 6,
  "rows": [
   [
    "counter",
    222392,
    2500,
    1.124,
    1237995.49,
    137555.05,
    35680.21
   ],
   [
    "edi",
    461656,
    0,
    0.0,
    null,
    null,
    null
   ],
   [
    "email",
    1195113,
    1850,
    0.155,
    988472.57,
    109830.29,
    26418.76
   ],
   [
    "phone",
    429969,
    635,
    0.148,
    342745.77,
    38082.86,
    9424.63
   ],
   [
    "web",
    254355,
    0,
    0.0,
    null,
    null,
    null
   ],
   [
    null,
    2563485,
    4985,
    0.194,
    2569213.83,
    285468.2,
    71523.61
   ]
  ],
  "error": null
 },
 {
  "id": "q232",
  "sql": "WITH s AS (\n SELECT l.*, o.branch, o.channel, o.customer_id, d.year,\n  NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=l.ship_day\n WHERE l.qty_shipped>0 AND l.ship_day<=2520)\nSELECT 'branch' dim, branch k, count(*) shipped, sum(uninv::int) un, round(100.0*sum(uninv::int)/count(*),3) pct FROM s GROUP BY branch\nUNION ALL SELECT 'channel', channel, count(*), sum(uninv::int), round(100.0*sum(uninv::int)/count(*),3) FROM s GROUP BY channel\nUNION ALL SELECT 'fulfil', fulfilment, count(*), sum(uninv::int), round(100.0*sum(uninv::int)/count(*),3) FROM s GROUP BY fulfilment\nUNION ALL SELECT 'year', year::varchar, count(*), sum(uninv::int), round(100.0*sum(uninv::int)/count(*),3) FROM s GROUP BY year\nUNION ALL SELECT 'all','all', count(*), sum(uninv::int), round(100.0*sum(uninv::int)/count(*),3) FROM s\nORDER BY 1,2",
  "columns": [
   "dim",
   "k",
   "shipped",
   "un",
   "pct"
  ],
  "row_count": 31,
  "rows": [
   [
    "all",
    "all",
    2563485,
    4985,
    0.194
   ],
   [
    "branch",
    "Akron",
    113395,
    208,
    0.183
   ],
   [
    "branch",
    "Cincinnati",
    319127,
    659,
    0.207
   ],
   [
    "branch",
    "Cleveland",
    346133,
    708,
    0.205
   ],
   [
    "branch",
    "Columbus",
    313435,
    591,
    0.189
   ],
   [
    "branch",
    "Dayton",
    129769,
    252,
    0.194
   ],
   [
    "branch",
    "Fort Wayne",
    71740,
    157,
    0.219
   ],
   [
    "branch",
    "Indianapolis",
    303809,
    599,
    0.197
   ],
   [
    "branch",
    "Lexington",
    76693,
    164,
    0.214
   ],
   [
    "branch",
    "Louisville",
    191297,
    337,
    0.176
   ],
   [
    "branch",
    "Pittsburgh",
    369730,
    731,
    0.198
   ],
   [
    "branch",
    "Toledo",
    107537,
    178,
    0.166
   ],
   [
    "branch",
    "Troy",
    220820,
    401,
    0.182
   ],
   [
    "channel",
    "counter",
    222392,
    2500,
    1.124
   ],
   [
    "channel",
    "edi",
    461656,
    0,
    0.0
   ],
   [
    "channel",
    "email",
    1195113,
    1850,
    0.155
   ],
   [
    "channel",
    "phone",
    429969,
    635,
    0.148
   ],
   [
    "channel",
    "web",
    254355,
    0,
    0.0
   ],
   [
    "fulfil",
    "special",
    127184,
    234,
    0.184
   ],
   [
    "fulfil",
    "stock",
    2313827,
    4529,
    0.196
   ],
   [
    "fulfil",
    "transfer",
    122474,
    222,
    0.181
   ],
   [
    "year",
    "2016",
    245008,
    443,
    0.181
   ],
   [
    "year",
    "2017",
    250795,
    480,
    0.191
   ],
   [
    "year",
    "2018",
    289929,
    627,
    0.216
   ],
   [
    "year",
    "2019",
    277756,
    554,
    0.199
   ],
   [
    "year",
    "2020",
    261042,
    491,
    0.188
   ],
   [
    "year",
    "2021",
    260549,
    494,
    0.19
   ],
   [
    "year",
    "2022",
    267816,
    512,
    0.191
   ],
   [
    "year",
    "2023",
    226265,
    434,
    0.192
   ],
   [
    "year",
    "2024",
    230454,
    460,
    0.2
   ],
   [
    "year",
    "2025",
    253871,
    490,
    0.193
   ]
  ],
  "error": null
 },
 {
  "id": "q224",
  "sql": "WITH u AS (\n SELECT l.*, d.year FROM erp_sales_order_lines l JOIN dim_date d ON d.day=l.ship_day\n WHERE l.qty_shipped>0 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id))\nSELECT year, count(*) n, round(sum(qty_shipped*unit_price),2) value, sum(CASE WHEN unit_price<=0 THEN 1 ELSE 0 END) zero_price,\n sum(CASE WHEN fulfilment='special' THEN 1 ELSE 0 END) special, min(ship_day) minday, max(ship_day) maxday\nFROM u GROUP BY year ORDER BY year",
  "columns": [
   "year",
   "n",
   "value",
   "zero_price",
   "special",
   "minday",
   "maxday"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    443,
    262163.35,
    0,
    44,
    1,
    252
   ],
   [
    2017,
    480,
    252827.81,
    0,
    16,
    253,
    504
   ],
   [
    2018,
    627,
    348493.66,
    0,
    26,
    505,
    756
   ],
   [
    2019,
    554,
    305574.1,
    0,
    24,
    757,
    1008
   ],
   [
    2020,
    491,
    253161.6,
    0,
    20,
    1009,
    1260
   ],
   [
    2021,
    494,
    318581.31,
    0,
    20,
    1261,
    1512
   ],
   [
    2022,
    512,
    277994.58,
    0,
    13,
    1513,
    1764
   ],
   [
    2023,
    434,
    253180.58,
    0,
    15,
    1765,
    2016
   ],
   [
    2024,
    460,
    297236.84,
    0,
    21,
    2017,
    2268
   ],
   [
    2025,
    490,
    271314.82,
    0,
    35,
    2269,
    2520
   ]
  ],
  "error": null
 },
 {
  "id": "q226",
  "sql": "WITH u AS (\n SELECT l.* FROM erp_sales_order_lines l\n WHERE l.qty_shipped>0 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id))\nSELECT (ship_day IS NULL) null_ship, (ship_day>2520) after_end, count(*) n, round(sum(qty_shipped*unit_price),2) v,\n sum(CASE WHEN EXISTS (SELECT 1 FROM finance_invoices i JOIN finance_invoice_lines il ON il.invoice_id=i.invoice_id WHERE i.order_id=u.order_id AND il.sku=u.sku) THEN 1 ELSE 0 END) rebilled_same_order_sku,\n sum(CASE WHEN EXISTS (SELECT 1 FROM finance_invoices i WHERE i.order_id=u.order_id) THEN 1 ELSE 0 END) order_has_invoice,\n sum(CASE WHEN EXISTS (SELECT 1 FROM wms_inventory_transactions w WHERE w.ref_id=u.order_id AND w.sku=u.sku AND w.reason='sale') THEN 1 ELSE 0 END) wms_sale\nFROM u GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "null_ship",
   "after_end",
   "n",
   "v",
   "rebilled_same_order_sku",
   "order_has_invoice",
   "wms_sale"
  ],
  "row_count": 2,
  "rows": [
   [
    false,
    false,
    4985,
    2840528.65,
    69,
    3846,
    4751
   ],
   [
    false,
    true,
    947,
    932590.69,
    2,
    617,
    176
   ]
  ],
  "error": null
 },
 {
  "id": "q290",
  "sql": "WITH u AS (SELECT l.*, o.customer_id FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\nr AS (SELECT u.line_id, sum(r.qty) rq FROM u JOIN erp_returns r ON r.line_id=u.line_id GROUP BY 1)\nSELECT count(*) lines, round(sum(qty_shipped*unit_price),2) gross,\n count(r.line_id) returned_lines, round(sum(coalesce(r.rq,0)*unit_price),2) returned_value,\n round(sum((qty_shipped-coalesce(r.rq,0))*unit_price),2) net_of_returns,\n sum(CASE WHEN ship_day>2520-252 THEN 1 ELSE 0 END) last252_lines, round(sum(CASE WHEN ship_day>2520-252 THEN (qty_shipped-coalesce(r.rq,0))*unit_price END),2) last252_value,\n sum(CASE WHEN ship_day>2520-85 THEN 1 ELSE 0 END) last85_lines, round(sum(CASE WHEN ship_day>2520-85 THEN (qty_shipped-coalesce(r.rq,0))*unit_price END),2) last85_value,\n count(DISTINCT CASE WHEN ship_day>2520-252 THEN customer_id END) last252_customers\nFROM u LEFT JOIN r USING(line_id)",
  "columns": [
   "lines",
   "gross",
   "returned_lines",
   "returned_value",
   "net_of_returns",
   "last252_lines",
   "last252_value",
   "last85_lines",
   "last85_value",
   "last252_customers"
  ],
  "row_count": 1,
  "rows": [
   [
    4985,
    2840528.65,
    16,
    4618.19,
    2835910.46,
    490,
    271314.82,
    156,
    90763.66,
    408
   ]
  ],
  "error": null
 },
 {
  "id": "q255",
  "sql": "SELECT count(*) n, sum(CASE WHEN line_id IS NULL THEN 1 ELSE 0 END) null_line,\n sum(CASE WHEN line_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM erp_sales_order_lines l WHERE l.line_id=il.line_id) THEN 1 ELSE 0 END) orphan_line,\n sum(CASE WHEN abs(amount-qty*unit_price)>0.03 THEN 1 ELSE 0 END) amt_ne_qtyprice,\n (SELECT count(*) FROM (SELECT line_id FROM finance_invoice_lines GROUP BY 1 HAVING count(*)>1)) dup_line_ids,\n (SELECT count(*) FROM finance_invoices WHERE order_id IS NULL OR order_id NOT IN (SELECT order_id FROM erp_sales_orders)) inv_no_order,\n (SELECT count(*) FROM finance_invoices i WHERE NOT EXISTS (SELECT 1 FROM finance_invoice_lines il2 WHERE il2.invoice_id=i.invoice_id)) inv_no_lines\nFROM finance_invoice_lines il",
  "columns": [
   "n",
   "null_line",
   "orphan_line",
   "amt_ne_qtyprice",
   "dup_line_ids",
   "inv_no_order",
   "inv_no_lines"
  ],
  "row_count": 1,
  "rows": [
   [
    2558500,
    0,
    0,
    1303,
    0,
    0,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q277",
  "sql": "SELECT count(*) n, sum(CASE WHEN il.qty>l.qty_shipped THEN 1 ELSE 0 END) qty_over, sum(CASE WHEN il.qty<l.qty_shipped THEN 1 ELSE 0 END) qty_under,\n sum(CASE WHEN abs(il.unit_price-l.unit_price)>0.005 THEN 1 ELSE 0 END) price_diff, sum(CASE WHEN il.sku<>l.sku THEN 1 ELSE 0 END) sku_diff,\n sum(CASE WHEN i.order_id<>l.order_id THEN 1 ELSE 0 END) order_diff, sum(CASE WHEN l.qty_shipped=0 OR l.qty_shipped IS NULL THEN 1 ELSE 0 END) billed_unshipped\nFROM finance_invoice_lines il JOIN erp_sales_order_lines l USING(line_id) JOIN finance_invoices i USING(invoice_id)",
  "columns": [
   "n",
   "qty_over",
   "qty_under",
   "price_diff",
   "sku_diff",
   "order_diff",
   "billed_unshipped"
  ],
  "row_count": 1,
  "rows": [
   [
    2558500,
    0,
    0,
    0,
    0,
    0,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q257",
  "sql": "WITH u AS (SELECT l.* FROM erp_sales_order_lines l WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\nx AS (SELECT il.*, i.order_id, ol.qty_shipped oq, ol.unit_price op FROM finance_invoice_lines il JOIN finance_invoices i USING(invoice_id) JOIN erp_sales_order_lines ol ON ol.line_id=il.line_id WHERE abs(il.amount-il.qty*il.unit_price)>0.03)\nSELECT count(*) n, sum(CASE WHEN order_id IN (SELECT order_id FROM u) THEN 1 ELSE 0 END) on_u_orders,\n sum(CASE WHEN qty<>oq THEN 1 ELSE 0 END) qty_diff, sum(CASE WHEN abs(unit_price-op)>0.005 THEN 1 ELSE 0 END) price_diff,\n round(sum(amount-qty*unit_price),2) net_diff, round(median(amount/(qty*unit_price)),4) med_ratio, round(min(amount/(qty*unit_price)),4) mn, round(max(amount/(qty*unit_price)),4) mx\nFROM x",
  "columns": [
   "n",
   "on_u_orders",
   "qty_diff",
   "price_diff",
   "net_diff",
   "med_ratio",
   "mn",
   "mx"
  ],
  "row_count": 1,
  "rows": [
   [
    1303,
    2,
    0,
    0,
    -74.47,
    0.9999,
    0.9771,
    1.0185
   ]
  ],
  "error": null
 },
 {
  "id": "q275",
  "sql": "WITH u AS (SELECT l.* FROM erp_sales_order_lines l WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND l.fulfilment<>'special' AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\nos AS (SELECT l.order_id, l.sku, sum(l.qty_shipped) shipped_all FROM erp_sales_order_lines l WHERE l.order_id IN (SELECT order_id FROM u) GROUP BY 1,2),\nw AS (SELECT ref_id order_id, sku, -sum(qty_delta) wq, min(day) wday FROM wms_inventory_transactions WHERE reason='sale' AND ref_id IN (SELECT order_id FROM u) GROUP BY 1,2)\nSELECT count(*) n, sum(CASE WHEN w.wq IS NULL THEN 1 ELSE 0 END) no_wms, sum(CASE WHEN abs(w.wq-os.shipped_all)<0.001 THEN 1 ELSE 0 END) wms_eq_all_shipped,\n sum(CASE WHEN abs(w.wq-(os.shipped_all-u.qty_shipped))<0.001 THEN 1 ELSE 0 END) wms_eq_excl_this,\n sum(CASE WHEN w.wday=u.ship_day THEN 1 ELSE 0 END) wms_same_day\nFROM u JOIN os USING(order_id, sku) LEFT JOIN w USING(order_id, sku)",
  "columns": [
   "n",
   "no_wms",
   "wms_eq_all_shipped",
   "wms_eq_excl_this",
   "wms_same_day"
  ],
  "row_count": 1,
  "rows": [
   [
    4751,
    0,
    4751,
    0,
    4529
   ]
  ],
  "error": null
 },
 {
  "id": "q229",
  "sql": "WITH u AS (\n SELECT l.* FROM erp_sales_order_lines l\n WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\nr AS (SELECT u.line_id, u.qty_shipped, il.line_id other_line, il.qty, ol.qty_shipped other_shipped\n FROM u JOIN finance_invoices i ON i.order_id=u.order_id JOIN finance_invoice_lines il ON il.invoice_id=i.invoice_id AND il.sku=u.sku\n LEFT JOIN erp_sales_order_lines ol ON ol.line_id=il.line_id)\nSELECT count(*) pairs, count(DISTINCT line_id) lines, sum(CASE WHEN other_line<>line_id THEN 1 ELSE 0 END) other_line_diff,\n sum(CASE WHEN qty=other_shipped THEN 1 ELSE 0 END) other_billed_own_qty,\n sum(CASE WHEN qty=other_shipped+qty_shipped THEN 1 ELSE 0 END) billed_combined\nFROM r",
  "columns": [
   "pairs",
   "lines",
   "other_line_diff",
   "other_billed_own_qty",
   "billed_combined"
  ],
  "row_count": 1,
  "rows": [
   [
    70,
    69,
    70,
    70,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q280",
  "sql": "WITH u AS (SELECT l.*, o.customer_id, o.customer_po, o.channel FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\nn AS (SELECT * FROM u WHERE NOT EXISTS (SELECT 1 FROM finance_invoices i WHERE i.order_id=u.order_id))\nSELECT count(*) lines, count(DISTINCT order_id) orders, sum(CASE WHEN customer_po IS NOT NULL AND customer_po<>'' THEN 1 ELSE 0 END) has_po,\n sum(CASE WHEN EXISTS (SELECT 1 FROM finance_invoices i WHERE i.customer_po=n.customer_po AND i.customer_id=n.customer_id AND n.customer_po<>'') THEN 1 ELSE 0 END) po_on_other_inv,\n sum(CASE WHEN EXISTS (SELECT 1 FROM finance_invoices i WHERE i.customer_id=n.customer_id AND i.day BETWEEN n.ship_day AND n.ship_day+60 AND abs(i.amount-n.qty_shipped*n.unit_price)<0.01) THEN 1 ELSE 0 END) same_amt_inv_60d,\n sum(CASE WHEN EXISTS (SELECT 1 FROM finance_credit_memos m WHERE m.order_id=n.order_id) THEN 1 ELSE 0 END) memo\nFROM n",
  "columns": [
   "lines",
   "orders",
   "has_po",
   "po_on_other_inv",
   "same_amt_inv_60d",
   "memo"
  ],
  "row_count": 1,
  "rows": [
   [
    1139,
    1135,
    684,
    8,
    4,
    3
   ]
  ],
  "error": null
 },
 {
  "id": "q282",
  "sql": "WITH u AS (SELECT l.*, o.customer_id, o.customer_po FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) AND NOT EXISTS (SELECT 1 FROM finance_invoices i WHERE i.order_id=l.order_id))\nSELECT u.line_id, u.order_id, u.sku, u.qty_shipped, u.ship_day, i.invoice_id, i.order_id inv_order, i.day, i.amount,\n (SELECT count(*) FROM finance_invoice_lines il WHERE il.invoice_id=i.invoice_id AND il.sku=u.sku) same_sku_lines,\n (SELECT sum(qty_shipped*unit_price) FROM erp_sales_order_lines l2 WHERE l2.order_id=i.order_id) other_order_value\nFROM u JOIN finance_invoices i ON i.customer_po=u.customer_po AND i.customer_id=u.customer_id WHERE u.customer_po<>''",
  "columns": [
   "line_id",
   "order_id",
   "sku",
   "qty_shipped",
   "ship_day",
   "invoice_id",
   "inv_order",
   "day",
   "amount",
   "same_sku_lines",
   "other_order_value"
  ],
  "row_count": 9,
  "rows": [
   [
    964384,
    448718,
    "REF150012",
    2.0,
    822,
    1328365,
    1214056,
    2406,
    462.52,
    0,
    462.51519999999994
   ],
   [
    1766428,
    822449,
    "REF150006",
    5.0,
    1553,
    1386051,
    1263465,
    2518,
    34.79,
    0,
    3731.0967
   ],
   [
    1766428,
    822449,
    "REF150006",
    5.0,
    1553,
    1385752,
    1263465,
    2517,
    3696.3,
    0,
    3731.0967
   ],
   [
    684058,
    318374,
    "NOR-CO035143A",
    1.0,
    591,
    822754,
    752311,
    1455,
    1386.17,
    0,
    1386.1742
   ],
   [
    2517981,
    1172200,
    "BLO000021",
    1.0,
    2305,
    668004,
    611661,
    1160,
    1464.52,
    0,
    1464.5205
   ],
   [
    2424112,
    1129003,
    "AIR080003",
    3.0,
    2254,
    1190733,
    1088998,
    2145,
    731.14,
    0,
    731.1434
   ],
   [
    1985107,
    924115,
    "CON020017",
    4.0,
    1774,
    254444,
    231565,
    480,
    40.91,
    0,
    40.9053
   ],
   [
    1643488,
    765245,
    "REC160021",
    1.0,
    1481,
    294031,
    268177,
    518,
    282.81,
    0,
    282.8052
   ],
   [
    1900295,
    884841,
    "REF150022",
    2.0,
    1714,
    1374854,
    1249344,
    2506,
    257.36,
    0,
    257.3636
   ]
  ],
  "error": null
 },
 {
  "id": "q260",
  "sql": "SELECT method, count(*) n, sum(CASE WHEN invoice_id IS NULL THEN 1 ELSE 0 END) no_inv,\n sum(CASE WHEN invoice_id IS NOT NULL AND invoice_id NOT IN (SELECT invoice_id FROM finance_invoices) THEN 1 ELSE 0 END) orphan_inv,\n round(sum(amount),2) amt FROM finance_customer_payments GROUP BY 1 ORDER BY 2 DESC",
  "columns": [
   "method",
   "n",
   "no_inv",
   "orphan_inv",
   "amt"
  ],
  "row_count": 2,
  "rows": [
   [
    "check",
    751147,
    0,
    0,
    791630062.2
   ],
   [
    "ACH",
    615670,
    0,
    0,
    648954414.28
   ]
  ],
  "error": null
 },
 {
  "id": "q262",
  "sql": "WITH p AS (SELECT invoice_id, sum(amount) paid, count(*) np FROM finance_customer_payments GROUP BY 1)\nSELECT count(*) invoices, sum(CASE WHEN p.paid IS NULL THEN 1 ELSE 0 END) unpaid,\n sum(CASE WHEN p.paid>i.amount+0.01 THEN 1 ELSE 0 END) overpaid, round(sum(CASE WHEN p.paid>i.amount+0.01 THEN p.paid-i.amount END),2) overpaid_amt,\n sum(CASE WHEN p.paid<i.amount-0.01 THEN 1 ELSE 0 END) underpaid\nFROM finance_invoices i LEFT JOIN p USING(invoice_id)",
  "columns": [
   "invoices",
   "unpaid",
   "overpaid",
   "overpaid_amt",
   "underpaid"
  ],
  "row_count": 1,
  "rows": [
   [
    1388665,
    21848,
    0,
    null,
    0
   ]
  ],
  "error": null
 },
 {
  "id": "q326",
  "sql": "WITH u AS (SELECT l.* FROM erp_sales_order_lines l WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\ni AS (SELECT DISTINCT i.invoice_id, i.amount FROM u JOIN finance_invoices i ON i.order_id=u.order_id AND abs(i.day-u.ship_day)<=1),\nh AS (SELECT i.invoice_id, i.amount, (SELECT sum(amount) FROM finance_invoice_lines il WHERE il.invoice_id=i.invoice_id) lsum,\n (SELECT sum(amount) FROM finance_customer_payments p WHERE p.invoice_id=i.invoice_id) paid FROM i)\nSELECT (SELECT count(*) FROM u WHERE EXISTS (SELECT 1 FROM finance_invoices i2 WHERE i2.order_id=u.order_id AND abs(i2.day-u.ship_day)<=1)) lines_with_inv,\n count(*) invoices, sum(CASE WHEN abs(amount-lsum)<0.02 THEN 1 ELSE 0 END) header_eq_lines,\n sum(CASE WHEN abs(paid-amount)<0.02 THEN 1 ELSE 0 END) paid_at_header, sum(CASE WHEN paid IS NULL THEN 1 ELSE 0 END) unpaid\nFROM h",
  "columns": [
   "lines_with_inv",
   "invoices",
   "header_eq_lines",
   "paid_at_header",
   "unpaid"
  ],
  "row_count": 1,
  "rows": [
   [
    3655,
    4009,
    3998,
    3956,
    53
   ]
  ],
  "error": null
 },
 {
  "id": "q329",
  "sql": "WITH u AS (SELECT l.* FROM erp_sales_order_lines l WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id)),\ni AS (SELECT DISTINCT i.invoice_id, i.order_id, i.amount FROM u JOIN finance_invoices i ON i.order_id=u.order_id AND abs(i.day-u.ship_day)<=1),\nh AS (SELECT i.*, (SELECT sum(amount) FROM finance_invoice_lines il WHERE il.invoice_id=i.invoice_id) lsum,\n (SELECT sum(qty_shipped*unit_price) FROM u WHERE u.order_id=i.order_id) uval FROM i)\nSELECT count(*) n_diff, round(min(amount-lsum),2) min_d, round(max(amount-lsum),2) max_d,\n sum(CASE WHEN abs(amount-lsum-uval)<1 THEN 1 ELSE 0 END) diff_eq_missing_line,\n sum(CASE WHEN abs(amount-lsum)<0.05 THEN 1 ELSE 0 END) within_5c\nFROM h WHERE abs(amount-lsum)>=0.02",
  "columns": [
   "n_diff",
   "min_d",
   "max_d",
   "diff_eq_missing_line",
   "within_5c"
  ],
  "row_count": 1,
  "rows": [
   [
    11,
    -0.02,
    0.03,
    0,
    11
   ]
  ],
  "error": null
 },
 {
  "id": "q268",
  "sql": "WITH s AS (\n SELECT o.taken_by, o.channel, NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id)\n WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND o.channel IN ('counter','email','phone')),\nr AS (SELECT taken_by, channel, count(*) n, sum(uninv::int) un FROM s GROUP BY 1,2),\nc AS (SELECT channel, sum(un)*1.0/sum(n) p FROM r GROUP BY 1)\nSELECT r.channel, count(*) reps, round(sum(power(un-n*p,2)/(n*p*(1-p))),1) chi2, sum(CASE WHEN abs(un-n*p)/sqrt(n*p*(1-p))>3 THEN 1 ELSE 0 END) reps_gt3sd,\n min(n) min_n, max(n) max_n\nFROM r JOIN c USING(channel) GROUP BY 1",
  "columns": [
   "channel",
   "reps",
   "chi2",
   "reps_gt3sd",
   "min_n",
   "max_n"
  ],
  "row_count": 3,
  "rows": [
   [
    "counter",
    48,
    36.5,
    0,
    1469,
    8614
   ],
   [
    "email",
    48,
    52.5,
    0,
    8196,
    43670
   ],
   [
    "phone",
    48,
    53.8,
    0,
    2948,
    16233
   ]
  ],
  "error": null
 },
 {
  "id": "q269",
  "sql": "WITH s AS (\n SELECT l.*, o.channel, p.category, p.list_price lp, NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN erp_products p USING(sku)\n WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND o.channel IN ('counter','email','phone'))\nSELECT channel, uninv, count(*) n, round(avg(markdown_pct),4) avg_md, round(median(qty_shipped*unit_price),2) med_val, round(avg(qty_shipped*unit_price),2) avg_val,\n round(avg(CASE WHEN qty_shipped<qty_ordered THEN 1.0 ELSE 0 END),4) partial, round(avg(unit_price/lp),4) price_to_list\nFROM s GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "channel",
   "uninv",
   "n",
   "avg_md",
   "med_val",
   "avg_val",
   "partial",
   "price_to_list"
  ],
  "row_count": 6,
  "rows": [
   [
    "counter",
    false,
    219892,
    0.0117,
    252.12,
    570.69,
    0.0123,
    0.8363
   ],
   [
    "counter",
    true,
    2500,
    0.011,
    235.64,
    559.1,
    0.0124,
    0.8361
   ],
   [
    "email",
    false,
    1193263,
    0.0117,
    252.92,
    570.6,
    0.0121,
    0.8364
   ],
   [
    "email",
    true,
    1850,
    0.0101,
    261.54,
    576.97,
    0.013,
    0.8336
   ],
   [
    "phone",
    false,
    429334,
    0.0117,
    251.19,
    568.82,
    0.0124,
    0.8357
   ],
   [
    "phone",
    true,
    635,
    0.0131,
    241.11,
    591.13,
    0.0142,
    0.8341
   ]
  ],
  "error": null
 },
 {
  "id": "q259",
  "sql": "WITH s AS (\n SELECT l.line_id, l.order_id, o.channel, l.ship_day,\n  NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv,\n  count(*) OVER (PARTITION BY l.order_id) nlines,\n  row_number() OVER (PARTITION BY l.order_id ORDER BY l.line_id) pos,\n  count(DISTINCT l.ship_day) OVER (PARTITION BY l.order_id) nship\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id)\n WHERE l.qty_shipped>0 AND l.ship_day<=2520)\nSELECT channel, CASE WHEN nlines=1 THEN '1' WHEN nlines<=3 THEN '2-3' ELSE '4+' END nl,\n count(*) lines, sum(uninv::int) un, round(100.0*sum(uninv::int)/count(*),3) pct,\n sum(CASE WHEN uninv AND pos=nlines THEN 1 ELSE 0 END) un_last, sum(CASE WHEN uninv AND pos=1 THEN 1 ELSE 0 END) un_first\nFROM s WHERE channel IN ('counter','email','phone') GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "channel",
   "nl",
   "lines",
   "un",
   "pct",
   "un_last",
   "un_first"
  ],
  "row_count": 9,
  "rows": [
   [
    "counter",
    "1",
    51366,
    579,
    1.127,
    579,
    579
   ],
   [
    "counter",
    "2-3",
    93607,
    1018,
    1.088,
    431,
    437
   ],
   [
    "counter",
    "4+",
    77419,
    903,
    1.166,
    167,
    175
   ],
   [
    "email",
    "1",
    274868,
    425,
    0.155,
    425,
    425
   ],
   [
    "email",
    "2-3",
    508349,
    775,
    0.152,
    330,
    322
   ],
   [
    "email",
    "4+",
    411896,
    650,
    0.158,
    130,
    130
   ],
   [
    "phone",
    "1",
    98352,
    127,
    0.129,
    127,
    127
   ],
   [
    "phone",
    "2-3",
    181079,
    280,
    0.155,
    107,
    130
   ],
   [
    "phone",
    "4+",
    150538,
    228,
    0.151,
    42,
    48
   ]
  ],
  "error": null
 },
 {
  "id": "q272",
  "sql": "WITH s AS (\n SELECT o.channel, c.terms_days, c.trade, d.month, NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv\n FROM erp_sales_order_lines l JOIN erp_sales_orders o USING(order_id) JOIN erp_customers c USING(customer_id) JOIN dim_date d ON d.day=l.ship_day\n WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND o.channel IN ('counter','email','phone'))\nSELECT 'terms' dim, channel, terms_days::varchar k, count(*) n, sum(uninv::int) un, round(100.0*sum(uninv::int)/count(*),3) pct FROM s GROUP BY 1,2,3\nUNION ALL SELECT 'trade', channel, trade, count(*), sum(uninv::int), round(100.0*sum(uninv::int)/count(*),3) FROM s WHERE channel='counter' GROUP BY 1,2,3\nUNION ALL SELECT 'month', channel, month::varchar, count(*), sum(uninv::int), round(100.0*sum(uninv::int)/count(*),3) FROM s WHERE channel='counter' GROUP BY 1,2,3\nORDER BY 1,2,3",
  "columns": [
   "dim",
   "channel",
   "k",
   "n",
   "un",
   "pct"
  ],
  "row_count": 24,
  "rows": [
   [
    "month",
    "counter",
    "1",
    31613,
    383,
    1.212
   ],
   [
    "month",
    "counter",
    "10",
    15622,
    170,
    1.088
   ],
   [
    "month",
    "counter",
    "11",
    22859,
    260,
    1.137
   ],
   [
    "month",
    "counter",
    "12",
    28642,
    328,
    1.145
   ],
   [
    "month",
    "counter",
    "2",
    27376,
    325,
    1.187
   ],
   [
    "month",
    "counter",
    "3",
    23279,
    261,
    1.121
   ],
   [
    "month",
    "counter",
    "4",
    14868,
    145,
    0.975
   ],
   [
    "month",
    "counter",
    "5",
    11543,
    122,
    1.057
   ],
   [
    "month",
    "counter",
    "6",
    12417,
    133,
    1.071
   ],
   [
    "month",
    "counter",
    "7",
    13923,
    158,
    1.135
   ],
   [
    "month",
    "counter",
    "8",
    11565,
    122,
    1.055
   ],
   [
    "month",
    "counter",
    "9",
    8685,
    93,
    1.071
   ],
   [
    "terms",
    "counter",
    "0",
    23156,
    244,
    1.054
   ],
   [
    "terms",
    "counter",
    "30",
    162907,
    1824,
    1.12
   ],
   [
    "terms",
    "counter",
    "45",
    36329,
    432,
    1.189
   ],
   [
    "terms",
    "email",
    "0",
    122013,
    176,
    0.144
   ],
   [
    "terms",
    "email",
    "30",
    878235,
    1366,
    0.156
   ],
   [
    "terms",
    "email",
    "45",
    194865,
    308,
    0.158
   ],
   [
    "terms",
    "phone",
    "0",
    43909,
    74,
    0.169
   ],
   [
    "terms",
    "phone",
    "30",
    316416,
    448,
    0.142
   ],
   [
    "terms",
    "phone",
    "45",
    69644,
    113,
    0.162
   ],
   [
    "trade",
    "counter",
    "commercial",
    41270,
    459,
    1.112
   ],
   [
    "trade",
    "counter",
    "mixed",
    45212,
    536,
    1.186
   ],
   [
    "trade",
    "counter",
    "residential",
    135910,
    1505,
    1.107
   ]
  ],
  "error": null
 },
 {
  "id": "q324",
  "sql": "WITH s AS (\n SELECT l.*, d.year, NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id) uninv\n FROM erp_sales_order_lines l JOIN dim_date d ON d.day=l.ship_day\n WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND d.year BETWEEN 2016 AND 2024),\ny AS (SELECT year, sum(CASE WHEN uninv THEN qty_shipped*unit_price END) v FROM s GROUP BY 1),\nb AS (SELECT sum(il.amount) billed FROM finance_invoice_lines il JOIN erp_sales_order_lines l USING(line_id) JOIN dim_date d ON d.day=l.ship_day WHERE d.year BETWEEN 2016 AND 2024)\nSELECT sum(uninv::int) lines, round(sum(CASE WHEN uninv THEN qty_shipped*unit_price END),2) v_total,\n round(sum(CASE WHEN uninv THEN qty_shipped*unit_price END)/9,2) v_per_yr,\n round(sum(CASE WHEN uninv THEN qty_shipped*unit_cost END)/9,2) cost_per_yr,\n round(sum(CASE WHEN uninv THEN qty_shipped*(unit_price-unit_cost) END)/9,2) margin_per_yr,\n (SELECT round(min(v),2) FROM y) min_yr, (SELECT round(max(v),2) FROM y) max_yr,\n round(100*sum(CASE WHEN uninv THEN qty_shipped*unit_price END)/(SELECT billed FROM b),4) pct_of_billed\nFROM s",
  "columns": [
   "lines",
   "v_total",
   "v_per_yr",
   "cost_per_yr",
   "margin_per_yr",
   "min_yr",
   "max_yr",
   "pct_of_billed"
  ],
  "row_count": 1,
  "rows": [
   [
    4495,
    2569213.83,
    285468.2,
    213944.6,
    71523.61,
    252827.81,
    348493.66,
    0.1948
   ]
  ],
  "error": null
 },
 {
  "id": "q291",
  "sql": "WITH u AS (SELECT l.* FROM erp_sales_order_lines l WHERE l.qty_shipped>0 AND l.ship_day<=2520 AND NOT EXISTS (SELECT 1 FROM finance_invoice_lines il WHERE il.line_id=l.line_id))\nSELECT count(*) returns, sum(CASE WHEN EXISTS (SELECT 1 FROM finance_credit_memos m WHERE m.order_id=r.order_id AND m.day BETWEEN r.day-2 AND r.day+30 AND abs(m.amount-r.qty*u.unit_price)<1) THEN 1 ELSE 0 END) credited_match,\n round(sum(r.qty*u.unit_price),2) ret_value\nFROM u JOIN erp_returns r ON r.line_id=u.line_id",
  "columns": [
   "returns",
   "credited_match",
   "ret_value"
  ],
  "row_count": 1,
  "rows": [
   [
    16,
    16,
    4618.19
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

Save `grade.json`: {"finding": "F5", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
