import json
from pathlib import Path

import pandas as pd


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_aq_weather_merged.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step1_preprocessing_audit.json"
)


REQUIRED_COLUMNS = [
    "timestamp_utc",
    "pm25_ug_m3",
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "wind_speed_m_s",
    "wind_direction_deg",
    "surface_pressure_hpa",
]


NUMERIC_COLUMNS = [
    "pm25_ug_m3",
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


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 1 PREPROCESSING AUDIT"
    )

    # -----------------------------------------------------
    # 1. Load dataset
    # -----------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Combined dataset not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print_section("1. DATASET STRUCTURE")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    missing_required_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    print(
        "Missing required columns:",
        (
            "None"
            if not missing_required_columns
            else missing_required_columns
        ),
    )

    if missing_required_columns:
        raise ValueError(
            "Required columns are missing. "
            "Audit cannot continue."
        )

    # -----------------------------------------------------
    # 2. Original data types
    # -----------------------------------------------------

    print_section("2. CURRENT DATA TYPES")

    print(df.dtypes.to_string())

    # -----------------------------------------------------
    # 3. Missing values
    # -----------------------------------------------------

    print_section("3. MISSING VALUES")

    missing_table = pd.DataFrame(
        {
            "missing_count": df.isna().sum(),
            "missing_percent": (
                df.isna().mean() * 100
            ).round(3),
        }
    )

    print(missing_table.to_string())

    # -----------------------------------------------------
    # 4. Duplicate checks
    # -----------------------------------------------------

    print_section("4. DUPLICATE CHECKS")

    exact_duplicate_rows = int(
        df.duplicated().sum()
    )

    print(
        f"Exact duplicate rows: "
        f"{exact_duplicate_rows:,}"
    )

    # -----------------------------------------------------
    # 5. Timestamp audit
    # -----------------------------------------------------

    print_section("5. TIMESTAMP AUDIT")

    df["timestamp_parsed"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = int(
        df["timestamp_parsed"]
        .isna()
        .sum()
    )

    duplicate_timestamps = int(
        df["timestamp_parsed"]
        .duplicated()
        .sum()
    )

    chronological = bool(
        df["timestamp_parsed"]
        .is_monotonic_increasing
    )

    print(
        f"Invalid timestamps:     "
        f"{invalid_timestamps:,}"
    )

    print(
        f"Duplicate timestamps:   "
        f"{duplicate_timestamps:,}"
    )

    print(
        f"Chronologically sorted: "
        f"{chronological}"
    )

    valid_times = (
        df["timestamp_parsed"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    start_timestamp = valid_times.min()
    end_timestamp = valid_times.max()

    print(
        f"Earliest timestamp: "
        f"{start_timestamp}"
    )

    print(
        f"Latest timestamp:   "
        f"{end_timestamp}"
    )

    # -----------------------------------------------------
    # 6. Numeric conversion audit
    # -----------------------------------------------------

    print_section("6. NUMERIC CONVERSION CHECK")

    numeric_conversion_failures = {}

    for column in NUMERIC_COLUMNS:
        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        failures = int(
            converted.isna().sum()
            - df[column].isna().sum()
        )

        numeric_conversion_failures[column] = failures

        print(
            f"{column}: "
            f"{failures:,} non-numeric values"
        )

        df[column] = converted

    # -----------------------------------------------------
    # 7. PM2.5 audit
    # -----------------------------------------------------

    print_section("7. PM2.5 AUDIT")

    pm25 = df["pm25_ug_m3"]

    print(
        pm25.describe(
            percentiles=[
                0.01,
                0.05,
                0.25,
                0.50,
                0.75,
                0.95,
                0.99,
            ]
        ).to_string()
    )

    pm25_negative = int(
        (pm25 < 0).sum()
    )

    pm25_zero = int(
        (pm25 == 0).sum()
    )

    print(
        f"\nNegative PM2.5 values: "
        f"{pm25_negative:,}"
    )

    print(
        f"Zero PM2.5 values:     "
        f"{pm25_zero:,}"
    )

    # IQR is used only to identify observations for review.
    # It does NOT imply they are invalid.
    q1 = pm25.quantile(0.25)
    q3 = pm25.quantile(0.75)
    iqr = q3 - q1

    iqr_lower = q1 - (1.5 * iqr)
    iqr_upper = q3 + (1.5 * iqr)

    iqr_outlier_mask = (
        (pm25 < iqr_lower)
        | (pm25 > iqr_upper)
    )

    iqr_outlier_count = int(
        iqr_outlier_mask.sum()
    )

    print(
        f"\nIQR review lower bound: "
        f"{iqr_lower:.2f}"
    )

    print(
        f"IQR review upper bound: "
        f"{iqr_upper:.2f}"
    )

    print(
        f"Values outside IQR review bounds: "
        f"{iqr_outlier_count:,}"
    )

    print(
        "\nIMPORTANT: These are review candidates, "
        "not automatically invalid measurements."
    )

    print("\n10 highest PM2.5 values:")

    print(
        df[
            [
                "timestamp_utc",
                "pm25_ug_m3",
                "has_flags",
            ]
        ]
        .sort_values(
            "pm25_ug_m3",
            ascending=False,
        )
        .head(10)
        .to_string(index=False)
    )

    print("\n10 lowest PM2.5 values:")

    print(
        df[
            [
                "timestamp_utc",
                "pm25_ug_m3",
                "has_flags",
            ]
        ]
        .sort_values(
            "pm25_ug_m3",
            ascending=True,
        )
        .head(10)
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # 8. OpenAQ quality flags
    # -----------------------------------------------------

    print_section("8. OPENAQ QUALITY FLAGS")

    if "has_flags" in df.columns:
        print(
            df["has_flags"]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

        flagged_rows = int(
            (df["has_flags"] == True).sum()
        )

    else:
        flagged_rows = 0

        print(
            "Column 'has_flags' not present."
        )

    # -----------------------------------------------------
    # 9. Weather validity
    # -----------------------------------------------------

    print_section("9. WEATHER VALIDITY")

    invalid_weather = {
        "humidity_below_0": int(
            (
                df["relative_humidity_pct"] < 0
            ).sum()
        ),
        "humidity_above_100": int(
            (
                df["relative_humidity_pct"] > 100
            ).sum()
        ),
        "negative_precipitation": int(
            (
                df["precipitation_mm"] < 0
            ).sum()
        ),
        "negative_wind_speed": int(
            (
                df["wind_speed_m_s"] < 0
            ).sum()
        ),
        "wind_direction_outside_0_360": int(
            (
                (
                    df["wind_direction_deg"] < 0
                )
                |
                (
                    df["wind_direction_deg"] > 360
                )
            ).sum()
        ),
    }

    for check, count in invalid_weather.items():
        print(
            f"{check}: {count:,}"
        )

    # -----------------------------------------------------
    # 10. Temporal gaps
    # -----------------------------------------------------

    print_section("10. TEMPORAL GAP AUDIT")

    expected_hours = pd.date_range(
        start=start_timestamp,
        end=end_timestamp,
        freq="h",
        tz="UTC",
    )

    observed_hours = pd.DatetimeIndex(
        valid_times
    )

    missing_hours = (
        expected_hours.difference(
            observed_hours
        )
    )

    coverage_percent = (
        len(observed_hours)
        / len(expected_hours)
        * 100
    )

    print(
        f"Expected calendar hours: "
        f"{len(expected_hours):,}"
    )

    print(
        f"Observed PM2.5 hours:    "
        f"{len(observed_hours):,}"
    )

    print(
        f"Missing PM2.5 hours:     "
        f"{len(missing_hours):,}"
    )

    print(
        f"Timestamp coverage:      "
        f"{coverage_percent:.2f}%"
    )

    # -----------------------------------------------------
    # 11. Gap lengths
    # -----------------------------------------------------

    print_section("11. GAP LENGTH DISTRIBUTION")

    time_diffs = (
        valid_times.diff()
    )

    gap_rows = []

    for index in range(1, len(valid_times)):
        difference = (
            valid_times.iloc[index]
            - valid_times.iloc[index - 1]
        )

        missing_between = int(
            difference / pd.Timedelta(hours=1)
        ) - 1

        if missing_between > 0:
            gap_rows.append(
                {
                    "gap_start_after": (
                        valid_times.iloc[index - 1]
                    ),
                    "gap_end_before": (
                        valid_times.iloc[index]
                    ),
                    "missing_hours": (
                        missing_between
                    ),
                }
            )

    gaps_df = pd.DataFrame(gap_rows)

    if gaps_df.empty:
        number_of_gaps = 0
        longest_gap = 0

        print("No temporal gaps detected.")

    else:
        number_of_gaps = len(gaps_df)

        longest_gap = int(
            gaps_df["missing_hours"].max()
        )

        print(
            f"Number of separate gaps: "
            f"{number_of_gaps:,}"
        )

        print(
            f"Longest missing sequence: "
            f"{longest_gap:,} hours"
        )

        print(
            "\nGap-size distribution:"
        )

        print(
            gaps_df["missing_hours"]
            .value_counts()
            .sort_index()
            .head(30)
            .to_string()
        )

        print(
            "\n10 longest gaps:"
        )

        print(
            gaps_df
            .sort_values(
                "missing_hours",
                ascending=False,
            )
            .head(10)
            .to_string(index=False)
        )

    # -----------------------------------------------------
    # 12. Continuous hourly segments
    # -----------------------------------------------------

    print_section("12. CONTINUOUS HOURLY SEGMENTS")

    if len(valid_times) > 0:
        breaks = (
            valid_times.diff()
            != pd.Timedelta(hours=1)
        )

        segment_id = (
            breaks.cumsum()
        )

        segment_table = (
            pd.DataFrame(
                {
                    "timestamp": valid_times,
                    "segment_id": segment_id,
                }
            )
            .groupby("segment_id")
            .agg(
                start=("timestamp", "min"),
                end=("timestamp", "max"),
                hours=("timestamp", "size"),
            )
            .sort_values(
                "hours",
                ascending=False,
            )
        )

        print(
            f"Number of continuous segments: "
            f"{len(segment_table):,}"
        )

        print(
            "\n10 longest continuous segments:"
        )

        print(
            segment_table
            .head(10)
            .to_string()
        )

        longest_continuous_segment = int(
            segment_table["hours"].max()
        )

    else:
        segment_table = pd.DataFrame()
        longest_continuous_segment = 0

    # -----------------------------------------------------
    # 13. Metadata consistency
    # -----------------------------------------------------

    print_section("13. STATION / SOURCE CONSISTENCY")

    metadata_columns = [
        "station_name",
        "openaq_location_id",
        "openaq_sensor_id",
        "station_latitude",
        "station_longitude",
        "weather_grid_latitude",
        "weather_grid_longitude",
    ]

    metadata_unique_counts = {}

    for column in metadata_columns:
        if column in df.columns:
            count = int(
                df[column].nunique(
                    dropna=False
                )
            )

            metadata_unique_counts[column] = count

            print(
                f"{column}: "
                f"{count} unique value(s)"
            )

    # -----------------------------------------------------
    # 14. Cleaning decision summary
    # -----------------------------------------------------

    print_section("14. PREPROCESSING AUDIT SUMMARY")

    print(
        "This step identifies issues only."
    )

    print(
        "No rows or values were changed."
    )

    print()

    print(
        f"Exact duplicate rows:       "
        f"{exact_duplicate_rows:,}"
    )

    print(
        f"Duplicate timestamps:       "
        f"{duplicate_timestamps:,}"
    )

    print(
        f"Missing PM2.5 values:       "
        f"{df['pm25_ug_m3'].isna().sum():,}"
    )

    print(
        f"Zero PM2.5 values:          "
        f"{pm25_zero:,}"
    )

    print(
        f"Flagged OpenAQ rows:        "
        f"{flagged_rows:,}"
    )

    print(
        f"Missing calendar hours:     "
        f"{len(missing_hours):,}"
    )

    print(
        f"Separate temporal gaps:     "
        f"{number_of_gaps:,}"
    )

    print(
        f"Longest gap:                "
        f"{longest_gap:,} hours"
    )

    print(
        f"Longest continuous segment: "
        f"{longest_continuous_segment:,} hours"
    )

    print(
        "\nWe will use these results to decide "
        "what should actually be cleaned in Step 2."
    )

    # -----------------------------------------------------
    # 15. Save report
    # -----------------------------------------------------

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 1,
        "purpose": "Preprocessing audit before modifying data",
        "input_file": str(INPUT_FILE),
        "dataset": {
            "rows": int(len(df)),
            "columns": int(len(df.columns) - 1),
            "start_timestamp_utc": str(
                start_timestamp
            ),
            "end_timestamp_utc": str(
                end_timestamp
            ),
            "expected_calendar_hours": int(
                len(expected_hours)
            ),
            "observed_hours": int(
                len(observed_hours)
            ),
            "missing_hours": int(
                len(missing_hours)
            ),
            "coverage_percent": round(
                coverage_percent,
                2,
            ),
        },
        "duplicates": {
            "exact_rows": exact_duplicate_rows,
            "duplicate_timestamps": (
                duplicate_timestamps
            ),
        },
        "pm25": {
            "missing": int(
                df["pm25_ug_m3"]
                .isna()
                .sum()
            ),
            "negative": pm25_negative,
            "zero": pm25_zero,
            "minimum": float(
                pm25.min()
            ),
            "median": float(
                pm25.median()
            ),
            "maximum": float(
                pm25.max()
            ),
            "iqr_review_lower": float(
                iqr_lower
            ),
            "iqr_review_upper": float(
                iqr_upper
            ),
            "iqr_review_count": (
                iqr_outlier_count
            ),
        },
        "quality": {
            "flagged_openaq_rows": (
                flagged_rows
            ),
            "numeric_conversion_failures": (
                numeric_conversion_failures
            ),
            "weather_validity": (
                invalid_weather
            ),
        },
        "temporal_gaps": {
            "number_of_gaps": int(
                number_of_gaps
            ),
            "longest_gap_hours": int(
                longest_gap
            ),
            "longest_continuous_segment_hours": int(
                longest_continuous_segment
            ),
        },
        "metadata_unique_counts": (
            metadata_unique_counts
        ),
        "data_modified": False,
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

    print_section("AUDIT COMPLETE")

    print(
        "Audit report saved to:"
    )

    print(REPORT_FILE)

    print(
        "\nThe combined dataset itself "
        "was not modified."
    )


if __name__ == "__main__":
    main()