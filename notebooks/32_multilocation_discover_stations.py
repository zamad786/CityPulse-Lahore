import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPORTS_DIR = PROJECT_ROOT / "reports"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

REPORTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

PROCESSED_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# CONFIG
# =========================================================

OPENAQ_BASE_URL = "https://api.openaq.org/v3"

# Central Lahore
LAHORE_LAT = 31.5204
LAHORE_LON = 74.3587

# OpenAQ parameter ID 2 = PM2.5
PM25_PARAMETER_ID = 2

# Maximum supported OpenAQ point/radius search
SEARCH_RADIUS_METERS = 25_000

# Fast validation window.
# We only inspect the last 30 days at this stage.
VALIDATION_DAYS = 30

# A station needs at least this much recent hourly coverage
# to be considered immediately useful.
MIN_RECENT_COVERAGE_PCT = 65.0

# Avoid hammering the API.
REQUEST_PAUSE_SECONDS = 0.15


# =========================================================
# API KEY
# =========================================================

def read_key_from_env_file() -> str | None:
    possible_files = [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / "backend" / ".env",
    ]

    for path in possible_files:
        if not path.exists():
            continue

        for line in path.read_text(
            encoding="utf-8"
        ).splitlines():
            line = line.strip()

            if (
                not line
                or line.startswith("#")
                or "=" not in line
            ):
                continue

            key, value = line.split(
                "=",
                1,
            )

            if key.strip() == "OPENAQ_API_KEY":
                return value.strip().strip(
                    "\"'"
                )

    return None


API_KEY = (
    os.getenv("OPENAQ_API_KEY")
    or read_key_from_env_file()
)


if not API_KEY:
    print(
        "\nERROR: OPENAQ_API_KEY was not found.\n"
    )

    print(
        "In PowerShell, set it for this terminal with:\n"
    )

    print(
        '$env:OPENAQ_API_KEY="YOUR_OPENAQ_API_KEY"'
    )

    print(
        "\nDo NOT send your API key to ChatGPT."
    )

    sys.exit(1)


HEADERS = {
    "X-API-Key": API_KEY,
}


# =========================================================
# HTTP HELPERS
# =========================================================

def get_json(
    endpoint: str,
    params: dict | None = None,
) -> dict:
    url = (
        f"{OPENAQ_BASE_URL}"
        f"{endpoint}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        params=params,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenAQ HTTP {response.status_code} "
            f"for {response.url}\n"
            f"{response.text[:500]}"
        )

    time.sleep(
        REQUEST_PAUSE_SECONDS
    )

    return response.json()


def parse_datetime(
    value,
) -> pd.Timestamp | None:
    if value is None:
        return None

    if isinstance(
        value,
        dict,
    ):
        value = (
            value.get("utc")
            or value.get("local")
        )

    if not value:
        return None

    ts = pd.to_datetime(
        value,
        utc=True,
        errors="coerce",
    )

    if pd.isna(ts):
        return None

    return ts


def get_nested(
    obj: dict,
    *keys,
):
    current = obj

    for key in keys:
        if not isinstance(
            current,
            dict,
        ):
            return None

        current = current.get(
            key
        )

    return current


# =========================================================
# DISCOVER LOCATIONS
# =========================================================

print(
    "\n=== CITYPULSE MULTI-LOCATION DISCOVERY ===\n"
)

print(
    "Searching OpenAQ for Lahore PM2.5 stations..."
)


locations_payload = get_json(
    "/locations",
    params={
        "coordinates":
            f"{LAHORE_LAT},{LAHORE_LON}",
        "radius":
            SEARCH_RADIUS_METERS,
        "parameters_id":
            PM25_PARAMETER_ID,
        "limit":
            1000,
        "page":
            1,
    },
)

locations = locations_payload.get(
    "results",
    [],
)


print(
    f"OpenAQ locations found: {len(locations)}"
)


if not locations:
    raise SystemExit(
        "No PM2.5 locations were returned."
    )


# =========================================================
# SENSOR + COVERAGE VALIDATION
# =========================================================

now_utc = datetime.now(
    timezone.utc
)

window_start = (
    now_utc
    - timedelta(
        days=VALIDATION_DAYS
    )
)

expected_recent_hours = (
    VALIDATION_DAYS * 24
)


station_rows: list[dict] = []


