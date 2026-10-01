import json
from pathlib import Path
from datetime import date

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "amazon_companyfacts.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "amazon_financials.csv"
)


# ============================================================
# AMAZON SEC XBRL CONCEPTS
# ============================================================

CONCEPTS = {
    "Revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",

    # Amazon does not provide a sufficiently complete
    # GrossProfit concept in Company Facts.
    # Therefore Gross Profit will be derived as:
    #
    # Revenue - Cost of Goods and Services Sold
    #
    "Cost of Revenue": "CostOfGoodsAndServicesSold",

    "Operating Income": "OperatingIncomeLoss",
    "Net Income": "NetIncomeLoss",

    "Assets": "Assets",
    "Equity": "StockholdersEquity",
    "Cash": "CashAndCashEquivalentsAtCarryingValue",
    "Long Term Debt": "LongTermDebt",

    "Operating Cash Flow":
        "NetCashProvidedByUsedInOperatingActivities",
}


# ============================================================
# METRIC TYPES
# ============================================================

FLOW_METRICS = {
    "Revenue",
    "Cost of Revenue",
    "Operating Income",
    "Net Income",
    "Operating Cash Flow",
}

BALANCE_METRICS = {
    "Assets",
    "Equity",
    "Cash",
    "Long Term Debt",
}


# ============================================================
# HELPER FUNCTION
# ============================================================

def get_annual_observations(
    facts,
    concept_name,
    metric_name
):
    """
    Extract annual 10-K observations from SEC Company Facts.

    For flow metrics:
        require start + end
        require duration between 300 and 400 days

    For balance-sheet metrics:
        use point-in-time observations
        no start date required
    """

    if concept_name not in facts:
        print(
            f"WARNING: Concept not found: "
            f"{concept_name}"
        )
        return []

    concept = facts[concept_name]

    units = concept.get("units", {})

    observations = []

    for unit, rows in units.items():

        # We expect USD for all metrics in this project.
        if unit != "USD":
            continue

        for row in rows:

            # ------------------------------------------------
            # Only 10-K
            # ------------------------------------------------

            if row.get("form") != "10-K":
                continue

            # ------------------------------------------------
            # Required fields
            # ------------------------------------------------

            if row.get("end") is None:
                continue

            if row.get("val") is None:
                continue

            if row.get("filed") is None:
                continue

            end_date = row["end"]

            # ------------------------------------------------
            # FLOW METRICS
            # ------------------------------------------------

            if metric_name in FLOW_METRICS:

                if row.get("start") is None:
                    continue

                try:
                    start_date = date.fromisoformat(
                        row["start"]
                    )

                    end_date_obj = date.fromisoformat(
                        end_date
                    )

                    duration_days = (
                        end_date_obj - start_date
                    ).days

                except Exception:
                    continue

                # Annual reporting period.
                #
                # Amazon calendar year:
                # 364 / 365 / 366 days.
                #
                # This removes quarterly and YTD observations.
                if not (
                    300
                    <= duration_days
                    <= 400
                ):
                    continue

                fiscal_year = int(
                    end_date[:4]
                )

                observations.append(
                    {
                        "company": "Amazon",
                        "fiscal_year": fiscal_year,
                        "metric": metric_name,
                        "value": row["val"],
                        "unit": unit,
                        "period_start": row["start"],
                        "period_end": row["end"],
                        "period_type": "annual",
                        "form": row["form"],
                        "filed": row["filed"],
                        "source": "SEC Company Facts",
                    }
                )

            # ------------------------------------------------
            # BALANCE-SHEET METRICS
            # ------------------------------------------------

            elif metric_name in BALANCE_METRICS:

                fiscal_year = int(
                    end_date[:4]
                )

                observations.append(
                    {
                        "company": "Amazon",
                        "fiscal_year": fiscal_year,
                        "metric": metric_name,
                        "value": row["val"],
                        "unit": unit,
                        "period_start": None,
                        "period_end": row["end"],
                        "period_type": "point_in_time",
                        "form": row["form"],
                        "filed": row["filed"],
                        "source": "SEC Company Facts",
                    }
                )

    return observations


# ============================================================
# MAIN
# ============================================================

print("=" * 70)
print("BUILDING AMAZON FINANCIALS")
print("=" * 70)

print()
print(f"Input:  {INPUT_FILE}")
print(f"Output: {OUTPUT_FILE}")
print()


# ============================================================
# LOAD SEC COMPANY FACTS
# ============================================================

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"Amazon Company Facts file not found:\n"
        f"{INPUT_FILE}"
    )


with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    data = json.load(f)


company_name = data.get(
    "entityName",
    "AMAZON.COM, INC."
)

facts = data["facts"]["us-gaap"]


print(
    f"SEC Company: {company_name}"
)

print(
    f"US-GAAP concepts available: "
    f"{len(facts)}"
)

