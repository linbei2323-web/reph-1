# Company design: Halvern Pharmaceuticals (fictional)

Stage 2 of the project. Halvern is a small fictional US drug maker with three branded
products, simulated for calendar year 2024. Prices and volumes come from real CMS
data (Medicare Part D and Medicaid) in the
[pharma-market-analytics](https://github.com/linbei2323-web/pharma-market-analytics)
project; everything marked *assumption* is a design choice, not data.

阶段 2:Halvern 是一家虚构的美国小型制药公司,有三个品牌产品,模拟 2024 年。价格和销量来自
pharma-market-analytics 项目中真实的 CMS 数据(Medicare Part D 和 Medicaid);标注
*assumption(假设)* 的是设计选择,不是数据。

Reproduce:

```
python data/channel_inputs.py ../pharma-market-analytics   # prescriptions by channel, 2022-2024
python data/design_inputs.py                               # prices, volumes, budget drivers
```

## Products / 产品

Unit = one prescription (about a 30-day fill). Volumes = real prescriptions ÷ 1,000.
Price = real average Medicare Part D spend per claim, pre-rebate (used as the list price for every channel).

| Product | Modelled on | Area | 2024 price / unit | 2024 units / month | Gross sales / month |
|---|---|---|---|---|---|
| Glyvanta | Jardiance (empagliflozin) | Diabetes & Metabolic | $1,006 | 1,646 | $1,655,876 |
| Respiqor | Trelegy Ellipta (triple inhaler) | Respiratory | $847 | 788 | $667,436 |
| Onkalyn | Xtandi (enzalutamide) | Oncology | $13,301 | 31 | $412,331 |
| **Total** | | | | | **$2,735,643** |

About $33M gross sales a year. 一年约 3,300 万美元毛销售额。

## Payer channels / 支付方渠道

Each prescription is reimbursed by one payer. The channel matters because rebate rates differ.
Prescriptions come from `data/channel_inputs.csv`:

- **Medicare:** Part D claims (CMS Part D spending by drug).
- **Medicaid:** prescriptions, national table, fee-for-service + managed care (Medicaid State Drug Utilization Data).
- **Commercial:** not in the data. *Assumption, to verify:* Jardiance 50% of Medicare; Trelegy and Xtandi 40%.

| Product | Channel | Rebate rate (assumption, to verify) | 2024 units / month |
|---|---|---|---|
| Glyvanta | Medicaid | 50% | 225 |
| Glyvanta | Medicare | 35% | 947 |
| Glyvanta | Commercial | 30% | 474 |
| Respiqor | Medicaid | 50% | 59 |
| Respiqor | Medicare | 35% | 521 |
| Respiqor | Commercial | 30% | 208 |
| Onkalyn | Medicaid | 30% | 1 |
| Onkalyn | Medicare | 3% | 21 |
| Onkalyn | Commercial | 5% | 9 |

- **Medicaid** rebates are set by law: a basic rebate of about 23.1% of the average manufacturer price for brand drugs, plus an inflation penalty when prices rise faster than inflation (to verify). That's why Medicaid has the highest rate.
- **Medicare Part D and commercial** rebates are negotiated with plans and benefit managers. Competitive classes (SGLT2 diabetes drugs, inhalers) pay large rebates for formulary position; specialty oncology pays little.
- Medicaid 法定返利最高(品牌药基本返利约为平均出厂价的 23.1%,外加通胀罚款,待核实);Medicare 和商业保险返利是谈判出来的,竞争激烈的类别返利高,专科肿瘤药返利低。

## Other gross-to-net rates (assumption, to verify) / 其他毛到净扣减率

| Product | Chargebacks | Returns | Prompt-pay | Blended rebate (2024 mix) | Total GTN | Net sales / month |
|---|---|---|---|---|---|---|
| Glyvanta | 2% | 1% | 2% | 35.6% | 40.6% | $983,404 |
| Respiqor | 2% | 1% | 2% | 34.8% | 39.8% | $401,806 |
| Onkalyn | 10% | 1% | 2% | 4.4% | 17.4% | $340,639 |
| **Total** | | | | | | **$1,725,849** |

Onkalyn's chargeback rate is a pure assumption: Part D data covers pharmacy-dispensed drugs only,
so it says nothing about contract pricing to clinics.

## Budget v1 vs actual: the year's story / 预算与实际:这一年的故事

**Budget v1** is the plan as if prepared in late 2023: each channel's 2023 prescriptions grown at its
2022→2023 growth rate, at 2023 prices. **Actual** follows the real 2024 market. So every variance in
the simulation is a real forecasting miss, not an invented one.

| Model drug | Channel | Growth 2022→23 (budget assumes) | Real growth 2023→24 |
|---|---|---|---|
| Jardiance | Medicaid | +36.9% | **+17.4%** |
| Jardiance | Medicare | +44.2% | +39.4% |
| Trelegy | Medicaid | +27.7% | +23.6% |
| Trelegy | Medicare | +27.6% | +24.8% |
| Xtandi | Medicaid | +5.7% | **−3.8%** |
| Xtandi | Medicare | +1.4% | **+33.4%** |

All Medicaid prescriptions fell from 784.4M (2023) to 737.6M (2024), **−6.0%**, as the Medicaid
unwinding removed about 25 million enrollees (continuous enrollment ended 31 March 2023; KFF).

What this means for Halvern:

1. **Medicaid volume below budget** for all three products (Glyvanta about −13%): the unwinding slowed
   growth even for brands that kept growing. A real finding: the market fell, but these brands still grew,
   just more slowly than planned.
2. **Onkalyn far above budget in Medicare (about +40%):** Xtandi's Medicare claims jumped 33% in 2024
   after two flat years. A likely reason is the label expansion approved in late 2023 (to verify).
3. **Prices below budget:** average Medicare spend per claim fell for all three drugs from 2023 to 2024
   (e.g. Jardiance $1,084 → $1,006). The budget held 2023 prices, so there is an unfavourable price variance.
4. **Net price per unit helped by mix:** losing Medicaid units, which carry the highest rebate, lowers the
   average rebate rate.

The simulation's full-year totals are printed by `generate_transactions.py`. The stage 6 report explains them.

## Cost centers and monthly expense budget (assumption) / 成本中心与月度费用

| Code | Cost center | What it spends on | Budget / month |
|---|---|---|---|
| 6000 | Commercial | Sales force, marketing agency | $350,000 |
| 6100 | R&D | Clinical research contractor, lab staff | $350,000 |
| 6200 | Manufacturing | Plant overhead, quality control (product cost is in COGS) | $150,000 |
| 6300 | G&A | Finance, HR, legal, office and IT | $120,000 |
| | **Total** | | **$970,000** (+ $250 bank fee in G&A) |

## Unit cost (assumption) / 单位成本

Glyvanta $60, Respiqor $70, Onkalyn $500 per unit → COGS about $169,420 a month at 2024 volumes.
Inventory purchases are sized to match (70% ingredients from Corvane, 30% packaging from Pacwell).

## Monthly P&L at 2024 drivers / 2024 年月度利润表(按实际驱动因素)

| Line | Amount |
|---|---|
| Gross sales | $2,735,643 |
| − GTN deductions | −$1,009,794 |
| **Net revenue** | **$1,725,849** |
| − Cost of goods sold | −$169,420 |
| **Gross margin** | **$1,556,429** |
| − Department expenses | −$970,250 |
| **Operating profit** | **$586,179** |

## Customers (Net 30) / 客户

| Customer (fictional) | Share of sales |
|---|---|
| Northstar Drug Supply | 40% |
| Meridian Health Distribution | 35% |
| Keystone Pharma Wholesale | 25% |

## Suppliers (Net 45) / 供应商

| Supplier (fictional) | Cost center or account |
|---|---|
| Corvane Ingredients (active ingredients) | 1200 Inventory |
| Pacwell Packaging | 1200 Inventory |
| Arclight Clinical Research | 6100 R&D |
| Brightline Marketing | 6000 Commercial |
| Tessaro Office & IT | 6300 G&A |

## Opening balances, 1 January / 期初余额

| Account | Debit | Credit |
|---|---|---|
| 1000 Bank | 5,000,000 | |
| 1200 Inventory (about 2 months of COGS) | 300,000 | |
| 3000 Equity | | 5,300,000 |
| **Total** | **5,300,000** | **5,300,000** |

## Chart of accounts / 科目表

As in `docs/pipeline-zh.md` stage 2 (1000 Bank … 6300 G&A), with 4100 Rebates,
4200 Chargebacks, 4300 Returns, 4400 Prompt-pay discounts, plus two liability
accounts added in generator piece 4: 2110 Chargeback accrual and 2120 Returns reserve
(so each GTN deduction has its own accrual to tie out).

## Open items / 待定

- A mid-year reforecast (budget v2) is optional and not built yet.
- Daniel to review the channel figures in `data/channel_inputs.csv` and the commercial-share assumption.
