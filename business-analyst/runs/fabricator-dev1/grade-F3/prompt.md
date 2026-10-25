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
 "id": "F3",
 "hypothesis": "H7",
 "title": "Late payment costs about $1.41M in excess receivables and splits into three parts: invoices billed above the customer's PO price (22.67% of overdue dollar-days on 7.32% of invoices), customers 6 and 7, and a broad background tail on correctly priced invoices",
 "conclusion": "Observed, for 69,850 invoices dated 2016-01-05 to 2024-12-31, each with exactly one payment and none unpaid (q165): measured against due_on, excess receivables average $1,413,693. At an assumed 8% cost of capital that is $113,095/yr (q199). The 2024 run-rate is similar at $1,398,641, or $111,891/yr (q199). The working-day due date doesn't create the lateness, because due_on falls 0.23 days after the calendar terms (q110). Invoices are never dated before shipment (q170). The excess splits into three parts that sum to the total (q202). (a) $320,443 sits on invoices billed more than 0.5% above shipped qty x PO unit price. These are 5,113 of 69,850 invoices (7.32%) but carry 22.67% of overdue dollar-days (q199, q211). Outside customers 6 and 7, 65.28% of them are paid more than 30 days late, against 16.74% of matching invoices (q181). The gap holds within the same customer: across 99 customers with at least 5 of each kind, above-PO invoices are more than 30 days late 65.5% of the time against 16.32% for the same customers' matching invoices. Above-PO invoices are worse for 97.98% of those customers, and the median within-customer gap is 37 days (q221). They are usually paid in full eventually: 80.42% exactly, at a median uplift of 1.0288 (q186). (b) $421,661 sits on matching invoices of customers 6 and 7. Of that, $247,935 is above the rest's 11.99-day pace, worth $19,835/yr at 8% (q199). (c) $671,588 sits on everyone else's matching invoices (q199). Their payment timing has two humps: 62.24% are paid within 5 days of due, and there is a second hump at 31-90 days (q175, q211). That hump is spread evenly. The 145 customers with a 10-25% rate of invoices over 30 days late hold 92.22% of matching billing (q189). Partial shipments, returns, late shipments and short payments barely move it (q187, q196). Interpretation: (a) looks like invoices held until a price discrepancy is resolved, so the lever is price agreement between invoice and PO, not collections. (b) is a persistent customer pattern whose cause is unknown. (c) is the only part a general collections process plausibly addresses.",
 "dollars_a_year": 113095.0,
 "size_query": "q199",
 "claims": [
  {
   "text": "69,850 invoices dated 2016-01-05 to 2024-12-31 all have exactly one payment (76,053 payments on 76,053 invoices overall), and none is unpaid. The 1,024 unpaid invoices are all dated in 2025.",
   "queries": [
    "q165"
   ]
  },
  {
   "text": "Amount-weighted days past due are 18.11 against due_on and 18.50 against calendar terms. 68.3% of invoices are paid late. due_on averages 0.23 days later than the calendar terms date. No invoice is dated before its shipment, and the invoice lag averages 1.15-1.19 days for every group.",
   "queries": [
    "q110",
    "q170"
   ]
  },
  {
   "text": "Excess AR is $1,413,693, or $113,095/yr at an assumed 8%. The 2024 run-rate is $1,398,641, or $111,891/yr, with customers 6 and 7 holding 34.1% of 2024 overdue dollar-days.",
   "queries": [
    "q139",
    "q199"
   ]
  },
  {
   "text": "Decomposition: $320,443 (22.67%) on above-PO invoices, $421,661 (29.83%) on matching invoices of customers 6 and 7, and $671,588 (47.51%) on matching invoices of everyone else. The parts sum to $1,413,692, which is the total up to rounding.",
   "queries": [
    "q199",
    "q202"
   ]
  },
  {
   "text": "Above-PO invoices are 5,113 of 69,850 (7.32%). Outside customers 6 and 7, the 4,110 above-PO invoices have a median of 40 days late and a 65.28% rate of more than 30 days late. The 50,622 matching invoices have a median of 2 days and a rate of 16.74%. For customers 6 and 7, weighted lateness is 54.67 days on above-PO invoices and 29.09 on matching ones.",
   "queries": [
    "q181",
    "q211"
   ]
  },
  {
   "text": "The above-PO effect holds within customers. For 99 customers outside 6 and 7 with at least 5 above-PO and 5 matching invoices, the rate of invoices more than 30 days late is 0.655 on above-PO invoices against 0.1632 on the same customers' matching invoices (weighted to the above-PO mix). 97.98% of those customers are worse on above-PO invoices, with a median within-customer gap of 37 days.",
   "queries": [
    "q221"
   ]
  },
  {
   "text": "Above-PO invoices have a median uplift of 1.0288 (p90 1.1165). 80.42% are paid exactly as billed, and none is paid at PO value plus freight.",
   "queries": [
    "q186"
   ]
  },
  {
   "text": "Customers 6 and 7 (both on recorded 30-day terms) paid 26.33-41.68 days late in every year from 2016 to 2024. On matching invoices alone they ran 26.67-32.54 weighted days late every year, against 9.45-14.81 for the rest. Their days to pay have a median of 54-55 and a p10 of 37, with only 3.38-3.57% paid on time. Lateness is spread evenly across 6-40 days, with no weekday payment pattern.",
   "queries": [
    "q119",
    "q182",
    "q174",
    "q175",
    "q172"
   ]
  },
  {
   "text": "Customer lateness persists: the year-to-year correlation is 0.80-0.95, or 0.71-0.94 excluding customers 6 and 7, among customers with at least 30 invoices in both years.",
   "queries": [
    "q124"
   ]
  },
  {
   "text": "Outside customers 6 and 7, payment timing has two humps: 39.51% of invoices are paid on time and 22.73% 1-5 days late (62.24% within 5 days), and a second hump sits at 31-90 days (5.04%, 5.89%, 3.84% and 5.34% across successive buckets).",
   "queries": [
    "q175",
    "q211"
   ]
  },
  {
   "text": "On matching invoices outside customers 6 and 7, the tail is broad. The 145 customers with a 10-25% rate of invoices over 30 days late hold 92.22% of billing and 86.09% of overdue dollar-days. Customer 36 is the clear exception among customers with 200+ invoices, at 77.78%. Partial shipments (19.36% vs 16.66%), return authorisations (16.18% vs 16.74%) and shipping after the promised date (18.07% vs 16.64%) barely move the rate, and neither do short or over-payments.",
   "queries": [
    "q189",
    "q192",
    "q196",
    "q187"
   ]
  },
  {
   "text": "The 2022 peak combined two things. The above-PO share of non-6/7 invoices was 13.83% in 2021-H2, 27.93% in 2022-H1 and 3.69% in 2023-H1. Matching invoices also slowed: 9.29 to 17.78 weighted days late, with the share over 30 days rising from 12.87% to 25.16%, then back to 10.49 days by 2023-H1. The 2019 rise is mostly mix: above-PO invoices were 19.16% of invoices, and matching lateness was 12.48 days.",
   "queries": [
    "q182",
    "q200"
   ]
  },
  {
   "text": "Lateness doesn't vary with invoice size (16.57-17.98 weighted days by quartile) or invoice month (15.51-19.18).",
   "queries": [
    "q132"
   ]
  }
 ],
 "confidence": "medium",
 "not_evidence_of": "Not evidence that above-PO invoices were disputed: there are no dispute, hold or remittance-reason records, only timing and amounts. Not evidence that the uplifts were wrong charges; they may be agreed surcharges invoiced before the PO was amended. Not evidence that customers 6 and 7 act in bad faith or are in financial difficulty. Their lag is a wide spread (p10 37 to p90 96-97 days to pay), not a fixed cycle, so it doesn't by itself show a terms mismatch or a payment run. Not evidence that a reminder would shorten the background tail. The dollar figures are carrying costs at an assumed 8%, not cash lost, and only part of them is recoverable.",
 "could_not_tell": "Why above-PO invoices are paid late: dispute or hold records, customer AP correspondence, or PO amendment history would be needed. Why invoices are priced above the PO: invoice line detail and price-change approvals would be needed. Whether customers 6 and 7 have agreed terms other than the recorded 30 days. What drives the background 31-90-day hump on correctly priced invoices: there is no dunning or collections history. Reasons for short payments.",
 "next_step": "1. Price agreement: before invoicing, check invoice price against PO price, and get a PO amendment or customer approval for any uplift. Then measure lateness on the formerly above-PO population. Its baseline is 65.28% over 30 days late (outside customers 6 and 7, q181). 2. Ask customers 6 and 7 about their agreed terms and when invoices reach their AP. Then either record and price the real terms or enforce net 30. 3. Test a reminder at due date + 15 days on matching invoices and measure the share over 30 days late. Its baseline is 16.74% outside customers 6 and 7 (q181).",
 "incomplete": false
}

