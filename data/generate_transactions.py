"""Generate 12 months of transactions for Halvern Pharmaceuticals.

Reads the product plan from data/design_inputs.csv (made by design_inputs.py) and
writes one CSV per document type to data/generated/. The random seed is fixed, so
every run produces exactly the same data.

Built piece by piece:
    1. calendar + sales invoices          (done)
    2. customer payments                  (done)
    3. purchase invoices + supplier payments  (done)
    4. journal entries + period close dates   (this version)
    5. bank lines + planned deviations

Usage:
    python data/generate_transactions.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

HERE = Path(__file__).parent
OUT = HERE / "generated"

SEED = 2025
YEAR = 2025

# Wholesalers and their share of every product's volume (docs/company-design.md).
CUSTOMERS = {
    "Northstar Drug Supply": 0.40,
    "Meridian Health Distribution": 0.35,
    "Keystone Pharma Wholesale": 0.25,
}

# How often each customer orders each product. Pharmacy drugs move in frequent
# small orders; the specialty drug in occasional orders of a few units.
ORDER_DAYS = {
    "Glyvanta": ["Mon", "Wed", "Fri"],
    "Respiqor": ["Mon", "Wed", "Fri"],
    "Onkalyn": ["Tue"],
}

UNIT_NOISE = 0.10  # each order's units vary randomly by about +/-10% around the plan

PAYMENT_TERMS_DAYS = 30
PROMPT_PAY_DISCOUNT = 0.02  # taken when the customer pays by the due date
ON_TIME_SHARE = 0.85        # share of invoices paid by the due date
MAX_DAYS_LATE = 15          # late payers pay 1 to 15 days after the due date

# Suppliers: what each bills for, how often, and the planned monthly spend.
# Inventory purchases replace what was sold (planned COGS about $103,790 a month).
# Department spend is the vendor share of each cost center budget; the rest of
# each budget is payroll, booked by journal entry in piece 4.
SUPPLIERS = [
    {"supplier": "Corvane Ingredients", "account": "1200 Inventory", "cost_center": "Manufacturing",
     "per_month": 4, "monthly_amount": 72_650},
    {"supplier": "Pacwell Packaging", "account": "1200 Inventory", "cost_center": "Manufacturing",
     "per_month": 2, "monthly_amount": 31_140},
    {"supplier": "Arclight Clinical Research", "account": "6100 R&D", "cost_center": "R&D",
     "per_month": 4, "monthly_amount": 200_000},
    {"supplier": "Brightline Marketing", "account": "6000 Commercial", "cost_center": "Commercial",
     "per_month": 4, "monthly_amount": 150_000},
    {"supplier": "Tessaro Office & IT", "account": "6300 G&A", "cost_center": "G&A",
     "per_month": 2, "monthly_amount": 40_000},
]
AMOUNT_NOISE = 0.15         # each supplier invoice varies by about +/-15%
SUPPLIER_TERMS_DAYS = 45
SUPPLIER_ON_TIME_SHARE = 0.90
PAYMENT_RUN_DAY = "Thu"     # Halvern pays suppliers in one weekly payment run

# Journal entries (piece 4).
OPENING_BALANCES = {"1000 Bank": 5_000_000, "1200 Inventory": 300_000}  # against 3000 Equity
# Monthly payroll per cost center: the part of each budget not spent with suppliers.
PAYROLL = {
    "Commercial": ("6000 Commercial", 200_000),
    "R&D": ("6100 R&D", 150_000),
    "Manufacturing": ("6200 Manufacturing", 150_000),
    "G&A": ("6300 G&A", 80_000),
}
PAYROLL_NOISE = 0.03        # overtime, bonuses, leavers: +/-3% a month
# GTN accruals are booked at month end from that month's gross sales by product.
# Settlement: when the cash is actually paid, and how far it may differ from the estimate.
ACCRUALS = {
    "rebate": {"expense": "4100 Rebates", "liability": "2100 Rebate accrual",
               "party": "Payer rebate programs", "settle": "quarterly", "lag_days": 45, "true_up_noise": 0.03},
    "chargeback": {"expense": "4200 Chargebacks", "liability": "2110 Chargeback accrual",
                   "party": "wholesaler", "settle": "monthly", "lag_days": 20, "true_up_noise": 0.02},
    "returns": {"expense": "4300 Returns", "liability": "2120 Returns reserve",
                "party": "wholesaler", "settle": "quarterly", "lag_days": 30, "true_up_noise": 0.10},
}
CLOSE_BUSINESS_DAYS = 5     # each month is closed on the 5th business day of the next month

# Banks and wholesalers don't work on US federal holidays.
BUSINESS_DAY = CustomBusinessDay(calendar=USFederalHolidayCalendar())


def business_days(year):
    """All Monday-to-Friday dates in the year, excluding US federal holidays."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq=BUSINESS_DAY)
    return pd.DataFrame({"date": days, "weekday": days.strftime("%a"), "month": days.month})


