# Layer 0: context primer

*Always load this first. It's short on purpose.*

## The business

**Summit Mechanical Services** is a commercial HVAC contractor in Arizona, with about 200 employees: roughly 145 field technicians, about 30 back-office staff, plus managers, estimators and warehouse.

- **Branches** (each with a branch code):
  - Phoenix (`PHX`), the largest, run from the East Valley
  - Tucson (`TUS`)
  - Flagstaff (`NTH`), called **"North" until mid-2023**
- **Customers:**
  - national restaurant and retail chains, which send work through their facilities-management portals with a PO number and a **not-to-exceed amount** (NTE: the most Summit may bill without asking for more);
  - property managers;
  - school districts;
  - regional chains;
  - about a thousand single-site businesses, who call or email.
- **Work types:**
  - **repair** (something broke);
  - **pm** (scheduled preventive maintenance under a service agreement);
  - **install** (replacing equipment after a customer accepts a quote).
- **Service agreements** come in three tiers:
  - `pm_only`: maintenance visits only;
  - `pm_labor`: also covers repair labour on the covered units;
  - `full`: also covers parts.

## What the data is

- **A reporting warehouse:** DuckDB, built nightly-style from five operational systems plus weather. It runs **2021-01-01 to 2025-12-31.**

| Schema | What it is |
|---|---|
| `fsm` | The field-service management system: customers, sites, equipment, agreements, work orders, visits, time, parts, quotes, notes |
| `portal` | Exports from customers' facilities-management portals: POs, NTEs, increase requests, invoice submissions and rejections |
| `acct` | The accounting package: its own customer list, invoices, invoice lines, payments, write-offs, payroll rates, supplier bills, fiscal periods |
| `inbox` | The shared service inbox: every email to service@, as free text |
| `inv` | The parts ledger: truck and warehouse stock movements |
| `ext` | NOAA monthly heating and cooling degree days for the three branch counties |
| `dw` | Conformed dimensions and facts that join the systems where a simple rule can (start here) |

## Universal conventions

| Thing | Meaning |
|---|---|
| `wo_id` | A work order: one job. A job can take several **visits**. |
| `equipment_id` | One unit at one site (a rooftop unit, a walk-in cooler…). The thread that connects repeat work. |
| Dates | `DATE` columns. Portal `status_events.event_at` and `fact_email.received_at` are timestamps. |
| Money | US dollars, nominal (prices rise each January). |
| Fiscal year | Accounting's fiscal year starts **1 October** (`dw.dim_date.fiscal_year`). The FSM uses calendar years. |
| Customer IDs | FSM `customer_id` and accounting `acct_customer_id` are **different numbering systems**. |

## What this warehouse cannot answer

- **Why** a job failed or came back. There is no root cause anywhere: only what was recorded, plus free-text technician notes.
- Technician **skill**. Only titles, certification and outcomes on their jobs.
- **Profit** on a job or agreement, directly. Labour cost rates exist (`fact_payroll_rate`, with history), and parts costs exist in the stock ledger, but nothing is pre-joined.
- **Customer satisfaction or churn reasons.** Customers simply stop calling. `fsm.customers.status` is what the office last set, and it's not reliable.
- **Which email belongs to which job.** Emails aren't linked to anything.
- **Anything before 2021.** Invoices for jobs started in 2020 aren't here, so receivables start near zero in January 2021.

## Schema

```
dim_customer ─┬─< dim_site ─< dim_equipment
              │       │              │
              │       └──< fact_work_order >──┴── (equipment_id: repeats on one unit)
              │                 │  ├──< fact_visit >── dim_tech
              │                 │  ├──< fact_parts_used
              │                 │  ├──< fact_quote
              │                 │  ├──< fact_nte_request      (portal)
              │                 │  └──< fact_portal_submission (portal)
              │                 └──< fact_invoice (wo_id) ─< fact_invoice_line
              │                                │
acct_customer_id ──────────────────────────────┘──< fact_payment, fact_writeoff
dim_tech ─< fact_payroll_rate
fact_stock_movement (sku, location: WH-<branch> or TRUCK-<tech_id>)
fact_email (unlinked free text)
degree_days (county_series = Phoenix | Tucson | Flagstaff, monthly hdd/cdd)
```
