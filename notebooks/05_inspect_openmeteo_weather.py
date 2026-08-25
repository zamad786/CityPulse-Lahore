import json
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

WEATHER_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_hourly.csv"
)

METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_metadata.json"
)


WEATHER_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — OPEN-METEO WEATHER INSPECTION"
    )

    # ---------------------------------------------------------
    # File checks
    # ---------------------------------------------------------

    if not WEATHER_FILE.exists():
        raise FileNotFoundError(
            f"Weather CSV not found:\n{WEATHER_FILE}"
        )

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            f"Weather metadata not found:\n{METADATA_FILE}"
        )

    df = pd.read_csv(WEATHER_FILE)

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        metadata = json.load(file)

    # ---------------------------------------------------------
    # 1. Dataset structure
    # ---------------------------------------------------------

    print_section("1. DATASET SHAPE")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print_section("2. COLUMN NAMES")

    for column in df.columns:
        print(f"- {column}")

    print_section("3. DATA TYPES")

    print(df.dtypes.to_string())

    # ---------------------------------------------------------
    # 2. Missing values
    # ---------------------------------------------------------

    print_section("4. MISSING VALUES")

    missing_table = pd.DataFrame(
        {
            "missing_count": df.isna().sum(),
            "missing_percent": (
                df.isna().mean() * 100
            ).round(2),
        }
    )

    print(missing_table.to_string())

    # ---------------------------------------------------------
    # 3. Duplicate checks
    # ---------------------------------------------------------

    print_section("5. EXACT DUPLICATE ROWS")

    duplicate_rows = df.duplicated().sum()

    print(
        f"Exact duplicate rows: "
        f"{duplicate_rows:,}"
    )

    # ---------------------------------------------------------
    # 4. Timestamp parsing
    # ---------------------------------------------------------

    print_section("6. TIMESTAMP VALIDATION")

    df["timestamp_parsed"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = (
        df["timestamp_parsed"]
        .isna()
        .sum()
    )

    print(
        f"Invalid/unparseable timestamps: "
        f"{invalid_timestamps:,}"
    )

    valid_df = df.dropna(
        subset=["timestamp_parsed"]
    ).copy()

    print(
        "Earliest UTC timestamp:",
        valid_df["timestamp_parsed"].min(),
    )

    print(
        "Latest UTC timestamp:",
        valid_df["timestamp_parsed"].max(),
    )

    # ---------------------------------------------------------
    # 5. Duplicate timestamps
    # ---------------------------------------------------------

    print_section("7. DUPLICATE TIMESTAMPS")

    duplicated_mask = (
        valid_df["timestamp_parsed"]
        .duplicated(keep=False)
    )

    duplicate_timestamp_rows = (
        duplicated_mask.sum()
    )

    duplicate_timestamp_values = (
        valid_df.loc[
            duplicated_mask,
            "timestamp_parsed",
        ]
        .nunique()
    )

    print(
        "Rows involved in duplicate timestamps:",
        f"{duplicate_timestamp_rows:,}",
    )

    print(
        "Unique timestamps duplicated:",
        f"{duplicate_timestamp_values:,}",
    )

    if duplicate_timestamp_rows > 0:
        print("\nExample duplicate timestamps:")

        print(
            valid_df.loc[
                duplicated_mask
            ]
            .sort_values(
                "timestamp_parsed"
            )
            .head(20)
            .to_string(index=False)
        )

    # ---------------------------------------------------------
    # 6. Timestamp frequency
    # ---------------------------------------------------------

    print_section("8. TIMESTAMP FREQUENCY")

    unique_times = (
        valid_df["timestamp_parsed"]
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    time_differences = (
        unique_times.diff()
    )

    interval_counts = (
        time_differences
        .value_counts()
        .sort_index()
    )

    print(
        "Timestamp interval counts:"
    )

    print(
        interval_counts
        .head(20)
        .to_string()
    )

    one_hour = pd.Timedelta(
        hours=1
    )

    one_hour_count = (
        time_differences
        == one_hour
    ).sum()

    non_one_hour_count = (
        time_differences
        .dropna()
        != one_hour
    ).sum()

    print(
        f"\n1-hour intervals:     "
        f"{one_hour_count:,}"
    )

    print(
        f"Non-1-hour intervals: "
        f"{non_one_hour_count:,}"
    )

    # ---------------------------------------------------------
    # 7. Expected hourly coverage
    # ---------------------------------------------------------

    print_section("9. HOURLY COVERAGE / GAPS")

    if len(unique_times) > 0:
        expected_hours = pd.date_range(
            start=unique_times.min(),
            end=unique_times.max(),
            freq="h",
            tz="UTC",
        )

        observed_times = pd.DatetimeIndex(
            unique_times
        )

        missing_hours = (
            expected_hours
            .difference(
                observed_times
            )
        )

        print(
            f"Expected hourly timestamps: "
            f"{len(expected_hours):,}"
        )

        print(
            f"Observed unique timestamps: "
            f"{len(observed_times):,}"
        )

        print(
            f"Missing hourly timestamps:  "
            f"{len(missing_hours):,}"
        )

        if len(expected_hours) > 0:
            coverage_percent = (
                len(observed_times)
                / len(expected_hours)
                * 100
            )

            print(
                f"Timestamp coverage: "
                f"{coverage_percent:.2f}%"
            )

        if len(missing_hours) > 0:
            print(
                "\nFirst 20 missing timestamps:"
            )

            for timestamp in missing_hours[:20]:
                print(timestamp)

    # ---------------------------------------------------------
    # 8. Numeric conversion
    # ---------------------------------------------------------

    print_section("10. WEATHER VARIABLE STATISTICS")

    for column in WEATHER_COLUMNS:
        if column not in df.columns:
            print(
                f"\nWARNING: Missing expected column: "
                f"{column}"
            )
            continue

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        print(f"\n--- {column} ---")

        print(
            df[column]
            .describe(
                percentiles=[
                    0.01,
                    0.05,
                    0.25,
                    0.50,
                    0.75,
                    0.95,
                    0.99,
                ]
            )
            .to_string()
        )

    # ---------------------------------------------------------
    # 9. Simple validity checks
    #
    # These do NOT remove anything.
    # ---------------------------------------------------------

    print_section("11. BASIC WEATHER VALIDITY CHECKS")

    print(
        "Missing/non-numeric temperature:",
        f"{df['temperature_2m'].isna().sum():,}",
    )

    print(
        "Missing/non-numeric humidity:",
        f"{df['relative_humidity_2m'].isna().sum():,}",
    )

    print(
        "Missing/non-numeric precipitation:",
        f"{df['precipitation'].isna().sum():,}",
    )

    print(
        "Missing/non-numeric wind speed:",
        f"{df['wind_speed_10m'].isna().sum():,}",
    )

    print(
        "Missing/non-numeric wind direction:",
        f"{df['wind_direction_10m'].isna().sum():,}",
    )

    print(
        "Missing/non-numeric surface pressure:",
        f"{df['surface_pressure'].isna().sum():,}",
    )

    print()

    print(
        "Humidity < 0:",
        f"{(df['relative_humidity_2m'] < 0).sum():,}",
    )

    print(
        "Humidity > 100:",
        f"{(df['relative_humidity_2m'] > 100).sum():,}",
    )

    print(
        "Negative precipitation:",
        f"{(df['precipitation'] < 0).sum():,}",
    )

    print(
        "Negative wind speed:",
        f"{(df['wind_speed_10m'] < 0).sum():,}",
    )

    invalid_direction = (
        (df["wind_direction_10m"] < 0)
        | (df["wind_direction_10m"] > 360)
    )

    print(
        "Wind direction outside 0–360:",
        f"{invalid_direction.sum():,}",
    )

    # ---------------------------------------------------------
    # 10. Requested location consistency
    # ---------------------------------------------------------

    print_section("12. REQUESTED LOCATION VALUES")

    print("Requested latitude values:")

    print(
        df["requested_latitude"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print(
        "\nRequested longitude values:"
    )

    print(
        df["requested_longitude"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print(
        "\nLocation name values:"
    )

    print(
        df["location_name"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    # ---------------------------------------------------------
    # 11. Open-Meteo metadata
    # ---------------------------------------------------------

    print_section("13. OPEN-METEO METADATA")

    print(
        "Source:",
        metadata.get("source"),
    )

    print(
        "Requested coordinates:",
        metadata.get(
            "requested_coordinates"
        ),
    )

    print(
        "Returned grid coordinates:",
        metadata.get(
            "returned_coordinates"
        ),
    )

    print(
        "Elevation:",
        metadata.get("elevation"),
    )

    print(
        "Timezone:",
        metadata.get("timezone"),
    )

    print(
        "Timezone abbreviation:",
        metadata.get(
            "timezone_abbreviation"
        ),
    )

    print(
        "UTC offset seconds:",
        metadata.get(
            "utc_offset_seconds"
        ),
    )

    print("\nHourly units:")

    hourly_units = metadata.get(
        "hourly_units",
        {}
    )

    for variable, unit in hourly_units.items():
        print(
            f"- {variable}: {unit}"
        )

    # ---------------------------------------------------------
    # 12. Monthly coverage
    # ---------------------------------------------------------

    print_section("14. RECORDS BY MONTH")

    valid_df["month"] = (
        valid_df["timestamp_parsed"]
        .dt.strftime("%Y-%m")
    )

    monthly_counts = (
        valid_df
        .groupby("month")
        .size()
    )

    print(
        monthly_counts.to_string()
    )

    # ---------------------------------------------------------
    # 13. First / last records
    # ---------------------------------------------------------

    preview_columns = [
        "timestamp_utc",
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "wind_direction_10m",
        "surface_pressure",
    ]

    print_section("15. FIRST 10 CHRONOLOGICAL RECORDS")

    print(
        valid_df
        .sort_values("timestamp_parsed")[
            preview_columns
        ]
        .head(10)
        .to_string(index=False)
    )

    print_section("16. LAST 10 CHRONOLOGICAL RECORDS")

    print(
        valid_df
        .sort_values("timestamp_parsed")[
            preview_columns
        ]
        .tail(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # Finish
    # ---------------------------------------------------------

    print_section("INSPECTION COMPLETE")

    print(
        "No weather values were cleaned, filled, "
        "interpolated, filtered, or modified."
    )


if __name__ == "__main__":
    main()