def sales_invoices(plan, calendar, rng):
    """One invoice per customer, product and order day.

    Each month's planned units are split across customers by their share, then
    evenly across that customer's order days in the month, with random noise.
    """
    rows = []
    for _, product in plan.iterrows():
        order_days = calendar[calendar["weekday"].isin(ORDER_DAYS[product["product"]])]
        for customer, share in CUSTOMERS.items():
            for month, days in order_days.groupby("month"):
                units_per_order = product["monthly_units"] * share / len(days)
                for date in days["date"]:
                    units = max(0, round(units_per_order * rng.normal(1, UNIT_NOISE)))
                    if units == 0:
                        continue
                    rows.append({
                        "posting_date": date.date(),
                        "customer": customer,
                        "item": product["product"],
                        "qty": units,
                        "rate": product["price_per_unit"],
                        "amount": units * product["price_per_unit"],
                        "cost_center": "Commercial",
                    })

    invoices = pd.DataFrame(rows).sort_values(["posting_date", "customer", "item"])
    invoices.insert(0, "invoice_no", [f"SINV-{YEAR}-{i:05d}" for i in range(1, len(invoices) + 1)])
    invoices["due_date"] = pd.to_datetime(invoices["posting_date"]) + pd.Timedelta(days=PAYMENT_TERMS_DAYS)
    invoices["due_date"] = invoices["due_date"].dt.date
    return invoices


def customer_payments(invoices, rng):
    """One payment per invoice.

    Most wholesalers pay on or just before the due date and take the prompt-pay
    discount; the rest pay late and pay in full. Payment dates fall on business
    days. Payments that would land after the year end are not created: those
    invoices stay open in accounts receivable at 31 December.
    """
    rows = []
    year_end = pd.Timestamp(f"{YEAR}-12-31")
    for inv in invoices.itertuples():
        due = pd.Timestamp(inv.due_date)
        on_time = rng.random() < ON_TIME_SHARE
        if on_time:
            pay_date = due - pd.Timedelta(days=int(rng.integers(0, 3)))  # 0 to 2 days early
        else:
            pay_date = due + pd.Timedelta(days=int(rng.integers(1, MAX_DAYS_LATE + 1)))
        pay_date = BUSINESS_DAY.rollforward(pay_date)
        if pay_date > year_end:
            continue

        discount = round(inv.amount * PROMPT_PAY_DISCOUNT) if on_time else 0
        rows.append({
            "payment_date": pay_date.date(),
            "customer": inv.customer,
            "invoice_no": inv.invoice_no,
            "invoice_amount": inv.amount,
            "discount": discount,
            "amount_received": inv.amount - discount,
            "on_time": on_time,
        })

    payments = pd.DataFrame(rows).sort_values(["payment_date", "customer", "invoice_no"])
    payments.insert(0, "payment_no", [f"PAY-IN-{YEAR}-{i:05d}" for i in range(1, len(payments) + 1)])
    return payments


