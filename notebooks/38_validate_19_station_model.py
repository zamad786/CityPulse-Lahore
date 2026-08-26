import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "citypulse_multilocation_model_19station.joblib"
)

LATEST_FEATURES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_19station_latest_features.csv"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "19station_artifact_validation.json"
)

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "reports"
    / "19station_latest_predictions.csv"
)


# =========================================================
# EXPECTATIONS
# =========================================================

EXPECTED_STATIONS = 19
EXPECTED_FEATURES = 42
EXPECTED_HORIZON = 1

HARD_MODEL_LIMIT_MB = 50.0


def check(condition, label):
    if not condition:
        raise RuntimeError(
            f"{label}: FAIL"
        )

    print(
        f"{label}: PASS"
    )


# =========================================================
# START
# =========================================================

print()
print(
    "=============================================="
)
print(
    "CITYPULSE 19-STATION ARTIFACT VALIDATION"
)
print(
    "=============================================="
)


# =========================================================
# FILE CHECKS
# =========================================================

check(
    MODEL_PATH.exists(),
    "MODEL FILE"
)

check(
    LATEST_FEATURES_PATH.exists(),
    "LATEST FEATURES FILE"
)


model_size_mb = (
    MODEL_PATH.stat().st_size
    / 1024
    / 1024
)


print(
    f"\nModel size: "
    f"{model_size_mb:.2f} MB"
)


check(
    model_size_mb
    < HARD_MODEL_LIMIT_MB,
    "MODEL SIZE"
)


# =========================================================
# LOAD MODEL
# =========================================================

bundle = joblib.load(
    MODEL_PATH
)


required_bundle_keys = [
    "model",
    "model_name",
    "model_type",
    "deployment_profile",
    "feature_columns",
    "target_column",
    "forecast_horizon_hours",
    "stations",
    "validation_metrics",
    "held_out_test_metrics",
]


for key in required_bundle_keys:

    check(
        key in bundle,
        f"BUNDLE KEY {key}"
    )


model = bundle[
    "model"
]


feature_columns = bundle[
    "feature_columns"
]


stations = bundle[
    "stations"
]


# =========================================================
# MODEL METADATA
# =========================================================

check(
    len(stations)
    == EXPECTED_STATIONS,
    "STATION COUNT"
)


check(
    len(feature_columns)
    == EXPECTED_FEATURES,
    "FEATURE COUNT"
)


check(
    bundle[
        "forecast_horizon_hours"
    ]
    == EXPECTED_HORIZON,
    "FORECAST HORIZON"
)


print()
print(
    f"Model:       "
    f"{bundle['model_name']}"
)

print(
    f"Type:        "
    f"{bundle['model_type']}"
)

print(
    f"Profile:     "
    f"{bundle['deployment_profile']}"
)

print(
    f"Horizon:     "
    f"+{bundle['forecast_horizon_hours']} hour"
)


# =========================================================
# LOAD LATEST FEATURES
# =========================================================

latest = pd.read_csv(
    LATEST_FEATURES_PATH
)


check(
    latest[
        "location_id"
    ].nunique()
    == EXPECTED_STATIONS,
    "LATEST FEATURE STATION COUNT"
)


missing_features = [
    column
    for column
    in feature_columns
    if column not in latest.columns
]


check(
    len(missing_features)
    == 0,
    "FEATURE COLUMN MATCH"
)


# =========================================================
# STATION ID MATCH
# =========================================================

bundle_station_ids = {
    int(
        station[
            "location_id"
        ]
    )
    for station
    in stations
}


feature_station_ids = set(
    latest[
        "location_id"
    ]
    .astype(int)
)


check(
    bundle_station_ids
    == feature_station_ids,
    "STATION ID MATCH"
)


# =========================================================
# FEATURE QUALITY
# =========================================================

X = latest[
    feature_columns
].copy()


check(
    not X.isna().any().any(),
    "NO MISSING INFERENCE FEATURES"
)


numeric_values = (
    X.to_numpy(
        dtype=float
    )
)


check(
    np.isfinite(
        numeric_values
    ).all(),
    "FINITE INFERENCE FEATURES"
)


# =========================================================
# INFERENCE TEST
# =========================================================

predictions = model.predict(
    X
)


