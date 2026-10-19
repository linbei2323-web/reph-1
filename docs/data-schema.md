# Data schema / 数据结构

Every file the project produces, what each column means, and how the files link.
项目生成的所有文件、每一列的含义,以及文件之间如何关联。

Final generated data (simulation year 2024). Regenerate with:

```
python data/channel_inputs.py ../pharma-market-analytics   # step 1: prescriptions by channel
python data/design_inputs.py                               # step 2: product drivers + budget drivers
python data/generate_transactions.py                       # step 3: transactions, budget, checks
```

## 1. How the data flows / 数据流

```
pharma-market-analytics (real CMS data: Medicare Part D + Medicaid, 2022-2024)
        │ channel_inputs.py
        ▼
channel_inputs.csv  (prescriptions by drug, channel and year)
        │ design_inputs.py
        ▼
design_inputs.csv (3 products)  +  channel_plan.csv (budget vs actual by channel)
        │ generate_transactions.py  (fixed seed 2024)
        ▼
sales_invoices ─► customer_payments
purchase_invoices ─► supplier_payments
journal_entries            periods            expected_trial_balance
bank_transactions (bank statement)   channel_utilization   budget (v1)
        │ you: import into ERPNext → ERPNext writes the general ledger
        ▼
your SQL database (stage 4) → controls (stage 5) → reporting (stage 6)
```

## 2. How the tables link / 表之间的关系

```mermaid
erDiagram
    PRODUCTS ||--o{ SALES_INVOICES : "item"
    CUSTOMERS ||--o{ SALES_INVOICES : "customer"
    SALES_INVOICES ||--o| CUSTOMER_PAYMENTS : "invoice_no"
    SUPPLIERS ||--o{ PURCHASE_INVOICES : "supplier"
    PURCHASE_INVOICES ||--o| SUPPLIER_PAYMENTS : "bill_no"
    ACCOUNTS ||--o{ PURCHASE_INVOICES : "account"
    ACCOUNTS ||--o{ JOURNAL_ENTRIES : "account"
    COST_CENTERS ||--o{ JOURNAL_ENTRIES : "cost_center"
    PRODUCTS ||--o{ JOURNAL_ENTRIES : "product"
    PERIODS ||--o{ JOURNAL_ENTRIES : "posting month"
```

- Each sales invoice has **zero or one** payment (zero = still open in AR at 31 Dec).
- Each purchase invoice has **zero or one** payment (zero = still open in AP at 31 Dec).
- Payments link to their document by `invoice_no` / `bill_no`. This link is what control 7 (unapplied payments) and control 2 (subledger = GL) rely on.
- 每张销售发票有 0 或 1 笔收款(0 = 年末仍未收);每张采购发票有 0 或 1 笔付款(0 = 年末仍未付)。付款通过 `invoice_no` / `bill_no` 关联到单据,控制 7 和控制 2 依靠这个关联。

## 3. Transaction tables / 交易表

Keys: **PK** = primary key (unique per row), **FK** = links to another table.

### sales_invoices.csv: 1,047 rows, one per wholesaler order / 销售发票

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| invoice_no | text | PK | Invoice number | SINV-2024-00001 |
| posting_date | date | | Date the sale is recorded | 2024-01-02 |
| customer | text | FK → customers | Wholesaler | Keystone Pharma Wholesale |
| item | text | FK → products | Product sold | Onkalyn |
| qty | integer | | Units (claims-equivalent) | 1 |
| rate | number | | Gross price per unit, USD | 13301 |
| amount | number | | qty × rate, USD (gross, before GTN) | 13301 |
| cost_center | text | FK → cost_centers | Always Commercial | Commercial |
| due_date | date | | posting_date + 30 days (Net 30) | 2024-02-01 |

**Ledger effect:** Dr 1100 Accounts receivable / Cr 4000 Gross product sales.

### customer_payments.csv: 959 rows / 客户收款

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| payment_no | text | PK | Payment number | PAY-IN-2024-00001 |
| payment_date | date | | Date cash arrives | 2024-01-30 |
| customer | text | FK → customers | Who paid | Northstar Drug Supply |
| invoice_no | text | FK → sales_invoices | Invoice paid | SINV-2024-00003 |
| invoice_amount | number | | Full invoice amount | 26602 |
| discount | number | | 2% prompt-pay discount if on time, else 0 | 532 |
| amount_received | number | | invoice_amount − discount | 26070 |
| on_time | true/false | | Paid by the due date | True |