def purchase_invoices(calendar, rng):
    """Supplier invoices spread evenly through each month.

    A supplier billing 4 times a month bills in weeks 1-4; twice a month, around
    the 1st and the 15th. Amounts vary randomly around the planned monthly spend.
    """
    rows = []
    for s in SUPPLIERS:
        for month, days in calendar.groupby("month"):
            dates = days["date"].tolist()
            # pick evenly spaced business days in the month
            picks = [dates[round(i * (len(dates) - 1) / s["per_month"])] for i in range(s["per_month"])]
            for date in picks:
                amount = round(s["monthly_amount"] / s["per_month"] * rng.normal(1, AMOUNT_NOISE), 2)
                rows.append({
                    "posting_date": date.date(),
                    "supplier": s["supplier"],
                    "account": s["account"],
                    "cost_center": s["cost_center"],
                    "amount": amount,
                })

    bills = pd.DataFrame(rows).sort_values(["posting_date", "supplier"])
    bills.insert(0, "bill_no", [f"PINV-{YEAR}-{i:05d}" for i in range(1, len(bills) + 1)])
    bills["due_date"] = (pd.to_datetime(bills["posting_date"])
                         + pd.Timedelta(days=SUPPLIER_TERMS_DAYS)).dt.date
    return bills


def supplier_payments(bills, rng):
    """Pay each bill in the weekly payment run.

    On time (90%): the last payment run on or before the due date.
    Late (10%): one or two runs after the due date, e.g. while an invoice is queried.
    Bills whose payment run falls after the year end stay open in accounts payable.
    """
    run_day = pd.offsets.Week(weekday=["Mon", "Tue", "Wed", "Thu", "Fri"].index(PAYMENT_RUN_DAY))
    year_end = pd.Timestamp(f"{YEAR}-12-31")
    rows = []
    for bill in bills.itertuples():
        due = pd.Timestamp(bill.due_date)
        on_time = rng.random() < SUPPLIER_ON_TIME_SHARE
        if on_time:
            pay_date = due if due.strftime("%a") == PAYMENT_RUN_DAY else run_day.rollback(due)
        else:
            pay_date = run_day.rollforward(due + pd.Timedelta(days=1)) + pd.Timedelta(weeks=int(rng.integers(0, 2)))
        pay_date = BUSINESS_DAY.rollforward(pay_date)  # a holiday run moves to the next business day
        if pay_date > year_end:
            continue
        rows.append({
            "payment_date": pay_date.date(),
            "supplier": bill.supplier,
            "bill_no": bill.bill_no,
            "amount_paid": bill.amount,
            "on_time": on_time,
        })

    payments = pd.DataFrame(rows).sort_values(["payment_date", "supplier", "bill_no"])
    payments.insert(0, "payment_no", [f"PAY-OUT-{YEAR}-{i:05d}" for i in range(1, len(payments) + 1)])
    return payments


class Journal:
    """Collects journal entries as balanced debit/credit lines."""

    def __init__(self):
        self.lines = []
        self.count = 0

    def add(self, date, je_type, lines, remark):
        """lines: (account, debit, credit, cost_center, product, party) tuples."""
        debit = round(sum(l[1] for l in lines), 2)
        credit = round(sum(l[2] for l in lines), 2)
        assert debit == credit, f"unbalanced {je_type} on {date}: {debit} vs {credit}"
        self.count += 1
        je_no = f"JE-{YEAR}-{self.count:05d}"
        for account, dr, cr, cost_center, product, party in lines:
            self.lines.append({
                "je_no": je_no, "posting_date": pd.Timestamp(date).date(), "je_type": je_type,
                "account": account, "debit": round(dr, 2), "credit": round(cr, 2),
                "cost_center": cost_center, "product": product, "party": party, "remark": remark,
            })

    def frame(self):
        return pd.DataFrame(self.lines)


