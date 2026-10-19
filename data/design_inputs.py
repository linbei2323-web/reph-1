"""Derive the simulated company's prices, volumes and budget from real CMS data.

Reads data/channel_inputs.csv (made by channel_inputs.py from the
pharma-market-analytics project) and writes two files:

    design_inputs.csv  one row per product: the 2024 drivers the generator uses
    channel_plan.csv   one row per product and payer channel: budget vs actual
                       units, prices and the channel's rebate rate

Budget (v1, as if prepared in late 2023): each channel's 2023 prescriptions grown
by its 2022->2023 growth rate, at the 2023 price. Actual: the real 2024
prescriptions at the 2024 price. Volumes are real prescriptions x SCALE.

Usage:
    python data/design_inputs.py
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
SCALE = 1 / 1000  # simulated units = real prescriptions x SCALE

# Fictional product -> the real drug it is modelled on.
# Rebate rates by channel, chargeback, returns, prompt-pay and unit cost are design
# assumptions, not data (to verify); see docs/company-design.md.
PRODUCTS = [
    {"product": "Glyvanta", "model_drug": "Jardiance", "area": "Diabetes & Metabolic",
     "rebates": {"Medicaid": 0.50, "Medicare": 0.35, "Commercial": 0.30},
     "chargeback": 0.02, "returns": 0.01, "prompt_pay": 0.02, "unit_cost": 60},
    {"product": "Respiqor", "model_drug": "Trelegy Ellipta", "area": "Respiratory",
     "rebates": {"Medicaid": 0.50, "Medicare": 0.35, "Commercial": 0.30},
     "chargeback": 0.02, "returns": 0.01, "prompt_pay": 0.02, "unit_cost": 70},
    {"product": "Onkalyn", "model_drug": "Xtandi", "area": "Oncology",
     "rebates": {"Medicaid": 0.30, "Medicare": 0.03, "Commercial": 0.05},
     "chargeback": 0.10, "returns": 0.01, "prompt_pay": 0.02, "unit_cost": 500},
]


def main():
    ch = pd.read_csv(HERE / "channel_inputs.csv")
    rx = ch.pivot_table(index=["model_drug", "channel"], columns="year", values="rx")
    price = ch[ch["channel"] == "Medicare"].set_index(["model_drug", "year"])["avg_spend_per_rx"]

    channel_rows, product_rows = [], []
    for p in PRODUCTS:
        drug = p["model_drug"]
        budget_price, actual_price = round(price[(drug, 2023)]), round(price[(drug, 2024)])
        for channel, rate in p["rebates"].items():
            r = rx.loc[(drug, channel)]
            budget_rx = r[2023] * (r[2023] / r[2022])  # 2023 grown at the 2022->23 rate
            channel_rows.append({
                "product": p["product"], "channel": channel, "rebate_rate": rate,
                "budget_units_month": round(budget_rx * SCALE / 12, 2),
                "actual_units_month": round(r[2024] * SCALE / 12, 2),
                "budget_price": budget_price, "actual_price": actual_price,
            })

        mine = pd.DataFrame([c for c in channel_rows if c["product"] == p["product"]])
        units = round(mine["actual_units_month"].sum())
        gross = units * actual_price
        rebate = (mine["actual_units_month"] * mine["rebate_rate"]).sum() / mine["actual_units_month"].sum()
        gtn = rebate + p["chargeback"] + p["returns"] + p["prompt_pay"]
        product_rows.append({
            "product": p["product"], "model_drug": drug, "area": p["area"],
            "price_per_unit": actual_price, "monthly_units": units, "monthly_gross": gross,
            "rebate": round(rebate, 4), "chargeback": p["chargeback"], "returns": p["returns"],
            "prompt_pay": p["prompt_pay"], "gtn_rate": round(gtn, 4),
            "monthly_net": round(gross * (1 - gtn)), "unit_cost": p["unit_cost"],
            "monthly_cogs": units * p["unit_cost"],
        })

    channels, products = pd.DataFrame(channel_rows), pd.DataFrame(product_rows)
    channels.to_csv(HERE / "channel_plan.csv", index=False)
    products.to_csv(HERE / "design_inputs.csv", index=False)

    pd.set_option("display.width", 200)
    print(channels.to_string(index=False))
    print()
    print(products.to_string(index=False))
    print()
    for col in ["monthly_gross", "monthly_net", "monthly_cogs"]:
        print(f"{col}: {products[col].sum():,}")


if __name__ == "__main__":
    main()
