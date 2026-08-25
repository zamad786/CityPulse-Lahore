import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_rolling_features.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_feature_target_base.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step9_target_summary.json"
)


FORECAST_HORIZON_HOURS = 1


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 9 FUTURE PM2.5 TARGET"
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
    # Timestamp validation
    # -----------------------------------------------------

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

    non_hourly_intervals = int(
        (
            df["timestamp_utc"]
            .diff()
            .dropna()
            != pd.Timedelta(hours=1)
        ).sum()
    )

    print_section("2. VALIDATE HOURLY TIMELINE")

    print(
        f"Invalid timestamps:   "
        f"{invalid_timestamps:,}"
    )

    print(
        f"Non-hourly intervals: "
        f"{non_hourly_intervals:,}"
    )

    if (
        invalid_timestamps > 0
        or non_hourly_intervals > 0
    ):
        raise ValueError(
            "Target creation requires a valid "
            "continuous hourly timeline."
        )

    # -----------------------------------------------------
    # Create target
    # -----------------------------------------------------

    print_section("3. CREATE 1-HOUR-AHEAD TARGET")

    df["target_timestamp_utc"] = (
        df["timestamp_utc"]
        + pd.Timedelta(
            hours=FORECAST_HORIZON_HOURS
        )
    )

    df["target_pm25_1h"] = (
        df["pm25_ug_m3"]
        .shift(
            -FORECAST_HORIZON_HOURS
        )
    )

    df["target_pm25_observed"] = (
        df["target_pm25_1h"]
        .notna()
    )

    target_available = int(
        df["target_pm25_1h"]
        .notna()
        .sum()
    )

    target_missing = int(
        df["target_pm25_1h"]
        .isna()
        .sum()
    )

    print(
        f"Forecast horizon: "
        f"{FORECAST_HORIZON_HOURS} hour"
    )

    print(
        f"Available targets: "
        f"{target_available:,}"
    )

    print(
        f"Missing targets:   "
        f"{target_missing:,}"
    )

    # -----------------------------------------------------
    # Leakage explanation
    # -----------------------------------------------------

    print_section("4. LEAKAGE SAFETY")

    print(
        "Feature row at timestamp t predicts "
        "PM2.5 at timestamp t+1 hour."
    )

    print(
        "Future PM2.5 is used only as the target."
    )

    print(
        "It is NOT included in the input features."
    )

    # -----------------------------------------------------
    # Example
    # -----------------------------------------------------

    print_section("5. TARGET PREVIEW")

    preview_columns = [
        "timestamp_utc",
        "pm25_ug_m3",
        "pm25_lag_1h",
        "pm25_rolling_mean_3h",
        "target_timestamp_utc",
        "target_pm25_1h",
        "target_pm25_observed",
    ]

    print(
        df[preview_columns]
        .head(20)
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # Determine initially complete ML rows
    #
    # This does NOT split or train anything.
    # It only reports how many rows currently have
    # all candidate historical features and target.
    # -----------------------------------------------------

    print_section("6. INITIAL ML ROW AVAILABILITY")

    candidate_feature_columns = [
        "pm25_ug_m3",

        "pm25_lag_1h",
        "pm25_lag_2h",
        "pm25_lag_3h",
        "pm25_lag_6h",
        "pm25_lag_12h",
        "pm25_lag_24h",

        "pm25_rolling_mean_3h",
        "pm25_rolling_mean_6h",
        "pm25_rolling_mean_12h",
        "pm25_rolling_mean_24h",

        "temperature_c",
        "relative_humidity_pct",
        "precipitation_mm",
        "wind_speed_m_s",
        "wind_direction_deg",
        "surface_pressure_hpa",

        "hour",
        "day_of_week",
        "month",
        "is_weekend",
    ]

    required_for_ml = (
        candidate_feature_columns
        + ["target_pm25_1h"]
    )

    complete_ml_mask = (
        df[required_for_ml]
        .notna()
        .all(axis=1)
    )

    complete_ml_rows = int(
        complete_ml_mask.sum()
    )

    incomplete_ml_rows = int(
        (~complete_ml_mask).sum()
    )

    print(
        f"Rows with all candidate features "
        f"+ target: {complete_ml_rows:,}"
    )

    print(
        f"Rows currently incomplete: "
        f"{incomplete_ml_rows:,}"
    )

    print(
        "\nNo rows are dropped in Step 9."
    )

    print(
        "Step 10 will create the final ML table "
        "and chronological train/validation/test split."
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    print_section("7. SAVE FEATURE + TARGET BASE")

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 9,
        "input_file": str(INPUT_FILE),
        "output_file": str(OUTPUT_FILE),

        "forecast_target": {
            "name": "target_pm25_1h",
            "definition": "PM2.5(t + 1 hour)",
            "horizon_hours": (
                FORECAST_HORIZON_HOURS
            ),
        },

        "rows": {
            "total": int(len(df)),
            "target_available": (
                target_available
            ),
            "target_missing": (
                target_missing
            ),
            "complete_candidate_ml_rows": (
                complete_ml_rows
            ),
            "incomplete_candidate_ml_rows": (
                incomplete_ml_rows
            ),
        },

        "methodology": {
            "timeline_frequency": "hourly",
            "target_uses_exact_next_clock_hour": True,
            "future_data_used_as_feature": False,
            "pm25_interpolated": False,
            "rows_dropped": False,
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

    print_section("STEP 9 COMPLETE")

    print(
        "Prediction target confirmed:"
    )

    print(
        "PM2.5(t + 1 hour)"
    )


if __name__ == "__main__":
    main()