def month_end(month):
    """Last business day of the month."""
    return BUSINESS_DAY.rollback(pd.Timestamp(YEAR, month, 1) + pd.offsets.MonthEnd(0))


def journal_entries(plan, invoices, rng):
    """Opening balances, payroll, cost of goods sold, GTN accruals and their settlements."""
    j = Journal()
    rates = plan.set_index("product")
    inv = invoices.assign(month=pd.to_datetime(invoices["posting_date"]).dt.month)

    # Opening balance sheet, 1 January.
    j.add(f"{YEAR}-01-01", "Opening balance",
          [(acc, amt, 0, "", "", "") for acc, amt in OPENING_BALANCES.items()]
          + [("3000 Equity", 0, sum(OPENING_BALANCES.values()), "", "", "")],
          "Opening balances")

    for month in range(1, 13):
        end = month_end(month)
        sold = inv[inv["month"] == month]

        # Payroll, paid on the last business day.
        lines, total = [], 0
        for cost_center, (account, amount) in PAYROLL.items():
            amt = round(amount * rng.normal(1, PAYROLL_NOISE), 2)
            total += amt
            lines.append((account, amt, 0, cost_center, "", ""))
        lines.append(("1000 Bank", 0, round(total, 2), "", "", ""))
        j.add(end, "Payroll", lines, f"Payroll {end:%b %Y}")

        # Cost of goods sold: units sold this month x standard unit cost.
        lines, total = [], 0
        for product, units in sold.groupby("item")["qty"].sum().items():
            cost = units * rates.loc[product, "unit_cost"]
            total += cost
            lines.append(("5000 Cost of goods sold", cost, 0, "Manufacturing", product, ""))
        lines.append(("1200 Inventory", 0, total, "Manufacturing", "", ""))
        j.add(end, "COGS", lines, f"Cost of goods sold {end:%b %Y}")

        # GTN accruals: this month's gross sales x the planned rate, by product.
        for kind, a in ACCRUALS.items():
            lines, total = [], 0
            for product, gross in sold.groupby("item")["amount"].sum().items():
                amt = round(gross * rates.loc[product, kind], 2)
                total += amt
                lines.append((a["expense"], amt, 0, "Commercial", product, ""))
            lines.append((a["liability"], 0, round(total, 2), "Commercial", "", ""))
            j.add(end, f"{kind.title()} accrual", lines, f"{kind.title()} accrual {end:%b %Y}")

    # Settlements: pay what was accrued for each period; the difference from the
    # estimate (true-up) goes back to the expense account.
    accrued = j.frame()
    accrued = accrued[accrued["je_type"].str.endswith("accrual") & (accrued["credit"] > 0)].copy()
    accrued["month"] = pd.to_datetime(accrued["posting_date"]).dt.month
    year_end = pd.Timestamp(f"{YEAR}-12-31")
    for kind, a in ACCRUALS.items():
        rows = accrued[accrued["account"] == a["liability"]]
        if a["settle"] == "quarterly":
            periods = [(f"Q{q}", [3 * q - 2, 3 * q - 1, 3 * q]) for q in range(1, 5)]
        else:
            periods = [(f"{pd.Timestamp(YEAR, m, 1):%b}", [m]) for m in range(1, 13)]
        for label, months in periods:
            amount = round(rows[rows["month"].isin(months)]["credit"].sum(), 2)
            pay_date = BUSINESS_DAY.rollforward(month_end(months[-1]) + pd.Timedelta(days=a["lag_days"]))
            if pay_date > year_end:
                continue  # still owed at year end
            actual = round(amount * rng.normal(1, a["true_up_noise"]), 2)
            true_up = round(actual - amount, 2)
            lines = [(a["liability"], amount, 0, "Commercial", "", "")]
            if true_up > 0:
                lines.append((a["expense"], true_up, 0, "Commercial", "", ""))
            elif true_up < 0:
                lines.append((a["expense"], 0, -true_up, "Commercial", "", ""))
            lines.append(("1000 Bank", 0, actual, "", "", ""))
            party = a["party"] if a["party"] != "wholesaler" else "Wholesalers (claims)"
            j.add(pay_date, f"{kind.title()} settlement",
                  [(acc, dr, cr, cc, prod, party) for acc, dr, cr, cc, prod, _ in lines],
                  f"{kind.title()} settlement {label} {YEAR}")

    return j.frame()


