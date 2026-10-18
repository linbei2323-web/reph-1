"""Derive the simulated company's product prices and volumes from real CMS data.

Reads the cleaned Medicare Part D spending table from the pharma-market-analytics
project, takes 2024 figures for the three model drugs, and scales volumes down to
a small company. Prices stay real (average Medicare spend per claim, pre-rebate).

Usage:
    python data/design_inputs.py [path/to/pharma-market-analytics]
"""

import sys
from pathlib import Path

import pandas as pd

MARKET_REPO = Path(sys.argv[1] if len(sys.argv) > 1 else "../pharma-market-analytics")
YEAR = 2024
SCALE = 1 / 1000  # simulated units = real Medicare claims x SCALE

# Fictional product -> the real drug it is modelled on (brand_key, generic_key as in dim_drug).
# GTN rates and unit cost are design assumptions, not from the data; see docs/company-design.md.
PRODUCTS = [
    {"product": "Glyvanta", "model_brand": "Jardiance", "area": "Diabetes & Metabolic",
     "rebate": 0.30, "chargeback": 0.02, "returns": 0.01, "prompt_pay": 0.02, "unit_cost": 60},
    {"product": "Respiqor", "model_brand": "Trelegy Ellipta", "area": "Respiratory",
     "rebate": 0.30, "chargeback": 0.02, "returns": 0.01, "prompt_pay": 0.02, "unit_cost": 70},
    {"product": "Onkalyn", "model_brand": "Xtandi", "area": "Oncology",
     "rebate": 0.05, "chargeback": 0.10, "returns": 0.01, "prompt_pay": 0.02, "unit_cost": 500},
]


def main():
    spending = pd.read_csv(MARKET_REPO / "data/csv/spending_overall.csv.gz")
    year = spending[spending["year"] == YEAR]

    rows = []
    for p in PRODUCTS:
        match = year[year["brand_name"] == p["model_brand"]]
        if len(match) != 1:
            raise ValueError(f"expected one {YEAR} row for {p['model_brand']}, found {len(match)}")
        real = match.iloc[0]

        price = round(real["avg_spend_per_claim"])
        annual_units = round(real["total_claims"] * SCALE)
        monthly_units = round(annual_units / 12)
        gross = monthly_units * price
        gtn_rate = round(p["rebate"] + p["chargeback"] + p["returns"] + p["prompt_pay"], 4)

        rows.append({
            "product": p["product"],
            "model_drug": f"{real['brand_name']} ({real['generic_name']})",
            "area": p["area"],
            "real_spend_usd_b": round(real["total_spending"] / 1e9, 2),
            "real_claims": int(real["total_claims"]),
            "price_per_unit": price,
            "monthly_units": monthly_units,
            "monthly_gross": gross,
            "gtn_rate": gtn_rate,
            "monthly_net": round(gross * (1 - gtn_rate)),
            "monthly_cogs": monthly_units * p["unit_cost"],
            "unit_cost": p["unit_cost"],
            "rebate": p["rebate"],
            "chargeback": p["chargeback"],
            "returns": p["returns"],
            "prompt_pay": p["prompt_pay"],
        })

    table = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(table.to_string(index=False))
    print()
    print("monthly gross:", f"{table['monthly_gross'].sum():,}")
    print("monthly net:  ", f"{table['monthly_net'].sum():,}")
    print("monthly COGS: ", f"{table['monthly_cogs'].sum():,}")

    out = Path(__file__).with_name("design_inputs.csv")
    table.to_csv(out, index=False)
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
