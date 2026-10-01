import json
from pathlib import Path

import requests


BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts"

CIK = "0000789019"

COMPANY = "microsoft"

HEADERS = {
    "User-Agent": (
        "Sergey Koverzen "
        "finance-bi-real-company-analysis/1.0 "
        "sergeykoverzen@gmail.com"
    )
}


PROJECT_ROOT = Path(__file__).resolve().parent.parent

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
)


def main():

    url = f"{BASE_URL}/CIK{CIK}.json"

    print("=" * 80)
    print("DOWNLOADING MICROSOFT SEC COMPANY FACTS")
    print("=" * 80)

    print(f"CIK: {CIK}")
    print(f"URL: {url}")
    print()

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        OUTPUT_DIR
        / f"{COMPANY}_companyfacts.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
        )

    print(f"Saved: {output_file}")
    print(f"Company: {data['entityName']}")
    print()
    print("Download completed successfully.")


if __name__ == "__main__":
    main()