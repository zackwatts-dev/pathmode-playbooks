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
 "id": "F3",
 "hypothesis": "H3",
 "title": "H3 is not supported as stated. R-410A stock is at a ten-year low, and its 2025 below-cost sales are one case of a company-wide pattern: once any equipment SKU passes its discontinued_on date, stock-fulfilled lines sell below cost and keep getting replenished. Losses on those stock lines averaged $1,689,105.48 a year over 2023-2025",
 "conclusion": "Not supported: that Hartwell holds an oversized R-410A stock. Year-end 2025 R-410A equipment stock is 5,601 units ($7,925,627.94 at master cost), the lowest of 2016-2025 (q140). Not supported: that the 2025 margin loss is a refrigerant-transition effect. R-410A stock and transfer lines did lose $458,003.64 in 2025 at 0.9397x cost (q158, q241). But every equipment SKU of any refrigerant, or none, sells from stock below cost once it passes its discontinued_on date: 0.7224-0.8516x after discontinuation against 1.2103-1.2221x before it (q231). Active equipment held about 1.20x in 2025: R-454B 1.2102x and no-refrigerant 1.1995x (q241). Observed, and new here: the below-cost pricing applies only to stock fulfilment. After discontinuation, special-order lines run at 1.1968-1.2113x and transfer lines at 1.2032-1.2183x. Stock lines run at 1.0665x in the first year after discontinuation, then 0.7707x, then 0.7023-0.7027x from the third year on (q259). Stock POs keep replenishing discontinued SKUs: 10,001 units ($11,212,307.23) in 2025 (q235). Size: post-discontinuation stock lines lost $1,689,105.48 a year on average over 2023-2025 (8,940.3 units a year), of which R-410A was $449,213.61 (q261). Interpretation: this looks like a pricing rule tied to the discontinued flag and stock fulfilment, combined with replenishment that ignores the flag. Neither the rule nor the reorder trigger is recorded.",
 "dollars_a_year": 1689105.48,
 "size_query": "q261",
 "claims": [
  {
   "text": "R-410A equipment on hand at cut-off: 5,601 units, $7,925,627.94 at master cost. Year-end stock was 9,045 units in 2024 and peaked at 11,366 in 2020. The 2025 level is the lowest of 2016-2025. On hand by discontinuation group: 2015 group 655 units ($816,087.80), 2023 group 1,375 ($1,841,588.18), 2025 group 3,571 ($5,267,951.96).",
   "queries": [
    "q140",
    "q214"
   ]
  },
  {
   "text": "The R-410A SKUs fall into three discontinuation groups: 44 SKUs discontinued 2015-01-01, 44 discontinued 2023-01-01 and 130 discontinued 2025-01-01. In 2025, stock and transfer lines lost $218,496.24 on the 2015 group and $547,810.66 on the 2023 group. The 2025 group made +$308,303.26 at 1.0646x. The 2015 group has sold from stock and transfer at 0.7159-0.7589x cost every year 2016-2025.",
   "queries": [
    "q203",
    "q214",
    "q220"
   ]
  },
  {
   "text": "Below-cost selling follows discontinuation, not refrigerant. Stock and transfer lines after discontinued_on run at 0.73x (R-410A, 2015 group), 0.8513x (R-410A, 2023), 0.7413x (R-454B, 2015), 0.8516x (R-454B, 2023), 0.7224x (no refrigerant, 2015) and 0.8438x (no refrigerant, 2023). Before discontinuation, every group runs at 1.2103-1.2221x (2016-2025). In 2025, active R-454B ran at 1.2102x and active no-refrigerant at 1.1995x.",
   "queries": [
    "q231",
    "q241"
   ]
  },
  {
   "text": "Only stock fulfilment is marked down. For all equipment after discontinuation (2016-2025), special-order lines run at 1.1968-1.2113x and transfer lines at 1.2032-1.2183x. Stock lines run at 1.0665x in year 0 (7,990 units), 0.7707x in year 1 (5,401), 0.7027x in year 2 (7,685) and 0.7023x in year 3 and later (19,393). In 2025, for the same R-410A SKU and quarter, the median stock/special price ratio was 0.8601 in Q2 (165 SKU-quarters) and 0.8078 in Q3 (149).",
   "queries": [
    "q259",
    "q208",
    "q224"
   ]
  },
  {
   "text": "Below-cost isn't an artifact of stale master cost. Sales-line cost equals master cost on every R-410A line 2022-2025, PO cost equals master in every year 2020-2025, and billed cost runs at 1.0008-1.0015x master on 2022-2025 vendor bills.",
   "queries": [
    "q197",
    "q199",
    "q227"
   ]
  },
  {
   "text": "Discontinued SKUs keep being bought for stock. Across all equipment, stock POs placed after discontinued_on ran at 1,346-2,698 units a year in 2016-2022, then 4,188 in 2023, 8,929 in 2024 and 10,001 ($11,212,307.23) in 2025. Of 2,967 R-410A stock PO units in 2025, 699 were for the 2015 group, 1,686 for the 2023 group and 582 for the 2025 group.",
   "queries": [
    "q235",
    "q221",
    "q249",
    "q175"
   ]
  },
  {
   "text": "Sizing, stock lines only, all equipment after discontinued_on: the loss was $408,748.50 in 2023, $2,174,845.71 in 2024 and $2,483,722.23 in 2025. That totals $5,067,316.44 over 2023-2025 on 26,821 units, or $1,689,105.48 a year on average. R-410A accounted for $449,213.61 a year. Pricing these lines at the same year's non-stock price/cost (1.2002-1.2057x) would have given $3,766,723.89 a year more. That is an upper bound, not an estimate, because demand at that price is unobserved.",
   "queries": [
    "q261"
   ]
  },
  {
   "text": "Returns to vendor against vendor credits: in 2025, R-410A returns to vendor were 1,009 units ($1,476,383.18) and credits $747,413.72. Credits lag returns: 2024 credits were 6.88x 2024 returns because 2023 returns were credited in 2024. Over 2023-2024, 323 R-410A units were returned and 323 credited, at a credit value of 0.8 of returned cost.",
   "queries": [
    "q161",
    "q244",
    "q249"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that the R-410A phase-down caused the losses, or that R-410A market prices fell: special-order and transfer prices of the same SKUs held near 1.20x (q208, q224, q259). Not evidence of over-buying R-410A in aggregate (q140). Not evidence that the whole $1,689,105.48 is avoidable. Without restocking, those sales and the customers' goodwill might be lost, and demand at full price for discontinued stock is unobserved. Not evidence about rebates or price protection, which aren't recorded. Not evidence that any person, rep or branch set these prices or placed these POs on purpose: there are no pricing-rule, reorder-trigger or approval records. Interpretation: the year-0 to year-2 deepening (1.0665x to 0.7027x, q259) fits a time-based clearance rule, but the records don't say that.",
 "could_not_tell": "What rule sets stock-line prices for discontinued SKUs, and why it doesn't apply to special or transfer lines. Why replenishment keeps placing stock POs for discontinued SKUs. Whether the discontinued_on dates are real: a SKU 'discontinued' in 2015 that is still bought and sold at full price on special orders in 2025 may be a master-data error. Vendor catalogs or the product manager would settle it. Whether the 2025 vendor-credit shortfall will clear in 2026: that needs post-cut-off credits or vendor return terms. Real net cost after any off-bill rebates.",
 "next_step": "Pull the pricing configuration that applies to stock lines of SKUs flagged discontinued, and the reorder parameters (min/max, auto-replenish flag) for discontinued SKUs. Start with the 44 R-410A SKUs discontinued 2015-01-01, bought for stock and sold below cost every year since 2016 (q220, q221). Ask the product manager whether those discontinued_on dates are correct. If they are wrong, fixing the master data may remove the markdown. If they are right, stop stock replenishment and route demand to special order, which holds about 1.20x (q259).",
 "incomplete": false
}

[
 {
  "id": "q140",
  "sql": "WITH p AS (SELECT sku, unit_cost FROM erp_products WHERE category='equipment' AND refrigerant='R-410A'),\ny AS (SELECT DISTINCT year FROM dim_date),\neoy AS (SELECT y.year, max(d.day) lastday FROM dim_date d JOIN y USING(year) GROUP BY 1)\nSELECT e.year, round(sum(t.qty_delta),1) units_eoy, round(sum(t.qty_delta*p.unit_cost),2) value_eoy\nFROM eoy e JOIN wms_inventory_transactions t ON t.day<=e.lastday JOIN p USING(sku)\nGROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "units_eoy",
   "value_eoy"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    6828.1,
    9769618.02
   ],
   [
    2017,
    9299.8,
    13274650.23
   ],
   [
    2018,
    10527.0,
    15069871.36
   ],
   [
    2019,
    10771.0,
    15397118.13
   ],
   [
    2020,
    11366.0,
    16301215.64
   ],
   [
    2021,
    11338.0,
    16247100.72
   ],
   [
    2022,
    10896.0,
    15572924.81
   ],
   [
    2023,
    9532.0,
    13756132.12
   ],
   [
    2024,
    9045.0,
    13010326.21
   ],
   [
    2025,
    5601.0,
    7925627.94
   ]
  ],
  "error": null
 },
 {
  "id": "q214",
  "sql": "WITH p AS (SELECT sku, unit_cost mc, discontinued_on disc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A'),\noh AS (SELECT sku, sum(qty_delta) q FROM wms_inventory_transactions JOIN p USING(sku) GROUP BY 1),\ns AS (SELECT l.sku, d.year, sum(l.qty_shipped) u, sum(l.qty_shipped*l.unit_price) rev, sum(l.qty_shipped*l.unit_cost) cost\n FROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\n WHERE l.fulfilment IN ('stock','transfer') AND l.qty_shipped>0 AND d.year IN (2022,2024,2025) GROUP BY 1,2)\nSELECT p.disc, count(DISTINCT p.sku) skus,\n (SELECT round(sum(q),1) FROM oh JOIN p p2 USING(sku) WHERE p2.disc=p.disc) units_oh,\n (SELECT round(sum(q*p2.mc),2) FROM oh JOIN p p2 USING(sku) WHERE p2.disc=p.disc) value_oh,\n sum(CASE WHEN s.year=2022 THEN s.u END) u22, sum(CASE WHEN s.year=2024 THEN s.u END) u24, sum(CASE WHEN s.year=2025 THEN s.u END) u25,\n round(sum(CASE WHEN s.year=2022 THEN s.rev END)/sum(CASE WHEN s.year=2022 THEN s.cost END),4) pc22,\n round(sum(CASE WHEN s.year=2024 THEN s.rev END)/sum(CASE WHEN s.year=2024 THEN s.cost END),4) pc24,\n round(sum(CASE WHEN s.year=2025 THEN s.rev END)/sum(CASE WHEN s.year=2025 THEN s.cost END),4) pc25,\n round(sum(CASE WHEN s.year=2025 THEN s.rev-s.cost END),2) gm25\nFROM p LEFT JOIN s USING(sku) GROUP BY 1 ORDER BY 1",
  "columns": [
   "disc",
   "skus",
   "units_oh",
   "value_oh",
   "u22",
   "u24",
   "u25",
   "pc22",
   "pc24",
   "pc25",
   "gm25"
  ],
  "row_count": 3,
  "rows": [
   [
    "2015-01-01",
    44,
    655.0,
    816087.8,
    679.0,
    734.0,
    653.0,
    0.7264,
    0.7279,
    0.7277,
    -218496.24
   ],
   [
    "2023-01-01",
    44,
    1375.0,
    1841588.18,
    3484.0,
    1658.0,
    1512.0,
    1.2165,
    0.8003,
    0.7301,
    -547810.66
   ],
   [
    "2025-01-01",
    130,
    3571.0,
    5267951.96,
    10923.0,
    10926.0,
    3252.0,
    1.21,
    1.204,
    1.0646,
    308303.26
   ]
  ],
  "error": null
 },
 {
  "id": "q203",
  "sql": "SELECT discontinued_on, count(*) skus FROM erp_products WHERE category='equipment' AND refrigerant='R-410A' GROUP BY 1 ORDER BY 1",
  "columns": [
   "discontinued_on",
   "skus"
  ],
  "row_count": 3,
  "rows": [
   [
    "2015-01-01",
    44
   ],
   [
    "2023-01-01",
    44
   ],
   [
    "2025-01-01",
    130
   ]
  ],
  "error": null
 },
 {
  "id": "q220",
  "sql": "WITH p AS (SELECT sku, discontinued_on disc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT d.year, p.disc, sum(l.qty_shipped) u, round(sum(l.qty_shipped*l.unit_price)/sum(l.qty_shipped*l.unit_cost),4) pc\nFROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\nWHERE l.fulfilment IN ('stock','transfer') AND l.qty_shipped>0 GROUP BY 1,2 ORDER BY 2,1",
  "columns": [
   "year",
   "disc",
   "u",
   "pc"
  ],
  "row_count": 30,
  "rows": [
   [
    2016,
    "2015-01-01",
    37.0,
    0.7589
   ],
   [
    2017,
    "2015-01-01",
    239.0,
    0.7442
   ],
   [
    2018,
    "2015-01-01",
    507.0,
    0.7295
   ],
   [
    2019,
    "2015-01-01",
    605.0,
    0.7254
   ],
   [
    2020,
    "2015-01-01",
    572.0,
    0.7384
   ],
   [
    2021,
    "2015-01-01",
    639.0,
    0.7442
   ],
   [
    2022,
    "2015-01-01",
    679.0,
    0.7264
   ],
   [
    2023,
    "2015-01-01",
    657.0,
    0.7159
   ],
   [
    2024,
    "2015-01-01",
    734.0,
    0.7279
   ],
   [
    2025,
    "2015-01-01",
    653.0,
    0.7277
   ],
   [
    2016,
    "2023-01-01",
    763.0,
    1.2248
   ],
   [
    2017,
    "2023-01-01",
    2706.0,
    1.2272
   ],
   [
    2018,
    "2023-01-01",
    3680.0,
    1.226
   ],
   [
    2019,
    "2023-01-01",
    3662.0,
    1.2207
   ],
   [
    2020,
    "2023-01-01",
    3400.0,
    1.2223
   ],
   [
    2021,
    "2023-01-01",
    3912.0,
    1.2206
   ],
   [
    2022,
    "2023-01-01",
    3484.0,
    1.2165
   ],
   [
    2023,
    "2023-01-01",
    1227.0,
    1.0691
   ],
   [
    2024,
    "2023-01-01",
    1658.0,
    0.8003
   ],
   [
    2025,
    "2023-01-01",
    1512.0,
    0.7301
   ],
   [
    2016,
    "2025-01-01",
    2405.7090000000026,
    1.2134
   ],
   [
    2017,
    "2025-01-01",
    7775.123000000001,
    1.2178
   ],
   [
    2018,
    "2025-01-01",
    10540.751,
    1.2179
   ],
   [
    2019,
    "2025-01-01",
    10664.0,
    1.2143
   ],
   [
    2020,
    "2025-01-01",
    10100.0,
    1.2132
   ],
   [
    2021,
    "2025-01-01",
    11364.0,
    1.2131
   ],
   [
    2022,
    "2025-01-01",
    10923.0,
    1.21
   ],
   [
    2023,
    "2025-01-01",
    10467.0,
    1.2047
   ],
   [
    2024,
    "2025-01-01",
    10926.0,
    1.204
   ],
   [
    2025,
    "2025-01-01",
    3252.0,
    1.0646
   ]
  ],
  "error": null
 },
 {
  "id": "q231",
  "sql": "WITH p AS (SELECT sku, coalesce(nullif(refrigerant,''),'none') refr, discontinued_on disc FROM erp_products WHERE category='equipment'),\nx AS (SELECT p.refr, coalesce(p.disc,'never') disc, d.year, CASE WHEN p.disc IS NOT NULL AND d.date>=CAST(p.disc AS DATE) THEN 'after_disc' ELSE 'before_disc' END phase,\n l.qty_shipped q, l.unit_price pr, l.unit_cost c\n FROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\n WHERE l.fulfilment IN ('stock','transfer') AND l.qty_shipped>0)\nSELECT refr, disc, phase, sum(q) units, round(sum(q*pr)/sum(q*c),4) pc, round(sum(q*(pr-c)),2) gm\nFROM x GROUP BY 1,2,3 ORDER BY 1,2,3",
  "columns": [
   "refr",
   "disc",
   "phase",
   "units",
   "pc",
   "gm"
  ],
  "row_count": 13,
  "rows": [
   [
    "R-410A",
    "2015-01-01",
    "after_disc",
    5322.0,
    0.73,
    -1763478.54
   ],
   [
    "R-410A",
    "2023-01-01",
    "after_disc",
    4397.0,
    0.8513,
    -876714.48
   ],
   [
    "R-410A",
    "2023-01-01",
    "before_disc",
    21607.0,
    1.2221,
    6419437.63
   ],
   [
    "R-410A",
    "2025-01-01",
    "after_disc",
    3252.0,
    1.0646,
    308303.26
   ],
   [
    "R-410A",
    "2025-01-01",
    "before_disc",
    85165.58300000001,
    1.2117,
    26467208.34
   ],
   [
    "R-454B",
    "2015-01-01",
    "after_disc",
    5463.0,
    0.7413,
    -1887910.8
   ],
   [
    "R-454B",
    "2023-01-01",
    "after_disc",
    4379.0,
    0.8516,
    -946701.35
   ],
   [
    "R-454B",
    "2023-01-01",
    "before_disc",
    21940.0,
    1.2211,
    7036121.06
   ],
   [
    "R-454B",
    "never",
    "before_disc",
    2516.626,
    1.2103,
    839324.18
   ],
   [
    "none",
    "2015-01-01",
    "after_disc",
    11581.0,
    0.7224,
    -2503279.67
   ],
   [
    "none",
    "2023-01-01",
    "after_disc",
    7932.0,
    0.8438,
    -1054839.66
   ],
   [
    "none",
    "2023-01-01",
    "before_disc",
    43170.0,
    1.2216,
    8125504.78
   ],
   [
    "none",
    "never",
    "before_disc",
    185174.83200000005,
    1.2105,
    36889585.19
   ]
  ],
  "error": null
 },
 {
  "id": "q241",
  "sql": "WITH p AS (SELECT sku, coalesce(nullif(refrigerant,''),'none') refr, discontinued_on disc FROM erp_products WHERE category='equipment'),\nx AS (SELECT p.refr, CASE WHEN p.disc IS NOT NULL AND p.disc<>'' AND d.date>=CAST(p.disc AS DATE) THEN 'after_disc' ELSE 'active' END phase, p.disc, d.year,\n l.qty_shipped q, l.unit_price pr, l.unit_cost c\n FROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\n WHERE l.fulfilment IN ('stock','transfer') AND l.qty_shipped>0 AND d.year IN (2022,2024,2025))\nSELECT refr, phase, year, sum(q) units, round(sum(q*c),2) cost, round(sum(q*pr)/sum(q*c),4) pc FROM x GROUP BY 1,2,3 ORDER BY 1,2,3",
  "columns": [
   "refr",
   "phase",
   "year",
   "units",
   "cost",
   "pc"
  ],
  "row_count": 17,
  "rows": [
   [
    "R-410A",
    "active",
    2022,
    14407.0,
    20713387.84,
    1.2115
   ],
   [
    "R-410A",
    "active",
    2024,
    10926.0,
    16059787.36,
    1.204
   ],
   [
    "R-410A",
    "after_disc",
    2022,
    679.0,
    844541.67,
    0.7264
   ],
   [
    "R-410A",
    "after_disc",
    2024,
    2392.0,
    3119604.38,
    0.7794
   ],
   [
    "R-410A",
    "after_disc",
    2025,
    5417.0,
    7601582.71,
    0.9397
   ],
   [
    "R-454B",
    "active",
    2022,
    3523.0,
    5126575.25,
    1.2192
   ],
   [
    "R-454B",
    "active",
    2024,
    104.0,
    161839.43,
    1.2122
   ],
   [
    "R-454B",
    "active",
    2025,
    2411.626,
    3828190.41,
    1.2102
   ],
   [
    "R-454B",
    "after_disc",
    2022,
    675.0,
    911983.41,
    0.7393
   ],
   [
    "R-454B",
    "after_disc",
    2024,
    2339.0,
    3304761.92,
    0.785
   ],
   [
    "R-454B",
    "after_disc",
    2025,
    2160.0,
    3057633.83,
    0.7328
   ],
   [
    "none",
    "active",
    2022,
    26186.0,
    24253463.88,
    1.2108
   ],
   [
    "none",
    "active",
    2024,
    19157.0,
    18101774.67,
    1.2028
   ],
   [
    "none",
    "active",
    2025,
    20090.0,
    19056843.29,
    1.1995
   ],
   [
    "none",
    "after_disc",
    2022,
    1288.0,
    987935.72,
    0.7218
   ],
   [
    "none",
    "after_disc",
    2024,
    3445.0,
    2835717.09,
    0.7654
   ],
   [
    "none",
    "after_disc",
    2025,
    4715.0,
    3916143.57,
    0.718
   ]
  ],
  "error": null
 },
 {
  "id": "q259",
  "sql": "WITH p AS (SELECT sku, discontinued_on disc FROM erp_products WHERE category='equipment' AND discontinued_on IS NOT NULL AND discontinued_on<>'')\nSELECT l.fulfilment, LEAST(floor(date_diff('month', CAST(p.disc AS DATE), d.date)/12),3) yrs_since_disc,\n count(*) lines, sum(l.qty_shipped) units, round(sum(l.qty_shipped*l.unit_price)/sum(l.qty_shipped*l.unit_cost),4) pc,\n round(sum(l.qty_shipped*(l.unit_price-l.unit_cost)),2) gm\nFROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\nWHERE l.qty_shipped>0 AND d.date>=CAST(p.disc AS DATE)\nGROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "fulfilment",
   "yrs_since_disc",
   "lines",
   "units",
   "pc",
   "gm"
  ],
  "row_count": 12,
  "rows": [
   [
    "special",
    0.0,
    1610,
    1610.0,
    1.1968,
    410909.2
   ],
   [
    "special",
    1.0,
    6419,
    6419.0,
    1.2113,
    1480322.87
   ],
   [
    "special",
    2.0,
    6321,
    6321.0,
    1.2104,
    1528484.16
   ],
   [
    "special",
    3.0,
    22854,
    22854.0,
    1.2075,
    5205305.67
   ],
   [
    "stock",
    0.0,
    7990,
    7990.0,
    1.0665,
    674712.06
   ],
   [
    "stock",
    1.0,
    5401,
    5401.0,
    0.7707,
    -1440095.28
   ],
   [
    "stock",
    2.0,
    7685,
    7685.0,
    0.7027,
    -2450705.5
   ],
   [
    "stock",
    3.0,
    19393,
    19393.0,
    0.7023,
    -5936265.49
   ],
   [
    "transfer",
    0.0,
    56,
    56.0,
    1.2032,
    11289.48
   ],
   [
    "transfer",
    1.0,
    347,
    347.0,
    1.2044,
    84814.28
   ],
   [
    "transfer",
    2.0,
    350,
    350.0,
    1.2183,
    86392.83
   ],
   [
    "transfer",
    3.0,
    1104,
    1104.0,
    1.2093,
    245236.37
   ]
  ],
  "error": null
 },
 {
  "id": "q208",
  "sql": "WITH p AS (SELECT sku, unit_cost mc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A'),\ns AS (SELECT l.sku, d.quarter,\n avg(CASE WHEN l.fulfilment='stock' THEN l.unit_price END) ps, avg(CASE WHEN l.fulfilment='special' THEN l.unit_price END) pp\n FROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\n WHERE l.qty_shipped>0 AND d.year=2025 GROUP BY 1,2)\nSELECT quarter, count(*) sku_quarters, round(median(ps/pp),4) med_stock_to_special, round(quantile_cont(ps/pp,0.1),4) p10, round(quantile_cont(ps/pp,0.9),4) p90\nFROM s WHERE ps IS NOT NULL AND pp IS NOT NULL GROUP BY 1 ORDER BY 1",
  "columns": [
   "quarter",
   "sku_quarters",
   "med_stock_to_special",
   "p10",
   "p90"
  ],
  "row_count": 4,
  "rows": [
   [
    1,
    18,
    0.7475,
    0.5789,
    1.0614
   ],
   [
    2,
    165,
    0.8601,
    0.5746,
    0.9593
   ],
   [
    3,
    149,
    0.8078,
    0.5641,
    0.9565
   ],
   [
    4,
    6,
    0.5532,
    0.4841,
    0.6874
   ]
  ],
  "error": null
 },
 {
  "id": "q224",
  "sql": "WITH p AS (SELECT sku, unit_cost mc, list_price lp, discontinued_on disc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT p.disc, l.fulfilment, count(*) lines, round(sum(l.qty_shipped*l.unit_price)/sum(l.qty_shipped*l.unit_cost),4) pc, round(avg(p.lp/p.mc),4) avg_list_to_cost\nFROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\nWHERE l.qty_shipped>0 AND d.year BETWEEN 2022 AND 2025 GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "disc",
   "fulfilment",
   "lines",
   "pc",
   "avg_list_to_cost"
  ],
  "row_count": 9,
  "rows": [
   [
    "2015-01-01",
    "special",
    3273,
    1.2022,
    1.4477
   ],
   [
    "2015-01-01",
    "stock",
    2551,
    0.692,
    1.4324
   ],
   [
    "2015-01-01",
    "transfer",
    172,
    1.1942,
    1.4358
   ],
   [
    "2023-01-01",
    "special",
    2758,
    1.2042,
    1.4526
   ],
   [
    "2023-01-01",
    "stock",
    7518,
    1.0035,
    1.4566
   ],
   [
    "2023-01-01",
    "transfer",
    363,
    1.2096,
    1.4565
   ],
   [
    "2025-01-01",
    "special",
    6839,
    1.2,
    1.4512
   ],
   [
    "2025-01-01",
    "stock",
    33889,
    1.193,
    1.4483
   ],
   [
    "2025-01-01",
    "transfer",
    1679,
    1.1992,
    1.448
   ]
  ],
  "error": null
 },
 {
  "id": "q197",
  "sql": "WITH p AS (SELECT sku, unit_cost mc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT d.year, l.fulfilment, count(*) lines,\n round(sum(l.qty_shipped*l.unit_cost)/sum(l.qty_shipped*p.mc),4) line_cost_to_master,\n sum(CASE WHEN abs(l.unit_cost-p.mc)>0.005 THEN 1 ELSE 0 END) lines_cost_ne_master,\n round(sum(l.qty_shipped*l.unit_price)/sum(l.qty_shipped*p.mc),4) price_to_master\nFROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\nWHERE l.qty_shipped>0 AND d.year>=2022 GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "year",
   "fulfilment",
   "lines",
   "line_cost_to_master",
   "lines_cost_ne_master",
   "price_to_master"
  ],
  "row_count": 12,
  "rows": [
   [
    2022,
    "special",
    3449,
    1.0,
    0,
    1.2015
   ],
   [
    2022,
    "stock",
    14319,
    1.0,
    0,
    1.1915
   ],
   [
    2022,
    "transfer",
    767,
    1.0,
    0,
    1.2096
   ],
   [
    2023,
    "special",
    3157,
    1.0,
    0,
    1.2025
   ],
   [
    2023,
    "stock",
    11729,
    1.0,
    0,
    1.1683
   ],
   [
    2023,
    "transfer",
    622,
    1.0,
    0,
    1.1965
   ],
   [
    2024,
    "special",
    3761,
    1.0,
    0,
    1.203
   ],
   [
    2024,
    "stock",
    12623,
    1.0,
    0,
    1.1318
   ],
   [
    2024,
    "transfer",
    695,
    1.0,
    0,
    1.1922
   ],
   [
    2025,
    "special",
    2503,
    1.0,
    0,
    1.1971
   ],
   [
    2025,
    "stock",
    5287,
    1.0,
    0,
    0.9335
   ],
   [
    2025,
    "transfer",
    130,
    1.0,
    0,
    1.2095
   ]
  ],
  "error": null
 },
 {
  "id": "q199",
  "sql": "WITH p AS (SELECT sku, unit_cost mc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT d.year, count(*) po_lines, round(sum(pl.qty*pl.unit_cost)/sum(pl.qty*p.mc),4) po_cost_to_master,\n round(median(pl.unit_cost/p.mc),4) med_ratio, round(min(pl.unit_cost/p.mc),4) mn, round(max(pl.unit_cost/p.mc),4) mx\nFROM erp_purchase_orders po JOIN erp_purchase_order_lines pl USING(po_id) JOIN p USING(sku) JOIN dim_date d ON d.day=po.day\nWHERE d.year>=2020 GROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "po_lines",
   "po_cost_to_master",
   "med_ratio",
   "mn",
   "mx"
  ],
  "row_count": 6,
  "rows": [
   [
    2020,
    7206,
    1.0,
    1.0,
    1.0,
    1.0
   ],
   [
    2021,
    8027,
    1.0,
    1.0,
    1.0,
    1.0
   ],
   [
    2022,
    7364,
    1.0,
    1.0,
    1.0,
    1.0
   ],
   [
    2023,
    6166,
    1.0,
    1.0,
    1.0,
    1.0
   ],
   [
    2024,
    7282,
    1.0,
    1.0,
    1.0,
    1.0
   ],
   [
    2025,
    3438,
    1.0,
    1.0,
    1.0,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q227",
  "sql": "WITH p AS (SELECT sku, unit_cost mc, discontinued_on disc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT p.disc, d.year, count(*) bill_lines, round(sum(bl.qty*bl.unit_cost)/sum(bl.qty*p.mc),4) billed_to_master, round(min(bl.unit_cost/p.mc),4) mn, round(max(bl.unit_cost/p.mc),4) mx\nFROM finance_vendor_bill_lines bl JOIN p USING(sku) JOIN finance_vendor_bills b USING(bill_id) JOIN dim_date d ON d.day=b.day\nWHERE d.year>=2022 GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "disc",
   "year",
   "bill_lines",
   "billed_to_master",
   "mn",
   "mx"
  ],
  "row_count": 12,
  "rows": [
   [
    "2015-01-01",
    2022,
    986,
    1.0012,
    1.0,
    1.0784
   ],
   [
    "2015-01-01",
    2023,
    1036,
    1.0013,
    1.0,
    1.08
   ],
   [
    "2015-01-01",
    2024,
    1172,
    1.0015,
    1.0,
    1.0774
   ],
   [
    "2015-01-01",
    2025,
    1043,
    1.001,
    1.0,
    1.0793
   ],
   [
    "2023-01-01",
    2022,
    1585,
    1.0012,
    1.0,
    1.0788
   ],
   [
    "2023-01-01",
    2023,
    340,
    1.0015,
    1.0,
    1.0759
   ],
   [
    "2023-01-01",
    2024,
    1255,
    1.0009,
    1.0,
    1.0781
   ],
   [
    "2023-01-01",
    2025,
    1517,
    1.0015,
    1.0,
    1.0799
   ],
   [
    "2025-01-01",
    2022,
    4846,
    1.0008,
    1.0,
    1.08
   ],
   [
    "2025-01-01",
    2023,
    4804,
    1.001,
    1.0,
    1.0797
   ],
   [
    "2025-01-01",
    2024,
    4883,
    1.0011,
    1.0,
    1.0799
   ],
   [
    "2025-01-01",
    2025,
    896,
    1.0014,
    1.0,
    1.0761
   ]
  ],
  "error": null
 },
 {
  "id": "q235",
  "sql": "WITH p AS (SELECT sku, discontinued_on disc FROM erp_products WHERE category='equipment' AND discontinued_on IS NOT NULL AND discontinued_on<>''),\ns AS (SELECT d.year, sum(l.qty_shipped) u, round(sum(l.qty_shipped*(l.unit_price-l.unit_cost)),2) gm, round(sum(l.qty_shipped*l.unit_price)/sum(l.qty_shipped*l.unit_cost),4) pc\n FROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\n WHERE l.fulfilment IN ('stock','transfer') AND l.qty_shipped>0 AND d.date>=CAST(p.disc AS DATE) GROUP BY 1),\nb AS (SELECT d.year, sum(pl.qty) po_u, round(sum(pl.qty*pl.unit_cost),2) po_val\n FROM erp_purchase_orders po JOIN erp_purchase_order_lines pl USING(po_id) JOIN p USING(sku) JOIN dim_date d ON d.day=po.day\n WHERE po.purpose='stock' AND d.date>=CAST(p.disc AS DATE) GROUP BY 1)\nSELECT s.year, s.u post_disc_stock_units, s.gm post_disc_gm, s.pc, b.po_u post_disc_stock_po_units, b.po_val FROM s LEFT JOIN b USING(year) ORDER BY 1",
  "columns": [
   "year",
   "post_disc_stock_units",
   "post_disc_gm",
   "pc",
   "post_disc_stock_po_units",
   "po_val"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    229.0,
    -53732.26,
    0.7407,
    1346.0,
    1284378.95
   ],
   [
    2017,
    1640.0,
    -409907.62,
    0.7319,
    2232.0,
    2242990.83
   ],
   [
    2018,
    2352.0,
    -637687.11,
    0.7349,
    2683.0,
    2835151.44
   ],
   [
    2019,
    2526.0,
    -697567.2,
    0.7329,
    2639.0,
    2679873.47
   ],
   [
    2020,
    2512.0,
    -678680.73,
    0.7331,
    2463.0,
    2516218.51
   ],
   [
    2021,
    2532.0,
    -687676.31,
    0.7377,
    2589.0,
    2703550.91
   ],
   [
    2022,
    2642.0,
    -743702.84,
    0.729,
    2698.0,
    2803534.84
   ],
   [
    2023,
    7425.0,
    -372468.27,
    0.9543,
    4188.0,
    4266209.12
   ],
   [
    2024,
    8176.0,
    -2063781.7,
    0.7771,
    8929.0,
    9868589.31
   ],
   [
    2025,
    12292.0,
    -2379417.2,
    0.8368,
    10001.0,
    11212307.23
   ]
  ],
  "error": null
 },
 {
  "id": "q221",
  "sql": "WITH p AS (SELECT sku, discontinued_on disc FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT p.disc, d.year, po.purpose, sum(pl.qty) units, count(DISTINCT po.po_id) pos\nFROM erp_purchase_orders po JOIN erp_purchase_order_lines pl USING(po_id) JOIN p USING(sku) JOIN dim_date d ON d.day=po.day\nWHERE d.year IN (2016,2022,2023,2024,2025) GROUP BY 1,2,3 ORDER BY 1,2,3",
  "columns": [
   "disc",
   "year",
   "purpose",
   "units",
   "pos"
  ],
  "row_count": 30,
  "rows": [
   [
    "2015-01-01",
    2016,
    "special",
    910.0,
    910
   ],
   [
    "2015-01-01",
    2016,
    "stock",
    230.0,
    66
   ],
   [
    "2015-01-01",
    2022,
    "special",
    756.0,
    756
   ],
   [
    "2015-01-01",
    2022,
    "stock",
    681.0,
    187
   ],
   [
    "2015-01-01",
    2023,
    "special",
    816.0,
    816
   ],
   [
    "2015-01-01",
    2023,
    "stock",
    647.0,
    178
   ],
   [
    "2015-01-01",
    2024,
    "special",
    887.0,
    887
   ],
   [
    "2015-01-01",
    2024,
    "stock",
    775.0,
    217
   ],
   [
    "2015-01-01",
    2025,
    "special",
    814.0,
    814
   ],
   [
    "2015-01-01",
    2025,
    "stock",
    699.0,
    186
   ],
   [
    "2023-01-01",
    2016,
    "special",
    1937.0,
    1937
   ],
   [
    "2023-01-01",
    2016,
    "stock",
    2457.0,
    519
   ],
   [
    "2023-01-01",
    2022,
    "special",
    712.0,
    712
   ],
   [
    "2023-01-01",
    2022,
    "stock",
    3243.0,
    674
   ],
   [
    "2023-01-01",
    2023,
    "special",
    246.0,
    246
   ],
   [
    "2023-01-01",
    2023,
    "stock",
    235.0,
    89
   ],
   [
    "2023-01-01",
    2024,
    "special",
    762.0,
    762
   ],
   [
    "2023-01-01",
    2024,
    "stock",
    1679.0,
    402
   ],
   [
    "2023-01-01",
    2025,
    "special",
    1038.0,
    1038
   ],
   [
    "2023-01-01",
    2025,
    "stock",
    1686.0,
    377
   ],
   [
    "2025-01-01",
    2016,
    "special",
    5303.0,
    5303
   ],
   [
    "2025-01-01",
    2016,
    "stock",
    7220.0,
    1113
   ],
   [
    "2025-01-01",
    2022,
    "special",
    1981.0,
    1981
   ],
   [
    "2025-01-01",
    2022,
    "stock",
    10657.0,
    1483
   ],
   [
    "2025-01-01",
    2023,
    "special",
    2095.0,
    2095
   ],
   [
    "2025-01-01",
    2023,
    "stock",
    10403.0,
    1423
   ],
   [
    "2025-01-01",
    2024,
    "special",
    2112.0,
    2112
   ],
   [
    "2025-01-01",
    2024,
    "stock",
    10326.0,
    1473
   ],
   [
    "2025-01-01",
    2025,
    "special",
    651.0,
    651
   ],
   [
    "2025-01-01",
    2025,
    "stock",
    582.0,
    190
   ]
  ],
  "error": null
 },
 {
  "id": "q249",
  "sql": "SELECT 312+11 r410a_rtv_units_23_24, round(418497.84+14418.16,2) r410a_rtv_value_23_24, 174+149 r410a_credit_units_23_24, round(185867.84+160464.94,2) r410a_credit_value_23_24,\n round((185867.84+160464.94)/(418497.84+14418.16),3) r410a_credit_to_rtv_23_24,\n 832+51 all_rtv_units_23_24, 492+379 all_credit_units_23_24,\n round(-458003.64-(-2379417.2),2) neg_of_non_r410a_post_disc_gm_2025,\n round(-372468.27-2063781.7-2379417.2,2) post_disc_gm_2023_2025,\n round((-372468.27-2063781.7-2379417.2)/3,2) post_disc_gm_avg_2023_2025,\n 699+1686+582 r410a_2025_stock_po_units_by_cohort,\n round(-458003.64/-2379417.2,3) r410a_share_post_disc_loss_2025",
  "columns": [
   "r410a_rtv_units_23_24",
   "r410a_rtv_value_23_24",
   "r410a_credit_units_23_24",
   "r410a_credit_value_23_24",
   "r410a_credit_to_rtv_23_24",
   "all_rtv_units_23_24",
   "all_credit_units_23_24",
   "neg_of_non_r410a_post_disc_gm_2025",
   "post_disc_gm_2023_2025",
   "post_disc_gm_avg_2023_2025",
   "r410a_2025_stock_po_units_by_cohort",
   "r410a_share_post_disc_loss_2025"
  ],
  "row_count": 1,
  "rows": [
   [
    323,
    432916.0,
    323,
    346332.78,
    0.8,
    883,
    871,
    1921413.56,
    -4815667.17,
    -1605222.39,
    2967,
    0.192
   ]
  ],
  "error": null
 },
 {
  "id": "q175",
  "sql": "WITH p AS (SELECT sku FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT d.year, sum(pl.qty) stock_po_units, round(sum(pl.qty*pl.unit_cost),2) stock_po_value, count(DISTINCT po.po_id) pos\nFROM erp_purchase_orders po JOIN erp_purchase_order_lines pl USING(po_id) JOIN p USING(sku) JOIN dim_date d ON d.day=po.day\nWHERE po.purpose='stock' AND d.year>=2022 GROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "stock_po_units",
   "stock_po_value",
   "pos"
  ],
  "row_count": 4,
  "rows": [
   [
    2022,
    14581.0,
    20790546.11,
    1730
   ],
   [
    2023,
    11285.0,
    16375089.33,
    1467
   ],
   [
    2024,
    12780.0,
    18360402.77,
    1624
   ],
   [
    2025,
    2967.0,
    3968754.27,
    574
   ]
  ],
  "error": null
 },
 {
  "id": "q261",
  "sql": "WITH p AS (SELECT sku, coalesce(nullif(refrigerant,''),'none') refr, discontinued_on disc FROM erp_products WHERE category='equipment' AND discontinued_on IS NOT NULL AND discontinued_on<>''),\nx AS (SELECT d.year, p.refr, l.fulfilment f, l.qty_shipped q, l.unit_price pr, l.unit_cost c\n FROM erp_sales_order_lines l JOIN p USING(sku) JOIN erp_sales_orders o USING(order_id) JOIN dim_date d ON d.day=o.day\n WHERE l.qty_shipped>0 AND d.date>=CAST(p.disc AS DATE) AND d.year BETWEEN 2023 AND 2025),\ny AS (SELECT year,\n sum(CASE WHEN f='stock' THEN q END) stock_units,\n round(sum(CASE WHEN f='stock' THEN q*c END),2) stock_cost,\n round(sum(CASE WHEN f='stock' THEN q*(pr-c) END),2) stock_gm,\n round(sum(CASE WHEN f='stock' AND refr='R-410A' THEN q*(pr-c) END),2) stock_gm_r410a,\n round(sum(CASE WHEN f<>'stock' THEN q*pr END)/sum(CASE WHEN f<>'stock' THEN q*c END),4) nonstock_pc,\n round(sum(CASE WHEN f='stock' THEN q*pr END)/sum(CASE WHEN f='stock' THEN q*c END),4) stock_pc\n FROM x GROUP BY 1)\nSELECT *, round(stock_cost*nonstock_pc - (stock_cost+stock_gm),2) gap_to_nonstock_price FROM y\nUNION ALL\nSELECT 9999, sum(stock_units), sum(stock_cost), sum(stock_gm), sum(stock_gm_r410a), NULL, NULL, round(sum(stock_cost*nonstock_pc-(stock_cost+stock_gm)),2) FROM y\nUNION ALL\nSELECT 9998, round(sum(stock_units)/3,1), round(sum(stock_cost)/3,2), round(-sum(stock_gm)/3,2), round(-sum(stock_gm_r410a)/3,2), NULL, NULL, round(sum(stock_cost*nonstock_pc-(stock_cost+stock_gm))/3,2) FROM y\nORDER BY 1",
  "columns": [
   "year",
   "stock_units",
   "stock_cost",
   "stock_gm",
   "stock_gm_r410a",
   "nonstock_pc",
   "stock_pc",
   "gap_to_nonstock_price"
  ],
  "row_count": 5,
  "rows": [
   [
    2023,
    7249.0,
    7970367.32,
    -408748.5,
    -126528.5,
    1.2057,
    0.9487,
    2048253.06
   ],
   [
    2024,
    7706.0,
    8710559.53,
    -2174845.71,
    -727222.05,
    1.2036,
    0.7503,
    3948315.63
   ],
   [
    2025,
    11866.0,
    14085318.43,
    -2483722.23,
    -493890.27,
    1.2002,
    0.8237,
    5303602.98
   ],
   [
    9998,
    8940.3,
    10255415.09,
    1689105.48,
    449213.61,
    null,
    null,
    3766723.89
   ],
   [
    9999,
    26821.0,
    30766245.28,
    -5067316.4399999995,
    -1347640.82,
    null,
    null,
    11300171.67
   ]
  ],
  "error": null
 },
 {
  "id": "q161",
  "sql": "WITH p AS (SELECT sku, unit_cost, vendor_id FROM erp_products WHERE category='equipment' AND refrigerant='R-410A')\nSELECT 'wms_return_vendor' src, d.year, count(*) n, -sum(t.qty_delta) units, round(-sum(t.qty_delta*p.unit_cost),2) value, count(DISTINCT p.vendor_id) vendors FROM wms_inventory_transactions t JOIN p USING(sku) JOIN dim_date d USING(day) WHERE t.reason='return_vendor' AND d.year>=2023 GROUP BY 1,2\nUNION ALL\nSELECT 'vendor_credit', d.year, count(*), sum(c.qty), round(sum(c.amount),2), count(DISTINCT c.vendor_id) FROM finance_vendor_credits c JOIN p USING(sku) JOIN dim_date d USING(day) WHERE d.year>=2023 GROUP BY 1,2\nORDER BY 1,2",
  "columns": [
   "src",
   "year",
   "n",
   "units",
   "value",
   "vendors"
  ],
  "row_count": 6,
  "rows": [
   [
    "vendor_credit",
    2023,
    108,
    174.0,
    185867.84,
    4
   ],
   [
    "vendor_credit",
    2024,
    95,
    149.0,
    160464.94,
    4
   ],
   [
    "vendor_credit",
    2025,
    387,
    638.0,
    747413.72,
    4
   ],
   [
    "wms_return_vendor",
    2023,
    194,
    312.0,
    418497.84,
    4
   ],
   [
    "wms_return_vendor",
    2024,
    9,
    11.0,
    14418.16,
    4
   ],
   [
    "wms_return_vendor",
    2025,
    616,
    1009.0,
    1476383.18,
    4
   ]
  ],
  "error": null
 },
 {
  "id": "q244",
  "sql": "WITH r AS (SELECT d.year AS yr, -sum(t.qty_delta) u, round(-sum(t.qty_delta*t.unit_cost),2) v FROM wms_inventory_transactions t JOIN dim_date d ON d.day=t.day WHERE t.reason='return_vendor' GROUP BY 1),\nc AS (SELECT d.year AS yr, sum(f.qty) u, round(sum(f.amount),2) v FROM finance_vendor_credits f JOIN dim_date d ON d.day=f.day GROUP BY 1)\nSELECT coalesce(r.yr,c.yr) yr, r.u rtv_units, r.v rtv_value, c.u credit_units, c.v credit_value, round(c.v/r.v,3) credit_to_rtv FROM r FULL JOIN c ON r.yr=c.yr ORDER BY 1",
  "columns": [
   "yr",
   "rtv_units",
   "rtv_value",
   "credit_units",
   "credit_value",
   "credit_to_rtv"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    104.0,
    105209.18,
    55.0,
    54106.46,
    0.514
   ],
   [
    2017,
    90.0,
    95852.96,
    132.0,
    102438.0,
    1.069
   ],
   [
    2018,
    39.0,
    48617.01,
    43.0,
    41144.34,
    0.846
   ],
   [
    2019,
    21.0,
    23307.4,
    23.0,
    19843.73,
    0.851
   ],
   [
    2020,
    23.0,
    24929.99,
    19.0,
    17526.61,
    0.703
   ],
   [
    2021,
    18.0,
    22807.95,
    22.0,
    20963.66,
    0.919
   ],
   [
    2022,
    19.0,
    19020.92,
    14.0,
    12055.07,
    0.634
   ],
   [
    2023,
    832.0,
    1065653.4,
    492.0,
    502966.56,
    0.472
   ],
   [
    2024,
    51.0,
    56057.1,
    379.0,
    385653.31,
    6.88
   ],
   [
    2025,
    1025.0,
    1494165.93,
    670.0,
    772908.76,
    0.517
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

Save `grade.json`: {"finding": "F3", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
