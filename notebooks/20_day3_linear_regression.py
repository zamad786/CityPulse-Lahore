import json
import time
from pathlib import Path

import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "splits"
    / "citypulse_train.csv"
)

VALIDATION_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "splits"
    / "citypulse_validation.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day3_linear_regression_results.json"
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


def calculate_metrics(y_true, y_pred):
    mae = mean_absolute_error(
        y_true,
        y_pred,
    )

    rmse = mean_squared_error(
        y_true,
        y_pred,
    ) ** 0.5

    r2 = r2_score(
        y_true,
        y_pred,
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
    }


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 3 STEP 1 LINEAR REGRESSION"
    )

    # -----------------------------------------------------
    # 1. Validate files
    # -----------------------------------------------------

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Train dataset not found:\n{TRAIN_FILE}"
        )

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(
            f"Validation dataset not found:\n{VALIDATION_FILE}"
        )

    # -----------------------------------------------------
    # 2. Load data
    # -----------------------------------------------------

    print_section("1. LOAD DATA")

    train = pd.read_csv(
        TRAIN_FILE
    )

    validation = pd.read_csv(
        VALIDATION_FILE
    )

    print(
        f"Train rows:      "
        f"{len(train):,}"
    )

    print(
        f"Validation rows: "
        f"{len(validation):,}"
    )

    # -----------------------------------------------------
    # 3. Validate required columns
    # -----------------------------------------------------

    print_section("2. VALIDATE FEATURES")

    required = (
        FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    for name, dataframe in [
        ("train", train),
        ("validation", validation),
    ]:
        missing_columns = [
            column
            for column in required
            if column not in dataframe.columns
        ]

        if missing_columns:
            raise ValueError(
                f"{name} missing columns: "
                f"{missing_columns}"
            )

        missing_values = int(
            dataframe[required]
            .isna()
            .sum()
            .sum()
        )

        print(
            f"{name} missing feature/target values: "
            f"{missing_values:,}"
        )

        if missing_values > 0:
            raise ValueError(
                f"{name} contains missing values."
            )

    print(
        f"\nNumber of model features: "
        f"{len(FEATURE_COLUMNS)}"
    )

    # -----------------------------------------------------
    # 4. Create matrices
    # -----------------------------------------------------

    X_train = train[
        FEATURE_COLUMNS
    ]

    y_train = train[
        TARGET_COLUMN
    ]

    X_validation = validation[
        FEATURE_COLUMNS
    ]

    y_validation = validation[
        TARGET_COLUMN
    ]

    # -----------------------------------------------------
    # 5. Train
    # -----------------------------------------------------

    print_section("3. TRAIN LINEAR REGRESSION")

    model = LinearRegression()

    start_time = time.perf_counter()

    model.fit(
        X_train,
        y_train,
    )

    training_seconds = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Training time: "
        f"{training_seconds:.4f} seconds"
    )

    # -----------------------------------------------------
    # 6. Predict validation
    # -----------------------------------------------------

    print_section("4. VALIDATION PREDICTIONS")

    validation_predictions = (
        model.predict(
            X_validation
        )
    )

    metrics = calculate_metrics(
        y_validation,
        validation_predictions,
    )

    print(
        f"MAE:  "
        f"{metrics['mae']:.4f}"
    )

    print(
        f"RMSE: "
        f"{metrics['rmse']:.4f}"
    )

    print(
        f"R²:   "
        f"{metrics['r2']:.4f}"
    )

    # -----------------------------------------------------
    # 7. Preview predictions
    # -----------------------------------------------------

    print_section("5. PREDICTION PREVIEW")

    preview = validation[
        [
            "timestamp_utc",
            "target_timestamp_utc",
            TARGET_COLUMN,
        ]
    ].copy()

    preview[
        "predicted_pm25_1h"
    ] = validation_predictions

    preview[
        "absolute_error"
    ] = (
        preview[TARGET_COLUMN]
        - preview["predicted_pm25_1h"]
    ).abs()

    print(
        preview
        .head(20)
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # 8. Coefficients
    # -----------------------------------------------------

    print_section("6. LARGEST COEFFICIENTS")

    coefficient_table = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "coefficient": model.coef_,
        }
    )

    coefficient_table[
        "absolute_coefficient"
    ] = (
        coefficient_table[
            "coefficient"
        ]
        .abs()
    )

    coefficient_table = (
        coefficient_table
        .sort_values(
            "absolute_coefficient",
            ascending=False,
        )
    )

    print(
        coefficient_table[
            [
                "feature",
                "coefficient",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # 9. Save results
    # -----------------------------------------------------

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "project": "CityPulse Lahore",
        "day": 3,
        "step": 1,

        "model": (
            "LinearRegression"
        ),

        "target": (
            "PM2.5(t + 1 hour)"
        ),

        "feature_count": int(
            len(FEATURE_COLUMNS)
        ),

        "rows": {
            "train": int(
                len(train)
            ),
            "validation": int(
                len(validation)
            ),
        },

        "validation_metrics": (
            metrics
        ),

        "training_time_seconds": float(
            training_seconds
        ),

        "feature_columns": (
            FEATURE_COLUMNS
        ),
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

    print_section("STEP 1 COMPLETE")

    print(
        "Linear Regression baseline trained."
    )

    print(
        "\nResults saved to:"
    )

    print(REPORT_FILE)

    print(
        "\nIMPORTANT:"
    )

    print(
        "These are validation results, "
        "not final test-set results."
    )


if __name__ == "__main__":
    main()