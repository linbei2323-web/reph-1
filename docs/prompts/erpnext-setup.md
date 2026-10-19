# Prompt: ERPNext company setup (for Claude Code on Daniel's Mac)

Paste the block below into Claude Code started in the local `reph-1` folder. It sets up the company
through ERPNext's REST API and logs every step to `docs/erpnext-setup-log.md`.

````text
Set up my ERPNext company for a simulated pharma finance project. ERPNext runs locally in Docker
(frappe_docker, pwd.yml) at http://localhost:8080. Use ERPNext's REST API (Python requests or curl);
do not click the browser.

Authentication: log in with POST /api/method/login (usr=Administrator, pwd=admin) and reuse the session
cookie. If that fails, ask me for an API key and secret (User settings -> API Access -> Generate Keys).

Rules:
- First READ the current state (company, fiscal years, system settings, the full account tree for the
  company) and show me a plan. Wait for my "go" before changing anything.
- Never delete or rename existing records. Only create what is missing and change the settings below.
- Be idempotent: if a record already exists, skip it and say so.
- Find parent account groups by querying Account (company = Halvern Pharmaceuticals, is_group = 1);
  don't guess names. Account names in ERPNext end with " - HP".
- When done, write a log to docs/erpnext-setup-log.md: every API call made, what was created or changed,
  what was skipped and why, and any errors. Then commit it to git (do not push).

Tasks:
1. Company "Halvern Pharmaceuticals" (abbr HP, currency USD, country United States): confirm it exists.
   Set enable_perpetual_inventory = 0.
2. Fiscal Year: create "2024" (2024-01-01 to 2024-12-31), linked to the company, if missing.
   Keep the existing 2026 year.
3. System Settings: set date_format = "yyyy-mm-dd".
4. Chart of accounts. Keep the standard chart. Confirm these existing accounts and record their exact names:
   Debtors (receivable), Creditors (payable), Capital Stock (equity; if missing use Opening Balance Equity),
   Sales (income), Cost of Goods Sold (expense).
   Create these leaf accounts if missing (set account_number; is_group = 0):
   | number | account_name           | parent group        | account_type |
   | 1000   | Operating Bank         | Bank Accounts       | Bank (skip if a bank account already exists; record its name) |
   | 1200   | Inventory              | Current Assets      | (blank, NOT Stock) |
   | 2100   | Rebate Accrual         | Current Liabilities |  |
   | 2110   | Chargeback Accrual     | Current Liabilities |  |
   | 2120   | Returns Reserve        | Current Liabilities |  |
   | 2200   | Accrued Expenses       | Current Liabilities |  |
   | 4100   | Rebates                | Direct Income       |  |
   | 4200   | Chargebacks            | Direct Income       |  |
   | 4300   | Returns                | Direct Income       |  |
   | 4400   | Prompt-pay Discounts   | Direct Income       |  |
   | 6000   | Commercial Expenses    | Indirect Expenses   |  |
   | 6100   | R&D Expenses           | Indirect Expenses   |  |
   | 6200   | Manufacturing Expenses | Indirect Expenses   |  |
   | 6300   | G&A Expenses           | Indirect Expenses   |  |
   Also set account_number on the existing accounts: Debtors 1100, Creditors 2000, Capital Stock 3000,
   Sales 4000, Cost of Goods Sold 5000 (only if they have no number yet).
5. Cost centers under the company's root cost center: Commercial, R&D, Manufacturing, G&A.
6. Write data/erpnext_account_map.csv with columns design_account,erpnext_account mapping the 19 design
   accounts (e.g. "1100 Accounts receivable" -> the exact ERPNext name) for later imports and the
   trial balance check. The 19 design accounts are listed in docs/data-schema.md section 6.

Finish by showing me: the fiscal year list, the new part of the account tree, the cost centers,
and the contents of data/erpnext_account_map.csv.
````
