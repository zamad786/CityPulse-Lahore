import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ML_DATASET_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_multilocation_ml_dataset.csv"
)

STATION_CANDIDATES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "lahore_multilocation_station_candidates.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "citypulse_multilocation_model.joblib"
)

FULL_MODEL_BACKUP_PATH = (
    PROJECT_ROOT
    / "models"
    / "citypulse_multilocation_model_full_reference.joblib"
)

TEMP_MODEL_PATH = (
    PROJECT_ROOT
    / "models"
    / "citypulse_multilocation_model_compact_temp.joblib"
)

REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "compact_deployment_model_report.json"
)


# =========================================================
# STATIONS
# =========================================================

SELECTED_LOCATION_IDS = [
    4757305,
    4527035,
    4527173,
    4515157,
    4609353,
    4618814,
    4568423,
    4555745,
]


# =========================================================
# FEATURES
# =========================================================

BASE_FEATURE_COLUMNS = [
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

    "latitude",
    "longitude",
]


STATION_FEATURE_COLUMNS = [
    f"station_{location_id}"
    for location_id
    in SELECTED_LOCATION_IDS
]


FEATURE_COLUMNS = (
    BASE_FEATURE_COLUMNS
    + STATION_FEATURE_COLUMNS
)


TARGET_COLUMN = (
    "target_pm25_1h"
)


# =========================================================
# DEPLOYMENT REQUIREMENTS
# =========================================================

# Manual GitHub upload should use a comfortably
# small deployment artifact.
MAX_FINAL_MODEL_MB = 24.0

# Selection is based ONLY on validation performance.
# We do not choose hyperparameters using the held-out test.
MAX_VALIDATION_MAE = 9.50
MIN_VALIDATION_R2 = 0.70


# Compact candidates.
# More constrained trees dramatically reduce file size.
CANDIDATES = [
    {
        "name": "compact_rf_80_d18",
        "n_estimators": 80,
        "max_depth": 18,
        "min_samples_leaf": 2,
        "max_features": 0.8,
    },
    {
        "name": "compact_rf_60_d16",
        "n_estimators": 60,
        "max_depth": 16,
        "min_samples_leaf": 2,
        "max_features": 0.8,
    },
    {
        "name": "compact_rf_40_d14",
        "n_estimators": 40,
        "max_depth": 14,
        "min_samples_leaf": 2,
        "max_features": 0.8,
    },
]


# =========================================================
# HELPERS
# =========================================================

def size_mb(
    path: Path,
) -> float:
    return (
        path.stat().st_size
        / 1024
        / 1024
    )


def make_model(
    config: dict,
):
    return RandomForestRegressor(
        n_estimators=
            config[
                "n_estimators"
            ],

        max_depth=
            config[
                "max_depth"
            ],

        min_samples_leaf=
            config[
                "min_samples_leaf"
            ],

        max_features=
            config[
                "max_features"
            ],

        random_state=42,

        n_jobs=-1,
    )


def metrics(
    actual,
    predicted,
):
    return {
        "mae":
            float(
                mean_absolute_error(
                    actual,
                    predicted,
                )
            ),

        "rmse":
            float(
                mean_squared_error(
                    actual,
                    predicted,
                )
                ** 0.5
            ),

        "r2":
            float(
                r2_score(
                    actual,
                    predicted,
                )
            ),
    }


# =========================================================
# VALIDATE INPUT FILES
# =========================================================

print()
print(
    "=============================================="
)
print(
    "CITYPULSE COMPACT DEPLOYMENT MODEL"
)
print(
    "=============================================="
)


if not ML_DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Missing ML dataset:\n"
        f"{ML_DATASET_PATH}"
    )


if not STATION_CANDIDATES_PATH.exists():
    raise FileNotFoundError(
        f"Missing station candidates:\n"
        f"{STATION_CANDIDATES_PATH}"
    )


if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Current multi-location model missing:\n"
        f"{MODEL_PATH}"
    )


original_size = size_mb(
    MODEL_PATH
)


print(
    f"Current deployment model: "
    f"{original_size:.2f} MB"
)


# =========================================================
# LOAD ML DATA
# =========================================================

print()
print(
    "Loading multi-location ML dataset..."
)


df = pd.read_csv(
    ML_DATASET_PATH
)


df[
    "timestamp_utc"
] = pd.to_datetime(
    df[
        "timestamp_utc"
    ],
    utc=True,
)


