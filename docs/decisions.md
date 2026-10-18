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
| 2026-10-18 | Daniel does the ERPNext work (setup, import, period close) and the SQL work himself; Claude prepares data and explains | He must be able to do and explain these hands-on parts in interviews |