**Ledger effect:** Dr 1000 Bank (amount_received) + Dr 4400 Prompt-pay discounts (discount) / Cr 1100 Accounts receivable (invoice_amount).

### purchase_invoices.csv: 192 rows / 采购发票

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| bill_no | text | PK | Supplier bill number | PINV-2024-00001 |
| posting_date | date | | Date the bill is recorded | 2024-01-02 |
| supplier | text | FK → suppliers | Supplier | Arclight Clinical Research |
| account | text | FK → accounts | What it's charged to | 6100 R&D |
| cost_center | text | FK → cost_centers | Department | R&D |
| amount | number | | USD | 56004.61 |
| due_date | date | | posting_date + 45 days (Net 45) | 2024-02-16 |

**Ledger effect:** Dr account (inventory or department expense) / Cr 2000 Accounts payable.

### supplier_payments.csv: 173 rows / 供应商付款

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| payment_no | text | PK | Payment number | PAY-OUT-2024-00001 |
| payment_date | date | | Weekly Thursday payment run (Friday if Thursday is a holiday) | 2024-02-15 |
| supplier | text | FK → suppliers | Who was paid | Arclight Clinical Research |
| bill_no | text | FK → purchase_invoices | Bill paid | PINV-2024-00001 |
| amount_paid | number | | USD, full bill amount | 56004.61 |
| on_time | true/false | | Paid by the due date | True |

**Ledger effect:** Dr 2000 Accounts payable / Cr 1000 Bank.

### journal_entries.csv: 90 entries, 330 lines / 日记账

One row per **line**; all lines with the same `je_no` form one balanced entry (debits = credits).
每行是一条分录**行**,同一个 `je_no` 的所有行构成一笔借贷平衡的分录。

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| je_no | text | PK with line order | Entry number | JE-2024-00005 |
| posting_date | date | | Date posted | 2024-01-31 |
| je_type | text | | Opening balance, Payroll, Bank fee, COGS, Rebate / Chargeback / Returns accrual or settlement | Rebate accrual |
| account | text | FK → accounts | Account | 4100 Rebates |
| debit | number | | USD | 606869.5 |
| credit | number | | USD | 0.0 |
| cost_center | text | FK → cost_centers | Department, blank for balance sheet lines | Commercial |
| product | text | FK → products | Product, on COGS and accrual lines | Glyvanta |
| party | text | | Who is paid, on settlements | Payer rebate programs |
| remark | text | | Description | Rebate accrual Jan 2024 |

| je_type | Entries | Entry |
|---|---|---|
| Opening balance | 1 | Dr Bank, Inventory / Cr Equity |
| Payroll | 12 | Dr 6000–6300 by cost center / Cr Bank |
| Bank fee | 12 | Dr 6300 G&A 250 / Cr Bank (monthly service charge) |
| COGS | 12 | Dr 5000 COGS (by product) / Cr 1200 Inventory |
| Rebate accrual | 12 | Dr 4100 (by product) / Cr 2100 |
| Chargeback accrual | 12 | Dr 4200 (by product) / Cr 2110 |
| Returns accrual | 12 | Dr 4300 (by product) / Cr 2120 |
| Rebate settlement | 3 | Dr 2100 / Cr Bank, ± true-up to 4100 |
| Chargeback settlement | 11 | Dr 2110 / Cr Bank, ± true-up to 4200 |
| Returns settlement | 3 | Dr 2120 / Cr Bank, ± true-up to 4300 |

### bank_transactions.csv: 1,170 rows, the bank statement / 银行流水

One line for every cash movement the bank processed by 31 Dec: customer receipts, supplier payments, payroll, GTN settlements and the bank's service charge. The statement opening balance is $5,000,000.
银行在 12 月 31 日前处理的每一笔现金流动一行。期初余额 $5,000,000。

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| bank_txn_id | text | PK | Bank line number | BANK-2024-00001 |
| bank_date | date | | Date the bank processed it: receipts 0–1, supplier ACH 1–2, settlements 1–2 business days after the book date; payroll and fees same day | 2024-01-30 |
| amount | number | | USD; + money in, − money out | 26070.0 |
| reference | text | | What the payer wrote: an invoice number on 90% of receipts, Halvern's payment or JE number on outgoing payments, blank otherwise | SINV-2024-00003 |
| description | text | | Bank's text | ACH CREDIT NORTHSTAR DRUG SUPPLY |

