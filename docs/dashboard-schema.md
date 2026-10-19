# Reporting data schema (star schema) / 报表数据结构(星型模型)

The tables behind the stage 5 controls and the stage 6 dashboard. You build these in SQL (stage 4) and load
them into Power BI. The raw generated files are documented in `docs/data-schema.md`; this file is the
**reporting model** built from them and from ERPNext.
第 5 阶段控制和第 6 阶段看板背后的表,由你在 SQL 中建好并导入 Power BI。生成的原始文件见 `docs/data-schema.md`;
本文件是在此基础上建立的**报表模型**。

Keys: **PK** = primary key, **FK** = foreign key to a dimension.

## 1. Model / 模型

```
                         dim_date
                            │ date_key
   dim_product ─┐           │           ┌─ dim_cost_center
   product_key  │           ▼           │  cost_center_key
                ├──────► fact_gl ◄──────┤
                │           ▲           │
   dim_channel  │       account_key     │
   channel_key  │           │           │
        │       │       dim_account     │
        ▼       │           │           │
 fact_channel_units   fact_budget ◄─────┘
                      fact_sales ◄── dim_customer
 dim_control ──► fact_exceptions
```

All relationships: dimension (one) → fact (many), single direction.
fact_budget is at **month** grain, so it joins dim_date on the first day of the month (`date_key` = month start).

## 2. Fact tables / 事实表

### fact_gl: one row per general ledger line (from ERPNext `tabGL Entry`)

| Column | Type | Key | Meaning |
|---|---|---|---|
| gl_id | text | PK | ERPNext GL Entry name |
| date_key | date | FK → dim_date | posting_date |
| account_key | int | FK → dim_account | account number, e.g. 4100 |
| cost_center_key | int | FK → dim_cost_center | blank for balance sheet lines |
| product_key | int | FK → dim_product | on revenue, GTN and COGS lines; blank otherwise |
| voucher_type | text | | Sales Invoice, Payment Entry, Purchase Invoice, Journal Entry |
| voucher_no | text | | source document number |
| party | text | | customer or supplier |
| debit | numeric(14,2) | | |
| credit | numeric(14,2) | | |
| amount | numeric(14,2) | | debit − credit (positive = debit) |
| created_at | timestamp | | when entered (ERPNext `creation`); used by the "posted after close" control |

Grain check: total debit = total credit, overall and per month (control 1).

### fact_budget: one row per budget line per month (from `budget.csv`)

| Column | Type | Key | Meaning |
|---|---|---|---|
| version | text | PK part | v1 = original budget (v2 = reforecast, later) |
| date_key | date | PK part, FK → dim_date | first day of the month |
| account_key | int | PK part, FK → dim_account | |
| cost_center_key | int | PK part, FK → dim_cost_center | |
| product_key | int | PK part, FK → dim_product | blank on expense lines |
| units | numeric(12,2) | | budget units, on product lines |
| amount | numeric(14,2) | | always positive; dim_account.sign_pl gives the P&L direction |

### fact_sales: one row per sales invoice line (from ERPNext Sales Invoice)

| Column | Type | Key | Meaning |
|---|---|---|---|
| invoice_no | text | PK | |
| date_key | date | FK → dim_date | posting date |
| customer_key | int | FK → dim_customer | |
| product_key | int | FK → dim_product | |
| qty | int | | units |
| rate | numeric(12,2) | | gross price per unit |
| amount | numeric(14,2) | | qty × rate |
| due_date | date | | |

Used for units and price in the price / volume split.

### fact_channel_units: units by payer per month (from `channel_utilization.csv`)

| Column | Type | Key | Meaning |
|---|---|---|---|
| date_key | date | PK part, FK → dim_date | first day of the month |
| product_key | int | PK part, FK → dim_product | |
| channel_key | int | PK part, FK → dim_channel | |
| units | int | | units reimbursed by that payer |

Check: Σ channels = units invoiced for the product and month.

### fact_exceptions: one row per exception found by a control (your exception register)

