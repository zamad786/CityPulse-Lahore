import json
import time
from pathlib import Path

import pandas as pd

from sklearn.ensemble import GradientBoostingRegressor
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
    / "day3_gradient_boosting_results.json"
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
    return {
        "mae": float(
            mean_absolute_error(
                y_true,
                y_pred,
            )
        ),
        "rmse": float(
            mean_squared_error(
                y_true,
                y_pred,
            ) ** 0.5
        ),
        "r2": float(
            r2_score(
                y_true,
                y_pred,
            )
        ),
    }


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 3 STEP 3 GRADIENT BOOSTING"
    )

    if not TRAIN_FILE.exists():
        raise FileNotFoundError(
            f"Train file not found:\n{TRAIN_FILE}"
        )

    if not VALIDATION_FILE.exists():
        raise FileNotFoundError(
            f"Validation file not found:\n{VALIDATION_FILE}"
        )

    # =====================================================
    # Load
    # =====================================================

    print_section("1. LOAD DATA")

    train = pd.read_csv(TRAIN_FILE)
    validation = pd.read_csv(
        VALIDATION_FILE
    )

    print(f"Train rows:      {len(train):,}")
    print(f"Validation rows: {len(validation):,}")

    required_columns = (
        FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    for name, dataframe in [
        ("train", train),
        ("validation", validation),
    ]:
        missing = int(
            dataframe[required_columns]
            .isna()
            .sum()
            .sum()
        )

        print(
            f"{name} missing feature/target values: "
            f"{missing:,}"
        )

        if missing > 0:
            raise ValueError(
                f"{name} contains missing values."
            )

    X_train = train[FEATURE_COLUMNS]
    y_train = train[TARGET_COLUMN]

    X_validation = validation[
        FEATURE_COLUMNS
    ]

    y_validation = validation[
        TARGET_COLUMN
    ]

    # =====================================================
    # Train
    # =====================================================

    print_section("2. TRAIN GRADIENT BOOSTING")

    model = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=3,
        min_samples_leaf=3,
        subsample=0.9,
        loss="squared_error",
        random_state=42,
    )

    start_time = time.perf_counter()

    model.fit(
        X_train,
        y_train,
    )

    training_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Training time: "
        f"{training_time:.4f} seconds"
    )

    # =====================================================
    # Validation
    # =====================================================

    print_section("3. VALIDATION RESULTS")

    predictions = model.predict(
        X_validation
    )

    metrics = calculate_metrics(
        y_validation,
        predictions,
    )

    print(
        f"MAE:  {metrics['mae']:.4f}"
    )

    print(
        f"RMSE: {metrics['rmse']:.4f}"
    )

    print(
        f"R²:   {metrics['r2']:.4f}"
    )

    # =====================================================
    # Feature importance
    # =====================================================

    print_section("4. FEATURE IMPORTANCE")

    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance": (
                model.feature_importances_
            ),
        }
    )

    importance = (
        importance
        .sort_values(
            "importance",
            ascending=False,
        )
    )

    print(
        importance
        .head(15)
        .to_string(index=False)
    )

    # =====================================================
    # Preview
    # =====================================================

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
    ] = predictions

    preview[
        "absolute_error"
    ] = (
        preview[TARGET_COLUMN]
        - preview["predicted_pm25_1h"]
    ).abs()

    print(
        preview
        .head(15)
        .to_string(index=False)
    )

    # =====================================================
    # Save
    # =====================================================

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "project": "CityPulse Lahore",
        "day": 3,
        "step": 3,

        "model": (
            "GradientBoostingRegressor"
        ),

        "target": (
            "PM2.5(t + 1 hour)"
        ),

        "parameters": {
            "n_estimators": 300,
            "learning_rate": 0.05,
            "max_depth": 3,
            "min_samples_leaf": 3,
            "subsample": 0.9,
            "random_state": 42,
        },

        "rows": {
            "train": int(len(train)),
            "validation": int(
                len(validation)
            ),
        },

        "validation_metrics": metrics,

        "training_time_seconds": float(
            training_time
        ),

        "feature_importance": {
            row["feature"]: float(
                row["importance"]
            )
            for _, row
            in importance.iterrows()
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

    print_section("STEP 3 COMPLETE")

    print(
        "Gradient Boosting validation complete."
    )

    print(
        "\nResults saved to:"
    )

    print(REPORT_FILE)

    print(
        "\nTest set was NOT used."
    )


if __name__ == "__main__":
    main()