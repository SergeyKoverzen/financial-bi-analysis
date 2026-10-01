import json
from pathlib import Path

import requests


# =========================
# AMAZON SEC CONFIG
# =========================

CIK = "0001018724"
COMPANY_NAME = "AMAZON.COM, INC."

URL = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json"

# ВАЖНО:
# Используй здесь тот же реальный email,
# который уже сработал у тебя в Microsoft script.
USER_AGENT = "Sergey Koverzen sergeykoverzen@gmail.com"


# =========================
# PATHS
# =========================

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_FILE = RAW_DIR / "amazon_companyfacts.json"

RAW_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# DOWNLOAD
# =========================

print("=" * 60)
print("DOWNLOADING AMAZON SEC COMPANY FACTS")
print("=" * 60)

print(f"Company: {COMPANY_NAME}")
print(f"CIK: {CIK}")
print(f"URL: {URL}")
print()


headers = {
    "User-Agent": USER_AGENT,
    "Accept-Encoding": "gzip, deflate",
    "Host": "data.sec.gov",
}


try:
    response = requests.get(
        URL,
        headers=headers,
        timeout=60
    )

    print(f"HTTP status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

except requests.exceptions.RequestException as e:
    print()
    print("DOWNLOAD FAILED")
    print(f"Error: {e}")
    raise SystemExit(1)

except json.JSONDecodeError:
    print()
    print("ERROR: SEC returned invalid JSON.")
    raise SystemExit(1)


# =========================
# BASIC VALIDATION
# =========================

if "entityName" not in data:
    print()
    print("ERROR: 'entityName' not found in SEC response.")
    raise SystemExit(1)

if "facts" not in data:
    print()
    print("ERROR: 'facts' section not found in SEC response.")
    raise SystemExit(1)


# =========================
# SAVE
# =========================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        data,
        f,
        ensure_ascii=False,
        indent=2
    )


# =========================
# RESULT
# =========================

us_gaap = data["facts"].get("us-gaap", {})

print()
print("=" * 60)
print("DOWNLOAD COMPLETED SUCCESSFULLY")
print("=" * 60)

print(f"Company: {data.get('entityName')}")
print(f"CIK: {data.get('cik')}")
print(f"US-GAAP concepts: {len(us_gaap)}")
print(f"Saved: {OUTPUT_FILE}")
print()