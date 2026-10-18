# Company design: Halvern Pharmaceuticals (fictional)

Stage 2 of the project. Halvern is a small fictional US drug maker with three branded
products. Prices and the volume mix come from real 2024 Medicare Part D data in the
[pharma-market-analytics](https://github.com/linbei2323-web/pharma-market-analytics)
project; everything marked *assumption* is a design choice, not data.

阶段 2:Halvern 是一家虚构的美国小型制药公司,有三个品牌产品。价格和销量结构来自
pharma-market-analytics 项目中真实的 2024 年 Medicare Part D 数据;标注 *assumption(假设)*
的是设计选择,不是数据。

## Products / 产品

Reproduce with `python data/design_inputs.py ../pharma-market-analytics`
(output: `data/design_inputs.csv`). Unit = one claim (about a 30-day fill).
Volumes = real 2024 Medicare claims ÷ 1,000. Prices = real average Medicare spend per claim, pre-rebate.

| Product | Modelled on | Area | 2024 Medicare spend | Price / unit | Units / month | Gross sales / month |
|---|---|---|---|---|---|---|
| Glyvanta | Jardiance (empagliflozin) | Diabetes & Metabolic | $11.44B | $1,006 | 947 | $952,682 |
| Respiqor | Trelegy Ellipta (triple inhaler) | Respiratory | $5.29B | $847 | 521 | $441,287 |
| Onkalyn | Xtandi (enzalutamide) | Oncology | $3.40B | $13,301 | 21 | $279,321 |
| **Total** | | | | | | **$1,673,290** |

About $20M gross sales a year. 一年约 2,000 万美元毛销售额。

## Gross-to-net rates (assumption, to verify) / 毛到净扣减率(假设,待核实)

| Product | Rebates | Chargebacks | Returns | Prompt-pay | Total | Net sales / month |
|---|---|---|---|---|---|---|
| Glyvanta | 30% | 2% | 1% | 2% | 35% | $619,243 |
| Respiqor | 30% | 2% | 1% | 2% | 35% | $286,837 |
| Onkalyn | 5% | 10% | 1% | 2% | 18% | $229,043 |
| **Total** | | | | | | **$1,135,123** |

- Pharmacy drugs in competitive classes (SGLT2 diabetes, inhalers) pay large rebates to
  insurers and benefit managers for formulary coverage.
- Onkalyn: specialty oncology drugs face less rebate competition. The chargeback rate
  is a pure assumption: Part D data covers pharmacy-dispensed drugs only, so it says
  nothing about contract pricing to clinics.
- 药店渠道、竞争激烈的类别返利高;专科肿瘤药返利低。Onkalyn 的价格补差率纯属假设:
  Part D 数据只覆盖药房配发,无法反映对诊所的合同价。

## Cost centers and monthly expense budget (assumption) / 成本中心与月度费用

| Code | Cost center | What it spends on | Budget / month |
|---|---|---|---|
| 6000 | Commercial | Sales force, marketing agency | $350,000 |
| 6100 | R&D | Clinical research contractor, lab staff | $350,000 |
| 6200 | Manufacturing | Plant overhead, quality control (product cost is in COGS) | $150,000 |
| 6300 | G&A | Finance, HR, legal, office and IT | $120,000 |
| | **Total** | | **$970,000** |

## Unit cost (assumption) / 单位成本

Glyvanta $60, Respiqor $70, Onkalyn $500 per unit → COGS about $103,790 a month.

## Monthly P&L at plan / 计划月度利润表

| Line | Amount |
|---|---|
| Gross sales | $1,673,290 |
| − GTN deductions | −$538,167 |
| **Net revenue** | **$1,135,123** |
| − Cost of goods sold | −$103,790 |
| **Gross margin** | **$1,031,333** |
| − Department expenses | −$970,000 |
| **Operating profit** | **$61,333** |

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
| 1200 Inventory (about 3 months of COGS) | 300,000 | |
| 3000 Equity | | 5,300,000 |
| **Total** | **5,300,000** | **5,300,000** |

## Chart of accounts / 科目表

As in `docs/pipeline-zh.md` stage 2 (1000 Bank … 6300 G&A), with 4100 Rebates,
4200 Chargebacks, 4300 Returns, 4400 Prompt-pay discounts, plus two liability
accounts added in generator piece 4: 2110 Chargeback accrual and 2120 Returns reserve
(so each GTN deduction has its own accrual to tie out).

## Open decisions / 待定

- Budget story for stage 6: build the v1 budget on one growth rate, then let actuals differ.
  Your market analysis shows Medicare drug cost growth slowing from +14.7% to +4.6%.
- Whether any product loses price during the year (a price-effect variance).