There is **no column linking a bank line to a book entry**: finding the match (amount, date within ±3 days, reference when present) is control 3's job. 75 receipts have no reference and must be matched on amount and date alone.
**没有**直接关联账面记录的列:匹配是控制 3 的工作。75 笔收款没有参考号,只能按金额和日期匹配。

**Reconciliation at 31 Dec:** statement closing balance $12,623,900.11 + three customer receipts booked on 31 Dec but cleared in January ($75,050.00) = book bank balance $12,698,950.11.

## 4. Control and check tables / 控制与核对表

### periods.csv: 12 rows / 会计期间

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| period | text (YYYY-MM) | PK | Month | 2024-01 |
| closed_on | date | | Planned close date: 5th business day of the next month | 2024-02-07 |

Use these dates when you close each month in ERPNext. Control 5 flags anything posted into a period after its `closed_on`.

### expected_trial_balance.csv: 18 rows / 预期试算平衡表

| Column | Type | Key | Meaning |
|---|---|---|---|
| account | text | PK | Account |
| debit | number | | Total debits for the year |
| credit | number | | Total credits for the year |
| balance | number | | debit − credit (positive = debit balance) |

Built from every document as ERPNext will post it. **Your check for stage 3:** after the import, ERPNext's trial balance should match this file.

### channel_utilization.csv: 108 rows / 支付方渠道用量

Units sold each month split by the payer that reimbursed them. Halvern doesn't know the payer when it invoices a wholesaler; it learns the mix later from utilization data. Rebate accruals are calculated from this table.

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| period | text (YYYY-MM) | PK (with product, channel) | Month | 2024-01 |
| product | text | FK → products | Product | Glyvanta |
| channel | text | | Medicaid, Medicare or Commercial | Medicaid |
| units | integer | | Units reimbursed by that channel | 221 |

For each product and month, units across the three channels add up to the units invoiced.
**Ledger link:** rebate accrual = Σ units × price × the channel's rebate rate (`channel_plan.csv`).

### budget.csv: 264 rows, budget v1 / 预算

The plan as if prepared in late 2023. One row per month and line.

| Column | Type | Key | Meaning | Example |
|---|---|---|---|---|
| version | text | PK (with period, account, cost_center, product) | v1 = original budget (a reforecast v2 may be added later) | v1 |
| period | text (YYYY-MM) | | Month | 2024-01 |
| account | text | FK → accounts | 4000–4400 revenue and deductions, 5000 COGS, 6000–6300 expenses | 4000 Gross product sales |
| cost_center | text | FK → cost_centers | Department | Commercial |
| product | text | FK → products | Product, on revenue, deduction and COGS lines; blank on expense lines | Glyvanta |
| units | number | | Budget units, on product lines | 1732.26 |
| amount | number | | USD, always positive; the account says whether it is revenue, a deduction or a cost | 1877769.84 |

Revenue lines: budget units × 2023 price; rebates at each channel's rate; other deductions and COGS at their planned rates. Expense lines: payroll + supplier spend (+ $250 bank fee in G&A).

## 5. Design inputs / 设计输入

### channel_inputs.csv: 27 rows / 渠道处方数据

Real prescriptions by drug, payer channel and year, from Daniel's market data (`channel_inputs.py`).

| Column | Type | Meaning | Example |
|---|---|---|---|
| model_drug | text | Real drug | Jardiance |
| year | integer | 2022, 2023 or 2024 | 2024 |
| channel | text | Medicare, Medicaid or Commercial | Medicaid |
| rx | number | Prescriptions (Medicare: Part D claims; Medicaid: national prescriptions, FFSU + MCOU; Commercial: assumed multiple of Medicare) | 2699654 |
| avg_spend_per_rx | number | Medicare average spend per claim (Medicare rows only) | 1005.96 |
| source | text | Where the number comes from, including the Medicaid product names matched | Medicaid SDUD national: Jardiance |

### channel_plan.csv: 9 rows / 渠道计划

One row per product and channel: budget vs actual drivers.

