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

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_cleaned.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step2_cleaning_summary.json"
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
        "CITYPULSE LAHORE — DAY 2 STEP 2 DATA CLEANING"
    )

    # -----------------------------------------------------
    # 1. Load
    # -----------------------------------------------------

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    original_rows = len(df)

    print_section("1. LOAD DATA")

    print(f"Input rows:    {original_rows:,}")
    print(f"Input columns: {len(df.columns)}")

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Required columns missing: {missing_columns}"
        )

    # -----------------------------------------------------
    # 2. Exact duplicates
    # -----------------------------------------------------

    print_section("2. EXACT DUPLICATE HANDLING")

    exact_duplicates = int(
        df.duplicated().sum()
    )

    print(
        f"Exact duplicates found: "
        f"{exact_duplicates:,}"
    )

    if exact_duplicates > 0:
        df = (
            df.drop_duplicates()
            .copy()
        )

    print(
        f"Rows after exact duplicate removal: "
        f"{len(df):,}"
    )

    # -----------------------------------------------------
    # 3. Timestamp cleaning
    # -----------------------------------------------------

    print_section("3. TIMESTAMP CLEANING")

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = int(
        df["timestamp_utc"]
        .isna()
        .sum()
    )

    print(
        f"Invalid timestamps: "
        f"{invalid_timestamps:,}"
    )

    if invalid_timestamps > 0:
        raise ValueError(
            "Invalid timestamps detected. "
            "Manual investigation is required."
        )

    duplicate_timestamps = int(
        df["timestamp_utc"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate timestamps: "
        f"{duplicate_timestamps:,}"
    )

    if duplicate_timestamps > 0:
        print(
            "\nDuplicate timestamps may contain "
            "different measurements."
        )

        print(
            df.loc[
                df["timestamp_utc"]
                .duplicated(keep=False)
            ]
            .sort_values("timestamp_utc")
            .head(20)
            .to_string(index=False)
        )

        raise ValueError(
            "Ambiguous duplicate timestamps detected. "
            "Cleaning stopped rather than silently "
            "discarding measurements."
        )

    df = (
        df.sort_values("timestamp_utc")
        .reset_index(drop=True)
    )

    print(
        "Chronologically sorted:",
        df["timestamp_utc"]
        .is_monotonic_increasing,
    )

    # -----------------------------------------------------
    # 4. Numeric type enforcement
    # -----------------------------------------------------

    print_section("4. NUMERIC TYPE CLEANING")

    numeric_failures = {}

    for column in NUMERIC_COLUMNS:
        existing_missing = int(
            df[column]
            .isna()
            .sum()
        )

        converted = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        converted_missing = int(
            converted
            .isna()
            .sum()
        )

        new_failures = (
            converted_missing
            - existing_missing
        )

        numeric_failures[column] = int(
            new_failures
        )

        print(
            f"{column}: "
            f"{new_failures:,} conversion failures"
        )

        if new_failures > 0:
            raise ValueError(
                f"Non-numeric values found in {column}."
            )

        df[column] = converted

    # -----------------------------------------------------
    # 5. Missing required values
    # -----------------------------------------------------

    print_section("5. REQUIRED VALUE CHECK")

    required_missing = {}

    for column in REQUIRED_COLUMNS:
        missing = int(
            df[column]
            .isna()
            .sum()
        )

        required_missing[column] = missing

        print(
            f"{column}: "
            f"{missing:,} missing"
        )

    if any(
        count > 0
        for count in required_missing.values()
    ):
        raise ValueError(
            "Required values are missing. "
            "Cleaning stopped."
        )

    # -----------------------------------------------------
    # 6. PM2.5 validity
    # -----------------------------------------------------

    print_section("6. PM2.5 CLEANING DECISION")

    negative_pm25 = int(
        (df["pm25_ug_m3"] < 0).sum()
    )

    zero_pm25 = int(
        (df["pm25_ug_m3"] == 0).sum()
    )

    print(
        f"Negative PM2.5 values: "
        f"{negative_pm25:,}"
    )

    print(
        f"Zero PM2.5 values:     "
        f"{zero_pm25:,}"
    )

    if negative_pm25 > 0:
        raise ValueError(
            "Negative PM2.5 values detected. "
            "Manual sensor-quality review required."
        )

    print(
        "\nDecision:"
    )

    print(
        "Zero PM2.5 values are retained."
    )

    print(
        "There is not enough evidence yet "
        "to classify them as sensor errors."
    )

    # -----------------------------------------------------
    # 7. Statistical outlier review
    # -----------------------------------------------------

    print_section("7. PM2.5 OUTLIER POLICY")

    pm25 = df["pm25_ug_m3"]

    q1 = pm25.quantile(0.25)
    q3 = pm25.quantile(0.75)

    iqr = q3 - q1

    lower_bound = (
        q1 - 1.5 * iqr
    )

    upper_bound = (
        q3 + 1.5 * iqr
    )

    outlier_mask = (
        (pm25 < lower_bound)
        | (pm25 > upper_bound)
    )

    outlier_count = int(
        outlier_mask.sum()
    )

    print(
        f"IQR lower review bound: "
        f"{lower_bound:.2f}"
    )

    print(
        f"IQR upper review bound: "
        f"{upper_bound:.2f}"
    )

    print(
        f"Values outside review bounds: "
        f"{outlier_count:,}"
    )

    print(
        "\nDecision:"
    )

    print(
        "IQR outliers are retained."
    )

    print(
        "Statistical extremeness alone is not "
        "evidence of an invalid pollution reading."
    )

    # -----------------------------------------------------
    # 8. OpenAQ flags
    # -----------------------------------------------------

    print_section("8. OPENAQ FLAGS")

    if "has_flags" in df.columns:
        flagged_rows = int(
            (df["has_flags"] == True)
            .sum()
        )

        print(
            f"Flagged rows: "
            f"{flagged_rows:,}"
        )

    else:
        flagged_rows = 0

        print(
            "has_flags column not present."
        )

    if flagged_rows > 0:
        print(
            "\nFlagged rows are retained for now "
            "and require explicit review."
        )

    # -----------------------------------------------------
    # 9. Weather validity
    # -----------------------------------------------------

    print_section("9. WEATHER VALIDITY")

    weather_checks = {
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

        "invalid_wind_direction": int(
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

    for name, count in weather_checks.items():
        print(
            f"{name}: "
            f"{count:,}"
        )

    if any(
        count > 0
        for count in weather_checks.values()
    ):
        raise ValueError(
            "Invalid weather measurements detected."
        )

    # -----------------------------------------------------
    # 10. Temporal gaps
    # -----------------------------------------------------

    print_section("10. TEMPORAL GAP POLICY")

    start = df["timestamp_utc"].min()
    end = df["timestamp_utc"].max()

    expected_hours = pd.date_range(
        start=start,
        end=end,
        freq="h",
        tz="UTC",
    )

    observed_hours = pd.DatetimeIndex(
        df["timestamp_utc"]
    )

    missing_hours = (
        expected_hours
        .difference(observed_hours)
    )

    print(
        f"Observed PM2.5 rows: "
        f"{len(df):,}"
    )

    print(
        f"Missing calendar hours: "
        f"{len(missing_hours):,}"
    )

    print(
        "\nDecision:"
    )

    print(
        "Temporal gaps are retained."
    )

    print(
        "PM2.5 will NOT be interpolated or "
        "forward-filled during cleaning."
    )

    print(
        "Step 3 will represent the complete "
        "hourly timeline explicitly."
    )

    # -----------------------------------------------------
    # 11. Save cleaned checkpoint
    # -----------------------------------------------------

    print_section("11. SAVE CLEANED DATASET")

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    final_rows = len(df)

    rows_removed = (
        original_rows - final_rows
    )

    print(
        f"Original rows: "
        f"{original_rows:,}"
    )

    print(
        f"Final rows:    "
        f"{final_rows:,}"
    )

    print(
        f"Rows removed:  "
        f"{rows_removed:,}"
    )

    print(
        "\nCleaned dataset saved to:"
    )

    print(OUTPUT_FILE)

    # -----------------------------------------------------
    # 12. Save cleaning report
    # -----------------------------------------------------

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 2,
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),

        "rows": {
            "original": int(
                original_rows
            ),
            "final": int(
                final_rows
            ),
            "removed": int(
                rows_removed
            ),
        },

        "cleaning": {
            "exact_duplicates_removed": int(
                exact_duplicates
            ),
            "invalid_timestamps": int(
                invalid_timestamps
            ),
            "duplicate_timestamps": int(
                duplicate_timestamps
            ),
            "numeric_conversion_failures": (
                numeric_failures
            ),
        },

        "pm25": {
            "negative_values": (
                negative_pm25
            ),
            "zero_values_retained": (
                zero_pm25
            ),
            "iqr_review_values_retained": (
                outlier_count
            ),
            "iqr_review_lower": float(
                lower_bound
            ),
            "iqr_review_upper": float(
                upper_bound
            ),
        },

        "openaq_flagged_rows": (
            flagged_rows
        ),

        "weather_checks": (
            weather_checks
        ),

        "temporal_gaps": {
            "missing_hours": int(
                len(missing_hours)
            ),
            "pm25_interpolated": False,
            "pm25_forward_filled": False,
        },

        "policy": {
            "zero_pm25": (
                "retained_pending_evidence"
            ),
            "iqr_outliers": (
                "retained_not_assumed_invalid"
            ),
            "temporal_gaps": (
                "retained_no_pm25_imputation"
            ),
        },
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    print(
        "\nCleaning report saved to:"
    )

    print(REPORT_FILE)

    # -----------------------------------------------------
    # Finish
    # -----------------------------------------------------

    print_section("STEP 2 COMPLETE")

    print(
        "Structural cleaning completed successfully."
    )

    print(
        "No pollution extremes or temporal gaps "
        "were artificially removed or filled."
    )


if __name__ == "__main__":
    main()