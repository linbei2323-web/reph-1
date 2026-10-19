# ERPNext and SQL: your step-by-step guide / ERPNext 与 SQL 操作指南

Stages 3b and 4. You do these yourself; this guide says what to do, in what order, and why.
When you get stuck, send a screenshot or the error message.
第 3b 和第 4 阶段由你自己完成。本指南说明做什么、按什么顺序、为什么。卡住时把截图或报错发给我。

**Your answer key:** `data/generated/expected_trial_balance.csv`. When the import is done, ERPNext's
trial balance for 2024 must match it. **你的答案:** 导入完成后,ERPNext 的 2024 年试算平衡表必须和这个文件一致。

---

## Part A: Install ERPNext / 安装 ERPNext

### Option 1 (recommended): Docker on your Mac / 推荐:在 Mac 上用 Docker

Local, free, and you get direct access to the database for stage 4.

1. Install **Docker Desktop for Mac** and start it.
2. In Terminal:
   ```bash
   git clone https://github.com/frappe/frappe_docker
   cd frappe_docker
   docker compose -f pwd.yml up -d
   ```
3. Wait a few minutes (watch progress with `docker compose -f pwd.yml logs -f create-site`).
4. Open http://localhost:8080 and log in as **Administrator** / **admin**.

Notes:
- `pwd.yml` is the project's **demo** setup: fine for this project, not for a real company.
- **Apple Silicon (M1–M4):** if the containers fail to start or are very slow, follow the ARM64 page in the
  frappe_docker repo (`docs/01-getting-started/03-arm64.md`): it builds ARM64 images with
  `docker buildx bake` and adds `platform: linux/arm64` to each service in `pwd.yml`.
- Stop with `docker compose -f pwd.yml down` (your data stays in Docker volumes); start again with `up -d`.

### Option 2: Frappe Cloud trial / 备选:Frappe Cloud 试用

No install, but no direct database access: in stage 4 you would export reports as CSV instead of querying the database.

---

## Part B: Set up the company / 建立公司

Do these **before importing any transaction**. 在导入任何交易之前完成。

### B1. Setup wizard / 初始化向导

| Field | Value |
|---|---|
| Country | United States |
| Currency | USD |
| Company | Halvern Pharmaceuticals (abbreviation: HP) |
| Fiscal year | 2024-01-01 to 2024-12-31 (if the wizard creates a different year, add **Fiscal Year 2024** afterwards) |
| Chart of accounts | Standard for now (you replace it in B2) |

### B2. Chart of accounts / 科目表

You need the 19 accounts in `docs/data-schema.md` §6. Two ways:
- **Chart of Accounts Importer** (Accounting → Chart of Accounts Importer): build a CSV of the 19 accounts and import it. Cleanest. It must be done before any transaction exists.
- Or edit the standard chart by hand: rename or add accounts to match.

Settings that matter (each one is something an interviewer could ask about):

| Account | Root type | Account type | Why |
|---|---|---|---|
| 1000 Bank | Asset | Bank | Needed for bank reconciliation |
| 1100 Accounts receivable | Asset | Receivable | Control account for customers |
| 1200 Inventory | Asset | *(leave blank)* | Items are non-stock, so this is a plain asset account (see B4) |
| 2000 Accounts payable | Liability | Payable | Control account for suppliers |
| 2100 / 2110 / 2120 accruals | Liability | | GTN accruals |
| 3000 Equity | Equity | | Opening balance |
| 4000 Gross product sales | Income | Income Account | |
| 4100–4400 deductions | Income | | Contra-revenue: income accounts that carry debit balances |
| 5000 Cost of goods sold | Expense | Cost of Goods Sold | |
| 6000–6300 departments | Expense | | One per cost center |

### B3. Cost centers / 成本中心

Under the company's root cost center: **Commercial, R&D, Manufacturing, G&A**.

### B4. Items / 物料

| Item | Type | Default account |
|---|---|---|
| Glyvanta, Respiqor, Onkalyn | Sales item, **Maintain Stock = off** | Income: 4000 |
| Active ingredients, Packaging | Purchase item, Maintain Stock = off | Expense: 1200 Inventory |
| Clinical research services | Purchase item | Expense: 6100 R&D |
| Marketing services | Purchase item | Expense: 6000 Commercial |
| Office & IT services | Purchase item | Expense: 6300 G&A |

**Why non-stock:** the generator books COGS by monthly journal entry at standard cost. If items tracked
stock, ERPNext would also post COGS automatically, and you'd count it twice. Also switch off
**perpetual inventory** for the company.

### B5. Parties and bank / 往来单位和银行

- **Customers (3):** Northstar Drug Supply, Meridian Health Distribution, Keystone Pharma Wholesale. Receivable account 1100.
- **Suppliers (5):** Corvane Ingredients, Pacwell Packaging, Arclight Clinical Research, Brightline Marketing, Tessaro Office & IT. Payable account 2000.
- **Bank Account:** one, linked to GL account 1000 (needed to import the bank statement).

### B6. Document numbering (a useful trick) / 单据编号

