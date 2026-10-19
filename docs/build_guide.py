import sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

pdfmetrics.registerFont(TTFont("STSong-Light", "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", subfontIndex=0))

NAVY = colors.HexColor("#1f3a5f")
GREY = colors.HexColor("#5f6b7a")
LIGHT = colors.HexColor("#eef2f7")
RULE = colors.HexColor("#c9d2dd")
GREEN = colors.HexColor("#2e7d32")
AMBER = colors.HexColor("#b26a00")
QUIET = colors.HexColor("#7a8594")

base = dict(fontName="Helvetica", fontSize=9.5, leading=13, textColor=colors.black)
S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=NAVY),
    "sub": ParagraphStyle("sub", fontName="Helvetica", fontSize=10, leading=14, textColor=GREY),
    "subzh": ParagraphStyle("subzh", fontName="STSong-Light", fontSize=9.5, leading=14, textColor=GREY),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=4),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=NAVY, spaceBefore=8, spaceAfter=2),
    "body": ParagraphStyle("body", **base),
    "zh": ParagraphStyle("zh", fontName="STSong-Light", fontSize=9, leading=13.5, textColor=GREY, wordWrap="CJK"),
    "quote": ParagraphStyle("quote", **{**base, "fontName": "Helvetica-Oblique"}, leftIndent=10),
    "quotezh": ParagraphStyle("quotezh", fontName="STSong-Light", fontSize=9, leading=13.5, textColor=GREY, leftIndent=10, wordWrap="CJK"),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8.5, leading=11),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=colors.white),
    "cellbzh": ParagraphStyle("cellbzh", fontName="STSong-Light", fontSize=8.5, leading=11, textColor=colors.white),
    "cellzh": ParagraphStyle("cellzh", fontName="STSong-Light", fontSize=8, leading=11, textColor=GREY, wordWrap="CJK"),
    "label": ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=9, leading=12, textColor=NAVY, spaceBefore=4),
}

STATUS_COLOR = {"Done": GREEN, "In progress": AMBER, "Not started": QUIET}


def p(text, style="body"):
    return Paragraph(text, S[style])


