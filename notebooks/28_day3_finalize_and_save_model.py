import json
import time
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
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

TEST_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "splits"
    / "citypulse_test.csv"
)

SELECTION_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day3_model_selection.json"
)

MODEL_FILE = (
    PROJECT_ROOT
    / "models"
    / "citypulse_pm25_model.joblib"
)

TEST_PREDICTIONS_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day3_final_test_predictions.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day3_final_model_report.json"
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


MODEL_PARAMETERS = {
    "n_estimators": 300,
    "max_depth": None,
    "min_samples_leaf": 2,
    "max_features": 0.8,
    "random_state": 42,
    "n_jobs": -1,
}


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


def build_model():
    return RandomForestRegressor(
        **MODEL_PARAMETERS
    )


def main():
    print_section(
        "CITYPULSE LAHORE — "
        "DAY 3 STEP 9 FINAL MODEL"
    )

    # =====================================================
    # Validate inputs
    # =====================================================

    required_files = [
        TRAIN_FILE,
        VALIDATION_FILE,
        TEST_FILE,
        SELECTION_FILE,
    ]

    for file_path in required_files:

        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file missing:\n{file_path}"
            )

    # =====================================================
    # Confirm selected model
    # =====================================================

    print_section("1. CONFIRM MODEL SELECTION")

    with open(
        SELECTION_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        selection = json.load(file)

    selected_model = selection[
        "selected_model"
    ]

    print(
        f"Selected model: "
        f"{selected_model}"
    )

    if (
        selected_model
        != "RandomForestRegressor"
    ):
        raise ValueError(
            "This finalization script expects "
            "RandomForestRegressor to be the "
            "selected model."
        )

    # =====================================================
    # Load splits
    # =====================================================

    print_section("2. LOAD CHRONOLOGICAL SPLITS")

    train = pd.read_csv(
        TRAIN_FILE
    )

    validation = pd.read_csv(
        VALIDATION_FILE
    )

    test = pd.read_csv(
        TEST_FILE
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

    required_columns = (
        FEATURE_COLUMNS
        + [TARGET_COLUMN]
    )

    for name, dataframe in [
        ("train", train),
        ("validation", validation),
        ("test", test),
    ]:

        missing = int(
            dataframe[
                required_columns
            ]
            .isna()
            .sum()
            .sum()
        )

        print(
            f"{name} missing values: "
            f"{missing:,}"
        )

        if missing > 0:
            raise ValueError(
                f"{name} contains missing "
                "feature/target values."
            )

    # =====================================================
    # Train evaluation model
    # =====================================================

    print_section(
        "3. TRAIN EVALUATION MODEL "
        "ON TRAIN + VALIDATION"
    )

    development = pd.concat(
        [
            train,
            validation,
        ],
        ignore_index=True,
    )

    X_development = development[
        FEATURE_COLUMNS
    ]

    y_development = development[
        TARGET_COLUMN
    ]

    X_test = test[
        FEATURE_COLUMNS
    ]

    y_test = test[
        TARGET_COLUMN
    ]

    evaluation_model = build_model()

    start_time = time.perf_counter()

    evaluation_model.fit(
        X_development,
        y_development,
    )

    evaluation_training_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Development rows: "
        f"{len(development):,}"
    )

    print(
        f"Training time: "
        f"{evaluation_training_time:.4f} s"
    )

    # =====================================================
    # Final test evaluation
    # =====================================================

    print_section("4. FINAL UNTOUCHED TEST EVALUATION")

    predictions = (
        evaluation_model.predict(
            X_test
        )
    )

    test_metrics = calculate_metrics(
        y_test,
        predictions,
    )

    print(
        f"TEST MAE:  "
        f"{test_metrics['mae']:.4f}"
    )

    print(
        f"TEST RMSE: "
        f"{test_metrics['rmse']:.4f}"
    )

    print(
        f"TEST R²:   "
        f"{test_metrics['r2']:.4f}"
    )

    print(
        "\nThese are the final held-out "
        "test metrics."
    )

    # =====================================================
    # Save test predictions
    # =====================================================

    print_section("5. SAVE TEST PREDICTIONS")

    test_predictions = test[
        [
            "timestamp_utc",
            "target_timestamp_utc",
            TARGET_COLUMN,
        ]
    ].copy()

    test_predictions[
        "predicted_pm25_1h"
    ] = predictions

    test_predictions[
        "absolute_error"
    ] = (
        test_predictions[
            TARGET_COLUMN
        ]
        - test_predictions[
            "predicted_pm25_1h"
        ]
    ).abs()

    test_predictions.to_csv(
        TEST_PREDICTIONS_FILE,
        index=False,
    )

    print(
        TEST_PREDICTIONS_FILE
    )

    # =====================================================
    # Refit deployment model on ALL data
    # =====================================================

    print_section(
        "6. REFIT DEPLOYMENT MODEL "
        "ON ALL LABELLED DATA"
    )

    all_data = pd.concat(
        [
            train,
            validation,
            test,
        ],
        ignore_index=True,
    )

    X_all = all_data[
        FEATURE_COLUMNS
    ]

    y_all = all_data[
        TARGET_COLUMN
    ]

    deployment_model = build_model()

    start_time = time.perf_counter()

    deployment_model.fit(
        X_all,
        y_all,
    )

    deployment_training_time = (
        time.perf_counter()
        - start_time
    )

    print(
        f"Deployment training rows: "
        f"{len(all_data):,}"
    )

    print(
        f"Training time: "
        f"{deployment_training_time:.4f} s"
    )

    # =====================================================
    # Save model bundle
    # =====================================================

    print_section("7. SAVE MODEL BUNDLE")

    MODEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_bundle = {
        "model": deployment_model,

        "model_name": (
            "RandomForestRegressor"
        ),

        "feature_columns": (
            FEATURE_COLUMNS
        ),

        "target_column": (
            TARGET_COLUMN
        ),

        "forecast_horizon_hours": 1,

        "model_parameters": (
            MODEL_PARAMETERS
        ),

        "validation_metrics": (
            selection[
                "selected_validation_metrics"
            ]
        ),

        "held_out_test_metrics": (
            test_metrics
        ),

        "deployment_training_rows": int(
            len(all_data)
        ),

        "methodology": {
            "model_selected_using": (
                "validation set"
            ),

            "test_used_for_selection": False,

            "test_evaluated_once": True,

            "deployment_refit_after_test_evaluation": True,

            "pm25_imputation": False,
        },
    }

    joblib.dump(
        model_bundle,
        MODEL_FILE,
    )

    print(
        f"Model saved to:\n{MODEL_FILE}"
    )

    # =====================================================
    # Reload integrity check
    # =====================================================

    print_section("8. MODEL RELOAD TEST")

    loaded_bundle = joblib.load(
        MODEL_FILE
    )

    loaded_model = loaded_bundle[
        "model"
    ]

    sample_prediction = float(
        loaded_model.predict(
            X_all.iloc[[0]]
        )[0]
    )

    print(
        f"Reloaded model: "
        f"{loaded_bundle['model_name']}"
    )

    print(
        f"Sample prediction: "
        f"{sample_prediction:.4f} µg/m³"
    )

    print(
        "Model reload: PASS"
    )

    # =====================================================
    # Save report
    # =====================================================

    report = {
        "project": "CityPulse Lahore",
        "day": 3,
        "step": 9,

        "model": (
            "RandomForestRegressor"
        ),

        "forecast_target": (
            "PM2.5(t + 1 hour)"
        ),

        "model_parameters": (
            MODEL_PARAMETERS
        ),

        "validation_metrics_used_for_selection": (
            selection[
                "selected_validation_metrics"
            ]
        ),

        "held_out_test_metrics": (
            test_metrics
        ),

        "rows": {
            "train": int(
                len(train)
            ),
            "validation": int(
                len(validation)
            ),
            "test": int(
                len(test)
            ),
            "evaluation_training": int(
                len(development)
            ),
            "deployment_training": int(
                len(all_data)
            ),
        },

        "timing": {
            "evaluation_training_seconds": float(
                evaluation_training_time
            ),
            "deployment_training_seconds": float(
                deployment_training_time
            ),
        },

        "files": {
            "model": str(
                MODEL_FILE
            ),
            "test_predictions": str(
                TEST_PREDICTIONS_FILE
            ),
        },

        "methodology": {
            "chronological_split": True,
            "random_shuffle": False,
            "test_used_for_model_selection": False,
            "test_evaluated_once": True,
            "deployment_refit_on_all_data": True,
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

    print_section("STEP 9 COMPLETE")

    print(
        "Final test evaluation complete."
    )

    print(
        "Deployment model saved successfully."
    )

    print(
        f"\nReport:\n{REPORT_FILE}"
    )


if __name__ == "__main__":
    main()