Payments must reference ERPNext's own invoice names. If you set the naming series to match the generator
(Sales Invoice `SINV-.YYYY.-.#####`, Purchase Invoice `PINV-.YYYY.-.#####`) and import invoices **in
file order**, ERPNext's names will equal the `invoice_no` / `bill_no` in the files, so payment files link
without a lookup. If any row fails and numbering shifts, export the invoice list (name + your number in
remarks) and map instead.

---

## Part C: Import the transactions / 导入交易

Use **Data Import** (search "Data Import"). For each document type: download ERPNext's template, map the
generator's columns onto it, import a small test batch (one month), check it, then import the rest.
**Send me the downloaded template if you want help mapping columns.**

Import in this order (later documents depend on earlier ones):

| # | Document | From file | Key mapping | Count |
|---|---|---|---|---|
| 1 | Journal Entry: opening balance | journal_entries.csv, je_type = Opening balance | 3 lines on 1 Jan | 1 |
| 2 | Sales Invoice | sales_invoices.csv | customer, posting_date (tick "Edit Posting Date and Time"), due_date, item, qty, rate, cost_center | 1,047 |
| 3 | Payment Entry: Receive | customer_payments.csv | party, posting_date, paid amount = amount_received; reference = invoice, allocated = invoice_amount; **Deductions** row: account 4400, cost center Commercial, amount = discount | 959 |
| 4 | Purchase Invoice | purchase_invoices.csv | supplier, posting_date, due_date, item (by account), expense account, cost_center, amount | 192 |
| 5 | Payment Entry: Pay | supplier_payments.csv | party, posting_date, amount_paid; reference = bill | 173 |
| 6 | Journal Entry: everything else | journal_entries.csv (rows with the same je_no = one entry, one child row per line) | account, debit, credit, cost_center | 89 |
| 7 | Bank Transaction | bank_transactions.csv | via **Bank Statement Import**, to the Bank Account | 1,170 |

Then:

8. **Check the trial balance:** Accounting → Trial Balance, company Halvern, 2024-01-01 to 2024-12-31.
   Compare every account with `expected_trial_balance.csv`. Differences = an import problem: find it.
9. **Lock each month:** create an **Accounting Period** per month (or set *Accounts Frozen Till Date* in
   Accounts Settings) using the dates in `periods.csv`. Lock **after** importing, otherwise ERPNext will
   refuse 2024 documents.
10. **Don't run a Period Closing Voucher yet.** It closes the year's income and expense into equity, so your
    trial balance would no longer match the expected one. Export or compare first.

**Expect problems. They're part of the work:** missing accounts, wrong date formats (use YYYY-MM-DD),
rounding on discounts, cost centers left blank. Each one you fix is an interview story.
**一定会遇到问题,这本身就是工作的一部分**:每解决一个,都是一个面试故事。

---

## Part D: SQL (stage 4) / SQL(第 4 阶段)

### D1. Choose your database / 选择数据库

PostgreSQL is a good choice: you already planned it for your market analysis project. MariaDB (the database
ERPNext uses) also works.

### D2. Get the data out of ERPNext / 从 ERPNext 导出数据

With Docker you can query ERPNext's MariaDB directly:
```bash
docker compose -f pwd.yml exec db mysql -uroot -p     # password: see the db service in pwd.yml
SHOW DATABASES;                                       # the site database has a generated name
```
The tables you need are named with a `tab` prefix, for example `` `tabGL Entry` ``, `` `tabSales Invoice` ``,
`` `tabPayment Entry` ``, `` `tabPayment Entry Reference` ``, `` `tabPurchase Invoice` ``,
`` `tabJournal Entry Account` ``, `` `tabBank Transaction` ``. Export them to CSV, or use the
General Ledger report's export if you're on Frappe Cloud.

### D3. Design and build your schema / 设计并建表

Your design, guided by the pipeline (stage 4) and `docs/data-schema.md`:

| Table | Kind | From |
|---|---|---|
| gl_entries | Fact | ERPNext `tabGL Entry` (the core of stages 5 and 6) |
| sales_invoices, purchase_invoices | Fact | ERPNext |
| payments | Fact | ERPNext Payment Entry + references |
| bank_transactions | Fact | ERPNext Bank Transaction |
| budget | Plan | `data/generated/budget.csv` (version column) |
| channel_utilization | Fact | `data/generated/channel_utilization.csv` |
| accounts, cost_centers, products, periods | Dimension | ERPNext masters + `periods.csv` (closed_on) |

Write it as `sql/01_schema.sql` so the whole database can be rebuilt from scratch.

### D4. Check your load / 核对导入

- Row counts per table match the counts above.
- Total debits = total credits in `gl_entries`, overall and per month.
- Balances by account match `expected_trial_balance.csv`.

These three checks are the start of your stage 5 control 1.

---

## What to send me / 发给我什么

- Screenshots of errors, or the ERPNext template you're mapping.
- Your trial balance once imported. I'll compare it with the expected one.
- Your `sql/01_schema.sql` for review. I'll comment, not rewrite it.