def period_close_dates():
    """Planned close date for each month: the 5th business day of the next month."""
    rows = []
    for month in range(1, 13):
        first_next = pd.Timestamp(YEAR, month, 1) + pd.offsets.MonthBegin(1)
        closed_on = BUSINESS_DAY.rollforward(first_next) + (CLOSE_BUSINESS_DAYS - 1) * BUSINESS_DAY
        rows.append({"period": f"{YEAR}-{month:02d}", "closed_on": closed_on.date()})
    return pd.DataFrame(rows)


def general_ledger(invoices, payments, bills, supplier_pay, journal):
    """Every document turned into debit/credit lines, as ERPNext will post them.

    Used only to check the generated data and to give an expected trial balance
    to compare with ERPNext after the import.
    """
    gl = []
    for r in invoices.itertuples():
        gl += [("1100 Accounts receivable", r.amount, 0), ("4000 Gross product sales", 0, r.amount)]
    for r in payments.itertuples():
        gl += [("1000 Bank", r.amount_received, 0), ("4400 Prompt-pay discounts", r.discount, 0),
               ("1100 Accounts receivable", 0, r.invoice_amount)]
    for r in bills.itertuples():
        gl += [(r.account, r.amount, 0), ("2000 Accounts payable", 0, r.amount)]
    for r in supplier_pay.itertuples():
        gl += [("2000 Accounts payable", r.amount_paid, 0), ("1000 Bank", 0, r.amount_paid)]
    gl += list(journal[["account", "debit", "credit"]].itertuples(index=False, name=None))
    gl = pd.DataFrame(gl, columns=["account", "debit", "credit"])
    tb = gl.groupby("account")[["debit", "credit"]].sum()
    tb["balance"] = (tb["debit"] - tb["credit"]).round(2)
    return tb