| Column | Type | Key | Meaning |
|---|---|---|---|
| exception_id | text | PK | e.g. EX-2024-0001 |
| control_key | int | FK → dim_control | which control flagged it |
| date_key | date | FK → dim_date | period of the flagged document |
| document | text | | voucher, payment or bank line |
| amount | numeric(14,2) | | amount at stake |
| found_on | date | | when the control ran |
| status | text | | Open / Investigating / Resolved / Timing (e.g. deposit in transit) |
| owner | text | | who investigates |
| resolution | text | | what was done |
| resolved_on | date | | |
| age_days | int | | found_on to resolved_on, or to today if open |

## 3. Dimension tables / 维度表

### dim_date

| Column | Type | Key | Meaning |
|---|---|---|---|
| date_key | date | PK | every day of 2024 |
| month_start | date | | first day of the month |
| period | text | | YYYY-MM |
| month_name | text | | Jan … Dec |
| quarter | text | | Q1 … Q4 |
| is_business_day | bool | | weekday and not a US federal holiday |
| closed_on | date | | the period's close date (from `periods.csv`) |

### dim_account

| Column | Type | Key | Meaning |
|---|---|---|---|
| account_key | int | PK | account number |
| account_name | text | | e.g. Rebates |
| erpnext_account | text | | exact ERPNext name, e.g. "4100 - Rebates - HP" |
| account_type | text | | Asset, Liability, Equity, Revenue, Contra-revenue, Expense |
| statement | text | | Balance sheet / P&L |
| pl_line | text | | Gross sales, GTN deductions, COGS, Operating expenses (P&L accounts only) |
| bridge_step | int | | waterfall order: 1 Gross sales, 2 Rebates, 3 Chargebacks, 4 Returns, 5 Prompt-pay |
| sign_pl | int | | +1 for revenue, −1 for deductions and costs: turns amounts into a P&L |

### dim_product

| Column | Type | Key | Meaning |
|---|---|---|---|
| product_key | int | PK | |
| product | text | | Glyvanta, Respiqor, Onkalyn |
| model_drug | text | | Jardiance, Trelegy Ellipta, Xtandi |
| therapeutic_area | text | | Diabetes & Metabolic, Respiratory, Oncology |
| unit_cost | numeric(10,2) | | standard cost |
| chargeback_rate, returns_rate, prompt_pay_rate | numeric(5,4) | | planned GTN rates |

### dim_channel

| Column | Type | Key | Meaning |
|---|---|---|---|
| channel_key | int | PK | |
| channel | text | | Medicaid, Medicare, Commercial |
| payer_type | text | | Government statutory / Government negotiated / Commercial |

(Rebate rates differ by product and channel, so they live in a small bridge table
`product_channel_rate(product_key, channel_key, rebate_rate)` from `channel_plan.csv`.)

### dim_cost_center

| Column | Type | Key | Meaning |
|---|---|---|---|
| cost_center_key | int | PK | |
| cost_center | text | | Commercial, R&D, Manufacturing, G&A |
| expense_account_key | int | FK → dim_account | its expense account (6000–6300) |

### dim_customer

| Column | Type | Key | Meaning |
|---|---|---|---|
| customer_key | int | PK | |
| customer | text | | Northstar, Meridian, Keystone |
| payment_terms_days | int | | 30 |

### dim_control

| Column | Type | Key | Meaning |
|---|---|---|---|
| control_key | int | PK | 1–7 |
| control_name | text | | Trial balance, Subledger to GL, Bank match, Duplicates, Cutoff, Classification, Unapplied payments |
| error_type | text | | what it catches: unbalanced, missing / extra postings, unmatched payments, duplicates, wrong period, misclassification |
| sql_view | text | | the SQL view that produces it |

## 4. Which page uses which tables / 每页用哪些表

| Dashboard page | Facts | Dimensions |
|---|---|---|
| 1. P&L and budget variance | fact_gl, fact_budget, fact_sales | date, account, product, cost_center |
| 2. Gross-to-net bridge | fact_gl, fact_budget, fact_channel_units | date, account (bridge_step), product, channel |
| 3. Close exceptions | fact_exceptions, fact_gl (trial balance check) | date, control |

## 5. Checks before you trust the dashboard / 看板可信之前的核对

1. fact_gl: debits = credits per month; balances match `expected_trial_balance.csv`.
2. fact_budget: totals match `budget.csv` (gross $35.0M, net $21.7M).
3. fact_channel_units: channel units add up to invoiced units per product and month.
4. Dashboard GTN total = ledger accounts 4100–4400 (tie-out card shows 0).
