import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_lag_features.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_rolling_features.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step8_rolling_features_summary.json"
)


ROLLING_WINDOWS = [3, 6, 12, 24]


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 8 ROLLING FEATURES"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print_section("1. LOAD DATA")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    df["pm25_ug_m3"] = pd.to_numeric(
        df["pm25_ug_m3"],
        errors="coerce",
    )

    # -----------------------------------------------------
    # Create rolling means
    #
    # Window includes current time t and previous hours.
    #
    # Example rolling 3h at time t:
    # mean(PM2.5[t], PM2.5[t-1], PM2.5[t-2])
    #
    # This is valid for predicting t+1 because PM2.5 at
    # time t is already known.
    #
    # min_periods=window prevents partial windows from
    # silently pretending to be complete windows.
    # -----------------------------------------------------

    print_section("2. CREATE ROLLING MEANS")

    created_columns = []

    for window in ROLLING_WINDOWS:
        column = (
            f"pm25_rolling_mean_{window}h"
        )

        df[column] = (
            df["pm25_ug_m3"]
            .rolling(
                window=window,
                min_periods=window,
            )
            .mean()
        )

        created_columns.append(column)

        print(
            f"{column}: "
            f"{df[column].notna().sum():,} available, "
            f"{df[column].isna().sum():,} missing"
        )

    # -----------------------------------------------------
    # Validate missing gaps
    # -----------------------------------------------------

    print_section("3. GAP SAFETY CHECK")

    print(
        "Rolling windows require complete observed "
        "PM2.5 values across the full window."
    )

    print(
        "If a source PM2.5 hour is missing, affected "
        "rolling windows remain NaN."
    )

    print(
        "No PM2.5 interpolation or forward filling "
        "has been performed."
    )

    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    print_section("4. PREVIEW")

    preview_columns = [
        "timestamp_utc",
        "pm25_ug_m3",
        "pm25_rolling_mean_3h",
        "pm25_rolling_mean_6h",
        "pm25_rolling_mean_12h",
        "pm25_rolling_mean_24h",
    ]

    print(
        df[preview_columns]
        .head(30)
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
        "step": 8,
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),
        "rows": int(len(df)),
        "rolling_windows_hours": (
            ROLLING_WINDOWS
        ),
        "availability": {
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
            "uses_future_pm25": False,
            "uses_current_pm25": True,
            "pm25_imputation": False,
            "requires_complete_window": True,
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

    print_section("STEP 8 COMPLETE")


if __name__ == "__main__":
    main()