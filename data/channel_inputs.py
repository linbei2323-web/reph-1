"""Prescriptions by payer channel for the three model drugs, 2022-2024.

Reads Daniel's cleaned CMS data (pharma-market-analytics) and writes
data/channel_inputs.csv with one row per drug, channel and year:

    Medicare   = Part D claims (spending_overall)
    Medicaid   = prescriptions, national table, FFSU + MCOU (medicaid_national)
    Commercial = not in the data: an assumed multiple of Medicare (to verify)

Usage:
    python data/channel_inputs.py [path/to/pharma-market-analytics]
"""

import sys
from pathlib import Path

import pandas as pd

MARKET_REPO = Path(sys.argv[1] if len(sys.argv) > 1 else "../pharma-market-analytics")
YEARS = [2022, 2023, 2024]

# Medicare brand name -> how the drug appears in the Medicaid data.
# Medicaid product names are cut to 10 characters and their case is not
# consistent ("Jardiance" in the national table, "JARDIANCE" in the state
# table), so match on an upper-cased prefix.
DRUGS = {
    "Jardiance": "JARDIANCE",
    "Trelegy Ellipta": "TRELEGY EL",
    "Xtandi": "XTANDI",
}

# Commercial prescriptions as a multiple of Medicare claims (assumption, to verify):
# SGLT2 diabetes drugs have many working-age patients; COPD inhalers and prostate
# cancer drugs skew older, so Medicare dominates.
COMMERCIAL_VS_MEDICARE = {"Jardiance": 0.50, "Trelegy Ellipta": 0.40, "Xtandi": 0.40}


def main():
    medicare = pd.read_csv(MARKET_REPO / "data/csv/spending_overall.csv.gz")
    medicaid = pd.read_csv(MARKET_REPO / "data/csv/medicaid_national.csv.gz", dtype={"ndc11": str})
    names = medicaid["product_name"].astype(str).str.upper()

    rows = []
    for brand, prefix in DRUGS.items():
        mc = medicare[(medicare["brand_name"] == brand) & medicare["year"].isin(YEARS)].set_index("year")
        md = medicaid[names.str.startswith(prefix) & medicaid["year"].isin(YEARS)]
        md_rx = md.groupby("year")["prescriptions"].sum(min_count=1)
        matched = sorted(md["product_name"].unique())
        for year in YEARS:
            claims = mc.loc[year, "total_claims"]
            rows += [
                {"model_drug": brand, "year": year, "channel": "Medicare", "rx": claims,
                 "avg_spend_per_rx": mc.loc[year, "avg_spend_per_claim"], "source": "CMS Part D spending"},
                {"model_drug": brand, "year": year, "channel": "Medicaid", "rx": md_rx[year],
                 "avg_spend_per_rx": None, "source": f"Medicaid SDUD national: {', '.join(matched)}"},
                {"model_drug": brand, "year": year, "channel": "Commercial",
                 "rx": round(claims * COMMERCIAL_VS_MEDICARE[brand]), "avg_spend_per_rx": None,
                 "source": f"assumption: {COMMERCIAL_VS_MEDICARE[brand]:.0%} of Medicare (to verify)"},
            ]

    out = pd.DataFrame(rows)
    out.to_csv(Path(__file__).with_name("channel_inputs.csv"), index=False)

    wide = out.pivot_table(index=["model_drug", "channel"], columns="year", values="rx")
    wide["growth_22_23"] = wide[2023] / wide[2022] - 1
    wide["growth_23_24"] = wide[2024] / wide[2023] - 1
    pd.set_option("display.width", 200)
    print(wide.to_string(float_format=lambda v: f"{v:,.3f}" if abs(v) < 10 else f"{v:,.0f}"))

    total = medicaid.groupby("year")["prescriptions"].sum(min_count=1)
    print("\nAll Medicaid prescriptions:", {y: f"{total[y]:,.0f}" for y in YEARS},
          f"| 2023->2024: {total[2024] / total[2023] - 1:+.1%}")


if __name__ == "__main__":
    main()
