# Interview: this project in SARL / 面试：SARL 回答

Situation, Action, Result, Learning, following Daniel's interview notes: short S with motivation and the
problem; A summarised by stage with tool keywords; R with numbers; L with an interpretation or a change
of perspective. **Only say what is done.** Brackets = fill in from real results.

## Version 1: today (in progress), about 90 seconds

**S.** After my pharma market analysis project, where I cleaned about $290B of Medicare drug spending, I
noticed that data stops at gross spending, before rebates, while a third or more of gross sales goes back
as rebates and other deductions. I wanted to understand how a drug company's finance team closes its books
and explains results against budget. Real ledgers are confidential, so I started a project to simulate one.

**A.** I hadn't studied accounting, so I taught myself from ERPNext's accounting documentation and the
revenue notes in BMS's 10-K: double entry, accruals, bank reconciliation, gross-to-net. I designed a
fictional company with three products modelled on Jardiance, Trelegy and Xtandi, using my own cleaned CMS
data (Medicare and Medicaid prescriptions 2022-2024) for prices, volumes and payer mix. I wrote a Python
generator for a full year of transactions (invoices, payments, rebate accruals, a bank statement) that checks
itself on every run. Now I'm recording it in ERPNext and loading it into SQL to build the close controls.

**R.** A 2024 ledger of about 3,600 transactions for a company with $33M gross sales, about 37% going to
gross-to-net deductions, and seven automated checks that all pass. The budget follows the trend known in
late 2023 and actuals follow the real 2024 market, so every variance is a real forecasting miss.

**L.** I expected the Medicaid unwinding (about 25M people disenrolled) to show up as falling Medicaid volume
for my drugs. All Medicaid prescriptions did fall 6%, but for these three brands Medicaid volume kept growing,
just much more slowly than budgeted. A market-level trend doesn't automatically apply to every product: check
at the level you make decisions.

## Version 2: finished (brackets = real results only)

**A.** Four stages: designed the company from real CMS data; generated twelve months of transactions and
recorded them in ERPNext; moved everything to [PostgreSQL] and built seven SQL month-end controls (duplicates,
cutoff, bank matching…) plus an Excel Power Query close workbook; built budget-vs-actual and gross-to-net
reporting in Power BI.

**R.** [N] transactions. Controls written on a development copy, run once unchanged on a held-out copy with 40
planted errors: caught [X] of 40, [Y] false positives. Main variance: [product] revenue [−$X] below budget:
[price $X] and [volume $Y] (of which Medicaid [$Z]), partly offset by lower rebates. Use the real split; in the
generated data, Glyvanta's gross miss is −$2.66M = price −$1.54M + volume −$1.12M (Medicaid about −$0.49M),
with rebates $1.00M lower, so −$1.67M after rebates. Price, not Medicaid, is the biggest driver. Monthly report [M] → [N] minutes, timed
on the same data.

**L** (choose by interviewer):
- Finance / accounting: a balanced ledger isn't a correct ledger; detective controls catch what still balances.
- Analytics: the Medicaid finding (market trend ≠ product trend).
- Senior: losing Medicaid patients cut volume but raised net price per unit (highest rebates): one event, two
  opposite effects.
- Any level: the obvious story ("it was Medicaid") was wrong: price was the biggest driver. Check the split
  before telling the story.

## Behavioural stories in reserve

| Question | Story | Sketch |
|---|---|---|
| Learning quickly | Accounting from zero | ERPNext docs + a 10-K → a ledger where AR, AP, accruals and bank reconcile; learn by building |
| Hypothesis was wrong | Medicaid unwinding | Market −6%, brands +17% / +24%; reframed as slower growth than budget; test assumptions at decision level |
| Detail / data quality | Medicaid data traps | Names cut to 10 characters; "Jardiance" vs "JARDIANCE" across tables; documented in the script |
| Ownership | Whole project | Self-initiated, end to end, decision log of every choice |
| Conflict | None in this project | Worked alone: use a team project, don't invent one |

## Delivery

- Junior interviewer: say tool keywords. Senior: results and dollars.
- Imply, don't claim: "I built controls that catch duplicates", not "I can help your team".
- Never state results you don't have yet.
