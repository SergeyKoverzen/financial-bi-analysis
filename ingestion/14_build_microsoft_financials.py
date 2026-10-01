import json
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "microsoft_companyfacts.json"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "microsoft_financials.csv"
)


# ============================================================
# COMPANY
# ============================================================

COMPANY = "Microsoft"


# ============================================================
# SEC XBRL CONCEPTS
# ============================================================

CONCEPTS = {
    "Revenue": "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Gross Profit": "GrossProfit",
    "Operating Income": "OperatingIncomeLoss",
    "Net Income": "NetIncomeLoss",
    "Assets": "Assets",
    "Liabilities": "Liabilities",
    "Equity": "StockholdersEquity",
    "Cash": "CashAndCashEquivalentsAtCarryingValue",
    "Long Term Debt": "LongTermDebt",
    "Operating Cash Flow": "NetCashProvidedByUsedInOperatingActivities",
}


# ============================================================
# FLOW / BALANCE METRICS
# ============================================================

FLOW_METRICS = {
    "Revenue",
    "Gross Profit",
    "Operating Income",
    "Net Income",
    "Operating Cash Flow",
}

BALANCE_METRICS = {
    "Assets",
    "Liabilities",
    "Equity",
    "Cash",
    "Long Term Debt",
}


# ============================================================
# EXPECTED FINAL COLUMNS
# ============================================================

EXPECTED_COLUMNS = [
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


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BUILDING MICROSOFT FINANCIALS")
    print("=" * 80)

    print(f"Input file:  {INPUT_FILE}")
    print(f"Output file: {OUTPUT_FILE}")
    print()


    # --------------------------------------------------------
    # Load SEC Company Facts
    # --------------------------------------------------------

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    facts = data["facts"]["us-gaap"]

    print(f"Company: {data['entityName']}")
    print()


    # --------------------------------------------------------
    # Extract observations
    # --------------------------------------------------------

    records = []

    for metric_name, concept_name in CONCEPTS.items():

        print(f"Processing: {metric_name}")
        print(f"Concept:   {concept_name}")

        if concept_name not in facts:
            print("WARNING: concept not found")
            print()
            continue

        concept_data = facts[concept_name]

        units = concept_data.get("units", {})

        if "USD" not in units:
            print("WARNING: USD unit not found")
            print()
            continue

        observations = units["USD"]

        metric_records = []

        for row in observations:

            # ------------------------------------------------
            # Only annual 10-K filings
            # ------------------------------------------------

            if row.get("form") != "10-K":
                continue

            # ------------------------------------------------
            # Required fields
            # ------------------------------------------------

            end_date = row.get("end")

            value = row.get("val")

            filed_date = row.get("filed")

            if not end_date or value is None or not filed_date:
                continue

            # ------------------------------------------------
            # Fiscal year
            #
            # IMPORTANT:
            # Do NOT use row["fy"].
            #
            # We derive the year from the actual period_end.
            # ------------------------------------------------

            fiscal_year = int(end_date[:4])

            # ------------------------------------------------
            # Flow metrics
            # ------------------------------------------------

            if metric_name in FLOW_METRICS:

                start_date = row.get("start")

                if not start_date:
                    continue

                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)

                duration_days = (end - start).days

                # Microsoft fiscal year should be approximately
                # one year. Ignore quarterly / YTD / unusual periods.
                if not (300 <= duration_days <= 400):
                    continue

                period_type = "annual"

            # ------------------------------------------------
            # Balance-sheet metrics
            # ------------------------------------------------

            elif metric_name in BALANCE_METRICS:

                period_type = "point_in_time"

            else:
                continue

            metric_records.append(
                {
                    "company": COMPANY,
                    "fiscal_year": fiscal_year,
                    "metric": metric_name,
                    "value": value,
                    "unit": "USD",
                    "period_start": row.get("start"),
                    "period_end": end_date,
                    "period_type": period_type,
                    "form": row.get("form"),
                    "filed": filed_date,
                    "source": "SEC Company Facts",
                }
            )

        print(f"Valid observations: {len(metric_records)}")
        print()

        records.extend(metric_records)


    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(records)

    if df.empty:
        raise RuntimeError(
            "No financial records were extracted."
        )


    # --------------------------------------------------------
    # Convert dates
    # --------------------------------------------------------

    df["period_end"] = pd.to_datetime(
        df["period_end"]
    )

    df["period_start"] = pd.to_datetime(
        df["period_start"]
    )

    df["filed"] = pd.to_datetime(
        df["filed"]
    )


    # --------------------------------------------------------
    # Deduplicate
    #
    # SEC frequently reports the same historical value again
    # in later 10-K filings.
    #
    # We keep the latest filed observation for the same:
    #
    # company + fiscal_year + metric + period_end
    # --------------------------------------------------------

    print("=" * 80)
    print("DEDUPLICATING")
    print("=" * 80)

    before = len(df)

    df = (
        df
        .sort_values(
            [
                "company",
                "fiscal_year",
                "metric",
                "period_end",
                "filed",
            ]
        )
        .drop_duplicates(
            subset=[
                "company",
                "fiscal_year",
                "metric",
                "period_end",
            ],
            keep="last",
        )
    )

    after = len(df)

    print(f"Rows before deduplication: {before}")
    print(f"Rows after deduplication:  {after}")
    print(f"Duplicates removed:       {before - after}")
    print()


    # --------------------------------------------------------
    # Sort final dataset
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "company",
            "fiscal_year",
            "metric",
        ]
    ).reset_index(drop=True)


    # --------------------------------------------------------
    # Convert dates to ISO strings for CSV
    # --------------------------------------------------------

    df["period_start"] = (
        df["period_start"]
        .dt.strftime("%Y-%m-%d")
    )

    df["period_end"] = (
        df["period_end"]
        .dt.strftime("%Y-%m-%d")
    )

    df["filed"] = (
        df["filed"]
        .dt.strftime("%Y-%m-%d")
    )


    # --------------------------------------------------------
    # Reorder columns explicitly
    #
    # This guarantees the same schema as:
    # Apple / Microsoft / Amazon
    # --------------------------------------------------------

    df = df[EXPECTED_COLUMNS]


    # --------------------------------------------------------
    # Final schema check
    # --------------------------------------------------------

    if list(df.columns) != EXPECTED_COLUMNS:

        raise RuntimeError(
            "Final column structure is incorrect.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Found:    {list(df.columns)}"
        )


    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print("=" * 80)
    print("BUILD COMPLETED")
    print("=" * 80)

    print(f"Output: {OUTPUT_FILE}")
    print()

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    print()

    print("Final columns:")
    print(df.columns.tolist())
    print()

    print("Fiscal years:")
    print(
        df["fiscal_year"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    print()

    print("Metrics:")
    print(
        df["metric"]
        .value_counts()
        .sort_index()
    )
    print()

    print("Source:")
    print(
        df["source"]
        .value_counts()
    )
    print()

    print("Latest available values:")
    print()

    latest_year = df["fiscal_year"].max()

    latest = (
        df[df["fiscal_year"] == latest_year]
        .sort_values("metric")
    )

    print(
        latest[
            [
                "fiscal_year",
                "metric",
                "value",
                "period_end",
                "period_type",
                "source",
            ]
        ].to_string(index=False)
    )

    print()

    print("=" * 80)
    print("DONE")
    print("=" * 80)


if __name__ == "__main__":
    main()