def main():
    rng = np.random.default_rng(SEED)
    plan = pd.read_csv(HERE / "design_inputs.csv")
    calendar = business_days(YEAR)

    invoices = sales_invoices(plan, calendar, rng)
    payments = customer_payments(invoices, rng)
    bills = purchase_invoices(calendar, rng)
    supplier_pay = supplier_payments(bills, rng)
    journal = journal_entries(plan, invoices, rng)
    periods = period_close_dates()

    OUT.mkdir(exist_ok=True)
    invoices.to_csv(OUT / "sales_invoices.csv", index=False)
    payments.to_csv(OUT / "customer_payments.csv", index=False)
    bills.to_csv(OUT / "purchase_invoices.csv", index=False)
    supplier_pay.to_csv(OUT / "supplier_payments.csv", index=False)
    journal.to_csv(OUT / "journal_entries.csv", index=False)
    periods.to_csv(OUT / "periods.csv", index=False)

    # Check: generated units per month vs plan.
    invoices["month"] = pd.to_datetime(invoices["posting_date"]).dt.month
    check = invoices.pivot_table(index="month", columns="item", values="qty", aggfunc="sum")
    print("Units per month (plan:", dict(zip(plan["product"], plan["monthly_units"])), ")")
    print(check.to_string())
    print()
    print("invoices:", len(invoices), f"(about {len(invoices) / 12:.0f} a month)")
    print("gross sales for the year:", f"${invoices['amount'].sum():,.0f}")
    print("holiday orders:", int(invoices["posting_date"].astype(str).isin(["2025-01-01", "2025-07-04", "2025-12-25"]).sum()))

    # Check: payments, discounts and what is still owed at year end.
    open_ar = invoices.loc[~invoices["invoice_no"].isin(payments["invoice_no"]), "amount"].sum()
    print()
    print("payments:", len(payments), f"(about {len(payments) / 12:.0f} a month)")
    print("paid on time:", f"{payments['on_time'].mean():.1%}")
    print("cash received:", f"${payments['amount_received'].sum():,.0f}")
    print("prompt-pay discounts:", f"${payments['discount'].sum():,.0f}",
          f"({payments['discount'].sum() / invoices['amount'].sum():.2%} of gross sales)")
    print("open AR at 31 Dec:", f"${open_ar:,.0f}")
    # Every invoice is either paid (in full, net of discount) or still open.
    paid = payments["amount_received"].sum() + payments["discount"].sum()
    assert paid + open_ar == invoices["amount"].sum(), "AR does not reconcile"
    print("AR check: paid + discounts + open AR = gross sales  OK")

    # Check: supplier side.
    open_ap = bills.loc[~bills["bill_no"].isin(supplier_pay["bill_no"]), "amount"].sum()
    print()
    print("purchase invoices:", len(bills), f"(about {len(bills) / 12:.0f} a month)")
    print(bills.groupby(["account", "cost_center"])["amount"].sum().map("${:,.0f}".format).to_string())
    print("supplier payments:", len(supplier_pay), "| paid on time:", f"{supplier_pay['on_time'].mean():.1%}")
    print("payment days:", sorted(pd.to_datetime(supplier_pay["payment_date"]).dt.strftime("%a").unique()))
    print("cash paid to suppliers:", f"${supplier_pay['amount_paid'].sum():,.0f}")
    print("open AP at 31 Dec:", f"${open_ap:,.0f}")
    assert round(supplier_pay["amount_paid"].sum() + open_ap, 2) == round(bills["amount"].sum(), 2), "AP does not reconcile"
    print("AP check: paid + open AP = purchases  OK")

    # Check: journal entries.
    print()
    print("journal entries:", journal["je_no"].nunique(), "| lines:", len(journal))
    print(journal.groupby("je_type")["je_no"].nunique().to_string())

    # Check: each GTN accrual account rolls forward (booked = settled + true-up + balance left).
    print()
    print("GTN accrual roll-forward (accrued = paid out - true-up + still owed at 31 Dec):")
    for kind, a in ACCRUALS.items():
        acc = journal[journal["account"] == a["liability"]]
        booked = acc.loc[acc["je_type"].str.endswith("accrual"), "credit"].sum()
        released = acc.loc[acc["je_type"].str.endswith("settlement"), "debit"].sum()
        settle = journal[journal["je_type"] == f"{kind.title()} settlement"]
        paid = settle.loc[settle["account"] == "1000 Bank", "credit"].sum()
        owed = booked - released
        print(f"  {a['liability']:<24} accrued ${booked:>12,.0f}  paid ${paid:>12,.0f}  "
              f"true-up ${paid - released:>9,.0f}  still owed ${owed:>11,.0f}")

    print()
    print("period close dates:", ", ".join(f"{r.period[-2:]}->{r.closed_on:%m-%d}" for r in periods.itertuples()))

    # Expected trial balance from all documents: what ERPNext should show after import.
    tb = general_ledger(invoices, payments, bills, supplier_pay, journal)
    tb.to_csv(OUT / "expected_trial_balance.csv")
    print()
    print("Expected trial balance at 31 Dec (debit balance +, credit balance -):")
    print(tb["balance"].map("{:>16,.2f}".format).to_string())
    assert abs(tb["balance"].sum()) < 0.01, "trial balance does not balance"
    print("TB check: total debits = total credits  OK")
    assert tb.loc["1000 Bank", "balance"] > 0 and tb.loc["1200 Inventory", "balance"] > 0


if __name__ == "__main__":
    main()
