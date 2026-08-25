import json
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AQ_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openaq_fcc_pm25_hourly.csv"
)

WEATHER_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_hourly.csv"
)

WEATHER_METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_metadata.json"
)

MERGED_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_aq_weather_merged.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day1_data_validation_summary.json"
)


# ---------------------------------------------------------
# Expected combined schema
# ---------------------------------------------------------

EXPECTED_COLUMNS = [
    "timestamp_utc",
    "station_name",
    "openaq_location_id",
    "openaq_sensor_id",
    "station_latitude",
    "station_longitude",
    "weather_grid_latitude",
    "weather_grid_longitude",
    "pm25_ug_m3",
    "has_flags",
    "coverage_expected_count",
    "coverage_observed_count",
    "coverage_percent_complete",
    "coverage_percent_coverage",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "wind_speed_m_s",
    "wind_direction_deg",
    "surface_pressure_hpa",
]


REQUIRED_MODEL_FOUNDATION_COLUMNS = [
    "timestamp_utc",
    "pm25_ug_m3",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "wind_speed_m_s",
    "wind_direction_deg",
    "surface_pressure_hpa",
]


WEATHER_COLUMNS = [
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "wind_speed_m_s",
    "wind_direction_deg",
    "surface_pressure_hpa",
]


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def record_check(checks, name, passed, details=""):
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "details": details,
        }
    )

    status = "PASS" if passed else "FAIL"

    print(f"[{status}] {name}")

    if details:
        print(f"       {details}")


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 1 FINAL DATA VALIDATION"
    )

    checks = []

    # -----------------------------------------------------
    # 1. Required files
    # -----------------------------------------------------

    print_section("1. REQUIRED FILE CHECK")

    required_files = [
        AQ_FILE,
        WEATHER_FILE,
        WEATHER_METADATA_FILE,
        MERGED_FILE,
    ]

    for path in required_files:
        exists = path.exists()

        record_check(
            checks,
            f"File exists: {path.name}",
            exists,
            str(path),
        )

    if not all(path.exists() for path in required_files):
        raise FileNotFoundError(
            "One or more required files are missing."
        )

    # -----------------------------------------------------
    # 2. Load data
    # -----------------------------------------------------

    print_section("2. LOAD DATASETS")

    aq = pd.read_csv(AQ_FILE)
    weather = pd.read_csv(WEATHER_FILE)
    merged = pd.read_csv(MERGED_FILE)

    with open(
        WEATHER_METADATA_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        weather_metadata = json.load(file)

    print(f"Raw AQ rows:       {len(aq):,}")
    print(f"Raw weather rows:  {len(weather):,}")
    print(f"Merged rows:       {len(merged):,}")

    # -----------------------------------------------------
    # 3. Schema validation
    # -----------------------------------------------------

    print_section("3. COMBINED SCHEMA")

    missing_columns = [
        column
        for column in EXPECTED_COLUMNS
        if column not in merged.columns
    ]

    unexpected_columns = [
        column
        for column in merged.columns
        if column not in EXPECTED_COLUMNS
    ]

    record_check(
        checks,
        "All expected columns are present",
        len(missing_columns) == 0,
        (
            "Missing: none"
            if not missing_columns
            else f"Missing: {missing_columns}"
        ),
    )

    record_check(
        checks,
        "No unexpected columns are present",
        len(unexpected_columns) == 0,
        (
            "Unexpected: none"
            if not unexpected_columns
            else f"Unexpected: {unexpected_columns}"
        ),
    )

    print(
        f"\nExpected columns: {len(EXPECTED_COLUMNS)}"
    )

    print(
        f"Actual columns:   {len(merged.columns)}"
    )

    # -----------------------------------------------------
    # 4. Timestamp parsing
    # -----------------------------------------------------

    print_section("4. TIMESTAMP VALIDATION")

    aq["timestamp"] = pd.to_datetime(
        aq["datetime_from_utc"],
        errors="coerce",
        utc=True,
    )

    weather["timestamp"] = pd.to_datetime(
        weather["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    merged["timestamp"] = pd.to_datetime(
        merged["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_merged_timestamps = (
        merged["timestamp"]
        .isna()
        .sum()
    )

    record_check(
        checks,
        "All merged timestamps parse successfully",
        invalid_merged_timestamps == 0,
        (
            f"Invalid timestamps: "
            f"{invalid_merged_timestamps:,}"
        ),
    )

    duplicate_timestamps = (
        merged["timestamp"]
        .duplicated()
        .sum()
    )

    record_check(
        checks,
        "Merged timestamps are unique",
        duplicate_timestamps == 0,
        (
            f"Duplicate timestamps: "
            f"{duplicate_timestamps:,}"
        ),
    )

    is_chronological = (
        merged["timestamp"]
        .is_monotonic_increasing
    )

    record_check(
        checks,
        "Merged dataset is chronologically sorted",
        is_chronological,
    )

    # -----------------------------------------------------
    # 5. Row-count fidelity
    # -----------------------------------------------------

    print_section("5. AIR-QUALITY ROW FIDELITY")

    same_row_count = (
        len(merged) == len(aq)
    )

    record_check(
        checks,
        "Merged row count equals observed AQ row count",
        same_row_count,
        (
            f"AQ={len(aq):,}, "
            f"merged={len(merged):,}"
        ),
    )

    aq_timestamp_set = set(
        aq["timestamp"].dropna()
    )

    merged_timestamp_set = set(
        merged["timestamp"].dropna()
    )

    exact_timestamp_set = (
        aq_timestamp_set
        == merged_timestamp_set
    )

    record_check(
        checks,
        "Merged timestamps exactly equal AQ timestamps",
        exact_timestamp_set,
        (
            f"AQ unique={len(aq_timestamp_set):,}, "
            f"merged unique={len(merged_timestamp_set):,}"
        ),
    )

    # -----------------------------------------------------
    # 6. PM2.5 source fidelity
    # -----------------------------------------------------

    print_section("6. PM2.5 SOURCE FIDELITY")

    aq_compare = aq[
        [
            "timestamp",
            "value",
        ]
    ].copy()

    aq_compare = aq_compare.rename(
        columns={
            "value": "raw_pm25"
        }
    )

    aq_compare["raw_pm25"] = pd.to_numeric(
        aq_compare["raw_pm25"],
        errors="coerce",
    )

    merged_compare = merged[
        [
            "timestamp",
            "pm25_ug_m3",
        ]
    ].copy()

    pm25_check = merged_compare.merge(
        aq_compare,
        on="timestamp",
        how="left",
        validate="one_to_one",
    )

    pm25_difference = (
        pm25_check["pm25_ug_m3"]
        - pm25_check["raw_pm25"]
    ).abs()

    changed_pm25_rows = (
        pm25_difference > 1e-9
    ).sum()

    missing_raw_pm25_matches = (
        pm25_check["raw_pm25"]
        .isna()
        .sum()
    )

    record_check(
        checks,
        "Every merged PM2.5 value matches raw OpenAQ",
        (
            changed_pm25_rows == 0
            and missing_raw_pm25_matches == 0
        ),
        (
            f"Changed values={changed_pm25_rows:,}, "
            f"missing source matches="
            f"{missing_raw_pm25_matches:,}"
        ),
    )

    # -----------------------------------------------------
    # 7. Weather source fidelity
    # -----------------------------------------------------

    print_section("7. WEATHER SOURCE FIDELITY")

    weather_compare = weather[
        [
            "timestamp",
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
        ]
    ].copy()

    weather_compare = weather_compare.rename(
        columns={
            "temperature_2m": "raw_temperature_c",
            "relative_humidity_2m": (
                "raw_relative_humidity_pct"
            ),
            "precipitation": (
                "raw_precipitation_mm"
            ),
            "wind_speed_10m": (
                "raw_wind_speed_m_s"
            ),
            "wind_direction_10m": (
                "raw_wind_direction_deg"
            ),
            "surface_pressure": (
                "raw_surface_pressure_hpa"
            ),
        }
    )

    weather_validation = merged[
        [
            "timestamp",
            "temperature_c",
            "relative_humidity_pct",
            "precipitation_mm",
            "wind_speed_m_s",
            "wind_direction_deg",
            "surface_pressure_hpa",
        ]
    ].merge(
        weather_compare,
        on="timestamp",
        how="left",
        validate="one_to_one",
    )

    comparison_pairs = [
        (
            "temperature_c",
            "raw_temperature_c",
        ),
        (
            "relative_humidity_pct",
            "raw_relative_humidity_pct",
        ),
        (
            "precipitation_mm",
            "raw_precipitation_mm",
        ),
        (
            "wind_speed_m_s",
            "raw_wind_speed_m_s",
        ),
        (
            "wind_direction_deg",
            "raw_wind_direction_deg",
        ),
        (
            "surface_pressure_hpa",
            "raw_surface_pressure_hpa",
        ),
    ]

    weather_source_ok = True

    for merged_column, raw_column in comparison_pairs:
        difference = (
            pd.to_numeric(
                weather_validation[merged_column],
                errors="coerce",
            )
            - pd.to_numeric(
                weather_validation[raw_column],
                errors="coerce",
            )
        ).abs()

        changed_rows = (
            difference > 1e-9
        ).sum()

        missing_matches = (
            weather_validation[raw_column]
            .isna()
            .sum()
        )

        passed = (
            changed_rows == 0
            and missing_matches == 0
        )

        if not passed:
            weather_source_ok = False

        record_check(
            checks,
            f"{merged_column} matches raw Open-Meteo",
            passed,
            (
                f"Changed={changed_rows:,}, "
                f"missing source matches="
                f"{missing_matches:,}"
            ),
        )

    # -----------------------------------------------------
    # 8. Missing required features
    # -----------------------------------------------------

    print_section("8. REQUIRED FEATURE COMPLETENESS")

    total_missing_required = 0

    for column in REQUIRED_MODEL_FOUNDATION_COLUMNS:
        missing_count = (
            merged[column]
            .isna()
            .sum()
        )

        total_missing_required += missing_count

        record_check(
            checks,
            f"No missing values: {column}",
            missing_count == 0,
            f"Missing={missing_count:,}",
        )

    # -----------------------------------------------------
    # 9. Basic numeric validity
    # -----------------------------------------------------

    print_section("9. BASIC NUMERIC VALIDITY")

    record_check(
        checks,
        "PM2.5 contains no negative values",
        (merged["pm25_ug_m3"] < 0).sum() == 0,
        (
            f"Negative values="
            f"{(merged['pm25_ug_m3'] < 0).sum():,}"
        ),
    )

    record_check(
        checks,
        "Humidity is within 0–100%",
        (
            (
                merged["relative_humidity_pct"] < 0
            ).sum()
            == 0
            and
            (
                merged["relative_humidity_pct"] > 100
            ).sum()
            == 0
        ),
    )

    record_check(
        checks,
        "Precipitation contains no negative values",
        (
            merged["precipitation_mm"] < 0
        ).sum()
        == 0,
    )

    record_check(
        checks,
        "Wind speed contains no negative values",
        (
            merged["wind_speed_m_s"] < 0
        ).sum()
        == 0,
    )

    record_check(
        checks,
        "Wind direction is within 0–360°",
        (
            (
                merged["wind_direction_deg"] < 0
            ).sum()
            == 0
            and
            (
                merged["wind_direction_deg"] > 360
            ).sum()
            == 0
        ),
    )

    # -----------------------------------------------------
    # 10. Temporal coverage / gaps
    # -----------------------------------------------------

    print_section("10. COMBINED TEMPORAL COVERAGE")

    start_timestamp = (
        merged["timestamp"].min()
    )

    end_timestamp = (
        merged["timestamp"].max()
    )

    expected_hours = pd.date_range(
        start=start_timestamp,
        end=end_timestamp,
        freq="h",
        tz="UTC",
    )

    observed_hours = pd.DatetimeIndex(
        merged["timestamp"]
        .drop_duplicates()
        .sort_values()
    )

    missing_hours = (
        expected_hours
        .difference(
            observed_hours
        )
    )

    coverage_percent = (
        len(observed_hours)
        / len(expected_hours)
        * 100
    )

    print(
        f"Start timestamp:          "
        f"{start_timestamp}"
    )

    print(
        f"End timestamp:            "
        f"{end_timestamp}"
    )

    print(
        f"Calendar hours in range:  "
        f"{len(expected_hours):,}"
    )

    print(
        f"Observed combined hours:  "
        f"{len(observed_hours):,}"
    )

    print(
        f"Missing AQ hours:         "
        f"{len(missing_hours):,}"
    )

    print(
        f"Timestamp coverage:       "
        f"{coverage_percent:.2f}%"
    )

    # Important:
    # gaps are acceptable because the combined dataset
    # intentionally contains only observed PM2.5 hours.
    record_check(
        checks,
        "No synthetic PM2.5 timestamps were introduced",
        len(observed_hours) == len(aq_timestamp_set),
        (
            f"Observed combined hours="
            f"{len(observed_hours):,}; "
            f"raw AQ timestamps="
            f"{len(aq_timestamp_set):,}"
        ),
    )

    # -----------------------------------------------------
    # 11. Metadata consistency
    # -----------------------------------------------------

    print_section("11. METADATA CONSISTENCY")

    returned_coordinates = (
        weather_metadata.get(
            "returned_coordinates",
            {}
        )
    )

    requested_coordinates = (
        weather_metadata.get(
            "requested_coordinates",
            {}
        )
    )

    expected_weather_lat = (
        returned_coordinates.get(
            "latitude"
        )
    )

    expected_weather_lon = (
        returned_coordinates.get(
            "longitude"
        )
    )

    expected_station_lat = (
        requested_coordinates.get(
            "latitude"
        )
    )

    expected_station_lon = (
        requested_coordinates.get(
            "longitude"
        )
    )

    station_lat_ok = (
        merged["station_latitude"]
        .eq(expected_station_lat)
        .all()
    )

    station_lon_ok = (
        merged["station_longitude"]
        .eq(expected_station_lon)
        .all()
    )

    grid_lat_ok = (
        merged["weather_grid_latitude"]
        .eq(expected_weather_lat)
        .all()
    )

    grid_lon_ok = (
        merged["weather_grid_longitude"]
        .eq(expected_weather_lon)
        .all()
    )

    record_check(
        checks,
        "Station latitude matches requested Open-Meteo location",
        station_lat_ok,
        str(expected_station_lat),
    )

    record_check(
        checks,
        "Station longitude matches requested Open-Meteo location",
        station_lon_ok,
        str(expected_station_lon),
    )

    record_check(
        checks,
        "Weather grid latitude matches metadata",
        grid_lat_ok,
        str(expected_weather_lat),
    )

    record_check(
        checks,
        "Weather grid longitude matches metadata",
        grid_lon_ok,
        str(expected_weather_lon),
    )

    # -----------------------------------------------------
    # 12. Dataset summary
    # -----------------------------------------------------

    print_section("12. FINAL DATASET SUMMARY")

    print(
        merged[
            [
                "pm25_ug_m3",
                "temperature_c",
                "relative_humidity_pct",
                "precipitation_mm",
                "wind_speed_m_s",
                "wind_direction_deg",
                "surface_pressure_hpa",
            ]
        ]
        .describe()
        .to_string()
    )

    # -----------------------------------------------------
    # 13. Overall result
    # -----------------------------------------------------

    print_section("13. FINAL VALIDATION RESULT")

    failed_checks = [
        check
        for check in checks
        if not check["passed"]
    ]

    overall_pass = (
        len(failed_checks) == 0
    )

    if overall_pass:
        print("DAY 1 DATA VALIDATION: PASS ✅")

        print(
            "\nThe combined Lahore PM2.5 + weather "
            "dataset passed all required validation checks."
        )
    else:
        print("DAY 1 DATA VALIDATION: FAIL ❌")

        print(
            f"\nFailed checks: "
            f"{len(failed_checks)}"
        )

        for check in failed_checks:
            print(
                f"- {check['name']}: "
                f"{check['details']}"
            )

    # -----------------------------------------------------
    # 14. Save validation report
    # -----------------------------------------------------

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "project": "CityPulse Lahore",
        "phase": "Day 1 — Data Foundation",
        "validation_status": (
            "PASS"
            if overall_pass
            else "FAIL"
        ),
        "source_files": {
            "air_quality": str(AQ_FILE),
            "weather": str(WEATHER_FILE),
            "weather_metadata": str(
                WEATHER_METADATA_FILE
            ),
        },
        "combined_file": str(
            MERGED_FILE
        ),
        "dataset": {
            "rows": int(len(merged)),
            "columns": int(
                len(merged.columns)
            ),
            "start_timestamp_utc": str(
                start_timestamp
            ),
            "end_timestamp_utc": str(
                end_timestamp
            ),
            "expected_calendar_hours": int(
                len(expected_hours)
            ),
            "observed_pm25_hours": int(
                len(observed_hours)
            ),
            "missing_pm25_hours": int(
                len(missing_hours)
            ),
            "timestamp_coverage_percent": round(
                coverage_percent,
                2,
            ),
        },
        "checks": checks,
    }

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\nValidation report saved to:")

    print(REPORT_FILE)

    print_section("VALIDATION SCRIPT COMPLETE")

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()