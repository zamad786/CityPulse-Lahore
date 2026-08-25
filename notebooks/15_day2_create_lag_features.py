import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_time_features.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_lag_features.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step7_lag_features_summary.json"
)


LAG_HOURS = [1, 2, 3, 6, 12, 24]


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 7 PM2.5 LAG FEATURES"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print_section("1. LOAD DATA")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # -----------------------------------------------------
    # Parse and validate timestamp
    # -----------------------------------------------------

    print_section("2. VALIDATE HOURLY TIMELINE")

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = int(
        df["timestamp_utc"].isna().sum()
    )

    duplicate_timestamps = int(
        df["timestamp_utc"].duplicated().sum()
    )

    non_hourly_intervals = int(
        (
            df["timestamp_utc"]
            .diff()
            .dropna()
            != pd.Timedelta(hours=1)
        ).sum()
    )

    print(
        f"Invalid timestamps:      {invalid_timestamps:,}"
    )

    print(
        f"Duplicate timestamps:    {duplicate_timestamps:,}"
    )

    print(
        f"Non-1-hour intervals:    {non_hourly_intervals:,}"
    )

    if (
        invalid_timestamps > 0
        or duplicate_timestamps > 0
        or non_hourly_intervals > 0
    ):
        raise ValueError(
            "Dataset is not a valid continuous hourly timeline."
        )

    # -----------------------------------------------------
    # Ensure PM2.5 is numeric
    # -----------------------------------------------------

    df["pm25_ug_m3"] = pd.to_numeric(
        df["pm25_ug_m3"],
        errors="coerce",
    )

    # -----------------------------------------------------
    # Create lag features
    #
    # Because Step 3 created a complete hourly timeline,
    # shift(1) really means 1 clock hour earlier.
    # -----------------------------------------------------

    print_section("3. CREATE LAG FEATURES")

    created_columns = []

    for hours in LAG_HOURS:
        column = f"pm25_lag_{hours}h"

        df[column] = (
            df["pm25_ug_m3"]
            .shift(hours)
        )

        created_columns.append(column)

        print(
            f"{column}: "
            f"{df[column].notna().sum():,} available, "
            f"{df[column].isna().sum():,} missing"
        )

    # -----------------------------------------------------
    # Leakage verification
    # -----------------------------------------------------

    print_section("4. LEAKAGE CHECK")

    print(
        "Lag features use only earlier PM2.5 observations."
    )

    print(
        "No future PM2.5 value is used in any lag feature."
    )

    print(
        "\nExample:"
    )

    preview_columns = [
        "timestamp_utc",
        "pm25_ug_m3",
        "pm25_lag_1h",
        "pm25_lag_2h",
        "pm25_lag_3h",
    ]

    print(
        df[preview_columns]
        .head(15)
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    print_section("5. SAVE DATASET")

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 7,
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "rows": int(len(df)),
        "lag_hours": LAG_HOURS,
        "lag_availability": {
            column: {
                "available": int(
                    df[column].notna().sum()
                ),
                "missing": int(
                    df[column].isna().sum()
                ),
            }
            for column in created_columns
        },
        "methodology": {
            "timeline_frequency": "1 hour",
            "future_data_used": False,
            "pm25_interpolated": False,
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
        )

    print(f"Saved dataset:\n{OUTPUT_FILE}")
    print(f"\nSaved report:\n{REPORT_FILE}")

    print_section("STEP 7 COMPLETE")


if __name__ == "__main__":
    main()