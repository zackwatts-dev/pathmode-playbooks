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
 "id": "F7",
 "hypothesis": "H7",
 "title": "Overdue receivables sit in a persistent 'very slow' tier: customers flagged on 2016-19 data alone (152 accounts, 5.3% of 2020-24 billing) held 29.0% of the 2020-24 overdue balance. No recorded attribute explains the tier, including terms and credit limits.",
 "conclusion": "Narrowed after the challenge. Observed: from 2016 to 2024 the overdue balance averaged 2,980,324, which is 20.0% of the 14,907,566 average total receivables (q343). Customers fall into three lateness tiers: prompt (about 2.4 days late, dollar-weighted), slow (about 8.7) and very slow (about 31) (q274, q278). A customer's tier persists. It also holds out of sample: customers classed on 2016-19 data only kept their tier's lateness in 2020-24 (prompt 2.45, slow 8.71, very slow 31.17). The 152 very slow accounts held 29.0% of the 2020-24 overdue balance on 5.3% of billing (q331). A customer's position within its tier does not persist. Year-to-year correlation inside each tier is 0.021, 0.013 and -0.061 (q341), so the overall 0.94 (q281) reflects only the gaps between tiers. The tier is the thing to act on; a ranking of individual customers is not. Terms, credit limit, size, tenure, discount, credit memos, invoice-question contacts, invoice month, payment method, trade and branch don't explain the tiers. Rep explains little if anything (q278, q283, q284, q289, q336, q337, q339, q347). Sizing: suppose the list had been drawn up in advance and the 152 accounts had been brought to prompt lateness in 2020-24. That would have released 786,932 of receivables, worth 62,955 a year at an assumed 8% (q357). Across scenarios the range runs from 30,760 a year (out-of-sample list moved only to slow lateness, at 5%; q357) to 136,567 a year (in-sample slow and very slow tiers both moved to prompt, at 8%; q343). Every figure is before any sales lost to tighter collections. Action: run a credit/AR review of the very slow tier, piloted against a control group, rather than tightening terms across the board.",
 "dollars_a_year": 62954.5539934848,
 "size_query": "q357",
 "claims": [
  {
   "text": "due_day is the invoice day plus 0, 21 or 31 operating days for 0-, 30- and 45-day terms, so lateness is not an artefact of the day count. Terms-0 accounts (140,772 invoices) are never late, and no invoice is paid before due_day.",
   "queries": [
    "q261",
    "q264"
   ]
  },
  {
   "text": "Every 2016-2024 invoice is paid in one payment for the full amount. All 21,848 unpaid invoices (17.29M) are from 2025, so 2016-2024 is the clean window for sizing.",
   "queries": [
    "q322"
   ]
  },
  {
   "text": "Tiers on all data: 326 very slow customers (20+ days dollar-weighted) hold 5.4% of billing and 33.3% of the overdue balance at 31.13 days late. There are 1,285 slow customers at 8.67 days and 3,813 prompt customers at 2.43 days.",
   "queries": [
    "q274",
    "q278"
   ]
  },
  {
   "text": "Out of sample: classed on 2016-19 (terms customers with at least 10 invoices), the tiers paid 2.45, 8.71 and 31.17 days late in 2020-24. The 152 very slow accounts held 5.3% of 2020-24 billing and 29.0% of the overdue balance. 1,635 customers who were new or had thin records in 2016-19 could not be classed beforehand; they account for 19.5% of billing and 18.5% of the overdue balance.",
   "queries": [
    "q331"
   ]
  },
  {
   "text": "Tier membership persists: 1,152 of 1,171 very-slow customer-years stay very slow the next year (19,109 customer-year pairs, Pearson 0.94, Spearman 0.64). Within a tier, lateness doesn't persist: within-tier year-to-year Pearson is 0.021 for prompt (13,313 pairs), 0.013 for slow (4,613) and -0.061 for very slow (1,183).",
   "queries": [
    "q281",
    "q341"
   ]
  },
  {
   "text": "No recorded attribute explains the tiers. Prompt against very slow: median invoice 1,042 against 1,054. Credit memos per invoice 0.0047 against 0.0050. Invoice-question contacts per invoice 0.0406 against 0.0413. Onboarded before 2016: 52.5% against 56.7%. Average discount 14.15% against 13.90%. Share on 45-day terms is 16.4%, 17.0% and 18.7% across the three tiers. Check and ACH payers show the same lateness. The very slow share is 5.1-6.2% by trade and 3.3-7.5% by branch. Across 36 reps, the very slow share has SD 0.021 against about 0.017 expected by chance.",
   "queries": [
    "q336",
    "q278",
    "q283",
    "q284",
    "q289",
    "q337"
   ]
  },
  {
   "text": "Credit limit carries no usable signal. Across 6,025 customers it correlates -0.009 with billing and 0.006 with lateness. Equal limits across tiers therefore do not show that credit policy was tried and failed.",
   "queries": [
    "q347",
    "q287"
   ]
  },
  {
   "text": "No seasonality: dollar-weighted lateness by invoice month runs 5.66-5.75 days for 2016-2024, while monthly billing ranges from 64.2M to 126.2M.",
   "queries": [
    "q339"
   ]
  },
  {
   "text": "2025 is censored. 28.5% of very slow customers' 2025 invoices are unpaid, against 15.7% for prompt customers. The 2025 low point in the very slow share of overdue (30.3%) is therefore not an improvement.",
   "queries": [
    "q327",
    "q293"
   ]
  },
  {
   "text": "Sizing. Out of sample for 2020-24: the 152 pre-classed very slow accounts hold 786,932 of receivables in excess of prompt lateness, worth 62,955 a year at 8%. Measured against slow lateness instead, the excess is 615,203, worth 30,760 a year at 5%. Adding the pre-classed slow tier at prompt lateness brings the total to 111,103 a year at 8%. In sample for 2016-24: 1,707,089 excess across the slow and very slow tiers, worth 136,567 a year at 8% (85,354 at 5%). Very slow alone is 921,328, worth 73,706 a year. The released receivables are a one-time release of cash; only the carrying cost recurs.",
   "queries": [
    "q357",
    "q343"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Credit risk or bad debt: every 2016-24 invoice is paid in full. That terms or limits are too generous, or that tightening them would work: limits track neither size nor lateness, and there's no history of terms or limits. Why accounts pay late: credit memos and invoice-question contacts don't differ by tier, and there are no dispute or dunning records. That collections effort would recover the sized amount: the figures rest on an assumed rate and ignore lost sales. That any rep or staff member is responsible: rep variation is close to chance. Interpretation: flat tiers with no persistence inside them, no seasonality and identical attributes look more like how the records were generated than like real payer behaviour. Treat the tiers as the record as given, not as established behaviour.",
 "could_not_tell": "Why these accounts pay late (disputes, deductions, cash-flow trouble, an informal agreement). Whether credit holds were ever applied, or whether credit limits are enforced. Whether early-pay discounts or late fees exist. How many sales tighter collections would cost. Answering these would take an AR adjustments ledger, collection activity logs, effective-dated credit terms and limits, and an order-to-collection history before and after any intervention.",
 "next_step": "Draw the very slow list from the most recent complete years with at least 10 invoices per customer (the q331 logic). Expect about a fifth of future overdue dollars to come from accounts not yet classifiable. Review the list with credit/AR for disputes or standing arrangements. Then randomise half the list to collection calls at due_day + 5 and keep half as a control. Measure the change in days late and in billing against the stable 31-day baseline. Confirm with finance whether credit limits are maintained or enforced.",
 "incomplete": false
}

[
 {
  "id": "q261",
  "sql": "SELECT c.terms_days, i.due_day - i.day AS gap, count(*) n, avg(p.day - i.due_day) avg_late, avg(CASE WHEN p.day > i.due_day THEN 1.0 ELSE 0 END) late_share\nFROM finance_invoices i JOIN erp_customers c USING(customer_id) LEFT JOIN finance_customer_payments p USING(invoice_id)\nGROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "terms_days",
   "gap",
   "n",
   "avg_late",
   "late_share"
  ],
  "row_count": 3,
  "rows": [
   [
    0,
    0,
    140772,
    0.0,
    0.0
   ],
   [
    30,
    21,
    1021494,
    5.647119797428425,
    0.6639735524633527
   ],
   [
    45,
    31,
    226399,
    5.680701485403007,
    0.6737971457471101
   ]
  ],
  "error": null
 },
 {
  "id": "q264",
  "sql": "SELECT c.terms_days, p.day - i.due_day AS late, count(*) n\nFROM finance_invoices i JOIN erp_customers c USING(customer_id) JOIN finance_customer_payments p USING(invoice_id)\nGROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "terms_days",
   "late",
   "n"
  ],
  "row_count": 169,
  "rows": [
   [
    0,
    0,
    140772
   ],
   [
    30,
    0,
    326042
   ],
   [
    30,
    1,
    75879
   ],
   [
    30,
    2,
    76367
   ],
   [
    30,
    3,
    72980
   ],
   [
    30,
    4,
    67347
   ],
   [
    30,
    5,
    59068
   ],
   [
    30,
    6,
    49701
   ],
   [
    30,
    7,
    41077
   ],
   [
    30,
    8,
    32814
   ],
   [
    30,
    9,
    26479
   ],
   [
    30,
    10,
    21513
   ],
   [
    30,
    11,
    17723
   ],
   [
    30,
    12,
    15045
   ],
   [
    30,
    13,
    12804
   ],
   [
    30,
    14,
    11096
   ],
   [
    30,
    15,
    9607
   ],
   [
    30,
    16,
    8488
   ],
   [
    30,
    17,
    7156
   ],
   [
    30,
    18,
    6181
   ],
   [
    30,
    19,
    5321
   ],
   [
    30,
    20,
    4535
   ],
   [
    30,
    21,
    3930
   ],
   [
    30,
    22,
    3309
   ],
   [
    30,
    23,
    2923
   ],
   [
    30,
    24,
    2686
   ],
   [
    30,
    25,
    2298
   ],
   [
    30,
    26,
    2172
   ],
   [
    30,
    27,
    2135
   ],
   [
    30,
    28,
    2009
   ],
   [
    30,
    29,
    1860
   ],
   [
    30,
    30,
    1813
   ],
   [
    30,
    31,
    1824
   ],
   [
    30,
    32,
    1780
   ],
   [
    30,
    33,
    1826
   ],
   [
    30,
    34,
    1775
   ],
   [
    30,
    35,
    1685
   ],
   [
    30,
    36,
    1665
   ],
   [
    30,
    37,
    1654
   ],
   [
    30,
    38,
    1582
   ],
   [
    30,
    39,
    1507
   ],
   [
    30,
    40,
    1409
   ],
   [
    30,
    41,
    1321
   ],
   [
    30,
    42,
    1314
   ],
   [
    30,
    43,
    1196
   ],
   [
    30,
    44,
    1179
   ],
   [
    30,
    45,
    1078
   ],
   [
    30,
    46,
    982
   ],
   [
    30,
    47,
    906
   ],
   [
    30,
    48,
    828
   ],
   [
    30,
    49,
    741
   ],
   [
    30,
    50,
    712
   ],
   [
    30,
    51,
    628
   ],
   [
    30,
    52,
    568
   ],
   [
    30,
    53,
    522
   ],
   [
    30,
    54,
    440
   ],
   [
    30,
    55,
    417
   ],
   [
    30,
    56,
    314
   ],
   [
    30,
    57,
    316
   ],
   [
    30,
    58,
    282
   ]
  ],
  "error": null
 },
 {
  "id": "q322",
  "sql": "WITH pc AS (SELECT invoice_id, count(*) np, sum(amount) pamt, min(day) pday FROM finance_customer_payments GROUP BY 1)\nSELECT d.year, count(*) inv, sum(CASE WHEN pc.invoice_id IS NULL THEN 1 ELSE 0 END) unpaid, sum(CASE WHEN pc.invoice_id IS NULL THEN i.amount ELSE 0 END) unpaid_amt,\n sum(CASE WHEN np>1 THEN 1 ELSE 0 END) multi_pay, sum(CASE WHEN pc.invoice_id IS NOT NULL AND abs(pamt-i.amount)>0.01 THEN 1 ELSE 0 END) amt_mismatch,\n sum(CASE WHEN pc.invoice_id IS NOT NULL THEN i.amount-pamt ELSE 0 END) short_paid, min(i.day) minday, max(i.day) maxday\nFROM finance_invoices i JOIN dim_date d ON d.day=i.day LEFT JOIN pc USING(invoice_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "inv",
   "unpaid",
   "unpaid_amt",
   "multi_pay",
   "amt_mismatch",
   "short_paid",
   "minday",
   "maxday"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    141732,
    0,
    0.0,
    0,
    0,
    0.0,
    1,
    252
   ],
   [
    2017,
    137195,
    0,
    0.0,
    0,
    0,
    0.0,
    253,
    504
   ],
   [
    2018,
    155221,
    0,
    0.0,
    0,
    0,
    0.0,
    505,
    756
   ],
   [
    2019,
    148017,
    0,
    0.0,
    0,
    0,
    0.0,
    757,
    1008
   ],
   [
    2020,
    138239,
    0,
    0.0,
    0,
    0,
    0.0,
    1009,
    1260
   ],
   [
    2021,
    139769,
    0,
    0.0,
    0,
    0,
    0.0,
    1261,
    1512
   ],
   [
    2022,
    143388,
    0,
    0.0,
    0,
    0,
    0.0,
    1513,
    1764
   ],
   [
    2023,
    119782,
    0,
    0.0,
    0,
    0,
    0.0,
    1765,
    2016
   ],
   [
    2024,
    125321,
    0,
    0.0,
    0,
    0,
    0.0,
    2017,
    2268
   ],
   [
    2025,
    140001,
    21848,
    17294845.149999928,
    0,
    0,
    0.0,
    2269,
    2520
   ]
  ],
  "error": null
 },
 {
  "id": "q274",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate, count(*) n\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id JOIN erp_customers c ON c.customer_id=i.customer_id WHERE c.terms_days>0 GROUP BY 1)\nSELECT floor(wlate/2)*2 bucket, count(*) customers, sum(n) invoices FROM x GROUP BY 1 ORDER BY 1",
  "columns": [
   "bucket",
   "customers",
   "invoices"
  ],
  "row_count": 25,
  "rows": [
   [
    0.0,
    825,
    37288
   ],
   [
    2.0,
    2833,
    816592
   ],
   [
    4.0,
    155,
    2242
   ],
   [
    6.0,
    289,
    21186
   ],
   [
    8.0,
    802,
    267729
   ],
   [
    10.0,
    145,
    7300
   ],
   [
    12.0,
    33,
    530
   ],
   [
    14.0,
    10,
    80
   ],
   [
    16.0,
    5,
    22
   ],
   [
    18.0,
    1,
    1
   ],
   [
    20.0,
    6,
    40
   ],
   [
    22.0,
    8,
    47
   ],
   [
    24.0,
    8,
    138
   ],
   [
    26.0,
    22,
    1375
   ],
   [
    28.0,
    48,
    7831
   ],
   [
    30.0,
    139,
    53043
   ],
   [
    32.0,
    48,
    8258
   ],
   [
    34.0,
    27,
    1847
   ],
   [
    36.0,
    9,
    287
   ],
   [
    38.0,
    5,
    142
   ],
   [
    40.0,
    1,
    35
   ],
   [
    42.0,
    1,
    6
   ],
   [
    44.0,
    1,
    12
   ],
   [
    46.0,
    2,
    11
   ],
   [
    54.0,
    1,
    3
   ]
  ],
  "error": null
 },
 {
  "id": "q278",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount) billed, sum(i.amount*greatest(p.day-i.due_day,0)) od_dd, count(*) n,\n  sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT x.*, c.terms_days, c.credit_limit, c.trade, CASE WHEN c.terms_days=0 THEN '0 terms' WHEN wlate<6 THEN 'A prompt <6' WHEN wlate<20 THEN 'B slow 6-20' ELSE 'C very slow 20+' END seg FROM x JOIN erp_customers c USING(customer_id))\nSELECT seg, count(*) customers, sum(n) invoices, sum(billed) billed, sum(billed)/(SELECT sum(billed) FROM s) billed_share, sum(od_dd)/(SELECT sum(od_dd) FROM s) od_share, sum(od_dd)/2520 avg_overdue_bal, sum(od_dd)/sum(billed) wlate, avg(credit_limit) avg_cl, median(credit_limit) med_cl, avg(CASE WHEN terms_days=45 THEN 1.0 ELSE 0 END) share_45\nFROM s GROUP BY 1 ORDER BY 1",
  "columns": [
   "seg",
   "customers",
   "invoices",
   "billed",
   "billed_share",
   "od_share",
   "avg_overdue_bal",
   "wlate",
   "avg_cl",
   "med_cl",
   "share_45"
  ],
  "row_count": 4,
  "rows": [
   [
    "0 terms",
    601,
    140772,
    147688604.03999996,
    0.10251991913786968,
    0.0,
    0.0,
    0.0,
    20082.26540765391,
    14098.73,
    0.0
   ],
   [
    "A prompt <6",
    3813,
    856122,
    906393341.2399997,
    0.6291844428691392,
    0.30173988277784025,
    875774.433234127,
    2.434871783955032,
    21097.34035929714,
    14480.72,
    0.16391292945187516
   ],
   [
    "B slow 6-20",
    1285,
    296848,
    308288032.09000003,
    0.2140020506421721,
    0.3654060268195537,
    1060560.0197499995,
    8.669202082388233,
    21859.4313229572,
    14565.55,
    0.16964980544747083
   ],
   [
    "C very slow 20+",
    326,
    73075,
    78214499.11,
    0.05429358735081847,
    0.33285409040260644,
    966080.7835158729,
    31.12624388268616,
    21089.15073619632,
    14565.255000000001,
    0.18711656441717792
   ]
  ],
  "error": null
 },
 {
  "id": "q331",
  "sql": "WITH base AS (SELECT i.customer_id, d.year, i.amount, greatest(p.day-i.due_day,0) late FROM finance_invoices i JOIN finance_customer_payments p USING(invoice_id) JOIN dim_date d ON d.day=i.day JOIN erp_customers c ON c.customer_id=i.customer_id WHERE c.terms_days>0),\ntr AS (SELECT customer_id, sum(amount*late)/sum(amount) wl, count(*) n FROM base WHERE year BETWEEN 2016 AND 2019 GROUP BY 1 HAVING count(*)>=10),\ns AS (SELECT customer_id, CASE WHEN wl<6 THEN 'A' WHEN wl<20 THEN 'B' ELSE 'C' END seg FROM tr)\nSELECT coalesce(s.seg,'unclassified (new/thin in 2016-19)') seg, count(DISTINCT b.customer_id) cust, sum(b.amount)/(SELECT sum(amount) FROM base WHERE year BETWEEN 2020 AND 2024) billed_share,\n sum(b.amount*b.late)/(SELECT sum(amount*late) FROM base WHERE year BETWEEN 2020 AND 2024) od_share, sum(b.amount*b.late)/sum(b.amount) wlate_test\nFROM base b LEFT JOIN s USING(customer_id) WHERE b.year BETWEEN 2020 AND 2024 GROUP BY 1 ORDER BY 1",
  "columns": [
   "seg",
   "cust",
   "billed_share",
   "od_share",
   "wlate_test"
  ],
  "row_count": 4,
  "rows": [
   [
    "A",
    1621,
    0.5652803516347319,
    0.24091178925090742,
    2.445018080190937
   ],
   [
    "B",
    572,
    0.1868921436391551,
    0.2838812358524791,
    8.714321007471689
   ],
   [
    "C",
    152,
    0.053326346055235424,
    0.2897615619137018,
    31.17359288416633
   ],
   [
    "unclassified (new/thin in 2016-19)",
    1635,
    0.1945011586708776,
    0.18544541298290848,
    5.469930580661732
   ]
  ],
  "error": null
 },
 {
  "id": "q281",
  "sql": "WITH y AS (\n SELECT i.customer_id, d.year, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate, count(*) n\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id JOIN dim_date d ON d.day=i.day JOIN erp_customers c ON c.customer_id=i.customer_id\n WHERE c.terms_days>0 GROUP BY 1,2 HAVING count(*)>=5),\nz AS (SELECT a.customer_id, a.year, a.wlate w0, b.wlate w1 FROM y a JOIN y b ON a.customer_id=b.customer_id AND b.year=a.year+1)\nSELECT count(*) pairs, count(DISTINCT customer_id) customers, corr(w0,w1) pearson, corr(rank_w0, rank_w1) spearman,\n sum(CASE WHEN w0>=20 THEN 1 END) vs_pairs, sum(CASE WHEN w0>=20 AND w1>=20 THEN 1 END) vs_stay,\n sum(CASE WHEN w0<6 THEN 1 END) prompt_pairs, sum(CASE WHEN w0<6 AND w1<6 THEN 1 END) prompt_stay\nFROM (SELECT *, rank() OVER (ORDER BY w0) rank_w0, rank() OVER (ORDER BY w1) rank_w1 FROM z)",
  "columns": [
   "pairs",
   "customers",
   "pearson",
   "spearman",
   "vs_pairs",
   "vs_stay",
   "prompt_pairs",
   "prompt_stay"
  ],
  "row_count": 1,
  "rows": [
   [
    19109,
    4057,
    0.9413881600314223,
    0.6401115640962194,
    1171,
    1152,
    13574,
    13189
   ]
  ],
  "error": null
 },
 {
  "id": "q341",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.customer_id, CASE WHEN c.terms_days=0 THEN '0' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id)),\ny AS (\n SELECT i.customer_id, d.year, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate, count(*) n\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id JOIN dim_date d ON d.day=i.day\n GROUP BY 1,2 HAVING count(*)>=5),\nz AS (SELECT a.customer_id, a.wlate w0, b.wlate w1 FROM y a JOIN y b ON a.customer_id=b.customer_id AND b.year=a.year+1)\nSELECT seg, count(*) pairs, corr(w0,w1) pearson_within, avg(w0) mean_w0, stddev_samp(w0) sd_w0\nFROM z JOIN s USING(customer_id) WHERE seg<>'0' GROUP BY 1 ORDER BY 1",
  "columns": [
   "seg",
   "pairs",
   "pearson_within",
   "mean_w0",
   "sd_w0"
  ],
  "row_count": 3,
  "rows": [
   [
    "A",
    13313,
    0.02061777388528758,
    2.4424364677315515,
    0.9903811704325554
   ],
   [
    "B",
    4613,
    0.012618004977148153,
    8.758875194008242,
    2.092314107740763
   ],
   [
    "C",
    1183,
    -0.06053489001324526,
    31.100992761532666,
    4.351635281780609
   ]
  ],
  "error": null
 },
 {
  "id": "q336",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount) billed, count(*) n, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate, avg(i.amount) avg_inv\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT x.*, c.onboarded_day, c.discount_pct, c.rep_id, CASE WHEN c.terms_days=0 THEN '0' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id)),\ncm AS (SELECT customer_id, count(*) n_cm, sum(amount) cm_amt FROM finance_credit_memos GROUP BY 1),\nsc AS (SELECT customer_id, count(*) n_sc, sum(CASE WHEN subject='Invoice question' THEN 1 ELSE 0 END) n_inv_q FROM crm_service_contacts GROUP BY 1)\nSELECT seg, count(*) cust, median(billed) med_billed, median(n) med_inv, median(avg_inv) med_avg_inv, avg(CASE WHEN onboarded_day<0 THEN 1.0 ELSE 0 END) pre2016, median(onboarded_day) med_onb, avg(discount_pct) avg_disc,\n sum(coalesce(n_cm,0))/sum(n) cm_per_inv, sum(coalesce(cm_amt,0))/sum(billed) cm_amt_share, sum(coalesce(n_sc,0))/sum(n) contacts_per_inv, sum(coalesce(n_inv_q,0))/sum(n) invq_per_inv,\n count(DISTINCT rep_id) reps\nFROM s LEFT JOIN cm USING(customer_id) LEFT JOIN sc USING(customer_id) GROUP BY 1 ORDER BY 1",
  "columns": [
   "seg",
   "cust",
   "med_billed",
   "med_inv",
   "med_avg_inv",
   "pre2016",
   "med_onb",
   "avg_disc",
   "cm_per_inv",
   "cm_amt_share",
   "contacts_per_inv",
   "invq_per_inv",
   "reps"
  ],
  "row_count": 4,
  "rows": [
   [
    "0",
    601,
    89695.67,
    86.0,
    1039.4812359550563,
    0.5257903494176372,
    -166.0,
    0.13868103161397655,
    0.005121757167618561,
    0.0022978584042143515,
    0.1495041627596397,
    0.040078992981558835,
    36
   ],
   [
    "A",
    3813,
    74466.66,
    71.0,
    1042.0275862068966,
    0.5247836349331235,
    -93.0,
    0.14151091004458424,
    0.004685079930196865,
    0.00230891019911615,
    0.15720539829603725,
    0.04057132044264719,
    36
   ],
   [
    "B",
    1285,
    85210.73,
    83.0,
    1043.6599259259258,
    0.5058365758754864,
    -24.0,
    0.14103750972762655,
    0.004517463482994664,
    0.002190862017643363,
    0.15217215544655852,
    0.04002048186277152,
    36
   ],
   [
    "C",
    326,
    70390.415,
    71.5,
    1053.781046875,
    0.5674846625766872,
    -245.0,
    0.13898711656441728,
    0.0049674991447143345,
    0.0022213376289177906,
    0.1536229900786863,
    0.04127266507013343,
    36
   ]
  ],
  "error": null
 },
 {
  "id": "q283",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT x.customer_id, c.trade, c.branch, CASE WHEN c.terms_days=0 THEN '0 terms' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id))\nSELECT s.seg, p.method, count(*) n, avg(p.day-i.due_day) avg_late, avg(CASE WHEN p.day>i.due_day THEN 1.0 ELSE 0 END) late_share\nFROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id JOIN s ON s.customer_id=i.customer_id\nGROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "seg",
   "method",
   "n",
   "avg_late",
   "late_share"
  ],
  "row_count": 8,
  "rows": [
   [
    "0 terms",
    "ACH",
    63076,
    0.0,
    0.0
   ],
   [
    "0 terms",
    "check",
    77696,
    0.0,
    0.0
   ],
   [
    "A",
    "ACH",
    385804,
    2.4353350405905587,
    0.5845766243999544
   ],
   [
    "A",
    "check",
    470318,
    2.431676014951586,
    0.5842748948583725
   ],
   [
    "B",
    "ACH",
    133769,
    8.665924093026037,
    0.8709790758695961
   ],
   [
    "B",
    "check",
    163079,
    8.689481784901796,
    0.8699096756786588
   ],
   [
    "C",
    "ACH",
    33021,
    31.046848974894765,
    0.9860089034250932
   ],
   [
    "C",
    "check",
    40054,
    31.116617566285516,
    0.9869675937484396
   ]
  ],
  "error": null
 },
 {
  "id": "q284",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.*, CASE WHEN c.terms_days=0 THEN '0 terms' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id))\nSELECT trade, count(*) n, avg(CASE WHEN seg='C' THEN 1.0 ELSE 0 END) c_share, avg(CASE WHEN seg='B' THEN 1.0 ELSE 0 END) b_share, avg(CASE WHEN seg='0 terms' THEN 1.0 ELSE 0 END) zero_share,\n avg(CASE WHEN onboarded_day<0 THEN 1.0 ELSE 0 END) pre2016\nFROM s GROUP BY ROLLUP(trade) ORDER BY 1",
  "columns": [
   "trade",
   "n",
   "c_share",
   "b_share",
   "zero_share",
   "pre2016"
  ],
  "row_count": 4,
  "rows": [
   [
    "commercial",
    1193,
    0.05699916177703269,
    0.21877619446772842,
    0.08801341156747695,
    0.5196982397317687
   ],
   [
    "mixed",
    1081,
    0.061979648473635525,
    0.20259019426456984,
    0.1036077705827937,
    0.5208140610545791
   ],
   [
    "residential",
    3751,
    0.05091975473207145,
    0.21460943748333777,
    0.10237270061316982,
    0.5249266862170088
   ],
   [
    null,
    6025,
    0.054107883817427385,
    0.21327800829875518,
    0.09975103734439834,
    0.5231535269709544
   ]
  ],
  "error": null
 },
 {
  "id": "q289",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate, sum(i.amount*greatest(p.day-i.due_day,0)) od\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1)\nSELECT c.branch, count(*) n, avg(CASE WHEN c.terms_days>0 AND wlate>=20 THEN 1.0 ELSE 0 END) c_share, sum(od)/2520 avg_overdue_bal\nFROM x JOIN erp_customers c USING(customer_id) GROUP BY 1 ORDER BY 3 DESC",
  "columns": [
   "branch",
   "n",
   "c_share",
   "avg_overdue_bal"
  ],
  "row_count": 12,
  "rows": [
   [
    "Fort Wayne",
    147,
    0.07482993197278912,
    72216.77721428574
   ],
   [
    "Lexington",
    188,
    0.06382978723404255,
    97991.13298015871
   ],
   [
    "Indianapolis",
    721,
    0.06241331484049931,
    321464.47457936546
   ],
   [
    "Troy",
    461,
    0.06073752711496746,
    259596.66162301556
   ],
   [
    "Cleveland",
    803,
    0.058530510585305104,
    353589.9229365075
   ],
   [
    "Cincinnati",
    788,
    0.0583756345177665,
    428131.24537698406
   ],
   [
    "Akron",
    255,
    0.054901960784313725,
    152553.1716349206
   ],
   [
    "Pittsburgh",
    903,
    0.053156146179401995,
    435225.7982301588
   ],
   [
    "Louisville",
    473,
    0.0507399577167019,
    194519.39176984117
   ],
   [
    "Toledo",
    236,
    0.046610169491525424,
    106532.6851626984
   ],
   [
    "Columbus",
    743,
    0.040376850605652756,
    369681.7066150795
   ],
   [
    "Dayton",
    307,
    0.03257328990228013,
    110912.26837698415
   ]
  ],
  "error": null
 },
 {
  "id": "q337",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.customer_id, c.rep_id, CASE WHEN c.terms_days=0 THEN '0' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id)),\nr AS (SELECT rep_id, count(*) n, avg(CASE WHEN seg='C' THEN 1.0 ELSE 0 END) c_share FROM s GROUP BY 1)\nSELECT count(*) reps, min(n) min_cust, max(n) max_cust, min(c_share) min_c, max(c_share) max_c, quantile_cont(c_share,0.1) p10, quantile_cont(c_share,0.9) p90, stddev_samp(c_share) sd_c, sqrt(0.0541*(1-0.0541)/avg(n)) binom_sd_expected FROM r",
  "columns": [
   "reps",
   "min_cust",
   "max_cust",
   "min_c",
   "max_c",
   "p10",
   "p90",
   "sd_c",
   "binom_sd_expected"
  ],
  "row_count": 1,
  "rows": [
   [
    36,
    47,
    312,
    0.020242914979757085,
    0.13725490196078433,
    0.03176823176823177,
    0.07407813871817384,
    0.021071484800148806,
    0.01748614075981888
   ]
  ],
  "error": null
 },
 {
  "id": "q347",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount) billed, count(*) n, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1)\nSELECT count(*) n, corr(c.credit_limit, x.billed) corr_cl_billed, corr(c.credit_limit, x.wlate) corr_cl_wlate, corr(c.discount_pct, x.wlate) corr_disc_wlate,\n sum(CASE WHEN c.terms_days>0 AND x.wlate>=20 AND x.n<20 THEN 1 ELSE 0 END) c_thin_lt20inv, sum(CASE WHEN c.terms_days>0 AND x.wlate>=20 THEN 1 ELSE 0 END) c_total\nFROM x JOIN erp_customers c USING(customer_id)",
  "columns": [
   "n",
   "corr_cl_billed",
   "corr_cl_wlate",
   "corr_disc_wlate",
   "c_thin_lt20inv",
   "c_total"
  ],
  "row_count": 1,
  "rows": [
   [
    6025,
    -0.009269086419864394,
    0.005844514740542606,
    -0.0003663745413841957,
    75,
    326
   ]
  ],
  "error": null
 },
 {
  "id": "q287",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate,\n  sum(i.amount*(p.day-i.day))/(max(p.day)-min(i.day)+1) avg_ar\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.*, x.avg_ar, CASE WHEN c.terms_days=0 THEN '0 terms' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id))\nSELECT seg, count(*) n, median(avg_ar) med_avg_ar, median(credit_limit) med_cl, median(avg_ar/credit_limit) med_util, avg(CASE WHEN avg_ar>credit_limit THEN 1.0 ELSE 0 END) share_avg_ar_over_limit, corr(credit_limit, avg_ar) corr_cl_ar\nFROM s GROUP BY 1 ORDER BY 1",
  "columns": [
   "seg",
   "n",
   "med_avg_ar",
   "med_cl",
   "med_util",
   "share_avg_ar_over_limit",
   "corr_cl_ar"
  ],
  "row_count": 4,
  "rows": [
   [
    "0 terms",
    601,
    0.0,
    14098.73,
    0.0,
    0.0,
    NaN
   ],
   [
    "A",
    3813,
    2055.658310708899,
    14480.72,
    0.13986477698555982,
    0.0920535011801731,
    -0.004048033633244848
   ],
   [
    "B",
    1285,
    2782.5744396014948,
    14565.55,
    0.19549435772181215,
    0.12762645914396886,
    -0.005950323860806251
   ],
   [
    "C",
    326,
    4020.073629939261,
    14565.255000000001,
    0.253649101812355,
    0.2085889570552147,
    -0.06530476354047247
   ]
  ],
  "error": null
 },
 {
  "id": "q339",
  "sql": "SELECT d.month, count(*) n, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate, sum(i.amount) billed\nFROM finance_invoices i JOIN finance_customer_payments p USING(invoice_id) JOIN dim_date d ON d.day=i.day JOIN erp_customers c ON c.customer_id=i.customer_id\nWHERE c.terms_days>0 AND d.year BETWEEN 2016 AND 2024 GROUP BY 1 ORDER BY 1",
  "columns": [
   "month",
   "n",
   "wlate",
   "billed"
  ],
  "row_count": 12,
  "rows": [
   [
    1,
    162564,
    5.700710460063425,
    126234777.46000013
   ],
   [
    2,
    133002,
    5.698837438805698,
    111442519.86999948
   ],
   [
    3,
    111094,
    5.721171133658276,
    101096253.1599998
   ],
   [
    4,
    68828,
    5.66272411925742,
    69433516.35000008
   ],
   [
    5,
    57738,
    5.747007720321004,
    92361770.84000014
   ],
   [
    6,
    65044,
    5.687051807041441,
    110717901.29999968
   ],
   [
    7,
    74249,
    5.74931284106716,
    102359638.55999976
   ],
   [
    8,
    60841,
    5.717317889769414,
    81528680.32999986
   ],
   [
    9,
    44645,
    5.6930119255087455,
    64157995.81999993
   ],
   [
    10,
    76987,
    5.660777033136622,
    101686627.34999971
   ],
   [
    11,
    118578,
    5.670277141543479,
    106134105.08999997
   ],
   [
    12,
    147902,
    5.734986953176475,
    117752708.08000027
   ]
  ],
  "error": null
 },
 {
  "id": "q327",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.customer_id, CASE WHEN c.terms_days=0 THEN '0' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id))\nSELECT coalesce(s.seg,'no paid inv') seg, count(*) inv_2025, sum(CASE WHEN p.invoice_id IS NULL THEN 1 ELSE 0 END) unpaid, avg(CASE WHEN p.invoice_id IS NULL THEN 1.0 ELSE 0 END) unpaid_share,\n sum(CASE WHEN p.invoice_id IS NULL THEN i.amount END) unpaid_amt, avg(CASE WHEN p.invoice_id IS NULL THEN 2520-i.due_day END) avg_days_past_due_at_end,\n sum(CASE WHEN p.invoice_id IS NULL AND i.due_day<2520 THEN 1 ELSE 0 END) unpaid_past_due\nFROM finance_invoices i LEFT JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id LEFT JOIN s ON s.customer_id=i.customer_id JOIN dim_date d ON d.day=i.day\nWHERE d.year=2025 GROUP BY 1 ORDER BY 1",
  "columns": [
   "seg",
   "inv_2025",
   "unpaid",
   "unpaid_share",
   "unpaid_amt",
   "avg_days_past_due_at_end",
   "unpaid_past_due"
  ],
  "row_count": 5,
  "rows": [
   [
    "0",
    13580,
    0,
    0.0,
    null,
    null,
    0
   ],
   [
    "A",
    90040,
    14165,
    0.1573189693469569,
    11133821.579999985,
    -11.04680550653018,
    841
   ],
   [
    "B",
    28366,
    5326,
    0.1877599943594444,
    4168873.65000001,
    -8.507134810364251,
    1054
   ],
   [
    "C",
    7909,
    2251,
    0.2846124668099633,
    1891967.3500000013,
    -0.4264771212794314,
    948
   ],
   [
    "no paid inv",
    106,
    106,
    1.0,
    100182.57000000008,
    -11.226415094339623,
    7
   ]
  ],
  "error": null
 },
 {
  "id": "q293",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.customer_id, CASE WHEN c.terms_days=0 THEN '0' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id))\nSELECT d.year, count(*) invoices,\n sum(i.amount*greatest(p.day-i.due_day,0))/252 avg_overdue_bal,\n sum(CASE WHEN seg='C' THEN i.amount*greatest(p.day-i.due_day,0) END)/252 c_overdue_bal,\n sum(CASE WHEN seg='C' THEN i.amount*greatest(p.day-i.due_day,0) END)/sum(i.amount*greatest(p.day-i.due_day,0)) c_share,\n sum(CASE WHEN seg='C' THEN i.amount END)/sum(i.amount) c_billed_share,\n count(DISTINCT CASE WHEN seg='C' THEN i.customer_id END) c_customers\nFROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id JOIN s ON s.customer_id=i.customer_id JOIN dim_date d ON d.day=i.day\nGROUP BY 1 ORDER BY 1",
  "columns": [
   "year",
   "invoices",
   "avg_overdue_bal",
   "c_overdue_bal",
   "c_share",
   "c_billed_share",
   "c_customers"
  ],
  "row_count": 10,
  "rows": [
   [
    2016,
    141732,
    2630103.9767460264,
    821621.5561111105,
    0.31239128314905,
    0.050596315103524706,
    192
   ],
   [
    2017,
    137195,
    2908062.757301601,
    911171.074047619,
    0.31332579455509996,
    0.05083438796112638,
    181
   ],
   [
    2018,
    155221,
    3271697.5359523753,
    1029918.2509523846,
    0.3147962914159118,
    0.05132026736912155,
    177
   ],
   [
    2019,
    148017,
    3278425.8792063473,
    1125638.3662301588,
    0.34334720616061554,
    0.057138411546063375,
    175
   ],
   [
    2020,
    138239,
    3223941.369166667,
    1188414.4355952358,
    0.368621603035672,
    0.0627661151880088,
    177
   ],
   [
    2021,
    139769,
    3163335.498095246,
    1095658.0786111166,
    0.346361642409049,
    0.05733571385255264,
    183
   ],
   [
    2022,
    143388,
    3125554.3576984266,
    1049438.6044841264,
    0.3357607913294794,
    0.05418432982739784,
    178
   ],
   [
    2023,
    119782,
    2591364.25123016,
    871225.0837698448,
    0.33620325022090625,
    0.05602734683996803,
    174
   ],
   [
    2024,
    125321,
    2630432.4146428527,
    900338.7955555532,
    0.34227786676579436,
    0.05453884906548785,
    175
   ],
   [
    2025,
    118153,
    2201234.3249603137,
    667383.5898015872,
    0.303186072574813,
    0.046217266776840314,
    180
   ]
  ],
  "error": null
 },
 {
  "id": "q357",
  "sql": "WITH base AS (SELECT i.customer_id, d.year, i.amount, greatest(p.day-i.due_day,0) late FROM finance_invoices i JOIN finance_customer_payments p USING(invoice_id) JOIN dim_date d ON d.day=i.day JOIN erp_customers c ON c.customer_id=i.customer_id WHERE c.terms_days>0),\ntr AS (SELECT customer_id, sum(amount*late)/sum(amount) wl FROM base WHERE year BETWEEN 2016 AND 2019 GROUP BY 1 HAVING count(*)>=10),\ns AS (SELECT customer_id, CASE WHEN wl<6 THEN 'A' WHEN wl<20 THEN 'B' ELSE 'C' END seg FROM tr),\nt AS (SELECT b.*, s.seg FROM base b JOIN s USING(customer_id) WHERE b.year BETWEEN 2020 AND 2024),\nra AS (SELECT sum(amount*late)/sum(amount) a_rate FROM t WHERE seg='A'),\nrb AS (SELECT sum(amount*late)/sum(amount) b_rate FROM t WHERE seg='B')\nSELECT a_rate, b_rate,\n (sum(CASE WHEN seg='C' THEN amount*late END) - sum(CASE WHEN seg='C' THEN amount END)*a_rate)/252/5 c_to_A_bal,\n (sum(CASE WHEN seg='C' THEN amount*late END) - sum(CASE WHEN seg='C' THEN amount END)*b_rate)/252/5 c_to_B_bal,\n (sum(CASE WHEN seg='B' THEN amount*late END) - sum(CASE WHEN seg='B' THEN amount END)*a_rate)/252/5 b_to_A_bal,\n (sum(CASE WHEN seg='C' THEN amount*late END) - sum(CASE WHEN seg='C' THEN amount END)*a_rate)/252/5*0.08 c_to_A_8pct,\n (sum(CASE WHEN seg='C' THEN amount*late END) - sum(CASE WHEN seg='C' THEN amount END)*b_rate)/252/5*0.05 c_to_B_5pct,\n ((sum(CASE WHEN seg='C' THEN amount*late END) - sum(CASE WHEN seg='C' THEN amount END)*a_rate)+(sum(CASE WHEN seg='B' THEN amount*late END) - sum(CASE WHEN seg='B' THEN amount END)*a_rate))/252/5*0.08 bc_to_A_8pct,\n count(DISTINCT CASE WHEN seg='C' THEN customer_id END) c_cust\nFROM t, ra, rb GROUP BY a_rate, b_rate",
  "columns": [
   "a_rate",
   "b_rate",
   "c_to_A_bal",
   "c_to_B_bal",
   "b_to_A_bal",
   "c_to_A_8pct",
   "c_to_B_5pct",
   "bc_to_A_8pct",
   "c_cust"
  ],
  "row_count": 1,
  "rows": [
   [
    2.445018080190926,
    8.714321007471732,
    786931.92491856,
    615203.4401564139,
    601854.5618681145,
    62954.5539934848,
    30760.1720078207,
    111102.91894293395,
    152
   ]
  ],
  "error": null
 },
 {
  "id": "q343",
  "sql": "WITH x AS (\n SELECT i.customer_id, sum(i.amount*greatest(p.day-i.due_day,0))/sum(i.amount) wlate\n FROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id GROUP BY 1),\ns AS (SELECT c.customer_id, CASE WHEN c.terms_days=0 THEN '0' WHEN wlate<6 THEN 'A' WHEN wlate<20 THEN 'B' ELSE 'C' END seg FROM x JOIN erp_customers c USING(customer_id)),\ny AS (\nSELECT d.year AS yr, sum(i.amount) billed,\n sum(i.amount*greatest(p.day-i.due_day,0))/252 overdue_bal,\n sum(i.amount*(p.day-i.day))/252 total_ar,\n (sum(CASE WHEN seg='C' THEN i.amount*greatest(p.day-i.due_day,0) END) - sum(CASE WHEN seg='C' THEN i.amount END)*2.434871783955032)/252 c_excess_to_A,\n (sum(CASE WHEN seg='C' THEN i.amount*greatest(p.day-i.due_day,0) END) - sum(CASE WHEN seg='C' THEN i.amount END)*8.669202082388233)/252 c_excess_to_B,\n (sum(CASE WHEN seg='B' THEN i.amount*greatest(p.day-i.due_day,0) END) - sum(CASE WHEN seg='B' THEN i.amount END)*2.434871783955032)/252 b_excess_to_A\nFROM finance_invoices i JOIN finance_customer_payments p ON p.invoice_id=i.invoice_id JOIN s ON s.customer_id=i.customer_id JOIN dim_date d ON d.day=i.day\nWHERE d.year BETWEEN 2016 AND 2024 GROUP BY 1)\nSELECT count(*) n_years, avg(billed) avg_billed, avg(overdue_bal) avg_overdue, avg(total_ar) avg_total_ar, avg(overdue_bal)/avg(total_ar) overdue_share_of_ar,\n avg(c_excess_to_A) c_to_A, avg(b_excess_to_A) b_to_A, avg(c_excess_to_A)+avg(b_excess_to_A) bc_total, (avg(c_excess_to_A)+avg(b_excess_to_A))*0.08 bc_8pct,\n avg(c_excess_to_A)*0.08 c_to_A_8pct, avg(c_excess_to_B) c_to_B, avg(c_excess_to_B)*0.08 c_to_B_8pct, avg(c_excess_to_B)*0.05 c_to_B_5pct, (avg(c_excess_to_A)+avg(b_excess_to_A))*0.05 bc_5pct,\n avg(c_excess_to_A)/326 c_excess_per_acct\nFROM y",
  "columns": [
   "n_years",
   "avg_billed",
   "avg_overdue",
   "avg_total_ar",
   "overdue_share_of_ar",
   "c_to_A",
   "b_to_A",
   "bc_total",
   "bc_8pct",
   "c_to_A_8pct",
   "c_to_B",
   "c_to_B_8pct",
   "c_to_B_5pct",
   "bc_5pct",
   "c_excess_per_acct"
  ],
  "row_count": 1,
  "rows": [
   [
    9,
    146565650.97777832,
    2980324.226671079,
    14907565.69770719,
    0.19992024768533861,
    921328.3459274671,
    785761.1325947781,
    1707089.4785222453,
    136567.15828177962,
    73706.26767419737,
    721765.4644501363,
    57741.2371560109,
    36088.27322250682,
    85354.47392611227,
    2826.1605703296536
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

Save `grade.json`: {"finding": "F7", "grade": "full | partly | true, not planted | wrong | unverifiable", "problem": "the key's problem id, or null", "truth_queries": ["t3"], "why": "two or three sentences with the truth's numbers"}
