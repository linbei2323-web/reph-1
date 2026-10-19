# Decision log / 决策记录

Decisions Daniel made, with the date and why. 每条决定、日期和原因。

| Date | Decision | Why |
|---|---|---|
| 2026-10-18 | Model products on Jardiance, Trelegy Ellipta, Xtandi; volumes = 2024 Medicare claims ÷ 1,000 | Three therapeutic areas, real price ratios and volume mix |
| 2026-10-18 | Seeded test errors: 4 types × 10 (duplicates, wrong periods, misclassifications, unmatched payments), about 8 deliberately hard | A realistic test must include errors the rules may miss |
| 2026-10-18 | Plant errors in a copy of the SQL data with a script (`tests/seed_errors.py`) that changes all related tables together, plus `tests/answer_key.csv` | ERPNext would block some errors (e.g. posting into a closed period); a script is reproducible |
| 2026-10-18 | Write control rules on a development copy with its own errors; run once, unchanged, on the held-out test copy | Keeps the recall / false-positive score honest |
| 2026-10-18 | Simulation year 2025; no orders or payments on US federal holidays | A full past calendar year; holiday activity would look unrealistic |
| 2026-10-18 | The resume states the actual final transaction count, not a target | Every claim must match the data |
| 2026-10-18 | Customer payments: 85% on time with a 2% prompt-pay discount, the rest 1 to 15 days late in full; payments after 31 Dec stay open in AR | Wholesalers usually take the discount; open year-end AR is realistic |
| 2026-10-18 | Department budgets split into vendor invoices and payroll: Commercial $150k vendor + $200k payroll; R&D $200k + $150k; Manufacturing $0 + $150k; G&A $40k + $80k (per month) | Realistic mix; payroll comes as journal entries in piece 4 |
| 2026-10-18 | Suppliers paid in a weekly Thursday payment run: 90% on the last run before the due date, 10% one or two runs late; no discount | Companies batch supplier payments; late runs give AP timing differences |
| 2026-10-18 | Customer payments stay one per invoice for now (batching can be added later); 85% on time kept | Defaults until Daniel decides |
| 2026-10-18 | Daniel does the ERPNext work (setup, import, period close), the SQL work and the Excel / Power Query work himself; Claude prepares data and explains | He must be able to do and explain these hands-on parts in interviews |
| 2026-10-18 | GTN accruals booked at month end from that month's gross sales × planned rate, by product. Rebates paid quarterly 45 days after quarter end (±3% true-up); chargebacks monthly after 20 days (±2%); returns quarterly after 30 days (±10%). Unpaid amounts stay accrued at year end | Mirrors how estimates are booked first and settled later; true-ups make the tie-out meaningful |
| 2026-10-18 | Added accounts 2110 Chargeback accrual and 2120 Returns reserve | Each GTN deduction gets its own liability to tie out |
| 2026-10-18 | Prompt-pay discounts recognised when the customer pays (not accrued at sale); COGS booked monthly at standard unit cost; payroll monthly, ±3% | Simplifications, noted for interviews |
| 2026-10-18 | Month close date = 5th business day of the next month (data/generated/periods.csv) | Needed for the "posted after close" control |
| 2026-10-18 | Simulation year changed from 2025 to 2024 | The Medicaid unwinding (continuous enrollment ended 31 Mar 2023; 25.2M disenrolled by Sep 2024, KFF) falls in 2024, matching the −3.0% Medicaid drug spend in the market data |
| 2026-10-18 | Year's story: the Medicaid unwinding. Budget (late 2023) assumes Medicaid volume holds; actual Medicaid-channel volume falls during 2024 | A real event, visible in Daniel's own data; gives an unfavourable volume / favourable net-price variance |
| 2026-10-18 | Add payer channels (Medicaid / Medicare / commercial) with different rebate rates | Needed to model the unwinding; Medicaid statutory rebates are high (to verify) |
| 2026-10-18 | Daniel calculates the channel shares and the 2023→2024 Medicaid change for the three model drugs from his own market data | His analysis; he must be able to explain it |
| 2026-10-19 | Bank statement: receipts clear 0–1 business days after booking, supplier ACH 1–2, settlements 1–2, payroll and fees same day; 90% of receipts quote the invoice number; $250 monthly bank fee booked to G&A | Realistic clearing lags and missing references make bank matching (control 3) a real test; year-end uncleared items give a true reconciliation |
| 2026-10-19 | Daniel asked Claude to finish the data generation, so Claude wrote `data/channel_inputs.py` (reverses the earlier "Daniel calculates channel shares" decision). Daniel to review and be able to explain it | Unblocks ERPNext; the script is transparent and reproducible |
| 2026-10-19 | Finding: Medicaid prescriptions for all three model drugs did NOT fall in 2024 (Jardiance +17.4%, Trelegy +23.6%, Xtandi −3.8%), while all Medicaid prescriptions fell 6.0%. Scenario reframed: the unwinding slowed growth below the budget trend | Honest to the data; still the real Medicaid unwinding |
| 2026-10-19 | Budget v1 = 2023 prescriptions grown at the 2022→23 rate per channel, at 2023 prices; actual = real 2024 prescriptions and prices; volumes ÷ 1,000 for all channels (company now ~$33M gross a year) | Every variance is a real forecasting miss |
| 2026-10-19 | Channel rebate rates (to verify): Glyvanta / Respiqor Medicaid 50%, Medicare 35%, Commercial 30%; Onkalyn 30% / 3% / 5%. Commercial volume assumed 50% (Jardiance) or 40% of Medicare | Commercial isn't in the CMS data; Medicaid statutory rebates are the highest |
| 2026-10-19 | Rebates accrued from monthly channel utilization (units by payer × price × channel rate); inventory purchases sized to planned COGS | Realistic: payer mix is learned after the sale |
| 2026-10-19 | ERPNext setup (fiscal year, settings, accounts, cost centers) scripted through the ERPNext API by Claude Code on Daniel's Mac, from docs/prompts/erpnext-setup.md; Daniel reviews the plan and the log | Faster and repeatable; Daniel must describe it as scripted |