print()


# ============================================================
# EXTRACT DIRECT METRICS
# ============================================================

all_rows = []

for metric_name, concept_name in CONCEPTS.items():

    observations = get_annual_observations(
        facts,
        concept_name,
        metric_name
    )

    print(
        f"{metric_name}: "
        f"{len(observations)} valid observations"
    )

    all_rows.extend(
        observations
    )


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(all_rows)


if df.empty:

    raise RuntimeError(
        "No financial observations were extracted."
    )


# ============================================================
# DATA TYPES
# ============================================================

df["fiscal_year"] = pd.to_numeric(
    df["fiscal_year"],
    errors="coerce"
).astype("Int64")


df["value"] = pd.to_numeric(
    df["value"],
    errors="coerce"
)


df["period_end"] = pd.to_datetime(
    df["period_end"],
    errors="coerce"
)


df["period_start"] = pd.to_datetime(
    df["period_start"],
    errors="coerce"
)


df["filed"] = pd.to_datetime(
    df["filed"],
    errors="coerce"
)


# ============================================================
# REMOVE INVALID ROWS
# ============================================================

df = df.dropna(
    subset=[
        "fiscal_year",
        "value",
        "period_end"
    ]
)


# ============================================================
# DEDUPLICATION
# ============================================================

print()
print("=" * 70)
print("DEDUPLICATING SEC OBSERVATIONS")
print("=" * 70)


rows_before = len(df)


# SEC Company Facts contains comparative observations
# repeated in later filings.
#
# Example:
#
# FY2024 may appear in:
#   2025 filing
#   2026 filing
#
# We keep the latest filed observation for the same:
#
# company + fiscal_year + metric + period_end

df = df.sort_values(
    [
        "company",
        "fiscal_year",
        "metric",
        "period_end",
        "filed",
    ]
)


df = (
    df
    .drop_duplicates(
        subset=[
            "company",
            "fiscal_year",
            "metric",
            "period_end",
        ],
        keep="last",
    )
    .reset_index(drop=True)
)


rows_after = len(df)


print(
    f"Rows before deduplication: "
    f"{rows_before}"
)

print(
    f"Rows after deduplication: "
    f"{rows_after}"
)

print(
    f"Duplicates removed: "
    f"{rows_before - rows_after}"
)


# ============================================================
# DERIVE GROSS PROFIT
# ============================================================

print()
print("=" * 70)
print("DERIVING GROSS PROFIT")
print("=" * 70)


revenue = (
    df[
        df["metric"] == "Revenue"
    ][
        [
            "company",
            "fiscal_year",
            "period_end",
            "value",
            "unit",
        ]
    ]
    .copy()
)


revenue = revenue.rename(
    columns={
        "value": "revenue"
    }
)


cost_of_revenue = (
    df[
        df["metric"] == "Cost of Revenue"
    ][
        [
            "company",
            "fiscal_year",
            "period_end",
            "value",
        ]
    ]
    .copy()
)


cost_of_revenue = (
    cost_of_revenue
    .rename(
        columns={
            "value":
                "cost_of_revenue"
        }
    )
)


gross_profit = revenue.merge(
    cost_of_revenue,
    on=[
        "company",
        "fiscal_year",
        "period_end",
    ],
    how="inner",
)


gross_profit["metric"] = (
    "Gross Profit"
)


gross_profit["value"] = (
    gross_profit["revenue"]
    -
    gross_profit["cost_of_revenue"]
)


gross_profit["unit"] = (
    gross_profit["unit"]
)


gross_profit["period_start"] = pd.NaT


gross_profit["period_type"] = (
    "annual"
)


gross_profit["form"] = (
    "Derived"
)


gross_profit["filed"] = pd.NaT


gross_profit["source"] = (
    "Derived: Revenue - "
    "CostOfGoodsAndServicesSold"
)


gross_profit = gross_profit[
    [
        "company",
        "fiscal_year",
        "metric",
        "value",
        "unit",
        "period_start",
        "period_end",
        "period_type",
        "form",
        "filed",
        "source",
    ]
]


print(
    f"Derived Gross Profit rows: "
    f"{len(gross_profit)}"
)


if not gross_profit.empty:

    print()
    print("Gross Profit history:")

    gross_profit_display = (
        gross_profit
        .sort_values("period_end")
        [
            [
                "fiscal_year",
                "value",
                "period_end",
            ]
        ]
        .copy()
    )

    print(
        gross_profit_display
        .to_string(index=False)
    )


# Add Gross Profit to main dataframe.

df = pd.concat(
    [
        df,
        gross_profit,
    ],
    ignore_index=True,
)


# ============================================================
# DERIVE LIABILITIES
# ============================================================

print()
print("=" * 70)
print("DERIVING LIABILITIES")
print("=" * 70)


