import json
import shutil
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_ml_split_ready.csv"
)

FINAL_DATASET_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_ml_dataset.csv"
)

SPLIT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "splits"
)

TRAIN_FILE = (
    SPLIT_DIR
    / "citypulse_train.csv"
)

VALIDATION_FILE = (
    SPLIT_DIR
    / "citypulse_validation.csv"
)

TEST_FILE = (
    SPLIT_DIR
    / "citypulse_test.csv"
)

FEATURE_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_feature_columns.json"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_final_validation_summary.json"
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


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 11 FINAL ML DATASET"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Split-ready dataset not found:\n{INPUT_FILE}"
        )

    # -----------------------------------------------------
    # Load
    # -----------------------------------------------------

    df = pd.read_csv(INPUT_FILE)

    print_section("1. LOAD ML DATASET")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

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

    # -----------------------------------------------------
    # Required schema
    # -----------------------------------------------------

    print_section("2. REQUIRED SCHEMA")

    required_columns = (
        [
            "sample_id",
            "timestamp_utc",
            "target_timestamp_utc",
            "split",
        ]
        + FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    print(
        "Missing columns:",
        (
            "None"
            if not missing_columns
            else missing_columns
        ),
    )

    if missing_columns:
        raise ValueError(
            "Required ML columns are missing."
        )

    # -----------------------------------------------------
    # Missing values
    # -----------------------------------------------------

    print_section("3. FEATURE + TARGET COMPLETENESS")

    missing_required = (
        df[
            FEATURE_COLUMNS
            + [TARGET_COLUMN]
        ]
        .isna()
        .sum()
    )

    print(
        missing_required.to_string()
    )

    total_missing = int(
        missing_required.sum()
    )

    print(
        f"\nTotal missing feature/target values: "
        f"{total_missing:,}"
    )

    if total_missing > 0:
        raise ValueError(
            "Final ML dataset still has missing "
            "feature or target values."
        )

    # -----------------------------------------------------
    # IDs and timestamps
    # -----------------------------------------------------

    print_section("4. SAMPLE INTEGRITY")

    duplicate_sample_ids = int(
        df["sample_id"]
        .duplicated()
        .sum()
    )

    duplicate_feature_times = int(
        df["timestamp_utc"]
        .duplicated()
        .sum()
    )

    duplicate_target_times = int(
        df["target_timestamp_utc"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate sample IDs:      "
        f"{duplicate_sample_ids:,}"
    )

    print(
        f"Duplicate feature times:   "
        f"{duplicate_feature_times:,}"
    )

    print(
        f"Duplicate target times:    "
        f"{duplicate_target_times:,}"
    )

    if (
        duplicate_sample_ids > 0
        or duplicate_feature_times > 0
        or duplicate_target_times > 0
    ):
        raise ValueError(
            "Duplicate ML samples detected."
        )

    # -----------------------------------------------------
    # Forecast-horizon check
    # -----------------------------------------------------

    print_section("5. TARGET HORIZON VALIDATION")

    expected_target = (
        df["timestamp_utc"]
        + pd.Timedelta(hours=1)
    )

    invalid_horizon = int(
        (
            expected_target
            != df["target_timestamp_utc"]
        ).sum()
    )

    print(
        f"Rows not exactly +1 hour: "
        f"{invalid_horizon:,}"
    )

    if invalid_horizon > 0:
        raise ValueError(
            "Forecast horizon validation failed."
        )

    # -----------------------------------------------------
    # Split validation
    # -----------------------------------------------------

    print_section("6. SPLIT VALIDATION")

    valid_split_names = {
        "train",
        "validation",
        "test",
    }

    actual_split_names = set(
        df["split"]
        .dropna()
        .unique()
    )

    print(
        "Split names:",
        sorted(actual_split_names),
    )

    if (
        actual_split_names
        != valid_split_names
    ):
        raise ValueError(
            "Unexpected split names detected."
        )

    train = (
        df[
            df["split"] == "train"
        ]
        .copy()
    )

    validation = (
        df[
            df["split"] == "validation"
        ]
        .copy()
    )

    test = (
        df[
            df["split"] == "test"
        ]
        .copy()
    )

    print(
        f"Train rows:      {len(train):,}"
    )

    print(
        f"Validation rows: {len(validation):,}"
    )

    print(
        f"Test rows:       {len(test):,}"
    )

    if (
        len(train)
        + len(validation)
        + len(test)
        != len(df)
    ):
        raise ValueError(
            "Split row counts do not sum "
            "to final dataset size."
        )

    # -----------------------------------------------------
    # Chronological ordering
    # -----------------------------------------------------

    print_section("7. CHRONOLOGICAL LEAKAGE CHECK")

    train_end = (
        train["target_timestamp_utc"].max()
    )

    validation_start = (
        validation[
            "target_timestamp_utc"
        ].min()
    )

    validation_end = (
        validation[
            "target_timestamp_utc"
        ].max()
    )

    test_start = (
        test[
            "target_timestamp_utc"
        ].min()
    )

    print(
        "Train final target:      ",
        train_end,
    )

    print(
        "Validation first target: ",
        validation_start,
    )

    print(
        "Validation final target: ",
        validation_end,
    )

    print(
        "Test first target:       ",
        test_start,
    )

    train_before_validation = (
        train_end < validation_start
    )

    validation_before_test = (
        validation_end < test_start
    )

    print(
        "\nTrain before validation:",
        train_before_validation,
    )

    print(
        "Validation before test:",
        validation_before_test,
    )

    if not (
        train_before_validation
        and validation_before_test
    ):
        raise ValueError(
            "Chronological split leakage detected."
        )

    # -----------------------------------------------------
    # Target summary
    # -----------------------------------------------------

    print_section("8. TARGET SUMMARY")

    print(
        df[TARGET_COLUMN]
        .describe()
        .to_string()
    )

    # -----------------------------------------------------
    # Save canonical ML dataset
    # -----------------------------------------------------

    print_section("9. SAVE FINAL DATASETS")

    FINAL_DATASET_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    SPLIT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        FINAL_DATASET_FILE,
        index=False,
        encoding="utf-8",
    )

    train.to_csv(
        TRAIN_FILE,
        index=False,
        encoding="utf-8",
    )

    validation.to_csv(
        VALIDATION_FILE,
        index=False,
        encoding="utf-8",
    )

    test.to_csv(
        TEST_FILE,
        index=False,
        encoding="utf-8",
    )

    print(
        "Final ML dataset:"
    )

    print(
        FINAL_DATASET_FILE
    )

    print(
        "\nTrain split:"
    )

    print(
        TRAIN_FILE
    )

    print(
        "\nValidation split:"
    )

    print(
        VALIDATION_FILE
    )

    print(
        "\nTest split:"
    )

    print(
        TEST_FILE
    )

    # -----------------------------------------------------
    # Save feature manifest
    # -----------------------------------------------------

    print_section("10. SAVE FEATURE MANIFEST")

    feature_manifest = {
        "project": "CityPulse Lahore",

        "prediction_target": (
            "PM2.5(t + 1 hour)"
        ),

        "target_column": (
            TARGET_COLUMN
        ),

        "feature_count": int(
            len(FEATURE_COLUMNS)
        ),

        "features": (
            FEATURE_COLUMNS
        ),

        "split_method": (
            "chronological 70/15/15"
        ),

        "random_shuffle": False,
    }

    FEATURE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        FEATURE_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            feature_manifest,
            file,
            indent=2,
        )

    print(
        FEATURE_FILE
    )

    # -----------------------------------------------------
    # Save final Day 2 report
    # -----------------------------------------------------

    report = {
        "project": "CityPulse Lahore",
        "day": 2,

        "status": "PASS",

        "forecast_target": (
            "PM2.5(t + 1 hour)"
        ),

        "dataset": {
            "rows": int(
                len(df)
            ),
            "feature_count": int(
                len(FEATURE_COLUMNS)
            ),
            "missing_feature_target_values": (
                total_missing
            ),
        },

        "splits": {
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

        "validation": {
            "duplicate_sample_ids": (
                duplicate_sample_ids
            ),
            "duplicate_feature_timestamps": (
                duplicate_feature_times
            ),
            "duplicate_target_timestamps": (
                duplicate_target_times
            ),
            "invalid_forecast_horizon_rows": (
                invalid_horizon
            ),
            "train_before_validation": (
                bool(
                    train_before_validation
                )
            ),
            "validation_before_test": (
                bool(
                    validation_before_test
                )
            ),
        },

        "files": {
            "ml_dataset": str(
                FINAL_DATASET_FILE
            ),
            "train": str(
                TRAIN_FILE
            ),
            "validation": str(
                VALIDATION_FILE
            ),
            "test": str(
                TEST_FILE
            ),
            "feature_manifest": str(
                FEATURE_FILE
            ),
        },
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
        )

    print_section("11. FINAL DAY 2 RESULT")

    print(
        "DAY 2 ML DATASET VALIDATION: PASS"
    )

    print(
        "\nThe dataset is ready for "
        "Day 3 model training."
    )

    print(
        "\nFinal validation report:"
    )

    print(
        REPORT_FILE
    )


if __name__ == "__main__":
    main()