missing_columns = [
    column
    for column
    in (
        FEATURE_COLUMNS
        + [
            TARGET_COLUMN
        ]
    )
    if column
    not in df.columns
]


if missing_columns:
    raise ValueError(
        "Dataset is missing required columns:\n"
        + "\n".join(
            missing_columns
        )
    )


df = (
    df
    .sort_values(
        [
            "timestamp_utc",
            "location_id",
        ]
    )
    .reset_index(
        drop=True
    )
)


print(
    f"Rows:     {len(df):,}"
)

print(
    f"Stations: "
    f"{df['location_id'].nunique()}"
)

print(
    f"Features: "
    f"{len(FEATURE_COLUMNS)}"
)


# =========================================================
# SAME CHRONOLOGICAL SPLIT METHODOLOGY
# =========================================================

unique_times = (
    pd.Series(
        df[
            "timestamp_utc"
        ].unique()
    )
    .sort_values()
    .reset_index(
        drop=True
    )
)


train_cut_index = int(
    len(unique_times)
    * 0.70
)


validation_cut_index = int(
    len(unique_times)
    * 0.85
)


train_end = (
    unique_times.iloc[
        train_cut_index - 1
    ]
)


validation_end = (
    unique_times.iloc[
        validation_cut_index - 1
    ]
)


train_df = df[
    df[
        "timestamp_utc"
    ]
    <= train_end
].copy()


validation_df = df[
    (
        df[
            "timestamp_utc"
        ]
        > train_end
    )
    &
    (
        df[
            "timestamp_utc"
        ]
        <= validation_end
    )
].copy()


test_df = df[
    df[
        "timestamp_utc"
    ]
    > validation_end
].copy()


print()
print(
    "CHRONOLOGICAL SPLIT"
)

print(
    f"Train:      "
    f"{len(train_df):,}"
)

print(
    f"Validation: "
    f"{len(validation_df):,}"
)

print(
    f"Test:       "
    f"{len(test_df):,}"
)

print(
    f"Train end: "
    f"{train_end}"
)

print(
    f"Validation end: "
    f"{validation_end}"
)


X_train = train_df[
    FEATURE_COLUMNS
]

y_train = train_df[
    TARGET_COLUMN
]


X_validation = validation_df[
    FEATURE_COLUMNS
]

y_validation = validation_df[
    TARGET_COLUMN
]


# =========================================================
# VALIDATION-ONLY MODEL SELECTION
# =========================================================

print()
print(
    "=============================================="
)
print(
    "COMPACT MODEL SEARCH"
)
print(
    "=============================================="
)


candidate_results = []


for config in CANDIDATES:

    print()
    print(
        f"Testing "
        f"{config['name']}..."
    )


    model = make_model(
        config
    )


    started = time.perf_counter()


    model.fit(
        X_train,
        y_train,
    )


    elapsed = (
        time.perf_counter()
        - started
    )


    predictions = model.predict(
        X_validation
    )


    result_metrics = metrics(
        y_validation,
        predictions,
    )


    temp_candidate_path = (
        PROJECT_ROOT
        / "models"
        / (
            f"{config['name']}"
            "_validation.joblib"
        )
    )


    joblib.dump(
        model,
        temp_candidate_path,
        compress=(
            "xz",
            3,
        ),
        protocol=5,
    )


    compressed_size = size_mb(
        temp_candidate_path
    )


    temp_candidate_path.unlink(
        missing_ok=True
    )


    passes_quality = (
        result_metrics[
            "mae"
        ]
        <= MAX_VALIDATION_MAE
        and
        result_metrics[
            "r2"
        ]
        >= MIN_VALIDATION_R2
    )


    candidate_result = {
        **config,

        "validation_mae":
            result_metrics[
                "mae"
            ],

        "validation_rmse":
            result_metrics[
                "rmse"
            ],

        "validation_r2":
            result_metrics[
                "r2"
            ],

        "compressed_validation_model_mb":
            compressed_size,

        "training_seconds":
            elapsed,

        "passes_quality":
            passes_quality,
    }


    candidate_results.append(
        candidate_result
    )


    print(
        f"  MAE:   "
        f"{result_metrics['mae']:.4f}"
    )

    print(
        f"  RMSE:  "
        f"{result_metrics['rmse']:.4f}"
    )

    print(
        f"  R²:    "
        f"{result_metrics['r2']:.4f}"
    )

    print(
        f"  Size:  "
        f"{compressed_size:.2f} MB"
    )

    print(
        f"  Time:  "
        f"{elapsed:.2f}s"
    )

    print(
        "  Quality: "
        + (
            "PASS"
            if passes_quality
            else "FAIL"
        )
    )