for index, location in enumerate(
    locations,
    start=1,
):
    location_id = location.get(
        "id"
    )

    location_name = (
        location.get("name")
        or f"Location {location_id}"
    )

    print(
        f"\n[{index}/{len(locations)}] "
        f"{location_name} "
        f"(ID {location_id})"
    )

    if not location_id:
        print(
            "  SKIP: missing location ID"
        )
        continue

    if location.get(
        "isMobile",
        False,
    ):
        print(
            "  SKIP: mobile location"
        )
        continue

    coordinates = (
        location.get("coordinates")
        or {}
    )

    latitude = coordinates.get(
        "latitude"
    )

    longitude = coordinates.get(
        "longitude"
    )


    try:
        sensors_payload = get_json(
            f"/locations/{location_id}/sensors",
            params={
                "limit": 1000,
                "page": 1,
            },
        )
    except Exception as exc:
        print(
            f"  SENSOR ERROR: {exc}"
        )
        continue


    sensors = sensors_payload.get(
        "results",
        [],
    )


    pm25_sensors = []

    for sensor in sensors:
        parameter = (
            sensor.get("parameter")
            or {}
        )

        parameter_id = parameter.get(
            "id"
        )

        parameter_name = str(
            parameter.get(
                "name",
                ""
            )
        ).lower()

        display_name = str(
            parameter.get(
                "displayName",
                ""
            )
        ).lower()

        sensor_name = str(
            sensor.get(
                "name",
                ""
            )
        ).lower()

        is_pm25 = (
            parameter_id
            == PM25_PARAMETER_ID
            or parameter_name
            == "pm25"
            or "pm2.5"
            in display_name
            or "pm25"
            in sensor_name
        )

        if is_pm25:
            pm25_sensors.append(
                sensor
            )


    if not pm25_sensors:
        print(
            "  SKIP: no PM2.5 sensor"
        )
        continue


    for sensor in pm25_sensors:
        sensor_id = sensor.get(
            "id"
        )

        if not sensor_id:
            continue

        first_ts = parse_datetime(
            sensor.get(
                "datetimeFirst"
            )
        )

        last_ts = parse_datetime(
            sensor.get(
                "datetimeLast"
            )
        )


        history_days = None

        if (
            first_ts is not None
            and last_ts is not None
        ):
            history_days = (
                last_ts - first_ts
            ).total_seconds() / 86400


        print(
            f"  PM2.5 sensor: {sensor_id}"
        )


        # ---------------------------------------------
        # Fetch recent hourly values
        # ---------------------------------------------

        recent_records = []

        try:
            page = 1

            while True:
                hours_payload = get_json(
                    f"/sensors/{sensor_id}/hours",
                    params={
                        "datetime_from":
                            window_start.isoformat(),
                        "datetime_to":
                            now_utc.isoformat(),
                        "limit":
                            1000,
                        "page":
                            page,
                    },
                )

                page_results = (
                    hours_payload.get(
                        "results",
                        [],
                    )
                )

                recent_records.extend(
                    page_results
                )

                meta = hours_payload.get(
                    "meta",
                    {},
                )

                found = meta.get(
                    "found"
                )

                if (
                    not page_results
                    or len(
                        recent_records
                    )
                    >= (
                        found
                        if isinstance(
                            found,
                            int,
                        )
                        else len(
                            recent_records
                        )
                    )
                    or len(
                        page_results
                    )
                    < 1000
                ):
                    break

                page += 1

        except Exception as exc:
            print(
                f"  HOURS ERROR: {exc}"
            )

            recent_records = []


        # ---------------------------------------------
        # Validate recent hourly records
        # ---------------------------------------------

        timestamps = []
        values = []

        for record in recent_records:
            value = record.get(
                "value"
            )

            timestamp_value = (
                get_nested(
                    record,
                    "period",
                    "datetimeFrom",
                    "utc",
                )
                or get_nested(
                    record,
                    "datetimeFrom",
                    "utc",
                )
                or record.get(
                    "datetime"
                )
            )

            timestamp = parse_datetime(
                timestamp_value
            )

            if timestamp is not None:
                timestamps.append(
                    timestamp
                )

            try:
                numeric_value = float(
                    value
                )
            except (
                TypeError,
                ValueError,
            ):
                numeric_value = None

            if numeric_value is not None:
                values.append(
                    numeric_value
                )


        unique_hours = len(
            set(timestamps)
        )

        recent_coverage_pct = (
            unique_hours
            / expected_recent_hours
            * 100
        )

        negative_count = sum(
            value < 0
            for value in values
        )

        recent_latest = (
            max(timestamps)
            if timestamps
            else last_ts
        )


        hours_since_latest = None

        if recent_latest is not None:
            hours_since_latest = max(
                0.0,
                (
                    pd.Timestamp(
                        now_utc
                    )
                    - recent_latest
                ).total_seconds()
                / 3600,
            )


        is_recent = (
            hours_since_latest
            is not None
            and hours_since_latest <= 72
        )

        sufficient_history = (
            history_days
            is not None
            and history_days >= 60
        )

        sufficient_coverage = (
            recent_coverage_pct
            >= MIN_RECENT_COVERAGE_PCT
        )

        valid_values = (
            len(values) > 0
            and negative_count == 0
        )


        # ---------------------------------------------
        # Score
        # ---------------------------------------------

        score = 0

        if is_recent:
            score += 3

        if sufficient_history:
            score += 2

        if history_days is not None:
            if history_days >= 180:
                score += 1

            if history_days >= 365:
                score += 1

        if sufficient_coverage:
            score += 3

        if recent_coverage_pct >= 85:
            score += 1

        if valid_values:
            score += 1


        usable = all(
            [
                is_recent,
                sufficient_history,
                sufficient_coverage,
                valid_values,
            ]
        )


        provider = (
            location.get("provider")
            or {}
        )

        owner = (
            location.get("owner")
            or {}
        )


        row = {
            "location_id":
                location_id,

            "location_name":
                location_name,

            "sensor_id":
                sensor_id,

            "latitude":
                latitude,

            "longitude":
                longitude,

            "provider":
                provider.get(
                    "name"
                ),

            "owner":
                owner.get(
                    "name"
                ),

            "is_reference_monitor":
                location.get(
                    "isMonitor"
                ),

            "is_mobile":
                location.get(
                    "isMobile"
                ),

            "sensor_datetime_first_utc":
                (
                    first_ts.isoformat()
                    if first_ts
                    is not None
                    else None
                ),

            "sensor_datetime_last_utc":
                (
                    last_ts.isoformat()
                    if last_ts
                    is not None
                    else None
                ),

            "history_days":
                (
                    round(
                        history_days,
                        1,
                    )
                    if history_days
                    is not None
                    else None
                ),

            "recent_window_days":
                VALIDATION_DAYS,

            "recent_unique_hours":
                unique_hours,

            "recent_expected_hours":
                expected_recent_hours,

            "recent_coverage_pct":
                round(
                    recent_coverage_pct,
                    2,
                ),

            "hours_since_latest":
                (
                    round(
                        hours_since_latest,
                        1,
                    )
                    if hours_since_latest
                    is not None
                    else None
                ),

            "recent_numeric_values":
                len(values),

            "negative_values":
                negative_count,

            "is_recent":
                is_recent,

            "sufficient_history":
                sufficient_history,

            "sufficient_recent_coverage":
                sufficient_coverage,

            "valid_values":
                valid_values,

            "usable_for_multilocation":
                usable,

            "score":
                score,
        }


        station_rows.append(
            row
        )


        print(
            "  "
            f"history={row['history_days']} days | "
            f"30d coverage={row['recent_coverage_pct']}% | "
            f"latest={row['hours_since_latest']}h ago | "
            f"usable={usable} | "
            f"score={score}"
        )