assets = (
    df[
        df["metric"] == "Assets"
    ][
        [
            "company",
            "fiscal_year",
            "period_end",
            "value",
        ]
    ]
    .copy()
)


assets = assets.rename(
    columns={
        "value":
            "assets"
    }
)


equity = (
    df[
        df["metric"] == "Equity"
    ][
        [
            "company",
            "fiscal_year",
            "period_end",
            "value",
        ]
    ]
    .copy()
)


equity = equity.rename(
    columns={
        "value":
            "equity"
    }
)


liabilities = assets.merge(
    equity,
    on=[
        "company",
        "fiscal_year",
        "period_end",
    ],
    how="inner",
)


liabilities["metric"] = (
    "Liabilities"
)


liabilities["value"] = (
    liabilities["assets"]
    -
    liabilities["equity"]
)


liabilities["unit"] = (
    "USD"
)


liabilities["period_start"] = (
    pd.NaT
)


liabilities["period_type"] = (
    "point_in_time"
)


liabilities["form"] = (
    "Derived"
)


liabilities["filed"] = (
    pd.NaT
)


liabilities["source"] = (
    "Derived: Assets - Equity"
)


liabilities = liabilities[
    [
        "company",
        "fiscal_year",
        "metric",
        "value",
        "unit",
        "period_start",
        "period_end",
        "period_type",
        "form",
        "filed",
        "source",
    ]
]


print(
    f"Derived Liabilities rows: "
    f"{len(liabilities)}"
)


# Add liabilities.

df = pd.concat(
    [
        df,
        liabilities,
    ],
    ignore_index=True,
)


# ============================================================
# FINAL SORT
# ============================================================

df = df.sort_values(
    [
        "fiscal_year",
        "metric",
        "period_end",
    ]
).reset_index(
    drop=True
)


# ============================================================
# FORMAT DATES FOR CSV
# ============================================================

df["period_end"] = (
    pd.to_datetime(
        df["period_end"],
        errors="coerce"
    )
    .dt.strftime("%Y-%m-%d")
)


df["period_start"] = (
    pd.to_datetime(
        df["period_start"],
        errors="coerce"
    )
    .dt.strftime("%Y-%m-%d")
)


df["filed"] = (
    pd.to_datetime(
        df["filed"],
        errors="coerce"
    )
    .dt.strftime("%Y-%m-%d")
)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8"
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("BUILD COMPLETED")
print("=" * 70)

print(
    f"Rows: {len(df)}"
)

print(
    f"Columns: {len(df.columns)}"
)


print(
    f"Fiscal years: "
    f"{df['fiscal_year'].min()} - "
    f"{df['fiscal_year'].max()}"
)


print()
print("Metrics:")

print(
    df["metric"]
    .value_counts()
    .sort_index()
    .to_string()
)


print()
print(
    f"Saved: {OUTPUT_FILE}"
)


# ============================================================
# LATEST FISCAL YEAR
# ============================================================

latest_year = int(
    df["fiscal_year"].max()
)


print()
print("=" * 70)
print(
    f"LATEST FISCAL YEAR: "
    f"{latest_year}"
)
print("=" * 70)


latest = (
    df[
        df["fiscal_year"]
        == latest_year
    ]
    [
        [
            "metric",
            "value",
            "period_end",
            "source",
        ]
    ]
    .sort_values("metric")
)


print(
    latest.to_string(
        index=False
    )
)


# ============================================================
# GROSS PROFIT CHECK
# ============================================================

print()
print("=" * 70)
print("GROSS PROFIT CHECK")
print("=" * 70)


latest_gross_profit = latest[
    latest["metric"]
    == "Gross Profit"
]


if latest_gross_profit.empty:

    print(
        "WARNING: Gross Profit "
        "was not derived for the latest "
        "fiscal year."
    )

else:

    gross_profit_value = (
        latest_gross_profit.iloc[0]["value"]
    )

    print(
        f"FY{latest_year} Gross Profit: "
        f"{gross_profit_value:,.0f} USD"
    )

    print(
        "Formula: "
        "Revenue - CostOfGoodsAndServicesSold"
    )


# ============================================================
# LIABILITY CHECK
# ============================================================

print()
print("=" * 70)
print("LIABILITIES CHECK")
print("=" * 70)


latest_liabilities = latest[
    latest["metric"]
    == "Liabilities"
]


if latest_liabilities.empty:

    print(
        "WARNING: Liabilities "
        "were not derived for the latest "
        "fiscal year."
    )

else:

    liabilities_value = (
        latest_liabilities.iloc[0]["value"]
    )

    print(
        f"FY{latest_year} Liabilities: "
        f"{liabilities_value:,.0f} USD"
    )

    print(
        "Formula: "
        "Assets - Equity"
    )


print()
print("=" * 70)
print("DONE")
print("=" * 70)