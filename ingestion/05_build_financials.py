import csv
import json
from datetime import date
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "apple_companyfacts.json"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "apple_financials.csv"


# ============================================================
# COMPANY
# ============================================================

COMPANY = "Apple"


# ============================================================
# FINANCIAL CONCEPTS
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
# FINAL OUTPUT SCHEMA
# ============================================================

FIELDNAMES = [
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
# FISCAL YEAR
# ============================================================

def get_fiscal_year(row):
    """
    Derive fiscal year from the actual financial period end date.
    Do not use SEC row['fy'].
    """

    end_date = row.get("end")

    if not end_date:
        return None

    return int(end_date[:4])


# ============================================================
# CHECK ANNUAL FLOW PERIOD
# ============================================================

def is_annual_period(row):
    """
    Check whether a flow observation represents
    approximately one full financial year.
    """

    start_date = row.get("start")
    end_date = row.get("end")

    if not start_date or not end_date:
        return False

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    duration_days = (end - start).days

    # Apple fiscal years are approximately one year.
    return 300 <= duration_days <= 400


# ============================================================
# EXTRACT ONE METRIC
# ============================================================

def extract_metric(facts, metric_name, concept_name):
    """
    Extract valid annual observations for one metric.
    """

    if concept_name not in facts:
        print(f"WARNING: {concept_name} not found")
        return []

    concept = facts[concept_name]

    units = concept.get("units", {})

    if "USD" not in units:
        print(f"WARNING: {concept_name} has no USD unit")
        return []

    observations = units["USD"]

    results = []

    for row in observations:

        # ----------------------------------------------------
        # Only 10-K filings
        # ----------------------------------------------------

        form = row.get("form")

        if form != "10-K":
            continue

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        value = row.get("val")
        end_date = row.get("end")
        filed_date = row.get("filed")

        if value is None:
            continue

        if end_date is None:
            continue

        if filed_date is None:
            continue

        # ----------------------------------------------------
        # Flow metrics
        # ----------------------------------------------------

        if metric_name in FLOW_METRICS:

            if not is_annual_period(row):
                continue

            period_type = "annual"

            period_start = row.get("start")

            if not period_start:
                continue

        # ----------------------------------------------------
        # Balance-sheet metrics
        # ----------------------------------------------------

        elif metric_name in BALANCE_METRICS:

            period_type = "point_in_time"

            # Balance-sheet metrics are point-in-time values.
            period_start = None

        else:
            continue

        # ----------------------------------------------------
        # Fiscal year
        # ----------------------------------------------------

        fiscal_year = get_fiscal_year(row)

        if fiscal_year is None:
            continue

        # ----------------------------------------------------
        # Standardized record
        # ----------------------------------------------------

        results.append(
            {
                "company": COMPANY,
                "fiscal_year": fiscal_year,
                "metric": metric_name,
                "value": value,
                "unit": "USD",
                "period_start": period_start,
                "period_end": end_date,
                "period_type": period_type,
                "form": form,
                "filed": filed_date,
                "source": "SEC Company Facts",
            }
        )

    return results


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(rows):
    """
    Remove duplicate observations.

    Keep one observation per:

        company
        fiscal_year
        metric
        period_end

    If multiple filings contain the same observation,
    keep the latest filed version.
    """

    unique = {}

    for row in rows:

        key = (
            row["company"],
            row["fiscal_year"],
            row["metric"],
            row["period_end"],
        )

        if key not in unique:

            unique[key] = row

        else:

            existing = unique[key]

            if row["filed"] > existing["filed"]:
                unique[key] = row

    return list(unique.values())


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("BUILDING APPLE FINANCIALS")
    print("=" * 80)

    print(f"Source: {RAW_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()


    # --------------------------------------------------------
    # Load SEC Company Facts
    # --------------------------------------------------------

    with RAW_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    company_name = data["entityName"]

    print(f"Company: {company_name}")
    print()

    facts = data["facts"]["us-gaap"]

    all_rows = []


    # --------------------------------------------------------
    # Extract metrics
    # --------------------------------------------------------

    for metric_name, concept_name in CONCEPTS.items():

        print(
            f"Extracting: {metric_name:<25} "
            f"({concept_name})"
        )

        rows = extract_metric(
            facts,
            metric_name,
            concept_name,
        )

        print(
            f"  observations found: {len(rows)}"
        )

        all_rows.extend(rows)


    print()

    print(
        "Total observations before deduplication: "
        f"{len(all_rows)}"
    )


    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    all_rows = remove_duplicates(all_rows)

    print(
        "Total observations after deduplication:  "
        f"{len(all_rows)}"
    )


    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    all_rows.sort(
        key=lambda row: (
            row["company"],
            row["fiscal_year"],
            row["metric"],
            row["period_end"],
        )
    )


    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


    # --------------------------------------------------------
    # Write standardized CSV
    # --------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()

        writer.writerows(all_rows)


    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print()
    print("=" * 80)
    print("FINAL SCHEMA CHECK")
    print("=" * 80)

    print()

    print("Expected columns:")

    for column in FIELDNAMES:
        print(f"  - {column}")

    print()

    print("Column count:")
    print(f"  {len(FIELDNAMES)}")


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 80)
    print("BUILD COMPLETED")
    print("=" * 80)

    print()

    print("Output file:")
    print(OUTPUT_FILE)

    print()

    print(f"Rows: {len(all_rows)}")
    print(f"Columns: {len(FIELDNAMES)}")

    print()

    print("Years found:")

    years = sorted(
        {
            row["fiscal_year"]
            for row in all_rows
        }
    )

    print(years)

    print()

    print("Metrics:")

    metrics = sorted(
        {
            row["metric"]
            for row in all_rows
        }
    )

    for metric in metrics:
        count = sum(
            1
            for row in all_rows
            if row["metric"] == metric
        )

        print(
            f"  - {metric}: {count}"
        )

    print()

    print("Source:")

    sources = sorted(
        {
            row["source"]
            for row in all_rows
        }
    )

    for source in sources:
        print(f"  - {source}")

    print()

    print("Done.")


if __name__ == "__main__":
    main()