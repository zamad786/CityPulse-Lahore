from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openaq_fcc_pm25_hourly.csv"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section("CITYPULSE LAHORE — AIR QUALITY DATA INSPECTION")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Could not find input file:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    # ---------------------------------------------------------
    # 1. Basic structure
    # ---------------------------------------------------------

    print_section("1. DATASET SHAPE")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print_section("2. COLUMN NAMES")

    for column in df.columns:
        print(f"- {column}")

    print_section("3. DATA TYPES")

    print(df.dtypes)

    # ---------------------------------------------------------
    # 2. Missing values
    # ---------------------------------------------------------

    print_section("4. MISSING VALUES")

    missing = pd.DataFrame(
        {
            "missing_count": df.isna().sum(),
            "missing_percent": (
                df.isna().mean() * 100
            ).round(2),
        }
    )

    print(missing.to_string())

    # ---------------------------------------------------------
    # 3. Duplicate checks
    # ---------------------------------------------------------

    print_section("5. DUPLICATE ROWS")

    duplicate_rows = df.duplicated().sum()

    print(f"Exact duplicate rows: {duplicate_rows:,}")

    # ---------------------------------------------------------
    # 4. Timestamp parsing
    # ---------------------------------------------------------

    print_section("6. TIMESTAMP VALIDATION")

    df["timestamp_utc"] = pd.to_datetime(
        df["datetime_from_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = df["timestamp_utc"].isna().sum()

    print(
        f"Invalid/unparseable UTC timestamps: "
        f"{invalid_timestamps:,}"
    )

    valid_df = df.dropna(
        subset=["timestamp_utc"]
    ).copy()

    print(
        "Earliest UTC timestamp:",
        valid_df["timestamp_utc"].min(),
    )

    print(
        "Latest UTC timestamp:",
        valid_df["timestamp_utc"].max(),
    )

    print_section("7. DUPLICATE TIMESTAMPS")

    duplicated_timestamps = (
        valid_df["timestamp_utc"]
        .duplicated(keep=False)
    )

    duplicate_timestamp_rows = (
        duplicated_timestamps.sum()
    )

    duplicate_timestamp_values = (
        valid_df.loc[
            duplicated_timestamps,
            "timestamp_utc"
        ]
        .nunique()
    )

    print(
        "Rows involved in duplicate timestamps:",
        f"{duplicate_timestamp_rows:,}",
    )

    print(
        "Unique timestamps that are duplicated:",
        f"{duplicate_timestamp_values:,}",
    )

    if duplicate_timestamp_rows > 0:
        print("\nExample duplicate timestamps:")

        print(
            valid_df.loc[
                duplicated_timestamps,
                [
                    "timestamp_utc",
                    "value",
                    "sensor_id",
                    "has_flags",
                ],
            ]
            .sort_values("timestamp_utc")
            .head(20)
            .to_string(index=False)
        )

    # ---------------------------------------------------------
    # 5. Frequency inspection
    # ---------------------------------------------------------

    print_section("8. TIMESTAMP FREQUENCY")

    unique_times = (
        valid_df["timestamp_utc"]
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    time_differences = unique_times.diff()

    difference_counts = (
        time_differences
        .value_counts()
        .sort_index()
    )

    print("Most common timestamp intervals:")

    print(
        difference_counts
        .head(20)
        .to_string()
    )

    one_hour = pd.Timedelta(hours=1)

    hourly_steps = (
        time_differences == one_hour
    ).sum()

    non_hourly_steps = (
        time_differences.dropna() != one_hour
    ).sum()

    print(
        f"\n1-hour intervals:     {hourly_steps:,}"
    )

    print(
        f"Non-1-hour intervals: {non_hourly_steps:,}"
    )

    # ---------------------------------------------------------
    # 6. Expected vs observed hourly timestamps
    # ---------------------------------------------------------

    print_section("9. HOURLY COVERAGE / GAPS")

    if len(unique_times) > 0:
        expected_hours = pd.date_range(
            start=unique_times.min(),
            end=unique_times.max(),
            freq="h",
            tz="UTC",
        )

        observed_set = pd.DatetimeIndex(
            unique_times
        )

        missing_hours = (
            expected_hours.difference(
                observed_set
            )
        )

        print(
            f"Expected hourly timestamps: "
            f"{len(expected_hours):,}"
        )

        print(
            f"Observed unique timestamps: "
            f"{len(observed_set):,}"
        )

        print(
            f"Missing hourly timestamps:  "
            f"{len(missing_hours):,}"
        )

        if len(expected_hours) > 0:
            coverage_percent = (
                len(observed_set)
                / len(expected_hours)
                * 100
            )

            print(
                f"Overall timestamp coverage: "
                f"{coverage_percent:.2f}%"
            )

        if len(missing_hours) > 0:
            print("\nFirst 20 missing hours:")

            for timestamp in missing_hours[:20]:
                print(timestamp)

    # ---------------------------------------------------------
    # 7. Station / sensor identity
    # ---------------------------------------------------------

    print_section("10. LOCATION AND SENSOR COVERAGE")

    fields = [
        "location_id",
        "location_name",
        "sensor_id",
        "parameter",
        "display_name",
        "units",
    ]

    for field in fields:
        if field in df.columns:
            print(f"\n{field}:")
            print(
                df[field]
                .value_counts(
                    dropna=False
                )
                .to_string()
            )

    # ---------------------------------------------------------
    # 8. Geographic consistency
    # ---------------------------------------------------------

    print_section("11. COORDINATES")

    print("Latitude values:")

    print(
        df["latitude"]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

    print("\nLongitude values:")

    print(
        df["longitude"]
        .value_counts(dropna=False)
        .head(20)
        .to_string()
    )

    # ---------------------------------------------------------
    # 9. PM2.5 numerical inspection
    # ---------------------------------------------------------

    print_section("12. PM2.5 VALUE INSPECTION")

    df["pm25"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    print(
        df["pm25"]
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

    print(
        "\nMissing/non-numeric PM2.5:",
        f"{df['pm25'].isna().sum():,}",
    )

    print(
        "Negative PM2.5 values:",
        f"{(df['pm25'] < 0).sum():,}",
    )

    print(
        "Zero PM2.5 values:",
        f"{(df['pm25'] == 0).sum():,}",
    )

    print("\n10 lowest PM2.5 observations:")

    print(
        df[
            [
                "datetime_from_utc",
                "pm25",
                "has_flags",
            ]
        ]
        .sort_values(
            "pm25",
            ascending=True,
        )
        .head(10)
        .to_string(index=False)
    )

    print("\n10 highest PM2.5 observations:")

    print(
        df[
            [
                "datetime_from_utc",
                "pm25",
                "has_flags",
            ]
        ]
        .sort_values(
            "pm25",
            ascending=False,
        )
        .head(10)
        .to_string(index=False)
    )

    # ---------------------------------------------------------
    # 10. OpenAQ flags
    # ---------------------------------------------------------

    print_section("13. OPENAQ FLAGS")

    if "has_flags" in df.columns:
        print(
            df["has_flags"]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

    # ---------------------------------------------------------
    # 11. Coverage metadata
    # ---------------------------------------------------------

    print_section("14. OPENAQ HOURLY COVERAGE METADATA")

    coverage_columns = [
        "coverage_expected_count",
        "coverage_observed_count",
        "coverage_percent_complete",
        "coverage_percent_coverage",
    ]

    for column in coverage_columns:
        if column in df.columns:
            print(f"\n{column}")

            numeric = pd.to_numeric(
                df[column],
                errors="coerce",
            )

            print(
                numeric.describe()
                .to_string()
            )

    # ---------------------------------------------------------
    # 12. Monthly availability
    # ---------------------------------------------------------

    print_section("15. RECORDS BY MONTH")

    valid_df["month"] = (
        valid_df["timestamp_utc"]
        .dt.to_period("M")
    )

    monthly_counts = (
        valid_df.groupby(
            "month"
        )
        .size()
    )

    print(monthly_counts.to_string())

    # ---------------------------------------------------------
    # 13. Chronological preview
    # ---------------------------------------------------------

    print_section("16. FIRST 10 CHRONOLOGICAL RECORDS")

    print(
        valid_df[
            [
                "timestamp_utc",
                "value",
                "has_flags",
            ]
        ]
        .sort_values("timestamp_utc")
        .head(10)
        .to_string(index=False)
    )

    print_section("17. LAST 10 CHRONOLOGICAL RECORDS")

    print(
        valid_df[
            [
                "timestamp_utc",
                "value",
                "has_flags",
            ]
        ]
        .sort_values("timestamp_utc")
        .tail(10)
        .to_string(index=False)
    )

    print_section("INSPECTION COMPLETE")

    print(
        "No cleaning, interpolation, filtering, "
        "or outlier removal was performed."
    )


if __name__ == "__main__":
    main()