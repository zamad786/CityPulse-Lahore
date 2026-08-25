import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------
# Selected Lahore OpenAQ location
# ---------------------------------------------------------

LOCATION_ID = 4757305
LOCATION_NAME = "Forman Christian College & Chartered University"

PM25_SENSOR_ID = 13341452

# Coverage reported by the OpenAQ location metadata.
# We will verify the ACTUAL measurements after downloading.
DATETIME_FROM = "2025-06-16T10:00:00Z"
DATETIME_TO = "2026-08-23T06:00:00Z"

API_BASE_URL = "https://api.openaq.org/v3"

PAGE_LIMIT = 1000

# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

PM25_OUTPUT_FILE = RAW_DATA_DIR / "openaq_fcc_pm25_hourly.csv"
METADATA_OUTPUT_FILE = RAW_DATA_DIR / "openaq_fcc_metadata.json"


def get_api_key():
    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        print("ERROR: OPENAQ_API_KEY is not set.")
        print()
        print("Set it again in PowerShell using:")
        print('$env:OPENAQ_API_KEY="YOUR_KEY"')
        sys.exit(1)

    return api_key


def request_json(session, url, params=None):
    """
    Send an OpenAQ request with basic retry handling.
    """

    max_attempts = 5

    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=60,
            )
        except requests.RequestException as exc:
            print(f"Request error: {exc}")

            if attempt == max_attempts:
                raise

            time.sleep(3)
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            wait_seconds = int(response.headers.get("Retry-After", 10))

            print(
                f"Rate limit reached. "
                f"Waiting {wait_seconds} seconds..."
            )

            time.sleep(wait_seconds)
            continue

        print(f"\nOpenAQ request failed.")
        print(f"HTTP status: {response.status_code}")
        print(response.text[:2000])

        sys.exit(1)

    print("ERROR: Maximum request attempts reached.")
    sys.exit(1)


def save_metadata(session):
    """
    Save the OpenAQ location and PM2.5 sensor metadata.
    """

    print("\nFetching location metadata...")

    location_url = f"{API_BASE_URL}/locations/{LOCATION_ID}"
    location_payload = request_json(session, location_url)

    print("Fetching PM2.5 sensor metadata...")

    sensor_url = f"{API_BASE_URL}/sensors/{PM25_SENSOR_ID}"
    sensor_payload = request_json(session, sensor_url)

    metadata = {
        "selection": {
            "location_id": LOCATION_ID,
            "location_name": LOCATION_NAME,
            "pm25_sensor_id": PM25_SENSOR_ID,
            "requested_datetime_from": DATETIME_FROM,
            "requested_datetime_to": DATETIME_TO,
        },
        "location_api_response": location_payload,
        "sensor_api_response": sensor_payload,
    }

    with open(
        METADATA_OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(f"Metadata saved to:")
    print(METADATA_OUTPUT_FILE)


def flatten_measurement(record, page_number, row_number):
    """
    Flatten one OpenAQ hourly measurement into a CSV-friendly row.

    No cleaning, interpolation, or missing-value handling is performed here.
    """

    parameter = record.get("parameter") or {}
    period = record.get("period") or {}

    datetime_from = period.get("datetimeFrom") or {}
    datetime_to = period.get("datetimeTo") or {}

    coordinates = record.get("coordinates") or {}
    coverage = record.get("coverage") or {}
    flag_info = record.get("flagInfo") or {}

    return {
        "api_page": page_number,
        "api_row": row_number,
        "location_id": LOCATION_ID,
        "location_name": LOCATION_NAME,
        "sensor_id": PM25_SENSOR_ID,

        "parameter": parameter.get("name"),
        "display_name": parameter.get("displayName"),
        "units": parameter.get("units"),

        "value": record.get("value"),

        "datetime_from_utc": datetime_from.get("utc"),
        "datetime_to_utc": datetime_to.get("utc"),

        "datetime_from_local": datetime_from.get("local"),
        "datetime_to_local": datetime_to.get("local"),

        "latitude": coordinates.get("latitude"),
        "longitude": coordinates.get("longitude"),

        "has_flags": flag_info.get("hasFlags"),

        "coverage_expected_count": coverage.get("expectedCount"),
        "coverage_observed_count": coverage.get("observedCount"),
        "coverage_percent_complete": coverage.get("percentComplete"),
        "coverage_percent_coverage": coverage.get("percentCoverage"),
    }


def download_pm25(session):
    """
    Download all available hourly PM2.5 records in the selected period.
    """

    url = f"{API_BASE_URL}/sensors/{PM25_SENSOR_ID}/hours"

    all_rows = []
    page = 1

    print("\nDownloading hourly PM2.5 measurements...")
    print(f"Location: {LOCATION_NAME}")
    print(f"Sensor ID: {PM25_SENSOR_ID}")
    print(f"Requested start: {DATETIME_FROM}")
    print(f"Requested end:   {DATETIME_TO}")
    print()

    while True:
        params = {
            "datetime_from": DATETIME_FROM,
            "datetime_to": DATETIME_TO,
            "limit": PAGE_LIMIT,
            "page": page,
        }

        payload = request_json(
            session,
            url,
            params=params,
        )

        results = payload.get("results", [])
        meta = payload.get("meta", {})

        found = meta.get("found")

        print(
            f"Page {page}: "
            f"{len(results)} records returned "
            f"(API found: {found})"
        )

        if not results:
            break

        for row_number, record in enumerate(results, start=1):
            all_rows.append(
                flatten_measurement(
                    record,
                    page,
                    row_number,
                )
            )

        # Stop if this was the final partial page.
        if len(results) < PAGE_LIMIT:
            break

        # Stop if OpenAQ gives us a numeric total and
        # we have already downloaded all of it.
        try:
            if found is not None and len(all_rows) >= int(found):
                break
        except (TypeError, ValueError):
            pass

        page += 1

        # Small pause to be courteous to the API.
        time.sleep(0.25)

    if not all_rows:
        print("\nERROR: No PM2.5 hourly measurements were returned.")
        sys.exit(1)

    dataframe = pd.DataFrame(all_rows)

    dataframe.to_csv(
        PM25_OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print("\nDownload complete.")
    print(f"Records saved: {len(dataframe):,}")
    print(f"CSV saved to:")
    print(PM25_OUTPUT_FILE)

    return dataframe


def main():
    print("=" * 70)
    print("CITYPULSE LAHORE — OPENAQ PM2.5 DOWNLOAD")
    print("=" * 70)

    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    api_key = get_api_key()

    session = requests.Session()

    session.headers.update(
        {
            "X-API-Key": api_key,
            "Accept": "application/json",
        }
    )

    save_metadata(session)

    dataframe = download_pm25(session)

    print("\n" + "=" * 70)
    print("STEP 5 DOWNLOAD FINISHED")
    print("=" * 70)

    print("\nColumns saved:")
    for column in dataframe.columns:
        print(f"- {column}")

    print(
        "\nIMPORTANT: No cleaning, interpolation, "
        "or missing-value handling has been performed."
    )
    print(
        "We will inspect the actual measurements "
        "before making any conclusions about frequency or quality."
    )


if __name__ == "__main__":
    main()