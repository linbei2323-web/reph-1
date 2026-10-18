# Decision log / 决策记录

Decisions Daniel made, with the date and why. 每条决定、日期和原因。

| Date | Decision | Why |
|---|---|---|
| 2026-10-18 | Model products on Jardiance, Trelegy Ellipta, Xtandi; volumes = 2024 Medicare claims ÷ 1,000 | Three therapeutic areas, real price ratios and volume mix |
| 2026-10-18 | Seeded test errors: 4 types × 10 (duplicates, wrong periods, misclassifications, unmatched payments), about 8 deliberately hard | A realistic test must include errors the rules may miss |
| 2026-10-18 | Plant errors in a copy of the SQL data with a script (`tests/seed_errors.py`) that changes all related tables together, plus `tests/answer_key.csv` | ERPNext would block some errors (e.g. posting into a closed period); a script is reproducible |
| 2026-10-18 | Write control rules on a development copy with its own errors; run once, unchanged, on the held-out test copy | Keeps the recall / false-positive score honest |
