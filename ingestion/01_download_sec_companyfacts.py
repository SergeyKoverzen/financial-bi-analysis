import json
from pathlib import Path

import requests


# SEC Company Facts API
BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts"

# Apple Inc.
COMPANY = "apple"
CIK = "0000320193"

# SEC requires a descriptive User-Agent for automated requests.
HEADERS = {
    "User-Agent": "Sergey Koverzen finance-bi-real-company-analysis/1.0 sergeykoverzen@gmail.com"
}


def download_company_facts(company: str, cik: str) -> None:
    """
    Download SEC Company Facts JSON for a company
    and save the original response to data/raw/.
    """

    url = f"{BASE_URL}/CIK{cik}.json"

    print(f"Downloading data for {company}...")
    print(f"URL: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    output_dir = Path(__file__).resolve().parent.parent / "data" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{company}_companyfacts.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"Saved: {output_file}")
    print(f"Company: {data['entityName']}")
    print("Download completed successfully.")


if __name__ == "__main__":
    download_company_facts(COMPANY, CIK)