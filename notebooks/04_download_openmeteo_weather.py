import json
import sys
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------
# Same location used for the OpenAQ PM2.5 station
# ---------------------------------------------------------

LOCATION_NAME = "Forman Christian College & Chartered University"

LATITUDE = 31.521146
LONGITUDE = 74.333954

# Air-quality data begins on 2025-06-16 and currently
# extends into 2026-08-23.
#
# Open-Meteo's historical endpoint accepts dates, rather
# than individual start/end hours, so we request the full
# boundary days. Exact timestamp overlap will be checked
# during the merge stage.
START_DATE = "2025-06-16"
END_DATE = "2026-08-23"


# ---------------------------------------------------------
# Open-Meteo API
# ---------------------------------------------------------

API_URL = "https://archive-api.open-meteo.com/v1/archive"

HOURLY_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

WEATHER_OUTPUT_FILE = (
    RAW_DATA_DIR
    / "openmeteo_fcc_weather_hourly.csv"
)

METADATA_OUTPUT_FILE = (
    RAW_DATA_DIR
    / "openmeteo_fcc_weather_metadata.json"
)


def main():
    print("=" * 72)
    print("CITYPULSE LAHORE — OPEN-METEO WEATHER DOWNLOAD")
    print("=" * 72)

    RAW_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": ",".join(HOURLY_VARIABLES),

        # Critical: keep weather timestamps aligned with
        # our OpenAQ UTC timestamps.
        "timezone": "UTC",

        # Use metres/second rather than km/h.
        "wind_speed_unit": "ms",
    }

    print("\nRequesting historical weather...")
    print(f"Location: {LOCATION_NAME}")
    print(
        f"Requested coordinates: "
        f"{LATITUDE}, {LONGITUDE}"
    )
    print(f"Start date: {START_DATE}")
    print(f"End date:   {END_DATE}")

    print("\nHourly variables:")

    for variable in HOURLY_VARIABLES:
        print(f"- {variable}")

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=60,
        )

    except requests.RequestException as exc:
        print("\nREQUEST FAILED")
        print(type(exc).__name__, exc)
        sys.exit(1)

    print(
        f"\nHTTP status: "
        f"{response.status_code}"
    )

    if response.status_code != 200:
        print("\nOpen-Meteo returned an error:")
        print(response.text[:3000])
        sys.exit(1)

    payload = response.json()

    # -----------------------------------------------------
    # Validate the response structure
    # -----------------------------------------------------

    if "hourly" not in payload:
        print(
            "\nERROR: Response does not contain "
            "an 'hourly' section."
        )

        print(
            json.dumps(
                payload,
                indent=2,
            )[:3000]
        )

        sys.exit(1)

    hourly = payload["hourly"]

    if "time" not in hourly:
        print(
            "\nERROR: Hourly response contains "
            "no time field."
        )
        sys.exit(1)

    # -----------------------------------------------------
    # Convert response directly to a dataframe
    # -----------------------------------------------------

    df = pd.DataFrame(hourly)

    # Rename "time" clearly before saving.
    df = df.rename(
        columns={
            "time": "timestamp_utc"
        }
    )

    # Record requested station coordinates separately.
    #
    # Open-Meteo returns a model grid-cell coordinate,
    # which may differ slightly from the sensor position.
    df.insert(
        0,
        "requested_latitude",
        LATITUDE,
    )

    df.insert(
        1,
        "requested_longitude",
        LONGITUDE,
    )

    df.insert(
        2,
        "location_name",
        LOCATION_NAME,
    )

    # -----------------------------------------------------
    # Save raw weather data
    # -----------------------------------------------------

    df.to_csv(
        WEATHER_OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    # -----------------------------------------------------
    # Save API metadata separately
    # -----------------------------------------------------

    metadata = {
        "source": "Open-Meteo Historical Weather API",
        "api_url": API_URL,
        "location_name": LOCATION_NAME,

        "requested_coordinates": {
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
        },

        "returned_coordinates": {
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
        },

        "elevation": payload.get("elevation"),
        "timezone": payload.get("timezone"),
        "timezone_abbreviation": (
            payload.get("timezone_abbreviation")
        ),
        "utc_offset_seconds": (
            payload.get("utc_offset_seconds")
        ),

        "requested_start_date": START_DATE,
        "requested_end_date": END_DATE,

        "hourly_units": payload.get(
            "hourly_units",
            {},
        ),

        "variables": HOURLY_VARIABLES,
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

    # -----------------------------------------------------
    # Basic download verification only
    # -----------------------------------------------------

    print("\n" + "=" * 72)
    print("WEATHER DOWNLOAD COMPLETE")
    print("=" * 72)

    print(
        f"\nRows saved: "
        f"{len(df):,}"
    )

    print(
        f"Columns saved: "
        f"{len(df.columns)}"
    )

    print("\nColumns:")

    for column in df.columns:
        print(f"- {column}")

    print(
        "\nFirst returned timestamp:",
        df["timestamp_utc"].iloc[0],
    )

    print(
        "Last returned timestamp:",
        df["timestamp_utc"].iloc[-1],
    )

    print("\nAPI returned grid location:")
    print(
        "Latitude:",
        payload.get("latitude"),
    )
    print(
        "Longitude:",
        payload.get("longitude"),
    )

    print(
        "Elevation:",
        payload.get("elevation"),
    )

    print(
        "Timezone:",
        payload.get("timezone"),
    )

    print("\nWeather CSV saved to:")
    print(WEATHER_OUTPUT_FILE)

    print("\nWeather metadata saved to:")
    print(METADATA_OUTPUT_FILE)

    print(
        "\nIMPORTANT: No cleaning, filling, "
        "or interpolation has been performed."
    )


if __name__ == "__main__":
    main()