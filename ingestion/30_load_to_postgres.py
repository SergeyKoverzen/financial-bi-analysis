from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data" / "processed"

DB_USER = "postgres"
DB_PASSWORD = "Bere$ka238"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "finance_bi"

TABLE_NAME = "staging.financials"


FILES = [
    DATA_DIR / "apple_financials.csv",
    DATA_DIR / "microsoft_financials.csv",
    DATA_DIR / "amazon_financials.csv",
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(DATABASE_URL)


# ============================================================
# EXPECTED COLUMNS
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
# VALIDATE CSV
# ============================================================

def validate_dataframe(df: pd.DataFrame, file_path: Path) -> None:

    print(f"\nValidating: {file_path.name}")

    # Check columns
    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            f"Unexpected columns in {file_path.name}\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Found:    {list(df.columns)}"
        )

    # Check required fields
    required_columns = [
        "company",
        "fiscal_year",
        "metric",
        "value",
        "period_end",
    ]

    for column in required_columns:
        if df[column].isna().any():
            raise ValueError(
                f"Column '{column}' contains NULL values "
                f"in {file_path.name}"
            )

    print(f"  Rows: {len(df):,}")
    print("  Columns: OK")
    print("  Required fields: OK")


# ============================================================
# LOAD CSV FILES
# ============================================================

def load_csv_files() -> pd.DataFrame:

    dataframes = []

    for file_path in FILES:

        if not file_path.exists():
            raise FileNotFoundError(
                f"CSV file not found:\n{file_path}"
            )

        df = pd.read_csv(file_path)

        validate_dataframe(df, file_path)

        dataframes.append(df)

    combined = pd.concat(
        dataframes,
        ignore_index=True
    )

    return combined


# ============================================================
# PREPARE DATA TYPES
# ============================================================

def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # Integer
    df["fiscal_year"] = pd.to_numeric(
        df["fiscal_year"],
        errors="raise"
    ).astype(int)

    # Numeric financial value
    df["value"] = pd.to_numeric(
        df["value"],
        errors="raise"
    )

    # Dates
    for column in [
        "period_start",
        "period_end",
        "filed",
    ]:
        df[column] = pd.to_datetime(
            df[column],
            errors="raise"
        ).dt.date

    return df


# ============================================================
# DATABASE VALIDATION
# ============================================================

def validate_database():

    print("\nChecking PostgreSQL...")

    with engine.connect() as connection:

        result = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM staging.financials
                """
            )
        )

        count = result.scalar()

    print(f"Rows currently in PostgreSQL: {count:,}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("FINANCE BI — PostgreSQL Loader")
    print("=" * 60)

    # --------------------------------------------------------
    # 1. Load CSV files
    # --------------------------------------------------------

    print("\n[1/5] Loading CSV files...")

    df = load_csv_files()

    print(
        f"\nCombined rows: {len(df):,}"
    )

    # --------------------------------------------------------
    # 2. Prepare data
    # --------------------------------------------------------

    print("\n[2/5] Preparing data types...")

    df = prepare_dataframe(df)

    print("Data types: OK")

    # --------------------------------------------------------
    # 3. Show companies
    # --------------------------------------------------------

    print("\n[3/5] Companies detected:")

    company_counts = (
        df.groupby("company")
        .size()
        .sort_index()
    )

    for company, count in company_counts.items():
        print(f"  {company}: {count:,} rows")

    # --------------------------------------------------------
    # 4. Replace staging table data
    # --------------------------------------------------------

    print("\n[4/5] Loading PostgreSQL...")

    with engine.begin() as connection:

        # Clear existing staging data
        connection.execute(
            text(
                "TRUNCATE TABLE staging.financials"
            )
        )

        # Insert new data
        df.to_sql(
            name="financials",
            con=connection,
            schema="staging",
            if_exists="append",
            index=False,
            method="multi",
        )

    print("PostgreSQL load: OK")

    # --------------------------------------------------------
    # 5. Validate database
    # --------------------------------------------------------

    print("\n[5/5] Validating PostgreSQL...")

    with engine.connect() as connection:

        # Total rows
        result = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM staging.financials
                """
            )
        )

        total_rows = result.scalar()

        # Companies
        result = connection.execute(
            text(
                """
                SELECT
                    company,
                    COUNT(*) AS rows
                FROM staging.financials
                GROUP BY company
                ORDER BY company
                """
            )
        )

        company_rows = result.fetchall()

        # Years
        result = connection.execute(
            text(
                """
                SELECT
                    MIN(fiscal_year),
                    MAX(fiscal_year)
                FROM staging.financials
                """
            )
        )

        min_year, max_year = result.fetchone()

    print(f"\nTotal rows in PostgreSQL: {total_rows:,}")

    print("\nRows by company:")

    for company, count in company_rows:
        print(f"  {company}: {count:,}")

    print(
        f"\nFiscal years: {min_year} — {max_year}"
    )

    # --------------------------------------------------------
    # Final check
    # --------------------------------------------------------

    if total_rows != len(df):

        raise RuntimeError(
            "Row count mismatch!\n"
            f"CSV rows:        {len(df):,}\n"
            f"PostgreSQL rows: {total_rows:,}"
        )

    print("\n" + "=" * 60)
    print("SUCCESS — PostgreSQL staging load completed")
    print("=" * 60)


if __name__ == "__main__":
    main()