import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_feature_target_base.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_ml_split_ready.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step10_split_summary.json"
)


FEATURE_COLUMNS = [
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

TARGET_COLUMN = "target_pm25_1h"


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def split_summary(name, dataframe):
    print(f"\n{name.upper()}")
    print(f"Rows: {len(dataframe):,}")

    print(
        "Feature start:",
        dataframe["timestamp_utc"].min(),
    )

    print(
        "Feature end:  ",
        dataframe["timestamp_utc"].max(),
    )

    print(
        "Target start: ",
        dataframe["target_timestamp_utc"].min(),
    )

    print(
        "Target end:   ",
        dataframe["target_timestamp_utc"].max(),
    )


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 10 CHRONOLOGICAL SPLIT"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print_section("1. LOAD FEATURE + TARGET DATA")

    print(f"Input rows:    {len(df):,}")
    print(f"Input columns: {len(df.columns)}")

    # -----------------------------------------------------
    # Parse timestamps
    # -----------------------------------------------------

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    df["target_timestamp_utc"] = pd.to_datetime(
        df["target_timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_feature_timestamps = int(
        df["timestamp_utc"].isna().sum()
    )

    invalid_target_timestamps = int(
        df["target_timestamp_utc"].isna().sum()
    )

    print_section("2. TIMESTAMP VALIDATION")

    print(
        "Invalid feature timestamps:",
        f"{invalid_feature_timestamps:,}",
    )

    print(
        "Invalid target timestamps:",
        f"{invalid_target_timestamps:,}",
    )

    if (
        invalid_feature_timestamps > 0
        or invalid_target_timestamps > 0
    ):
        raise ValueError(
            "Invalid timestamps detected."
        )

    expected_target_time = (
        df["timestamp_utc"]
        + pd.Timedelta(hours=1)
    )

    incorrect_target_time = int(
        (
            df["target_timestamp_utc"]
            != expected_target_time
        ).sum()
    )

    print(
        "Incorrect +1-hour target timestamps:",
        f"{incorrect_target_time:,}",
    )

    if incorrect_target_time > 0:
        raise ValueError(
            "Target timestamps are not exactly "
            "one hour after feature timestamps."
        )

    # -----------------------------------------------------
    # Keep only valid supervised ML samples
    # -----------------------------------------------------

    print_section("3. CREATE COMPLETE ML SAMPLES")

    required_columns = (
        FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    complete_mask = (
        df[required_columns]
        .notna()
        .all(axis=1)
    )

    ml = (
        df.loc[complete_mask]
        .copy()
        .sort_values("target_timestamp_utc")
        .reset_index(drop=True)
    )

    total_input_rows = len(df)
    complete_rows = len(ml)
    removed_incomplete = (
        total_input_rows - complete_rows
    )

    print(
        f"Input timeline rows:       "
        f"{total_input_rows:,}"
    )

    print(
        f"Complete ML samples:       "
        f"{complete_rows:,}"
    )

    print(
        f"Incomplete rows excluded:  "
        f"{removed_incomplete:,}"
    )

    if complete_rows == 0:
        raise ValueError(
            "No complete ML samples available."
        )

    # -----------------------------------------------------
    # Chronological 70 / 15 / 15 split
    # -----------------------------------------------------

    print_section("4. CHRONOLOGICAL 70/15/15 SPLIT")

    train_end = int(
        complete_rows * 0.70
    )

    validation_size = int(
        complete_rows * 0.15
    )

    validation_end = (
        train_end + validation_size
    )

    train = ml.iloc[
        :train_end
    ].copy()

    validation = ml.iloc[
        train_end:validation_end
    ].copy()

    test = ml.iloc[
        validation_end:
    ].copy()

    train["split"] = "train"
    validation["split"] = "validation"
    test["split"] = "test"

    split_summary(
        "train",
        train,
    )

    split_summary(
        "validation",
        validation,
    )

    split_summary(
        "test",
        test,
    )

    # -----------------------------------------------------
    # Validate chronological boundaries
    # -----------------------------------------------------

    print_section("5. SPLIT BOUNDARY VALIDATION")

    train_before_validation = (
        train["target_timestamp_utc"].max()
        <
        validation["target_timestamp_utc"].min()
    )

    validation_before_test = (
        validation["target_timestamp_utc"].max()
        <
        test["target_timestamp_utc"].min()
    )

    print(
        "Train targets before validation targets:",
        train_before_validation,
    )

    print(
        "Validation targets before test targets:",
        validation_before_test,
    )

    if not (
        train_before_validation
        and validation_before_test
    ):
        raise ValueError(
            "Chronological split boundaries are invalid."
        )

    # -----------------------------------------------------
    # Combine split labels
    # -----------------------------------------------------

    ml_split = pd.concat(
        [
            train,
            validation,
            test,
        ],
        ignore_index=True,
    )

    ml_split.insert(
        0,
        "sample_id",
        range(
            1,
            len(ml_split) + 1,
        ),
    )

    # -----------------------------------------------------
    # Final checks
    # -----------------------------------------------------

    print_section("6. SPLIT COUNTS")

    counts = (
        ml_split["split"]
        .value_counts()
    )

    print(
        counts.to_string()
    )

    print("\nActual percentages:")

    for split_name in [
        "train",
        "validation",
        "test",
    ]:
        count = int(
            (ml_split["split"] == split_name)
            .sum()
        )

        percent = (
            count
            / len(ml_split)
            * 100
        )

        print(
            f"{split_name}: "
            f"{count:,} "
            f"({percent:.2f}%)"
        )

    # -----------------------------------------------------
    # Save staging ML dataset
    # -----------------------------------------------------

    print_section("7. SAVE SPLIT-READY DATASET")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ml_split.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print(
        "Saved to:"
    )

    print(OUTPUT_FILE)

    # -----------------------------------------------------
    # Save report
    # -----------------------------------------------------

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 10,

        "forecast_target": (
            "PM2.5(t + 1 hour)"
        ),

        "rows": {
            "timeline_input": int(
                total_input_rows
            ),
            "complete_ml_samples": int(
                complete_rows
            ),
            "excluded_incomplete": int(
                removed_incomplete
            ),
        },

        "split": {
            "method": (
                "chronological_no_shuffle"
            ),

            "requested_ratio": {
                "train": 0.70,
                "validation": 0.15,
                "test": 0.15,
            },

            "actual_counts": {
                "train": int(
                    len(train)
                ),
                "validation": int(
                    len(validation)
                ),
                "test": int(
                    len(test)
                ),
            },

            "train": {
                "feature_start": str(
                    train[
                        "timestamp_utc"
                    ].min()
                ),
                "feature_end": str(
                    train[
                        "timestamp_utc"
                    ].max()
                ),
                "target_start": str(
                    train[
                        "target_timestamp_utc"
                    ].min()
                ),
                "target_end": str(
                    train[
                        "target_timestamp_utc"
                    ].max()
                ),
            },

            "validation": {
                "feature_start": str(
                    validation[
                        "timestamp_utc"
                    ].min()
                ),
                "feature_end": str(
                    validation[
                        "timestamp_utc"
                    ].max()
                ),
                "target_start": str(
                    validation[
                        "target_timestamp_utc"
                    ].min()
                ),
                "target_end": str(
                    validation[
                        "target_timestamp_utc"
                    ].max()
                ),
            },

            "test": {
                "feature_start": str(
                    test[
                        "timestamp_utc"
                    ].min()
                ),
                "feature_end": str(
                    test[
                        "timestamp_utc"
                    ].max()
                ),
                "target_start": str(
                    test[
                        "target_timestamp_utc"
                    ].min()
                ),
                "target_end": str(
                    test[
                        "target_timestamp_utc"
                    ].max()
                ),
            },
        },

        "feature_columns": (
            FEATURE_COLUMNS
        ),

        "target_column": (
            TARGET_COLUMN
        ),

        "methodology": {
            "random_shuffle": False,
            "future_target_used_as_feature": False,
            "target_horizon_hours": 1,
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

    print(
        "\nSaved report:"
    )

    print(REPORT_FILE)

    print_section("STEP 10 COMPLETE")

    print(
        "Chronological split completed successfully."
    )


if __name__ == "__main__":
    main()