# =========================================================
# OUTPUT
# =========================================================

if not station_rows:
    raise SystemExit(
        "No PM2.5 station records could be validated."
    )


df = pd.DataFrame(
    station_rows
)


df = df.sort_values(
    by=[
        "usable_for_multilocation",
        "score",
        "recent_coverage_pct",
        "history_days",
    ],
    ascending=[
        False,
        False,
        False,
        False,
    ],
).reset_index(
    drop=True
)


csv_path = (
    PROCESSED_DIR
    / "lahore_multilocation_station_candidates.csv"
)

json_path = (
    REPORTS_DIR
    / "multilocation_station_discovery.json"
)


df.to_csv(
    csv_path,
    index=False,
)


usable_df = df[
    df[
        "usable_for_multilocation"
    ]
].copy()


report = {
    "generated_at_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "search": {
        "center_latitude":
            LAHORE_LAT,

        "center_longitude":
            LAHORE_LON,

        "radius_meters":
            SEARCH_RADIUS_METERS,

        "parameter":
            "PM2.5",

        "parameter_id":
            PM25_PARAMETER_ID,

        "recent_validation_days":
            VALIDATION_DAYS,

        "minimum_recent_coverage_pct":
            MIN_RECENT_COVERAGE_PCT,
    },

    "locations_returned":
        len(locations),

    "pm25_sensor_candidates":
        len(df),

    "usable_station_count":
        len(usable_df),

    "usable_stations":
        usable_df[
            [
                "location_id",
                "location_name",
                "sensor_id",
                "latitude",
                "longitude",
                "provider",
                "history_days",
                "recent_coverage_pct",
                "hours_since_latest",
                "score",
            ]
        ].to_dict(
            orient="records"
        ),
}


json_path.write_text(
    json.dumps(
        report,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)


print(
    "\n\n=== RANKED LAHORE PM2.5 STATIONS ===\n"
)


display_columns = [
    "location_id",
    "location_name",
    "sensor_id",
    "provider",
    "history_days",
    "recent_coverage_pct",
    "hours_since_latest",
    "usable_for_multilocation",
    "score",
]


print(
    df[
        display_columns
    ].to_string(
        index=False
    )
)


print(
    "\n----------------------------------------"
)

print(
    f"USABLE STATIONS: {len(usable_df)}"
)

print(
    f"CSV:    {csv_path}"
)

print(
    f"REPORT: {json_path}"
)

print(
    "----------------------------------------\n"
)


if len(
    usable_df
) < 2:
    print(
        "WARNING: Fewer than 2 usable stations passed "
        "the current criteria."
    )

    print(
        "Do not build multi-location prediction yet. "
        "Review station coverage first."
    )
else:
    print(
        "MULTI-LOCATION DISCOVERY: PASS"
    )

    print(
        "Next step: download full history for the "
        "top supported stations."
    )