[
 {
  "id": "q165",
  "sql": "SELECT (SELECT count(*) FROM erp_payments) n_pay, (SELECT count(DISTINCT invoice_id) FROM erp_payments) n_pay_inv, (SELECT count(*) FROM erp_invoices) n_inv, (SELECT count(*) FROM erp_invoices WHERE invoiced_on<'2025-01-01') n_inv_pre25, (SELECT count(*) FROM erp_invoices i WHERE invoiced_on<'2025-01-01' AND NOT EXISTS (SELECT 1 FROM erp_payments p WHERE p.invoice_id=i.invoice_id)) unpaid_pre25, (SELECT count(*) FROM erp_invoices i WHERE invoiced_on>='2025-01-01' AND NOT EXISTS (SELECT 1 FROM erp_payments p WHERE p.invoice_id=i.invoice_id)) unpaid_25, (SELECT max(paid_on) FROM erp_payments) max_paid, (SELECT max(invoiced_on) FROM erp_invoices) max_inv, (SELECT min(invoiced_on) FROM erp_invoices) min_inv",
  "columns": [
   "n_pay",
   "n_pay_inv",
   "n_inv",
   "n_inv_pre25",
   "unpaid_pre25",
   "unpaid_25",
   "max_paid",
   "max_inv",
   "min_inv"
  ],
  "row_count": 1,
  "rows": [
   [
    76053,
    76053,
    77077,
    69850,
    0,
    1024,
    "2025-12-31",
    "2025-12-31",
    "2016-01-05"
   ]
  ],
  "error": null
 },
 {
  "id": "q110",
  "sql": "WITH b AS (SELECT i.invoice_id, i.customer_id, CAST(i.invoiced_on AS DATE) inv, CAST(i.due_on AS DATE) due, i.amount+i.freight AS billed, CAST(p.paid_on AS DATE) paid, p.amount paid_amt, c.terms_days FROM erp_invoices i LEFT JOIN erp_payments p USING(invoice_id) JOIN erp_customers c USING(customer_id) WHERE i.invoiced_on < '2025-01-01')\nSELECT count(*) n, count(paid) n_paid, count(DISTINCT customer_id) cust, sum(billed) billed,\n avg(due - inv) avg_due_gap_cal, avg(due-inv - terms_days) avg_due_vs_terms,\n sum(billed*greatest(paid-due,0))/sum(billed) FILTER (WHERE paid IS NOT NULL) w_days_late_due,\n sum(billed*greatest(paid-(inv+terms_days::INT),0))/sum(billed) FILTER (WHERE paid IS NOT NULL) w_days_late_terms,\n sum(billed*(paid-inv))/sum(billed) FILTER (WHERE paid IS NOT NULL) w_days_to_pay,\n sum(billed*terms_days)/sum(billed) w_terms,\n avg(CASE WHEN paid>due THEN 1 ELSE 0 END) FILTER (WHERE paid IS NOT NULL) share_late_due,\n avg(CASE WHEN paid>inv+terms_days::INT THEN 1 ELSE 0 END) FILTER (WHERE paid IS NOT NULL) share_late_terms,\n min(inv) mn, max(inv) mx\nFROM b",
  "columns": [
   "n",
   "n_paid",
   "cust",
   "billed",
   "avg_due_gap_cal",
   "avg_due_vs_terms",
   "w_days_late_due",
   "w_days_late_terms",
   "w_days_to_pay",
   "w_terms",
   "share_late_due",
   "share_late_terms",
   "mn",
   "mx"
  ],
  "row_count": 1,
  "rows": [
   [
    69850,
    69850,
    265,
    256681320.44000036,
    36.61547602004295,
    0.23151037938439514,
    18.108919401739385,
    18.502830407560438,
    55.03098423954784,
    36.688186256628214,
    0.6829205440229063,
    0.7785397279885469,
    "2016-01-05",
    "2024-12-31"
   ]
  ],
  "error": null
 },
 {
  "id": "q170",
  "sql": "WITH b AS (SELECT i.customer_id, CAST(i.invoiced_on AS DATE) inv, CAST(i.due_on AS DATE) due, CAST(s.shipped_on AS DATE) shp, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed, p.amount pamt, i.freight ifr, s.freight sfr FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN erp_shipments s USING(shipment_id) WHERE i.invoiced_on<'2025-01-01')\nSELECT CASE WHEN customer_id IN (6,7) THEN customer_id::VARCHAR ELSE 'rest' END g, count(*) n, round(avg(inv-shp),2) avg_inv_minus_ship, min(inv-shp) mn_lag, max(inv-shp) mx_lag, round(avg(CASE WHEN inv<shp THEN 1 ELSE 0 END),4) share_inv_before_ship, round(avg(CASE WHEN abs(ifr-sfr)>0.005 THEN 1 ELSE 0 END),4) share_freight_mismatch, round(avg(CASE WHEN pamt < billed-0.005 THEN 1 ELSE 0 END),4) share_short, round(avg(CASE WHEN pamt > billed+0.005 THEN 1 ELSE 0 END),4) share_over\nFROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "g",
   "n",
   "avg_inv_minus_ship",
   "mn_lag",
   "mx_lag",
   "share_inv_before_ship",
   "share_freight_mismatch",
   "share_short",
   "share_over"
  ],
  "row_count": 3,
  "rows": [
   [
    "6",
    7195,
    1.16,
    0,
    6,
    0.0,
    0.0,
    0.1008,
    0.0845
   ],
   [
    "7",
    7923,
    1.19,
    0,
    6,
    0.0,
    0.0,
    0.1027,
    0.0822
   ],
   [
    "rest",
    54732,
    1.15,
    0,
    6,
    0.0,
    0.0,
    0.106,
    0.0856
   ]
  ],
  "error": null
 },
 {
  "id": "q139",
  "sql": "WITH b AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, i.amount+i.freight AS billed, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) WHERE i.invoiced_on < '2025-01-01'),\nt AS (SELECT sum(billed*greatest(paid-due,0)) dd, sum(billed*greatest(paid-due,0)) FILTER (WHERE customer_id IN (6,7)) dd67, sum(billed) FILTER (WHERE customer_id IN (6,7)) b67,\n sum(billed*greatest(paid-due,0)) FILTER (WHERE customer_id NOT IN (6,7))/sum(billed) FILTER (WHERE customer_id NOT IN (6,7)) w_rest, (DATE '2025-01-01' - DATE '2016-01-01') ndays FROM b)\nSELECT ndays, round(dd/ndays,0) excess_ar_all, round(dd/ndays*0.08,0) carry_all_8pct,\n round(dd67/ndays,0) excess_ar_67, round((dd67 - b67*w_rest)/ndays,0) excess_ar_67_above_rest, round((dd67 - b67*w_rest)/ndays*0.08,0) carry_67_above_rest_8pct, round(w_rest,2) w_rest\nFROM t",
  "columns": [
   "ndays",
   "excess_ar_all",
   "carry_all_8pct",
   "excess_ar_67",
   "excess_ar_67_above_rest",
   "carry_67_above_rest_8pct",
   "w_rest"
  ],
  "row_count": 1,
  "rows": [
   [
    3288,
    1413693.0,
    113095.0,
    505351.0,
    270734.0,
    21659.0,
    14.64
   ]
  ],
  "error": null
 },
 {
  "id": "q199",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id IN (6,7) g67, year(CAST(i.invoiced_on AS DATE)) yr, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01'),\nt AS (SELECT sum(billed*greatest(paid-due,0)) dd, sum(billed*greatest(paid-due,0)) FILTER (WHERE above) dd_above, sum(billed*greatest(paid-due,0)) FILTER (WHERE g67 AND NOT above) dd67m, sum(billed) FILTER (WHERE g67 AND NOT above) b67m,\n sum(billed*greatest(paid-due,0)) FILTER (WHERE NOT g67 AND NOT above)/sum(billed) FILTER (WHERE NOT g67 AND NOT above) w_rest_m,\n sum(billed*greatest(paid-due,0)) FILTER (WHERE NOT g67 AND NOT above) dd_rest_m,\n sum(billed*greatest(paid-due,0)) FILTER (WHERE yr=2024) dd24, sum(billed*greatest(paid-due,0)) FILTER (WHERE yr=2024 AND g67) dd24_67,\n 3288 nd FROM b)\nSELECT round(dd/nd,0) excess_ar_all, round(dd/nd*0.08,0) carry_all, round(dd_above/nd,0) excess_ar_above_po, round(dd_above/dd,4) share_above, round(dd_above/nd*0.08,0) carry_above,\n round(dd67m/nd,0) excess_ar_67_match, round((dd67m-b67m*w_rest_m)/nd,0) excess_67_above_rest_match, round((dd67m-b67m*w_rest_m)/nd*0.08,0) carry_67_gap, round(w_rest_m,2) w_rest_match,\n round(dd_rest_m/nd,0) excess_rest_match, round(dd24/366,0) excess_ar_2024_rate, round(dd24/366*0.08,0) carry_2024, round(dd24_67/dd24,4) share67_2024\nFROM t",
  "columns": [
   "excess_ar_all",
   "carry_all",
   "excess_ar_above_po",
   "share_above",
   "carry_above",
   "excess_ar_67_match",
   "excess_67_above_rest_match",
   "carry_67_gap",
   "w_rest_match",
   "excess_rest_match",
   "excess_ar_2024_rate",
   "carry_2024",
   "share67_2024"
  ],
  "row_count": 1,
  "rows": [
   [
    1413693.0,
    113095.0,
    320443.0,
    0.2267,
    25635.0,
    421661.0,
    247935.0,
    19835.0,
    11.99,
    671588.0,
    1398641.0,
    111891.0,
    0.341
   ]
  ],
  "error": null
 },
 {
  "id": "q202",
  "sql": "SELECT 26.43-14.81 rise_all, 17.78-9.29 rise_match, round((17.78-9.29)/(26.43-14.81),4) share_rise_within_match, round(320443.0/1413693.0,4) above_share_ar, round(671588.0/1413693.0,4) rest_match_share_ar, round(421661.0/1413693.0,4) c67_match_share_ar, 320443+421661+671588 check_sum, 0.6528-0.1674 r30_gap_rest",
  "columns": [
   "rise_all",
   "rise_match",
   "share_rise_within_match",
   "above_share_ar",
   "rest_match_share_ar",
   "c67_match_share_ar",
   "check_sum",
   "r30_gap_rest"
  ],
  "row_count": 1,
  "rows": [
   [
    11.62,
    8.49,
    0.7306,
    0.2267,
    0.4751,
    0.2983,
    1413692,
    0.4854
   ]
  ],
  "error": null
 },
 {
  "id": "q181",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id IN (6,7) g67, year(CAST(i.invoiced_on AS DATE)) yr, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01')\nSELECT g67, above, count(*) n, round(sum(billed),0) billed, round(sum(billed*greatest(paid-due,0))/sum(billed),2) w_late, round(median(paid-due),1) med_late, round(avg(CASE WHEN paid-due>30 THEN 1 ELSE 0 END),4) rate_over30, round(sum(billed*greatest(paid-due,0))/sum(sum(billed*greatest(paid-due,0))) OVER (),4) share_dd_all\nFROM b GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "g67",
   "above",
   "n",
   "billed",
   "w_late",
   "med_late",
   "rate_over30",
   "share_dd_all"
  ],
  "row_count": 4,
  "rows": [
   [
    false,
    false,
    50622,
    184228213.0,
    11.99,
    2.0,
    0.1674,
    0.4751
   ],
   [
    false,
    true,
    4110,
    19763666.0,
    39.39,
    40.0,
    0.6528,
    0.1675
   ],
   [
    true,
    false,
    14115,
    47656090.0,
    29.09,
    23.0,
    0.3227,
    0.2983
   ],
   [
    true,
    true,
    1003,
    5033351.0,
    54.67,
    56.0,
    0.7886,
    0.0592
   ]
  ],
  "error": null
 },
 {
  "id": "q211",
  "sql": "SELECT round(5113.0/69850,4) above_share_inv, 0.3951+0.2273 within5_rest",
  "columns": [
   "above_share_inv",
   "within5_rest"
  ],
  "row_count": 1,
  "rows": [
   [
    0.0732,
    0.6224
   ]
  ],
  "error": null
 },
 {
  "id": "q221",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01' AND i.customer_id NOT IN (6,7)),\nc AS (SELECT customer_id, count(*) FILTER (WHERE above) na, count(*) FILTER (WHERE NOT above) nm,\n avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END) FILTER (WHERE above) ra, avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END) FILTER (WHERE NOT above) rm,\n median(paid-due) FILTER (WHERE above) mda, median(paid-due) FILTER (WHERE NOT above) mdm FROM b GROUP BY 1)\nSELECT count(*) ncust, sum(na) n_above, sum(nm) n_match, round(sum(ra*na)/sum(na),4) r30_above_within, round(sum(rm*na)/sum(na),4) r30_match_reweighted, round(avg(CASE WHEN ra>rm THEN 1.0 ELSE 0 END),4) share_cust_above_worse, round(median(mda-mdm),1) med_within_gap_days\nFROM c WHERE na>=5 AND nm>=5",
  "columns": [
   "ncust",
   "n_above",
   "n_match",
   "r30_above_within",
   "r30_match_reweighted",
   "share_cust_above_worse",
   "med_within_gap_days"
  ],
  "row_count": 1,
  "rows": [
   [
    99,
    3939,
    46518,
    0.655,
    0.1632,
    0.9798,
    37.0
   ]
  ],
  "error": null
 },
 {
  "id": "q186",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount, i.freight, i.amount+i.freight billed, p.amount pamt, sl.po_val, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01')\nSELECT above, count(*) n, round(median(amount/po_val),4) med_uplift, round(quantile_cont(amount/po_val,0.9),4) p90_uplift,\n round(avg(CASE WHEN abs(pamt-billed)<=0.005 THEN 1 ELSE 0 END),4) paid_exact, round(avg(CASE WHEN abs(pamt-(po_val+freight))<=0.01 THEN 1 ELSE 0 END),4) paid_at_po_plus_freight,\n round(avg(CASE WHEN pamt<billed-0.005 THEN 1 ELSE 0 END),4) short_rate, round(sum(billed-pamt) FILTER (WHERE pamt<billed-0.005),2) short_dollars, round(median(pamt/billed) FILTER (WHERE pamt<billed-0.005),4) med_short_ratio\nFROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "above",
   "n",
   "med_uplift",
   "p90_uplift",
   "paid_exact",
   "paid_at_po_plus_freight",
   "short_rate",
   "short_dollars",
   "med_short_ratio"
  ],
  "row_count": 2,
  "rows": [
   [
    false,
    64737,
    1.0,
    1.0001,
    0.8103,
    0.2166,
    0.1048,
    152372.07,
    1.0
   ],
   [
    true,
    5113,
    1.0288,
    1.1165,
    0.8042,
    0.0,
    0.108,
    15548.1,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q119",
  "sql": "WITH b AS (SELECT i.customer_id, year(CAST(i.invoiced_on AS DATE)) yr, CAST(i.due_on AS DATE) due, i.amount+i.freight AS billed, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) WHERE i.invoiced_on < '2025-01-01')\nSELECT yr, round(sum(billed*greatest(paid-due,0))/sum(billed),2) all_w,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE customer_id=7)/sum(billed) FILTER (WHERE customer_id=7),2) c7,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE customer_id=6)/sum(billed) FILTER (WHERE customer_id=6),2) c6,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE customer_id NOT IN (6,7))/sum(billed) FILTER (WHERE customer_id NOT IN (6,7)),2) rest,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE customer_id IN (6,7))/sum(billed*greatest(paid-due,0)),4) share_dd_67,\n round(sum(billed) FILTER (WHERE customer_id IN (6,7))/sum(billed),4) share_billed_67,\n count(*) n\nFROM b GROUP BY yr ORDER BY yr",
  "columns": [
   "yr",
   "all_w",
   "c7",
   "c6",
   "rest",
   "share_dd_67",
   "share_billed_67",
   "n"
  ],
  "row_count": 9,
  "rows": [
   [
    2016,
    17.97,
    26.97,
    26.33,
    14.81,
    0.396,
    0.2669,
    7916
   ],
   [
    2017,
    17.03,
    28.25,
    30.57,
    12.82,
    0.4395,
    0.255,
    8034
   ],
   [
    2018,
    17.57,
    28.97,
    32.24,
    13.58,
    0.4082,
    0.2346,
    8566
   ],
   [
    2019,
    20.16,
    34.69,
    32.2,
    16.94,
    0.3239,
    0.1954,
    7919
   ],
   [
    2020,
    16.61,
    30.51,
    30.69,
    13.03,
    0.3755,
    0.2038,
    7512
   ],
   [
    2021,
    17.18,
    32.89,
    33.04,
    13.18,
    0.3881,
    0.2023,
    7958
   ],
   [
    2022,
    26.04,
    37.3,
    41.68,
    23.09,
    0.2759,
    0.1831,
    7508
   ],
   [
    2023,
    14.54,
    28.12,
    29.67,
    11.39,
    0.3577,
    0.1805,
    7171
   ],
   [
    2024,
    15.17,
    31.02,
    34.24,
    11.87,
    0.341,
    0.1582,
    7266
   ]
  ],
  "error": null
 },
 {
  "id": "q182",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id IN (6,7) g67, year(CAST(i.invoiced_on AS DATE)) yr, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01')\nSELECT yr, round(avg(CASE WHEN above THEN 1 ELSE 0 END) FILTER (WHERE NOT g67),4) above_rate_rest, round(avg(CASE WHEN above THEN 1 ELSE 0 END) FILTER (WHERE g67),4) above_rate_67,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE NOT g67 AND NOT above)/sum(billed) FILTER (WHERE NOT g67 AND NOT above),2) wlate_rest_match,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE NOT g67 AND above)/sum(billed) FILTER (WHERE NOT g67 AND above),2) wlate_rest_above,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE g67 AND NOT above)/sum(billed) FILTER (WHERE g67 AND NOT above),2) wlate_67_match,\n round(avg(CASE WHEN paid-due>30 THEN 1 ELSE 0 END) FILTER (WHERE NOT g67 AND NOT above),4) over30_rest_match, count(*) n\nFROM b GROUP BY yr ORDER BY yr",
  "columns": [
   "yr",
   "above_rate_rest",
   "above_rate_67",
   "wlate_rest_match",
   "wlate_rest_above",
   "wlate_67_match",
   "over30_rest_match",
   "n"
  ],
  "row_count": 9,
  "rows": [
   [
    2016,
    0.0,
    0.0,
    14.81,
    null,
    26.67,
    0.2117,
    7916
   ],
   [
    2017,
    0.0,
    0.0,
    12.82,
    null,
    29.36,
    0.18,
    8034
   ],
   [
    2018,
    0.0649,
    0.0522,
    11.63,
    42.09,
    28.81,
    0.155,
    8566
   ],
   [
    2019,
    0.1916,
    0.1753,
    12.48,
    33.69,
    29.59,
    0.1731,
    7919
   ],
   [
    2020,
    0.0384,
    0.0388,
    12.28,
    29.68,
    29.54,
    0.167,
    7512
   ],
   [
    2021,
    0.0948,
    0.1146,
    9.45,
    44.11,
    28.54,
    0.125,
    7958
   ],
   [
    2022,
    0.2429,
    0.225,
    13.65,
    42.05,
    30.35,
    0.1931,
    7508
   ],
   [
    2023,
    0.0272,
    0.0242,
    10.2,
    35.51,
    27.34,
    0.1338,
    7171
   ],
   [
    2024,
    0.0041,
    0.0024,
    11.72,
    45.93,
    32.54,
    0.1735,
    7266
   ]
  ],
  "error": null
 },
 {
  "id": "q174",
  "sql": "WITH b AS (SELECT i.customer_id, c.terms_days, CAST(i.invoiced_on AS DATE) inv, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN erp_customers c USING(customer_id) WHERE i.invoiced_on<'2025-01-01')\nSELECT CASE WHEN customer_id IN (6,7) THEN 'c'||customer_id ELSE 'terms'||terms_days END g, count(*) n, count(DISTINCT customer_id) ncust, quantile_cont(paid-inv,0.1) p10_dtp, quantile_cont(paid-inv,0.25) p25_dtp, median(paid-inv) med_dtp, quantile_cont(paid-inv,0.75) p75_dtp, quantile_cont(paid-inv,0.9) p90_dtp, median(paid-due) med_late, round(avg(CASE WHEN paid<=due THEN 1 ELSE 0 END),4) share_on_time\nFROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "g",
   "n",
   "ncust",
   "p10_dtp",
   "p25_dtp",
   "med_dtp",
   "p75_dtp",
   "p90_dtp",
   "med_late",
   "share_on_time"
  ],
  "row_count": 5,
  "rows": [
   [
    "c6",
    7195,
    1,
    37.0,
    44.0,
    55.0,
    69.0,
    96.0,
    24.0,
    0.0338
   ],
   [
    "c7",
    7923,
    1,
    37.0,
    44.0,
    54.0,
    69.0,
    97.0,
    24.0,
    0.0357
   ],
   [
    "terms30",
    38468,
    258,
    29.0,
    30.0,
    33.0,
    49.0,
    80.0,
    2.0,
    0.4073
   ],
   [
    "terms45",
    2800,
    1,
    45.0,
    47.0,
    50.0,
    56.0,
    93.0,
    4.0,
    0.27
   ],
   [
    "terms60",
    13464,
    4,
    59.0,
    61.0,
    63.0,
    77.0,
    111.0,
    2.0,
    0.3861
   ]
  ],
  "error": null
 },
 {
  "id": "q175",
  "sql": "WITH b AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) WHERE i.invoiced_on<'2025-01-01')\nSELECT CASE WHEN customer_id IN (6,7) THEN '67' ELSE 'rest' END g, CASE WHEN paid-due<=0 THEN '00 <=0' WHEN paid-due<=5 THEN '01 1-5' WHEN paid-due<=10 THEN '02 6-10' WHEN paid-due<=15 THEN '03 11-15' WHEN paid-due<=20 THEN '04 16-20' WHEN paid-due<=25 THEN '05 21-25' WHEN paid-due<=30 THEN '06 26-30' WHEN paid-due<=40 THEN '07 31-40' WHEN paid-due<=50 THEN '08 41-50' WHEN paid-due<=60 THEN '09 51-60' WHEN paid-due<=90 THEN '10 61-90' ELSE '11 >90' END bucket, count(*) n, round(count(*)*1.0/sum(count(*)) OVER (PARTITION BY CASE WHEN customer_id IN (6,7) THEN '67' ELSE 'rest' END),4) share\nFROM b GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "g",
   "bucket",
   "n",
   "share"
  ],
  "row_count": 24,
  "rows": [
   [
    "67",
    "00 <=0",
    526,
    0.0348
   ],
   [
    "67",
    "01 1-5",
    608,
    0.0402
   ],
   [
    "67",
    "02 6-10",
    1262,
    0.0835
   ],
   [
    "67",
    "03 11-15",
    1844,
    0.122
   ],
   [
    "67",
    "04 16-20",
    1806,
    0.1195
   ],
   [
    "67",
    "05 21-25",
    1985,
    0.1313
   ],
   [
    "67",
    "06 26-30",
    1741,
    0.1152
   ],
   [
    "67",
    "07 31-40",
    1795,
    0.1187
   ],
   [
    "67",
    "08 41-50",
    957,
    0.0633
   ],
   [
    "67",
    "09 51-60",
    662,
    0.0438
   ],
   [
    "67",
    "10 61-90",
    1598,
    0.1057
   ],
   [
    "67",
    "11 >90",
    334,
    0.0221
   ],
   [
    "rest",
    "00 <=0",
    21622,
    0.3951
   ],
   [
    "rest",
    "01 1-5",
    12438,
    0.2273
   ],
   [
    "rest",
    "02 6-10",
    4865,
    0.0889
   ],
   [
    "rest",
    "03 11-15",
    1852,
    0.0338
   ],
   [
    "rest",
    "04 16-20",
    742,
    0.0136
   ],
   [
    "rest",
    "05 21-25",
    855,
    0.0156
   ],
   [
    "rest",
    "06 26-30",
    1201,
    0.0219
   ],
   [
    "rest",
    "07 31-40",
    2760,
    0.0504
   ],
   [
    "rest",
    "08 41-50",
    3223,
    0.0589
   ],
   [
    "rest",
    "09 51-60",
    2104,
    0.0384
   ],
   [
    "rest",
    "10 61-90",
    2920,
    0.0534
   ],
   [
    "rest",
    "11 >90",
    150,
    0.0027
   ]
  ],
  "error": null
 },
 {
  "id": "q172",
  "sql": "WITH b AS (SELECT i.customer_id, CAST(i.invoiced_on AS DATE) inv, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) WHERE i.invoiced_on<'2025-01-01' AND i.customer_id IN (6,7,8))\nSELECT customer_id, dayofweek(paid) dow, count(*) n FROM b GROUP BY 1,2 ORDER BY 1,2",
  "columns": [
   "customer_id",
   "dow",
   "n"
  ],
  "row_count": 15,
  "rows": [
   [
    6,
    1,
    1413
   ],
   [
    6,
    2,
    1426
   ],
   [
    6,
    3,
    1459
   ],
   [
    6,
    4,
    1445
   ],
   [
    6,
    5,
    1452
   ],
   [
    7,
    1,
    1427
   ],
   [
    7,
    2,
    1646
   ],
   [
    7,
    3,
    1667
   ],
   [
    7,
    4,
    1573
   ],
   [
    7,
    5,
    1610
   ],
   [
    8,
    1,
    2105
   ],
   [
    8,
    2,
    2262
   ],
   [
    8,
    3,
    2267
   ],
   [
    8,
    4,
    2299
   ],
   [
    8,
    5,
    2235
   ]
  ],
  "error": null
 },
 {
  "id": "q124",
  "sql": "WITH b AS (SELECT i.customer_id, year(CAST(i.invoiced_on AS DATE)) yr, CAST(i.due_on AS DATE) due, i.amount+i.freight AS billed, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) WHERE i.invoiced_on < '2025-01-01'),\ncy AS (SELECT customer_id, yr, count(*) n, sum(billed*greatest(paid-due,0))/sum(billed) w FROM b GROUP BY 1,2 HAVING count(*)>=30)\nSELECT a.yr, count(*) n_cust, round(corr(a.w, c.w),3) corr_next_yr, round(corr(a.w,c.w) FILTER (WHERE a.customer_id NOT IN (6,7)),3) corr_excl67\nFROM cy a JOIN cy c ON c.customer_id=a.customer_id AND c.yr=a.yr+1 GROUP BY a.yr ORDER BY a.yr",
  "columns": [
   "yr",
   "n_cust",
   "corr_next_yr",
   "corr_excl67"
  ],
  "row_count": 8,
  "rows": [
   [
    2016,
    14,
    0.877,
    0.913
   ],
   [
    2017,
    19,
    0.95,
    0.936
   ],
   [
    2018,
    21,
    0.91,
    0.887
   ],
   [
    2019,
    24,
    0.855,
    0.838
   ],
   [
    2020,
    25,
    0.836,
    0.814
   ],
   [
    2021,
    25,
    0.88,
    0.892
   ],
   [
    2022,
    20,
    0.8,
    0.712
   ],
   [
    2023,
    18,
    0.887,
    0.845
   ]
  ],
  "error": null
 },
 {
  "id": "q189",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01' AND i.customer_id NOT IN (6,7) AND NOT (i.amount > sl.po_val*1.005)),\nc AS (SELECT customer_id, count(*) n, avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END) r30, sum(billed*greatest(paid-due,0)) dd, sum(billed) bl FROM b GROUP BY 1)\nSELECT CASE WHEN r30>=0.5 THEN 'a r30>=0.5' WHEN r30>=0.25 THEN 'b 0.25-0.5' WHEN r30>=0.1 THEN 'c 0.1-0.25' ELSE 'd <0.1' END band, count(*) ncust, sum(n) n_inv, round(sum(bl)/sum(sum(bl)) OVER (),4) share_billed, round(sum(dd)/sum(sum(dd)) OVER (),4) share_dd, round(sum(r30*n)/sum(n),4) r30_band\nFROM c GROUP BY 1 ORDER BY 1",
  "columns": [
   "band",
   "ncust",
   "n_inv",
   "share_billed",
   "share_dd",
   "r30_band"
  ],
  "row_count": 4,
  "rows": [
   [
    "a r30>=0.5",
    18,
    723,
    0.0134,
    0.0578,
    0.7856
   ],
   [
    "b 0.25-0.5",
    30,
    1301,
    0.0278,
    0.0608,
    0.3228
   ],
   [
    "c 0.1-0.25",
    145,
    46712,
    0.9222,
    0.8609,
    0.1574
   ],
   [
    "d <0.1",
    70,
    1886,
    0.0365,
    0.0204,
    0.071
   ]
  ],
  "error": null
 },
 {
  "id": "q192",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01' AND i.customer_id NOT IN (6,7) AND NOT (i.amount > sl.po_val*1.005))\nSELECT customer_id, count(*) n, round(avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END),4) r30, median(paid-due) med_late FROM b GROUP BY 1 HAVING count(*)>=200 ORDER BY r30 DESC, customer_id",
  "columns": [
   "customer_id",
   "n",
   "r30",
   "med_late"
  ],
  "row_count": 29,
  "rows": [
   [
    36,
    315,
    0.7778,
    51.0
   ],
   [
    37,
    312,
    0.2981,
    22.0
   ],
   [
    56,
    261,
    0.2146,
    9.0
   ],
   [
    12,
    2391,
    0.2137,
    10.0
   ],
   [
    3,
    1853,
    0.2008,
    10.0
   ],
   [
    4,
    3088,
    0.1865,
    4.0
   ],
   [
    50,
    385,
    0.1818,
    5.0
   ],
   [
    16,
    335,
    0.1791,
    8.0
   ],
   [
    10,
    2186,
    0.1679,
    0.0
   ],
   [
    14,
    304,
    0.1645,
    0.0
   ],
   [
    9,
    3120,
    0.1612,
    0.0
   ],
   [
    21,
    212,
    0.1604,
    9.5
   ],
   [
    5,
    2852,
    0.1557,
    0.0
   ],
   [
    1,
    3919,
    0.1521,
    0.0
   ],
   [
    139,
    231,
    0.1515,
    4.0
   ],
   [
    147,
    227,
    0.1498,
    3.0
   ],
   [
    46,
    234,
    0.1453,
    0.0
   ],
   [
    8,
    10348,
    0.1441,
    0.0
   ],
   [
    11,
    2583,
    0.1425,
    4.0
   ],
   [
    26,
    237,
    0.135,
    3.0
   ],
   [
    183,
    234,
    0.1325,
    0.0
   ],
   [
    47,
    230,
    0.1304,
    10.5
   ],
   [
    24,
    239,
    0.1297,
    0.0
   ],
   [
    2,
    3269,
    0.1285,
    0.0
   ],
   [
    40,
    242,
    0.124,
    0.0
   ],
   [
    57,
    346,
    0.1185,
    0.0
   ],
   [
    49,
    290,
    0.1138,
    3.0
   ],
   [
    34,
    317,
    0.1104,
    3.0
   ],
   [
    122,
    212,
    0.0802,
    0.0
   ]
  ],
  "error": null
 },
 {
  "id": "q196",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val, max(sl.partial) partial, bool_or(EXISTS (SELECT 1 FROM erp_return_authorisations r WHERE r.job_id=sl.job_id)) has_ra, max(CASE WHEN so.promised_date < s.shipped_on THEN 1 ELSE 0 END) shipped_late FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) JOIN erp_shipments s USING(shipment_id) GROUP BY 1),\nb AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, sl.* FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01' AND NOT (i.amount > sl.po_val*1.005))\nSELECT customer_id IN (6,7) g67, 'partial='||partial k, count(*) n, round(avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END),4) r30, median(paid-due) med FROM b GROUP BY 1,2\nUNION ALL SELECT customer_id IN (6,7), 'ra='||has_ra, count(*), round(avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END),4), median(paid-due) FROM b GROUP BY 1,2\nUNION ALL SELECT customer_id IN (6,7), 'shipped_after_promise='||shipped_late, count(*), round(avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END),4), median(paid-due) FROM b GROUP BY 1,2\nORDER BY 1,2",
  "columns": [
   "g67",
   "k",
   "n",
   "r30",
   "med"
  ],
  "row_count": 11,
  "rows": [
   [
    false,
    "partial=0",
    49124,
    0.1666,
    2.0
   ],
   [
    false,
    "partial=1",
    1498,
    0.1936,
    1.0
   ],
   [
    false,
    "ra=false",
    50554,
    0.1674,
    2.0
   ],
   [
    false,
    "ra=true",
    68,
    0.1618,
    1.0
   ],
   [
    false,
    "shipped_after_promise=0",
    46970,
    0.1664,
    2.0
   ],
   [
    false,
    "shipped_after_promise=1",
    3652,
    0.1807,
    2.0
   ],
   [
    true,
    "partial=0",
    14115,
    0.3227,
    23.0
   ],
   [
    true,
    "ra=false",
    14108,
    0.3227,
    23.0
   ],
   [
    true,
    "ra=true",
    7,
    0.2857,
    25.0
   ],
   [
    true,
    "shipped_after_promise=0",
    13182,
    0.3217,
    23.0
   ],
   [
    true,
    "shipped_after_promise=1",
    933,
    0.3376,
    23.0
   ]
  ],
  "error": null
 },
 {
  "id": "q187",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT i.customer_id, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed, p.amount pamt, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on<'2025-01-01' AND i.customer_id NOT IN (6,7))\nSELECT CASE WHEN pamt<billed-0.005 THEN 'short' WHEN pamt>billed+0.005 THEN 'over' ELSE 'exact' END pay, count(*) n, round(avg(CASE WHEN paid-due>30 THEN 1 ELSE 0 END),4) rate_over30, round(median(paid-due),1) med_late\nFROM b WHERE NOT above GROUP BY 1 ORDER BY 1",
  "columns": [
   "pay",
   "n",
   "rate_over30",
   "med_late"
  ],
  "row_count": 3,
  "rows": [
   [
    "exact",
    40965,
    0.1694,
    2.0
   ],
   [
    "over",
    4306,
    0.1533,
    1.0
   ],
   [
    "short",
    5351,
    0.1631,
    1.0
   ]
  ],
  "error": null
 },
 {
  "id": "q200",
  "sql": "WITH sl AS (SELECT sl.shipment_id, sum(sl.quantity*so.unit_price) po_val FROM erp_shipment_lines sl JOIN erp_so_lines so USING(line_id) GROUP BY 1),\nb AS (SELECT CAST(i.invoiced_on AS DATE) inv, CAST(i.due_on AS DATE) due, CAST(p.paid_on AS DATE) paid, i.amount+i.freight billed, i.amount > sl.po_val*1.005 above FROM erp_invoices i JOIN erp_payments p USING(invoice_id) JOIN sl USING(shipment_id) WHERE i.invoiced_on>='2021-07-01' AND i.invoiced_on<'2023-07-01' AND i.customer_id NOT IN (6,7))\nSELECT strftime(inv,'%Y-H')||CASE WHEN month(inv)<=6 THEN '1' ELSE '2' END half, count(*) n, round(avg(CASE WHEN above THEN 1.0 ELSE 0 END),4) above_share, round(sum(billed*greatest(paid-due,0))/sum(billed),2) w_all,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE NOT above)/sum(billed) FILTER (WHERE NOT above),2) w_match, round(avg(CASE WHEN paid-due>30 THEN 1.0 ELSE 0 END) FILTER (WHERE NOT above),4) r30_match,\n round(sum(billed*greatest(paid-due,0)) FILTER (WHERE above)/sum(billed) FILTER (WHERE above),2) w_above\nFROM b GROUP BY 1 ORDER BY 1",
  "columns": [
   "half",
   "n",
   "above_share",
   "w_all",
   "w_match",
   "r30_match",
   "w_above"
  ],
  "row_count": 4,
  "rows": [
   [
    "2021-H2",
    3138,
    0.1383,
    14.81,
    9.29,
    0.1287,
    43.75
   ],
   [
    "2022-H1",
    3000,
    0.2793,
    26.43,
    17.78,
    0.2516,
    42.37
   ],
   [
    "2022-H2",
    3068,
    0.2073,
    20.09,
    10.16,
    0.141,
    41.74
   ],
   [
    "2023-H1",
    2979,
    0.0369,
    12.12,
    10.49,
    0.1366,
    34.6
   ]
  ],
  "error": null
 },
 {
  "id": "q132",
  "sql": "WITH b AS (SELECT i.customer_id, month(CAST(i.invoiced_on AS DATE)) mo, CAST(i.due_on AS DATE) due, i.amount+i.freight AS billed, CAST(p.paid_on AS DATE) paid FROM erp_invoices i JOIN erp_payments p USING(invoice_id) WHERE i.invoiced_on < '2025-01-01'),\nq AS (SELECT *, ntile(4) OVER (ORDER BY billed, customer_id, due) sz FROM b)\nSELECT 'size_q'||sz k, count(*) n, round(min(billed),0) lo, round(max(billed),0) hi, round(avg(greatest(paid-due,0)),2) avg_late, round(avg(greatest(paid-due,0)) FILTER (WHERE customer_id NOT IN (6,7)),2) avg_late_excl67 FROM q GROUP BY sz\nUNION ALL\nSELECT 'month_'||lpad(mo::VARCHAR,2,'0'), count(*), NULL, NULL, round(avg(greatest(paid-due,0)),2), round(avg(greatest(paid-due,0)) FILTER (WHERE customer_id NOT IN (6,7)),2) FROM b GROUP BY mo\nORDER BY 1",
  "columns": [
   "k",
   "n",
   "lo",
   "hi",
   "avg_late",
   "avg_late_excl67"
  ],
  "row_count": 16,
  "rows": [
   [
    "month_01",
    5992,
    null,
    null,
    16.74,
    12.74
   ],
   [
    "month_02",
    5638,
    null,
    null,
    19.18,
    15.88
   ],
   [
    "month_03",
    6210,
    null,
    null,
    17.25,
    14.05
   ],
   [
    "month_04",
    5768,
    null,
    null,
    16.6,
    13.11
   ],
   [
    "month_05",
    5756,
    null,
    null,
    16.45,
    13.06
   ],
   [
    "month_06",
    5864,
    null,
    null,
    16.28,
    12.88
   ],
   [
    "month_07",
    5852,
    null,
    null,
    15.51,
    11.94
   ],
   [
    "month_08",
    6180,
    null,
    null,
    16.37,
    12.71
   ],
   [
    "month_09",
    5526,
    null,
    null,
    17.61,
    13.91
   ],
   [
    "month_10",
    5935,
    null,
    null,
    18.58,
    14.65
   ],
   [
    "month_11",
    5485,
    null,
    null,
    18.27,
    14.19
   ],
   [
    "month_12",
    5644,
    null,
    null,
    16.77,
    13.34
   ],
   [
    "size_q1",
    17463,
    43.0,
    824.0,
    16.57,
    12.81
   ],
   [
    "size_q2",
    17463,
    825.0,
    1719.0,
    16.82,
    13.23
   ],
   [
    "size_q3",
    17462,
    1719.0,
    4216.0,
    17.11,
    13.58
   ],
   [
    "size_q4",
    17462,
    4216.0,
    217646.0,
    17.98,
    14.46
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
