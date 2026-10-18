"""Generate 12 months of transactions for Halvern Pharmaceuticals.

Reads the product plan from data/design_inputs.csv (made by design_inputs.py) and
writes one CSV per document type to data/generated/. The random seed is fixed, so
every run produces exactly the same data.

Built piece by piece:
    1. calendar + sales invoices          (this version)
    2. customer payments
    3. purchase invoices + supplier payments
    4. journal entries
    5. bank lines + planned deviations

Usage:
    python data/generate_transactions.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

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


def business_days(year):
    """All Monday-to-Friday dates in the year."""
    days = pd.bdate_range(f"{year}-01-01", f"{year}-12-31")
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
    invoices["due_date"] = pd.to_datetime(invoices["posting_date"]) + pd.Timedelta(days=30)
    invoices["due_date"] = invoices["due_date"].dt.date
    return invoices


def main():
    rng = np.random.default_rng(SEED)
    plan = pd.read_csv(HERE / "design_inputs.csv")
    calendar = business_days(YEAR)

    invoices = sales_invoices(plan, calendar, rng)

    OUT.mkdir(exist_ok=True)
    invoices.to_csv(OUT / "sales_invoices.csv", index=False)

    # Check: generated units per month vs plan.
    invoices["month"] = pd.to_datetime(invoices["posting_date"]).dt.month
    check = invoices.pivot_table(index="month", columns="item", values="qty", aggfunc="sum")
    print("Units per month (plan:", dict(zip(plan["product"], plan["monthly_units"])), ")")
    print(check.to_string())
    print()
    print("invoices:", len(invoices), f"(about {len(invoices) / 12:.0f} a month)")
    print("gross sales for the year:", f"${invoices['amount'].sum():,.0f}")


if __name__ == "__main__":
    main()