check(
    len(predictions)
    == EXPECTED_STATIONS,
    "PREDICTION COUNT"
)


check(
    np.isfinite(
        predictions
    ).all(),
    "FINITE PREDICTIONS"
)


check(
    (
        predictions
        >= 0
    ).all(),
    "NON-NEGATIVE PREDICTIONS"
)


# =========================================================
# PREDICTION OUTPUT
# =========================================================

prediction_df = pd.DataFrame(
    {
        "location_id":
            latest[
                "location_id"
            ].astype(int),

        "location_name":
            latest[
                "location_name"
            ],

        "timestamp_utc":
            latest[
                "timestamp_utc"
            ],

        "measured_pm25":
            latest[
                "pm25_ug_m3"
            ],

        "predicted_pm25_1h":
            np.round(
                predictions,
                2,
            ),
    }
)


prediction_df = (
    prediction_df
    .sort_values(
        "location_name"
    )
    .reset_index(
        drop=True
    )
)


prediction_df.to_csv(
    PREDICTIONS_PATH,
    index=False,
)


print()
print(
    "=============================================="
)

print(
    "LATEST 19-STATION PREDICTIONS"
)

print(
    "=============================================="
)


print(
    prediction_df.to_string(
        index=False
    )
)


# =========================================================
# METRICS
# =========================================================

validation_metrics = bundle[
    "validation_metrics"
]


test_metrics = bundle[
    "held_out_test_metrics"
]


print()
print(
    "=============================================="
)

print(
    "MODEL METRICS"
)

print(
    "=============================================="
)


print(
    f"Validation MAE:  "
    f"{validation_metrics['mae']:.4f}"
)

print(
    f"Validation RMSE: "
    f"{validation_metrics['rmse']:.4f}"
)

print(
    f"Validation R²:   "
    f"{validation_metrics['r2']:.4f}"
)


print()

print(
    f"Test MAE:        "
    f"{test_metrics['mae']:.4f}"
)

print(
    f"Test RMSE:       "
    f"{test_metrics['rmse']:.4f}"
)

print(
    f"Test R²:         "
    f"{test_metrics['r2']:.4f}"
)


# =========================================================
# SPATIAL COVERAGE
# =========================================================

spatial = (
    bundle.get(
        "spatial_coverage"
    )
    or {}
)


coverage_pct = (
    spatial.get(
        "coverage_pct"
    )
)


coverage_radius = (
    spatial.get(
        "coverage_radius_km"
    )
)


if coverage_pct is not None:

    print()
    print(
        "=============================================="
    )

    print(
        "SPATIAL COVERAGE"
    )

    print(
        "=============================================="
    )


    print(
        f"Coverage radius: "
        f"{coverage_radius:.2f} km"
    )

    print(
        f"Coverage:        "
        f"{coverage_pct:.2f}%"
    )


# =========================================================
# SAVE VALIDATION REPORT
# =========================================================

report = {
    "status":
        "PASS",

    "station_count":
        len(
            stations
        ),

    "feature_count":
        len(
            feature_columns
        ),

    "forecast_horizon_hours":
        bundle[
            "forecast_horizon_hours"
        ],

    "deployment_profile":
        bundle[
            "deployment_profile"
        ],

    "model_size_mb":
        model_size_mb,

    "validation_metrics":
        validation_metrics,

    "held_out_test_metrics":
        test_metrics,

    "spatial_coverage":
        spatial,

    "prediction_count":
        len(
            predictions
        ),

    "prediction_file":
        str(
            PREDICTIONS_PATH
        ),
}


REPORT_PATH.write_text(
    json.dumps(
        report,
        indent=2,
        ensure_ascii=False,
        default=str,
    ),
    encoding="utf-8",
)


# =========================================================
# FINAL
# =========================================================

print()
print(
    "=============================================="
)

print(
    "19-STATION ARTIFACT VALIDATION: PASS"
)

print(
    "=============================================="
)


print(
    f"Model size: "
    f"{model_size_mb:.2f} MB"
)


print(
    f"Stations:   "
    f"{len(stations)}"
)


print(
    f"Features:   "
    f"{len(feature_columns)}"
)


print()
print(
    f"Report:"
    f"\n{REPORT_PATH}"
)


print()
print(
    f"Predictions:"
    f"\n{PREDICTIONS_PATH}"
)
