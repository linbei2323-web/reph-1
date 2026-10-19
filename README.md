# Pharma FP&A & Financial Close Analytics

A simulated pharmaceutical company's finance function: 12 months of transactions
recorded in ERPNext, moved to SQL, checked with month-end close and reconciliation
controls, and reported as budget-versus-actual and gross-to-net revenue.

> Status: in progress. Results below are filled in only from actual runs.
>
> Full project pipeline in Chinese: [docs/pipeline-zh.md](docs/pipeline-zh.md)
>
> Next steps for ERPNext and SQL: [docs/erpnext-sql-guide.md](docs/erpnext-sql-guide.md) · Data schema: [docs/data-schema.md](docs/data-schema.md)

## Stages

| # | Stage | Tools | Status |
|---|---|---|---|
| 1 | Learn the accounting | ERPNext docs, a 10-K | In progress |
| 2 | Design the company | Spreadsheet, CMS data | In progress |
| 3 | Record 12 months of transactions | Python generator (done), ERPNext | In progress |
| 4 | Move the data to SQL | SQL | Not started |
| 5 | Close & reconciliation controls, tested | SQL, Excel Power Query | Not started |
| 6 | Variance & gross-to-net reporting | Power Query, Power BI | Not started |
| 7 | Package & publish | GitHub | Not started |

## Repository layout

```
docs/      glossary, company design
data/      synthetic exports + the generator script
sql/       schema, controls, reporting queries
tests/     answer key and scoring query for the held-out test ledger
excel/     Power Query close workbook
powerbi/   dashboard file and PDF export
report/    management report and timing log
```

## Results

To be filled in from actual runs.