# =========================================================
# SELECT USING VALIDATION ONLY
# =========================================================

quality_candidates = [
    result
    for result
    in candidate_results
    if result[
        "passes_quality"
    ]
]


if not quality_candidates:
    print()
    print(
        "COMPACT DEPLOYMENT MODEL: FAIL"
    )

    print(
        "No compact candidate met the "
        "validation-quality requirement."
    )

    print(
        "The existing 620 MB model has NOT "
        "been changed."
    )

    raise SystemExit(1)


# Prefer the smallest passing model,
# then validation MAE as tie-breaker.
selected = min(
    quality_candidates,
    key=lambda item: (
        item[
            "compressed_validation_model_mb"
        ],
        item[
            "validation_mae"
        ],
    ),
)


print()
print(
    "SELECTED ON VALIDATION"
)

print(
    f"Configuration: "
    f"{selected['name']}"
)

print(
    f"Validation MAE: "
    f"{selected['validation_mae']:.4f}"
)

print(
    f"Validation R²: "
    f"{selected['validation_r2']:.4f}"
)


# =========================================================
# HELD-OUT TEST — ONE FINAL EVALUATION
# =========================================================

selected_config = {
    "name":
        selected[
            "name"
        ],

    "n_estimators":
        selected[
            "n_estimators"
        ],

    "max_depth":
        selected[
            "max_depth"
        ],

    "min_samples_leaf":
        selected[
            "min_samples_leaf"
        ],

    "max_features":
        selected[
            "max_features"
        ],
}


train_validation_df = pd.concat(
    [
        train_df,
        validation_df,
    ],
    ignore_index=True,
)


evaluation_model = make_model(
    selected_config
)


print()
print(
    "Training selected compact model "
    "on train + validation..."
)


evaluation_model.fit(
    train_validation_df[
        FEATURE_COLUMNS
    ],
    train_validation_df[
        TARGET_COLUMN
    ],
)


test_predictions = (
    evaluation_model.predict(
        test_df[
            FEATURE_COLUMNS
        ]
    )
)


test_metrics = metrics(
    test_df[
        TARGET_COLUMN
    ],
    test_predictions,
)


print()
print(
    "=============================================="
)
print(
    "COMPACT MODEL HELD-OUT TEST"
)
print(
    "=============================================="
)

print(
    f"MAE:  "
    f"{test_metrics['mae']:.4f} µg/m³"
)

print(
    f"RMSE: "
    f"{test_metrics['rmse']:.4f} µg/m³"
)

print(
    f"R²:   "
    f"{test_metrics['r2']:.4f}"
)


# =========================================================
# FINAL DEPLOYMENT MODEL ON ALL LABELLED DATA
# =========================================================

print()
print(
    "Training final compact deployment model "
    "on all labelled samples..."
)


deployment_model = make_model(
    selected_config
)


deployment_model.fit(
    df[
        FEATURE_COLUMNS
    ],
    df[
        TARGET_COLUMN
    ],
)


# =========================================================
# STATION METADATA
# =========================================================

station_candidates = pd.read_csv(
    STATION_CANDIDATES_PATH
)


stations = []


for location_id in (
    SELECTED_LOCATION_IDS
):

    rows = station_candidates[
        station_candidates[
            "location_id"
        ].astype(int)
        == int(
            location_id
        )
    ]


    if rows.empty:
        raise ValueError(
            f"Missing metadata for "
            f"location {location_id}"
        )


    row = rows.iloc[0]


    stations.append(
        {
            "location_id":
                int(
                    row[
                        "location_id"
                    ]
                ),

            "sensor_id":
                int(
                    row[
                        "sensor_id"
                    ]
                ),

            "name":
                str(
                    row[
                        "location_name"
                    ]
                ).strip(),

            "latitude":
                float(
                    row[
                        "latitude"
                    ]
                ),

            "longitude":
                float(
                    row[
                        "longitude"
                    ]
                ),

            "provider":
                str(
                    row[
                        "provider"
                    ]
                ),
        }
    )


# =========================================================
# SAVE COMPACT BUNDLE
# =========================================================