def table(rows, widths, header=True):
    data = [[p(c, "cellb" if header and i == 0 else "cell") if isinstance(c, str) else c
             for c in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    return t


def note_box(flowables):
    t = Table([[flowables]], colWidths=[7.0 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LINEBEFORE", (0, 0), (0, -1), 3, NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def status(s):
    return Paragraph(f'<font color="{STATUS_COLOR[s].hexval()}"><b>{s}</b></font>', S["cell"])


ROADMAP = [
    ("1", "Learn the accounting", "In progress",
     "Accounting guide with exercises and bilingual glossary", "Write your own one-page glossary: docs/glossary.md"),
    ("2", "Design the company", "Done",
     "Halvern Pharmaceuticals: 3 products modelled on CMS 2024 Part D data, GTN, cost centers, opening balances",
     "Review and defend every assumption"),
    ("3", "Generate & record 12 months", "In progress",
     "Generator finished (2024): 1,047 sales invoices, 1,132 payments, 192 purchase invoices, 90 journal entries, 1,170 bank lines, budget v1, channel data",
     "You: set up ERPNext and import; check the trial balance against expected_trial_balance.csv"),
    ("4", "Move the data to SQL", "Not started", "-", "Schema script, fact / dimension / versioned budget tables"),
    ("5", "Close controls, tested", "Not started",
     "Error plan designed: 4 types x 10, held-out test", "7 control queries, close workbook, seeded test, score"),
    ("6", "Variance & GTN reporting", "Not started", "-", "Price / volume split, GTN bridge, 3-page dashboard, timing log"),
    ("7", "Package & publish", "In progress",
     "GitHub repo, folder layout, README, Chinese pipeline", "Merge to main, screenshots, results, resume links"),
]

STAGES = [
    {
        "n": "1", "name": "Learn the accounting", "status": "In progress",
        "what": "Learn the five concepts every control relies on: general ledger, AR/AP, accruals, "
                "bank reconciliation and gross-to-net.",
        "say": "\"I started by learning the accounting the controls depend on: double entry, subledgers "
               "versus control accounts, accruals, bank reconciliation and gross-to-net. In pharma, "
               "gross-to-net matters most, because a large share of gross sales goes to rebates and "
               "chargebacks that are only estimates when they're booked.\"",
        "sayzh": "“我先学习了控制所依赖的会计基础：复式记账、明细账与控制科目、应计、银行对账和毛到净。在制药行业毛到净最重要，因为很大一部分毛销售额会变成返利和价格补差，而记账时这些都只是估计数。”",
        "qa": [("Walk me through the entry for a rebate.",
                "Month-end: Dr Rebates (contra-revenue) / Cr Rebate accrual (liability). When paid: "
                "Dr Rebate accrual / Cr Bank. Revenue is reduced in the month of the sale, not the month of payment.")],
        "evidence": "Your glossary; the accounting guide exercises.",
    },
    {
        "n": "2", "name": "Design the company", "status": "Done",
        "what": "Halvern Pharmaceuticals, fictional. Glyvanta, Respiqor and Onkalyn are modelled on Jardiance, "
                "Trelegy Ellipta and Xtandi using real Medicare Part D and Medicaid prescriptions (2022-2024) and "
                "Medicare price per claim, with volumes scaled by 1/1000. About $33M gross sales a year.",
        "say": "\"I designed the company from real data. In an earlier project I cleaned CMS Medicare Part D "
               "data, 288.7 billion dollars of 2024 drug spending. I picked three drugs from different "
               "therapeutic areas, kept their real price per claim and scaled Medicare and Medicaid "
               "prescriptions down by a thousand. "
               "A script reproduces every number. The gross-to-net rates are my assumptions, and I can explain "
               "each one: pharmacy drugs in competitive classes pay large rebates, while the oncology drug "
               "pays small rebates but more chargebacks.\"",
        "sayzh": "“公司是用真实数据设计的。我在之前的项目里清洗了 CMS Medicare Part D 数据（2024 年共 2,887 亿美元药品支出），从不同治疗领域选了三个药，保留真实的单次处方价格，销量缩小一千倍。每个数字都能用脚本重现。毛到净扣减率是我的假设，每一个我都能解释。”",
        "qa": [("Why fictional products instead of the real drugs?",
                "Real companies' internal books are confidential. Real prices and volume mix keep it realistic; "
                "fictional names make clear I'm not claiming anyone's actual financials."),
               ("What does your data not cover?",
                "Part D covers pharmacy-dispensed drugs only, not hospital-administered ones (Part B), so the "
                "chargeback rate is an assumption, not data. All CMS figures are gross, before rebates.")],
        "evidence": "docs/company-design.md, data/design_inputs.py.",
    },
    {
        "n": "3", "name": "Generate & record 12 months", "status": "In progress",
        "what": "A Python generator creates about 400 transactions a month (sales invoices, payments, purchases, "
                "journal entries, bank lines) with a fixed random seed, then they're imported into ERPNext, "
                "which writes the general ledger.",
        "say": "\"The transactions are synthetic. I generated them with a Python script with a fixed seed, so "
               "anyone can reproduce them, and built in realistic behaviour: weekly wholesaler order patterns, "
               "Net 30 and Net 45 payment timing, monthly accruals. Then I loaded them into ERPNext, so the "
               "general ledger was created by a real accounting system that enforces balanced entries and "
               "linked documents, not by my script.\"",
        "sayzh": "“交易是模拟的。我用固定随机种子的 Python 脚本生成，任何人都能重现，并加入了真实的业务规律：批发商每周下单、Net 30 和 Net 45 的付款时间、每月应计。然后导入 ERPNext，总账是由真实的会计系统生成的，而不是我的脚本。”",
        "qa": [("Why go through ERPNext instead of writing the ledger directly?",
                "ERPNext enforces accounting rules: balanced entries, invoices linked to payments, closed "
                "periods. It also gives the ledger the same structure a real company's ERP export would have."),
               ("How many transactions, and how do you know?",
                "Say the actual final count from your row counts by month, not a target number.")],
        "evidence": "data/generate_transactions.py, ERPNext screenshots, row counts by month.",
    },
    {
        "n": "4", "name": "Move the data to SQL", "status": "Not started",
        "what": "Export the ERPNext general ledger and documents into fact and dimension tables, plus a "
                "versioned budget table (v1 original, v2 reforecast). Keep a schema script so the database can "
                "be rebuilt from scratch.",
        "say": "\"I modelled the data as a star schema: general-ledger and budget facts joined to accounts, "
               "cost centers, products and periods. The budget table is versioned, so I can compare actuals "
               "against the original budget or the reforecast. The whole database rebuilds from one script.\"",
        "sayzh": "“我把数据建成星型模型：总账和预算事实表，连接科目、成本中心、产品和期间维度表。预算表有版本号，可以和原始预算或滚动预测对比。整个数据库一个脚本就能重建。”",
        "qa": [("Why a versioned budget?",
                "Companies reforecast mid-year. Without a version column you can't say which plan a variance is measured against.")],
        "evidence": "sql/01_schema.sql, table row counts.",
    },
    {
        "n": "5", "name": "Close & reconciliation controls, tested", "status": "Not started",
        "what": "Seven SQL controls (trial balance, subledger-to-GL, bank match, duplicates, cutoff, classification, "
                "unapplied payments) feed an exception register in an Excel Power Query close workbook. Tested on "
                "a held-out ledger with 40 seeded errors: 10 duplicates, 10 wrong periods, 10 misclassifications, "
                "10 unmatched payments.",
        "say": "\"A balanced trial balance doesn't prove the books are right, so I built seven controls, each a "
               "SQL query whose output rows are exceptions. To test them honestly I wrote the rules on a "
               "development copy, then ran them once, unchanged, on a held-out copy with 40 planted errors and "
               "an answer key. They found [X] of 40 with [Y] false positives. The ones they missed were [type], "
               "because [reason].\"",
        "sayzh": "“试算平衡不代表账对，所以我建了七个控制，每个是一个 SQL 查询，输出的行就是异常。为了诚实地测试，我在开发副本上写规则，然后在植入 40 个错误的留出副本上只运行一次、不改规则。找到了 [X] 个，误报 [Y] 个。漏掉的是 [类型]，原因是 [原因]。”",
        "qa": [("What does 'held-out' mean?",
                "I never looked at the test copy while writing rules, and didn't change any rule after running "
                "it. Like practising on old exams, then sitting a new one."),
               ("Why use synthetic data to test controls?",
                "You need to know the right answer. With planted errors and an answer key I can measure recall "
                "and false positives; with real books you never know every error.")],
        "evidence": "sql/02_controls.sql, tests/answer_key.csv, score output, exception register.",
    },
    {
        "n": "6", "name": "Variance & gross-to-net reporting", "status": "Not started",
        "what": "Budget vs actual by month, product and cost center; price / volume split; GTN deductions "
                "reconciled to the ledger; three Power BI pages; a management report; manual vs automated "
                "preparation timed with a stopwatch.",
        "say": "\"The dashboard explains why results differ from plan. Revenue variance is split into volume "
               "and price, and the two always add back to the total. The gross-to-net bridge walks from gross "
               "sales through each deduction to net revenue, and every bar ties to its ledger account. I timed "
               "the monthly package both ways on the same data: [M] minutes manually, [N] automated.\"",
        "sayzh": "“看板解释为什么结果和计划不同。收入差异拆成量差和价差，两者加起来正好等于总差异。毛到净桥接图从毛销售额经过每一项扣减到净收入，每一项都和总账科目核对。同一数据上我分别计时：手工 [M] 分钟，自动化 [N] 分钟。”",
        "qa": [("Walk me through a price / volume split.",
                "Volume = (actual units - budget units) x budget price. Price = (actual price - budget price) x "
                "actual units. Example: budget 1,000 at $100, actual 1,100 at $95: volume +10,000, price -5,500, "
                "total +4,500."),
               ("What was the main variance story?",
                "The Medicaid unwinding. The budget extrapolated 2022-23 growth; in 2024 all Medicaid prescriptions fell "
                "6% as about 25M people were disenrolled (KFF), so Medicaid growth for my products slowed well below "
                "budget. Onkalyn's Medicare volume beat budget by about 40%. In the generated data Glyvanta's gross miss is mostly price (-$1.5M) then volume (-$1.1M, about half Medicaid). [Your price / volume numbers.]"),
               ("What did the 90 / 20 minutes consist of?",
                "Describe your actual steps from the timing log: export, lookups, rebuild pivots versus refresh, review, write commentary.")],
        "evidence": "Dashboard pages, management report, report/timing_log.csv.",
    },
    {
        "n": "7", "name": "Package & publish", "status": "In progress",
        "what": "GitHub repo with data, SQL, tests, workbook, dashboard and report; screenshots; links on the resume.",
        "say": "\"Everything is on GitHub: the generator, the SQL, the answer key and scoring query, the timing "
               "log. Anyone can rebuild the data and rerun the test and get the same numbers.\"",
        "sayzh": "“所有内容都在 GitHub 上：生成脚本、SQL、答案表和评分查询、计时记录。任何人都能重建数据、重跑测试，得到同样的数字。”",
        "qa": [("What would you do differently?",
                "Prepare an honest answer once done, e.g. start the controls earlier, or test on a second seeded ledger.")],
        "evidence": "github.com/linbei2323-web/reph-1",
    },
]

TOUGH = [
    ("Is this a real company?",
     "No. It's a simulated company in a self-directed project. Prices and volume mix come from real CMS data; "
     "the transactions are synthetic. Say so plainly: interviewers respect it."),
    ("Where does the data come from?",
     "Two layers: real 2024 CMS Medicare Part D data for prices and mix (from my market analysis project), and "
     "script-generated transactions recorded in ERPNext."),
    ("What was hardest?",
     "Pick a real moment from your own work, e.g. a control that flagged too many false positives and how you fixed it on the development copy."),
    ("How does this connect to your market analysis project?",
     "That project stops at gross spending, before rebates. This one covers what comes after gross: "
     "gross-to-net, the close and variance analysis. Together they cover both halves of pharma finance."),
]

QUESTION_BANK = [
    ("The big picture", [
        ("Walk me through this project.", "Use the 60-second pitch (section 2).", "介绍一下这个项目。"),
        ("Why did you build this?", "To learn how a pharma finance team closes its books and explains results; real ledgers are confidential, so I simulated one.", "为什么做这个项目？"),
        ("Is this a real company?", "No: a self-directed project with a fictional company; prices and volumes come from real CMS data.", "这是真实公司吗？"),
        ("What was the hardest part?", "A real moment from your own work, e.g. Medicaid product names cut to 10 characters, and Jardiance spelled 'Jardiance' in one table and 'JARDIANCE' in another.", "最难的是什么？"),
    ]),
    ("Data and design", [
        ("Where does the data come from?", "Real CMS Medicare Part D and Medicaid data (2022-2024) for prices, volumes and payer mix; transactions generated by a fixed-seed Python script and recorded in ERPNext.", "数据从哪来？"),
        ("Why these three drugs?", "Three therapeutic areas and two channel types: high-rebate pharmacy drugs and a specialty drug with chargebacks.", "为什么选这三个药？"),
        ("How did you scale real data?", "Real price per claim; real prescriptions / 1,000 for every channel. About $33M gross a year.", "怎么缩小规模？"),
        ("Why synthetic transactions?", "To test controls you need the right answer: planted errors plus an answer key give recall and false positives.", "为什么用模拟交易？"),
        ("What does your data not cover?", "Hospital drugs (Part B), commercial insurance (assumed), net prices: all CMS figures are gross, pre-rebate.", "数据有什么局限？"),
        ("How do you know the data is consistent?", "The generator checks itself every run: entries balance, AR and AP reconcile, accruals roll forward, bank reconciles.", "怎么知道数据内部一致？"),
    ]),
    ("Accounting", [
        ("Book a credit sale and its payment.", "Dr AR / Cr Gross sales; then Dr Bank + Dr Prompt-pay discount / Cr AR.", "赊销和收款怎么记账？"),
        ("How do you account for rebates?", "Accrue monthly from the payer mix: Dr 4100 / Cr 2100. Pay quarterly about 45 days later: Dr 2100 / Cr Bank, true-up to 4100.", "返利怎么记账？"),
        ("What's a true-up?", "The difference between the estimate and the actual bill, booked back to the deduction account.", "什么是调整（true-up）？"),
        ("What's gross-to-net?", "Gross sales minus rebates, chargebacks, returns and discounts. About 37% of gross is deducted in the 2024 data.", "什么是毛到净？"),
        ("Rebate vs chargeback?", "Rebates go to payers for coverage; chargebacks repay wholesalers the gap to a lower contract price.", "返利和价格补差的区别？"),
        ("The trial balance balances. Are the books right?", "Not necessarily: wrong periods and misclassifications still balance. Hence seven controls.", "试算平衡了，账就对吗？"),
        ("Why didn't the bank reconciliation reach zero?", "Three receipts booked 31 Dec cleared in January: $75,050 deposits in transit, named item by item.", "银行对账为什么不是零？"),
        ("Why a big rebate liability at year end?", "Q4 rebates are paid in February: about $2.5M still owed at 31 Dec.", "年末为什么有大额应计返利？"),
    ]),
    ("Controls and testing", [
        ("What controls did you build?", "Trial balance, subledger to GL, bank match, duplicates, cutoff, classification, unapplied payments: SQL queries whose rows are exceptions.", "建了哪些控制？"),
        ("What does held-out mean?", "Rules written on a development copy; run once, unchanged, on a test copy with 40 planted errors.", "“留出”是什么意思？"),
        ("What did you miss and why?", "[Your actual misses], e.g. a duplicate with a typo in the amount escapes an exact-amount rule.", "漏掉了什么、为什么？"),
        ("Recall vs precision?", "Recall = found / 40; precision = found / (found + false positives). [Your numbers.]", "召回率和精确率？"),
        ("How would you catch the misses?", "E.g. near-amount matching for duplicates, traded off against more false positives.", "怎么抓住漏掉的错误？"),
    ]),
    ("FP&A and reporting", [
        ("Explain price vs volume variance.", "Volume = (actual - budget units) x budget price; price = (actual - budget price) x actual units; they add to the total.", "解释量差和价差。"),
        ("What was the variance story?", "Medicaid unwinding: budget extrapolated 2022-23 growth; Medicaid growth slowed in 2024 as all Medicaid prescriptions fell 6%. Onkalyn Medicare beat budget. [Your numbers.]", "差异的故事是什么？"),
        ("Why does losing Medicaid units help net price?", "Medicaid carries the highest statutory rebate (about 23.1% basic, to verify), so the average rebate rate falls.", "为什么失去 Medicaid 销量反而提高净价？"),
        ("Did Medicaid volume fall for your drugs?", "No, and that's the insight: the market fell 6% but these brands still grew, only more slowly than budget. Aggregate trends don't always apply to every product.", "你的药在 Medicaid 销量下降了吗？"),
        ("How do you know the dashboard is right?", "Every GTN bar ties to its ledger account; volume + price = total variance.", "怎么知道看板是对的？"),
        ("What did the 90 / 20 minutes consist of?", "[Only from your stopwatch log.]", "90 / 20 分钟包括什么？"),
    ]),
    ("Pharma industry", [
        ("What's happening in drug pricing?", "IRA Medicare negotiation: Trelegy and Xtandi selected January 2025 for prices from 2027; Jardiance in the first round from 2026 (to verify).", "药价领域最近有什么变化？"),
        ("How did Medicaid change recently?", "From your data: drug spend +11.6% in 2023, -3.0% in 2024; prescriptions -6.0% in 2024.", "Medicaid 最近有什么变化？"),
        ("Who are wholesalers?", "A few large distributors buy most US drugs; they take prompt-pay discounts and file chargebacks.", "批发商是谁、为什么重要？"),
    ]),
    ("Technical", [
        ("Why ERPNext rather than your script?", "It enforces accounting rules and produces a real ERP structure.", "为什么用 ERPNext？"),
        ("Show me a SQL query you wrote.", "[Your own control query]: explain every line.", "给我看一个你写的 SQL。"),
        ("How did you model the database?", "[Your stage 4 design]: star schema, versioned budget, rebuild script.", "数据库怎么设计的？"),
        ("Is it reproducible?", "Yes: fixed seed, scripts in GitHub, same numbers every run.", "可以重现吗？"),
    ]),
    ("Trap questions", [
        ("How many transactions exactly?", "The real final count, not a target.", "交易到底有多少笔？"),
        ("Why 2024?", "So the real Medicaid unwinding falls inside the simulated year.", "为什么是 2024 年？"),
        ("Why does profit differ from plan?", "[Your variance analysis.]", "利润为什么和计划不同？"),
        ("What would you do differently?", "An honest answer, e.g. batched customer payments or accrued prompt-pay discounts.", "如果重做会怎么改？"),
    ]),
]

FILL = [
    ("Transactions recorded", "Generated: 3,631 records incl. 1,170 bank lines (before ERPNext)", "Actual final row count"),
    ("Errors found / false positives", "Not run yet", "Your score output"),
    ("Report time manual / automated", "Not measured yet", "Your stopwatch log"),
    ("Project dates", "Started Oct 2026", "The months you actually worked on it"),
]


def build(path):
    doc = SimpleDocTemplate(path, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.7 * inch, bottomMargin=0.7 * inch,
                            title="Pharma FP&A Roadmap and Interview Guide", author="Daniel Zhang")
    story = [
        p("Pharma FP&amp;A &amp; Financial Close Analytics", "title"),
        Spacer(1, 4),
        p("Roadmap and interview guide · as of 18 October 2026 · Daniel Zhang", "sub"),
        p("路线图与面试指南 · 2026 年 10 月 18 日", "subzh"),
        Spacer(1, 10),
        note_box([
            p("<b>One rule for every answer</b>"),
            p("Say only what you actually did. Numbers in [brackets] are filled in from your real results when "
              "each stage is done. If a result differs from the resume draft, change the resume, not the story."),
            p("每个回答只说你真正做过的。[方括号] 里的数字等阶段完成后用实际结果填写。如果结果和简历草稿不同，改简历，不改故事。", "zh"),
        ]),
        p("1. Roadmap at a glance", "h1"),
        p("路线图总览", "zh"),
        Spacer(1, 4),
        table([["#", "Stage", "Status", "Done so far", "Next"]] +
              [[n, name, status(st), done, nxt] for n, name, st, done, nxt in ROADMAP],
              [0.3 * inch, 1.35 * inch, 0.85 * inch, 2.35 * inch, 2.15 * inch]),
        p("2. The 60-second pitch", "h1"),
        p("一分钟项目介绍", "zh"),
        p("\"This is a self-directed project on how a pharma finance team closes its books and explains its "
          "results. Real ledgers are confidential, so I built a simulated drug company whose products, prices "
          "and volume mix come from real 2024 Medicare Part D data I'd already cleaned. I generated twelve "
          "months of transactions, recorded them in ERPNext, moved them to SQL, and built two things on top: "
          "close controls that catch errors, tested on a held-out ledger with planted errors, and "
          "budget-versus-actual and gross-to-net reporting in Power BI. The lesson I took away: balanced books "
          "aren't the same as correct books.\"", "quote"),
        Spacer(1, 3),
        p("“这是我自主做的项目，研究制药公司财务部怎么结账、怎么解释业绩。真实账本是保密的，所以我搭建了一家模拟药企，产品、价格和销量结构来自我清洗好的真实 2024 年 Medicare Part D 数据。我生成了十二个月的交易，在 ERPNext 记账，导入 SQL，然后做了两件事：能发现错误的月结控制（在植入错误的留出账本上测试），以及 Power BI 中的预算对比和毛到净报告。我的收获：账平不等于账对。”", "quotezh"),
        PageBreak(),
        p("3. Stage by stage: what to say", "h1"),
        p("逐阶段：面试怎么说", "zh"),
    ]

    for s in STAGES:
        block = [
            p(f"Stage {s['n']}: {s['name']}  "
              f"<font size=8.5 color=\"{STATUS_COLOR[s['status']].hexval()}\">[{s['status']}]</font>", "h2"),
            p(s["what"]),
            p("What to say", "label"),
            p(s["say"], "quote"),
            p(s["sayzh"], "quotezh"),
            p("Likely questions", "label"),
        ]
        for q, a in s["qa"]:
            block.append(p(f"<b>Q:</b> {q} <b>A:</b> {a}"))
        block.append(p(f"<b>Evidence to show:</b> {s['evidence']}"))
        block.append(Spacer(1, 4))
        story.append(KeepTogether(block))

    story += [
        PageBreak(),
        p("4. Tough questions", "h1"),
        p("难题", "zh"),
        Spacer(1, 4),
        table([["Question", "How to answer"]] + [[q, a] for q, a in TOUGH], [2.0 * inch, 5.0 * inch]),
        p("5. Numbers to fill in from real results only", "h1"),
        p("只能用实际结果填写的数字", "zh"),
        Spacer(1, 4),
        table([["Claim", "Status today", "Source of the final number"]] + [list(r) for r in FILL],
              [2.0 * inch, 2.6 * inch, 2.4 * inch]),
        PageBreak(),
        p("6. Question bank", "h1"),
        p("\u9762\u8bd5\u9898\u5e93\uff1a\u53ef\u80fd\u88ab\u95ee\u5230\u7684\u95ee\u9898\u548c\u56de\u7b54\u8981\u70b9", "zh"),
        p("[Brackets] = fill in from your own results when that stage is done."),
    ]
    for category, rows in QUESTION_BANK:
        story += [
            p(category, "h2"),
            table([["Question", "How to answer", Paragraph("\u4e2d\u6587", S["cellbzh"])]]
                  + [[q, a, Paragraph(zh, S["cellzh"])] for q, a, zh in rows],
                  [2.0 * inch, 3.7 * inch, 1.3 * inch]),
        ]
    story += [
        Spacer(1, 10),
        note_box([
            p("<b>Takeaway</b>"),
            p("Balanced accounts do not necessarily mean correct accounts. Reliable reporting requires checks on "
              "classification, timing, source documents and reconciliation, not just matching totals."),
            p("账平不等于账对：可靠的报告需要检查分类、时间、原始单据和对账，而不只是总数相等。", "zh"),
        ]),
    ]

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(GREY)
        canvas.drawString(0.75 * inch, 0.45 * inch, "Pharma FP&A & Financial Close Analytics · Roadmap and interview guide")
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.45 * inch, f"Page {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build(sys.argv[1])