| Column | Type | Meaning | Example |
|---|---|---|---|
| product | text | Product | Glyvanta |
| channel | text | Medicaid, Medicare or Commercial | Medicaid |
| rebate_rate | number | Rebate rate for this channel (assumption, to verify) | 0.50 |
| budget_units_month | number | 2023 prescriptions × (1 + 2022→23 growth) ÷ 1,000 ÷ 12 | 262.41 |
| actual_units_month | number | 2024 prescriptions ÷ 1,000 ÷ 12 | 224.97 |
| budget_price | number | 2023 Medicare spend per claim | 1084 |
| actual_price | number | 2024 Medicare spend per claim | 1006 |

## 6. Reference lists (masters) / 主数据

These are set up in ERPNext before importing. They're defined in `docs/company-design.md` and the generator; they will also become dimension tables in your SQL database.

**Products** (`design_inputs.csv`, 3 rows; key: `product`): the 2024 drivers the generator uses

| product | model_drug | price_per_unit | monthly_units | unit_cost | rebate (blended) | chargeback | returns | prompt_pay |
|---|---|---|---|---|---|---|---|---|
| Glyvanta | Jardiance | 1,006 | 1,646 | 60 | 35.6% | 2% | 1% | 2% |
| Respiqor | Trelegy Ellipta | 847 | 788 | 70 | 34.8% | 2% | 1% | 2% |
| Onkalyn | Xtandi | 13,301 | 31 | 500 | 4.4% | 10% | 1% | 2% |

Also in the file: `area`, `monthly_gross`, `gtn_rate`, `monthly_net`, `monthly_cogs`.

**Customers** (Net 30): Northstar Drug Supply (40%), Meridian Health Distribution (35%), Keystone Pharma Wholesale (25%).

**Suppliers** (Net 45):

| Supplier | Account | Cost center |
|---|---|---|
| Corvane Ingredients | 1200 Inventory | Manufacturing |
| Pacwell Packaging | 1200 Inventory | Manufacturing |
| Arclight Clinical Research | 6100 R&D | R&D |
| Brightline Marketing | 6000 Commercial | Commercial |
| Tessaro Office & IT | 6300 G&A | G&A |

**Cost centers:** Commercial, R&D, Manufacturing, G&A.

**Chart of accounts:**

| No. | Account | Type | Used by |
|---|---|---|---|
| 1000 | Bank | Asset | Payments, payroll, settlements |
| 1100 | Accounts receivable | Asset | Sales invoices, customer payments |
| 1200 | Inventory | Asset | Purchase invoices, COGS |
| 2000 | Accounts payable | Liability | Purchase invoices, supplier payments |
| 2100 | Rebate accrual | Liability | Rebate accruals and settlements |
| 2110 | Chargeback accrual | Liability | Chargeback accruals and settlements |
| 2120 | Returns reserve | Liability | Returns accruals and settlements |
| 2200 | Accrued expenses | Liability | Not used yet |
| 3000 | Equity | Equity | Opening balance |
| 4000 | Gross product sales | Revenue | Sales invoices |
| 4100 | Rebates | Contra-revenue | Accruals, true-ups |
| 4200 | Chargebacks | Contra-revenue | Accruals, true-ups |
| 4300 | Returns | Contra-revenue | Accruals, true-ups |
| 4400 | Prompt-pay discounts | Contra-revenue | Customer payments |
| 5000 | Cost of goods sold | Expense | COGS entries |
| 6000 | Commercial | Expense | Marketing bills, payroll |
| 6100 | R&D | Expense | Research bills, payroll |
| 6200 | Manufacturing | Expense | Payroll |
| 6300 | G&A | Expense | Office / IT bills, payroll |

## 7. Rules the data follows / 数据规则

1. Every journal entry balances: debits = credits.
2. paid + prompt-pay discounts + open AR = gross sales ($32,865,858; checked by the generator).
3. paid + open AP = purchases (checked by the generator).
4. For each GTN accrual account: accrued = paid − true-up + still owed at 31 Dec.
5. No transactions on weekends or US federal holidays (payroll and settlements roll to the next business day).
6. Amounts are USD. Sales amounts are gross (before rebates, chargebacks, returns and discounts).
7. Bank statement + items not yet cleared = GL bank balance (checked by the generator).
8. For each product and month, channel units add up to invoiced units.
9. The data is clean: the 40 test errors are added later, to a copy, in stage 5.