bundle = {
    "model":
        deployment_model,

    "model_name":
        "RandomForestRegressor",

    "model_type":
        "compact station-aware pooled model",

    "deployment_profile":
        selected[
            "name"
        ],

    "feature_columns":
        FEATURE_COLUMNS,

    "target_column":
        TARGET_COLUMN,

    "forecast_horizon_hours":
        1,

    "stations":
        stations,

    "validation_metrics": {
        "mae":
            selected[
                "validation_mae"
            ],

        "rmse":
            selected[
                "validation_rmse"
            ],

        "r2":
            selected[
                "validation_r2"
            ],
    },

    "held_out_test_metrics":
        test_metrics,

    "methodology": (
        "Compact station-aware Random Forest. "
        "PM2.5 lag and rolling features are "
        "calculated independently for each "
        "monitoring station. Model selection "
        "used chronological validation data. "
        "The held-out test period was evaluated "
        "only after selecting the compact "
        "deployment configuration."
    ),
}


TEMP_MODEL_PATH.unlink(
    missing_ok=True
)


joblib.dump(
    bundle,
    TEMP_MODEL_PATH,
    compress=(
        "xz",
        6,
    ),
    protocol=5,
)


final_size = size_mb(
    TEMP_MODEL_PATH
)


# Try maximum XZ compression if needed.
if final_size > MAX_FINAL_MODEL_MB:

    print()
    print(
        f"First compressed artifact: "
        f"{final_size:.2f} MB"
    )

    print(
        "Trying stronger compression..."
    )


    TEMP_MODEL_PATH.unlink(
        missing_ok=True
    )


    joblib.dump(
        bundle,
        TEMP_MODEL_PATH,
        compress=(
            "xz",
            9,
        ),
        protocol=5,
    )


    final_size = size_mb(
        TEMP_MODEL_PATH
    )


print()
print(
    f"Final compressed size: "
    f"{final_size:.2f} MB"
)


# =========================================================
# ONLY REPLACE CURRENT MODEL IF DEPLOYABLE
# =========================================================

if final_size > MAX_FINAL_MODEL_MB:

    print()
    print(
        "COMPACT DEPLOYMENT MODEL: FAIL"
    )

    print(
        f"Artifact is still "
        f"{final_size:.2f} MB."
    )

    print(
        "Existing model has NOT been replaced."
    )


    TEMP_MODEL_PATH.unlink(
        missing_ok=True
    )


    raise SystemExit(1)


# Keep original 620 MB reference model locally.
if not FULL_MODEL_BACKUP_PATH.exists():

    shutil.move(
        str(
            MODEL_PATH
        ),
        str(
            FULL_MODEL_BACKUP_PATH
        ),
    )

else:

    MODEL_PATH.unlink(
        missing_ok=True
    )


shutil.move(
    str(
        TEMP_MODEL_PATH
    ),
    str(
        MODEL_PATH
    ),
)


# =========================================================
# REPORT
# =========================================================

report = {
    "generated_at_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "status":
        "PASS",

    "original_model_size_mb":
        original_size,

    "compact_model_size_mb":
        final_size,

    "selected_configuration":
        selected_config,

    "candidate_validation_results":
        candidate_results,

    "compact_held_out_test_metrics":
        test_metrics,

    "supported_station_count":
        len(
            stations
        ),

    "deployment_model":
        str(
            MODEL_PATH
        ),

    "full_reference_model":
        str(
            FULL_MODEL_BACKUP_PATH
        ),
}


REPORT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)


REPORT_PATH.write_text(
    json.dumps(
        report,
        indent=2,
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
    "COMPACT DEPLOYMENT MODEL: PASS"
)
print(
    "=============================================="
)

print(
    f"Selected: "
    f"{selected['name']}"
)

print(
    f"Old size: "
    f"{original_size:.2f} MB"
)

print(
    f"New size: "
    f"{final_size:.2f} MB"
)

print()
print(
    "Compact held-out performance:"
)

print(
    f"MAE:  "
    f"{test_metrics['mae']:.4f}"
)

print(
    f"RMSE: "
    f"{test_metrics['rmse']:.4f}"
)

print(
    f"R²:   "
    f"{test_metrics['r2']:.4f}"
)

print()
print(
    "Deployment model:"
)
print(
    MODEL_PATH
)

print()
print(
    "Full 620 MB reference model retained locally:"
)
print(
    FULL_MODEL_BACKUP_PATH
)

print()
print(
    "NEXT: re-run final API QA."
)