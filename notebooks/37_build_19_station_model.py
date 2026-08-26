import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import requests

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)


SELECTED_STATIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "lahore_spatial_selected_stations.csv"
)


SPATIAL_REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "lahore_spatial_coverage_report.json"
)


RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "multilocation"
)


PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


MODEL_DIR = (
    PROJECT_ROOT
    / "models"
)


REPORT_DIR = (
    PROJECT_ROOT
    / "reports"
)


for directory in [
    RAW_DIR,
    PROCESSED_DIR,
    MODEL_DIR,
    REPORT_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# =========================================================
# VERSIONED OUTPUT FILES
#
# IMPORTANT:
# We intentionally DO NOT overwrite the current deployed
# 8-station model yet.
# =========================================================

TIMELINE_PATH = (
    PROCESSED_DIR
    / "citypulse_19station_hourly.csv"
)


ML_DATASET_PATH = (
    PROCESSED_DIR
    / "citypulse_19station_ml_dataset.csv"
)


LATEST_FEATURES_PATH = (
    PROCESSED_DIR
    / "citypulse_19station_latest_features.csv"
)


MODEL_PATH = (
    MODEL_DIR
    / "citypulse_multilocation_model_19station.joblib"
)


TEMP_MODEL_PATH = (
    MODEL_DIR
    / "citypulse_multilocation_model_19station_temp.joblib"
)


REPORT_PATH = (
    REPORT_DIR
    / "multilocation_19station_model_report.json"
)


STATION_METRICS_PATH = (
    REPORT_DIR
    / "multilocation_19station_station_test_metrics.csv"
)


TEST_PREDICTIONS_PATH = (
    REPORT_DIR
    / "multilocation_19station_test_predictions.csv"
)


# =========================================================
# EXPECTATIONS / DEPLOYMENT LIMITS
# =========================================================

EXPECTED_STATION_COUNT = 19

COVERAGE_RADIUS_KM = 5.0


# We want this comfortably below the Vercel limit.
MODEL_SIZE_TARGET_MB = 25.0

# Do not allow deployment artifact beyond this.
MODEL_SIZE_HARD_LIMIT_MB = 50.0


# =========================================================
# EXTERNAL APIs
# =========================================================

OPENAQ_BASE_URL = (
    "https://api.openaq.org/v3"
)


OPEN_METEO_ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


WEATHER_VARIABLES = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
    "wind_direction_10m",
    "surface_pressure",
]


LAGS = [
    1,
    2,
    3,
    6,
    12,
    24,
]


ROLLING_WINDOWS = [
    3,
    6,
    12,
    24,
]


# =========================================================
# COMPACT RANDOM FOREST CANDIDATES
#
# Model selection uses validation data only.
#
# We do NOT use the held-out test to choose the model.
# =========================================================

MODEL_CANDIDATES = [
    {
        "name":
            "compact_rf_60_d16",

        "n_estimators":
            60,

        "max_depth":
            16,

        "min_samples_leaf":
            2,

        "max_features":
            0.8,
    },

    {
        "name":
            "compact_rf_40_d14",

        "n_estimators":
            40,

        "max_depth":
            14,

        "min_samples_leaf":
            2,

        "max_features":
            0.8,
    },

    {
        "name":
            "compact_rf_30_d12",

        "n_estimators":
            30,

        "max_depth":
            12,

        "min_samples_leaf":
            2,

        "max_features":
            0.8,
    },
]


# =========================================================
# API KEY
#
# Only required while collecting / rebuilding training data.
# It is NOT required by the deployed dashboard runtime.
# =========================================================

def read_api_key():

    key = os.getenv(
        "OPENAQ_API_KEY"
    )


    if key:
        return key


    for env_path in [
        PROJECT_ROOT
        / ".env",

        PROJECT_ROOT
        / "backend"
        / ".env",
    ]:

        if not env_path.exists():
            continue


        for line in env_path.read_text(
            encoding="utf-8"
        ).splitlines():

            line = line.strip()


            if (
                not line
                or line.startswith("#")
                or "=" not in line
            ):
                continue


            name, value = (
                line.split(
                    "=",
                    1,
                )
            )


            if (
                name.strip()
                == "OPENAQ_API_KEY"
            ):

                return (
                    value
                    .strip()
                    .strip("\"'")
                )


    return None


OPENAQ_API_KEY = (
    read_api_key()
)


if not OPENAQ_API_KEY:

    print()
    print(
        "ERROR: OPENAQ_API_KEY missing."
    )

    print()
    print(
        "Set it temporarily in PowerShell:"
    )

    print(
        '$env:OPENAQ_API_KEY="YOUR_KEY"'
    )

    print()
    print(
        "The key is required only for "
        "rebuilding training data."
    )

    sys.exit(1)


OPENAQ_HEADERS = {
    "X-API-Key":
        OPENAQ_API_KEY,
}


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


def request_json(
    url,
    *,
    headers=None,
    params=None,
    retries=3,
):

    last_error = None


    for attempt in range(
        1,
        retries + 1,
    ):

        try:

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=90,
            )


            response.raise_for_status()


            return (
                response.json()
            )


        except Exception as exc:

            last_error = exc


            print(
                f"  Request attempt "
                f"{attempt}/{retries} failed: "
                f"{exc}"
            )


            if attempt < retries:

                time.sleep(
                    attempt
                    * 2
                )


    raise RuntimeError(
        "Request failed after "
        f"{retries} attempts: "
        f"{last_error}"
    )


def parse_openaq_timestamp(
    record,
):

    period = (
        record.get(
            "period"
        )
        or {}
    )


    datetime_from = (
        period.get(
            "datetimeFrom"
        )
        or record.get(
            "datetimeFrom"
        )
        or record.get(
            "datetime"
        )
    )


    if isinstance(
        datetime_from,
        dict,
    ):

        datetime_from = (
            datetime_from.get(
                "utc"
            )
            or datetime_from.get(
                "local"
            )
        )


    return pd.to_datetime(
        datetime_from,
        utc=True,
        errors="coerce",
    )


def make_model(
    config,
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


def calculate_metrics(
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
# LOAD SPATIALLY SELECTED STATIONS
# =========================================================

if not SELECTED_STATIONS_PATH.exists():

    raise FileNotFoundError(
        "Missing spatial station selection:\n"
        f"{SELECTED_STATIONS_PATH}\n\n"
        "Run notebooks/"
        "36_select_spatial_coverage_stations.py "
        "first."
    )


selected = pd.read_csv(
    SELECTED_STATIONS_PATH
)


selected = (
    selected
    .sort_values(
        "selection_order"
    )
    .drop_duplicates(
        subset=[
            "location_id"
        ]
    )
    .reset_index(
        drop=True
    )
)


if len(selected) != (
    EXPECTED_STATION_COUNT
):

    raise ValueError(
        f"Expected "
        f"{EXPECTED_STATION_COUNT} "
        f"stations but received "
        f"{len(selected)}."
    )


SELECTED_LOCATION_IDS = (
    selected[
        "location_id"
    ]
    .astype(int)
    .tolist()
)


selected[
    "sensor_datetime_first_utc"
] = pd.to_datetime(
    selected[
        "sensor_datetime_first_utc"
    ],
    utc=True,
)


selected[
    "sensor_datetime_last_utc"
] = pd.to_datetime(
    selected[
        "sensor_datetime_last_utc"
    ],
    utc=True,
)


# =========================================================
# COMMON TIME RANGE
#
# All stations must share the same chronological range.
# =========================================================

common_start = (
    selected[
        "sensor_datetime_first_utc"
    ]
    .max()
    .ceil(
        "h"
    )
)


common_end = (
    selected[
        "sensor_datetime_last_utc"
    ]
    .min()
    .floor(
        "h"
    )
)


if common_end <= common_start:

    raise ValueError(
        "Invalid common station time range."
    )


print()
print(
    "=============================================="
)

print(
    "CITYPULSE 19-STATION MODEL PIPELINE"
)

print(
    "=============================================="
)

print(
    f"Stations:       "
    f"{len(selected)}"
)

print(
    f"Common start:   "
    f"{common_start}"
)

print(
    f"Common end:     "
    f"{common_end}"
)

print()
print(
    "Selected locations:"
)


for _, station in (
    selected.iterrows()
):

    print(
        f"  "
        f"{int(station['selection_order']):02d} | "
        f"{int(station['location_id'])} | "
        f"{station['location_name']} | "
        f"sensor="
        f"{int(station['sensor_id'])}"
    )


# =========================================================
# DOWNLOAD OPENAQ
# =========================================================

def download_openaq(
    station,
):

    location_id = int(
        station[
            "location_id"
        ]
    )


    sensor_id = int(
        station[
            "sensor_id"
        ]
    )


    output_path = (
        RAW_DIR
        / (
            f"openaq_"
            f"{location_id}"
            "_pm25_hourly.csv"
        )
    )


    if output_path.exists():

        print(
            "  Using cached OpenAQ file."
        )


        df = pd.read_csv(
            output_path
        )


        df[
            "timestamp_utc"
        ] = pd.to_datetime(
            df[
                "timestamp_utc"
            ],
            utc=True,
        )


        # Existing files may contain a wider
        # time range from the previous model.
        df = df[
            (
                df[
                    "timestamp_utc"
                ]
                >= common_start
            )
            &
            (
                df[
                    "timestamp_utc"
                ]
                <= common_end
            )
        ].copy()


        return df


    print(
        "  Downloading OpenAQ hourly PM2.5..."
    )


    rows = []

    page = 1


    while True:

        payload = request_json(
            (
                f"{OPENAQ_BASE_URL}"
                f"/sensors/"
                f"{sensor_id}/hours"
            ),

            headers=
                OPENAQ_HEADERS,

            params={
                "datetime_from":
                    common_start
                    .isoformat(),

                "datetime_to":
                    common_end
                    .isoformat(),

                "limit":
                    1000,

                "page":
                    page,
            },
        )


        results = payload.get(
            "results",
            []
        )


        if not results:
            break


        for record in results:

            timestamp = (
                parse_openaq_timestamp(
                    record
                )
            )


            value = record.get(
                "value"
            )


            if pd.isna(
                timestamp
            ):
                continue


            try:

                value = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):
                continue


            if not np.isfinite(
                value
            ):
                continue


            if value < 0:
                continue


            rows.append(
                {
                    "timestamp_utc":
                        timestamp,

                    "pm25_ug_m3":
                        value,
                }
            )


        print(
            f"    page {page}: "
            f"{len(results)} rows"
        )


        if len(
            results
        ) < 1000:
            break


        page += 1


        time.sleep(
            0.15
        )


    df = pd.DataFrame(
        rows
    )


    if df.empty:

        raise ValueError(
            "No OpenAQ data for "
            f"location {location_id}"
        )


    df = (
        df
        .drop_duplicates(
            subset=[
                "timestamp_utc"
            ],
            keep="last",
        )
        .sort_values(
            "timestamp_utc"
        )
    )


    df = df[
        (
            df[
                "timestamp_utc"
            ]
            >= common_start
        )
        &
        (
            df[
                "timestamp_utc"
            ]
            <= common_end
        )
    ].copy()


    df.to_csv(
        output_path,
        index=False,
    )


    return df


# =========================================================
# DOWNLOAD WEATHER
# =========================================================

def download_weather(
    station,
):

    location_id = int(
        station[
            "location_id"
        ]
    )


    latitude = float(
        station[
            "latitude"
        ]
    )


    longitude = float(
        station[
            "longitude"
        ]
    )


    output_path = (
        RAW_DIR
        / (
            f"openmeteo_"
            f"{location_id}"
            "_weather_hourly.csv"
        )
    )


    if output_path.exists():

        print(
            "  Using cached Open-Meteo file."
        )


        df = pd.read_csv(
            output_path
        )


        df[
            "timestamp_utc"
        ] = pd.to_datetime(
            df[
                "timestamp_utc"
            ],
            utc=True,
        )


        df = df[
            (
                df[
                    "timestamp_utc"
                ]
                >= common_start
            )
            &
            (
                df[
                    "timestamp_utc"
                ]
                <= common_end
            )
        ].copy()


        return df


    print(
        "  Downloading Open-Meteo weather..."
    )


    payload = request_json(
        OPEN_METEO_ARCHIVE_URL,

        params={
            "latitude":
                latitude,

            "longitude":
                longitude,

            "start_date":
                common_start
                .date()
                .isoformat(),

            "end_date":
                common_end
                .date()
                .isoformat(),

            "hourly":
                ",".join(
                    WEATHER_VARIABLES
                ),

            "timezone":
                "UTC",

            "wind_speed_unit":
                "ms",
        },
    )


    hourly = payload.get(
        "hourly"
    )


    if not hourly:

        raise ValueError(
            "Open-Meteo response "
            "missing hourly data for "
            f"{location_id}"
        )


    weather = pd.DataFrame(
        {
            "timestamp_utc":
                pd.to_datetime(
                    hourly[
                        "time"
                    ],
                    utc=True,
                ),

            "temperature_c":
                hourly[
                    "temperature_2m"
                ],

            "relative_humidity_pct":
                hourly[
                    "relative_humidity_2m"
                ],

            "precipitation_mm":
                hourly[
                    "precipitation"
                ],

            "wind_speed_m_s":
                hourly[
                    "wind_speed_10m"
                ],

            "wind_direction_deg":
                hourly[
                    "wind_direction_10m"
                ],

            "surface_pressure_hpa":
                hourly[
                    "surface_pressure"
                ],
        }
    )


    weather = weather[
        (
            weather[
                "timestamp_utc"
            ]
            >= common_start
        )
        &
        (
            weather[
                "timestamp_utc"
            ]
            <= common_end
        )
    ].copy()


    weather.to_csv(
        output_path,
        index=False,
    )


    return weather


# =========================================================
# MODEL FEATURE COLUMNS
# =========================================================

station_dummy_columns = [
    f"station_{location_id}"
    for location_id
    in SELECTED_LOCATION_IDS
]


base_feature_columns = [
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


FEATURE_COLUMNS = (
    base_feature_columns
    + station_dummy_columns
)


TARGET_COLUMN = (
    "target_pm25_1h"
)


print()
print(
    f"Feature count: "
    f"{len(FEATURE_COLUMNS)}"
)


# =========================================================
# BUILD EACH STATION TIMELINE
# =========================================================

all_timelines = []

latest_feature_rows = []


for station_number, (
    _,
    station,
) in enumerate(
    selected.iterrows(),
    start=1,
):


    location_id = int(
        station[
            "location_id"
        ]
    )


    station_name = str(
        station[
            "location_name"
        ]
    ).strip()


    latitude = float(
        station[
            "latitude"
        ]
    )


    longitude = float(
        station[
            "longitude"
        ]
    )


    print()
    print(
        "----------------------------------------------"
    )

    print(
        f"[{station_number}/"
        f"{len(selected)}] "
        f"{station_name}"
    )

    print(
        "----------------------------------------------"
    )


    aq = download_openaq(
        station
    )


    weather = (
        download_weather(
            station
        )
    )


    timeline = pd.DataFrame(
        {
            "timestamp_utc":
                pd.date_range(
                    start=
                        common_start,

                    end=
                        common_end,

                    freq=
                        "h",

                    tz=
                        "UTC",
                )
        }
    )


    timeline = (
        timeline.merge(
            aq,
            how="left",
            on="timestamp_utc",
        )
    )


    timeline = (
        timeline.merge(
            weather,
            how="left",
            on="timestamp_utc",
        )
    )


    timeline[
        "location_id"
    ] = location_id


    timeline[
        "location_name"
    ] = station_name


    timeline[
        "sensor_id"
    ] = int(
        station[
            "sensor_id"
        ]
    )


    timeline[
        "provider"
    ] = station[
        "provider"
    ]


    timeline[
        "latitude"
    ] = latitude


    timeline[
        "longitude"
    ] = longitude


    # -----------------------------------------------------
    # Lahore local-time features
    # -----------------------------------------------------

    local_time = (
        timeline[
            "timestamp_utc"
        ]
        .dt
        .tz_convert(
            "Asia/Karachi"
        )
    )


    timeline[
        "timestamp_lahore"
    ] = local_time


    timeline[
        "hour"
    ] = (
        local_time
        .dt
        .hour
    )


    timeline[
        "day_of_week"
    ] = (
        local_time
        .dt
        .dayofweek
    )


    timeline[
        "month"
    ] = (
        local_time
        .dt
        .month
    )


    timeline[
        "is_weekend"
    ] = (
        local_time
        .dt
        .dayofweek
        .isin(
            [
                5,
                6,
            ]
        )
        .astype(int)
    )


    # -----------------------------------------------------
    # Leakage-safe station-specific lags
    # -----------------------------------------------------

    for lag in LAGS:

        timeline[
            f"pm25_lag_{lag}h"
        ] = (
            timeline[
                "pm25_ug_m3"
            ]
            .shift(
                lag
            )
        )


    # -----------------------------------------------------
    # Rolling means
    #
    # Includes t and previous observations only.
    # Target is t+1, therefore no future leakage.
    # -----------------------------------------------------

    for window in (
        ROLLING_WINDOWS
    ):

        timeline[
            (
                "pm25_rolling_mean_"
                f"{window}h"
            )
        ] = (
            timeline[
                "pm25_ug_m3"
            ]
            .rolling(
                window=
                    window,

                min_periods=
                    window,
            )
            .mean()
        )


    # -----------------------------------------------------
    # Future target
    # -----------------------------------------------------

    timeline[
        TARGET_COLUMN
    ] = (
        timeline[
            "pm25_ug_m3"
        ]
        .shift(
            -1
        )
    )


    timeline[
        "target_timestamp_utc"
    ] = (
        timeline[
            "timestamp_utc"
        ]
        + pd.Timedelta(
            hours=1
        )
    )


    # -----------------------------------------------------
    # Station identity
    # -----------------------------------------------------

    for selected_location_id in (
        SELECTED_LOCATION_IDS
    ):

        column_name = (
            f"station_"
            f"{selected_location_id}"
        )


        timeline[
            column_name
        ] = int(
            location_id
            == selected_location_id
        )


    # -----------------------------------------------------
    # Latest inference-ready feature row
    # -----------------------------------------------------

    feature_ready = (
        timeline
        .dropna(
            subset=
                FEATURE_COLUMNS
        )
    )


    if feature_ready.empty:

        raise ValueError(
            "No complete feature row "
            f"for {station_name}."
        )


    latest_row = (
        feature_ready
        .iloc[-1]
        .copy()
    )


    latest_feature_rows.append(
        latest_row
    )


    coverage_pct = (
        timeline[
            "pm25_ug_m3"
        ]
        .notna()
        .mean()
        * 100
    )


    complete_ml_rows = (
        timeline
        .dropna(
            subset=(
                FEATURE_COLUMNS
                + [
                    TARGET_COLUMN
                ]
            )
        )
    )


    print(
        f"Timeline hours:      "
        f"{len(timeline):,}"
    )


    print(
        f"Observed PM2.5:      "
        f"{timeline['pm25_ug_m3'].notna().sum():,}"
    )


    print(
        f"Coverage:            "
        f"{coverage_pct:.2f}%"
    )


    print(
        f"Complete ML samples: "
        f"{len(complete_ml_rows):,}"
    )


    print(
        f"Latest feature time: "
        f"{latest_row['timestamp_utc']}"
    )


    all_timelines.append(
        timeline
    )


# =========================================================
# COMBINE ALL STATIONS
# =========================================================

combined_timeline = pd.concat(
    all_timelines,
    ignore_index=True,
)


combined_timeline = (
    combined_timeline
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


combined_timeline.to_csv(
    TIMELINE_PATH,
    index=False,
)


ml_df = (
    combined_timeline
    .dropna(
        subset=(
            FEATURE_COLUMNS
            + [
                TARGET_COLUMN
            ]
        )
    )
    .copy()
)


ml_df = (
    ml_df
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


ml_df.to_csv(
    ML_DATASET_PATH,
    index=False,
)


latest_df = pd.DataFrame(
    latest_feature_rows
)


latest_df = (
    latest_df
    .sort_values(
        "location_id"
    )
)


latest_df.to_csv(
    LATEST_FEATURES_PATH,
    index=False,
)


print()
print(
    "=============================================="
)

print(
    "COMBINED 19-STATION DATASET"
)

print(
    "=============================================="
)


print(
    f"Timeline rows:    "
    f"{len(combined_timeline):,}"
)


print(
    f"Complete ML rows: "
    f"{len(ml_df):,}"
)


print(
    f"Stations:         "
    f"{ml_df['location_id'].nunique()}"
)


print(
    f"Features:         "
    f"{len(FEATURE_COLUMNS)}"
)


# =========================================================
# CHRONOLOGICAL SPLIT
# =========================================================

unique_times = (
    pd.Series(
        ml_df[
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
        train_cut_index
        - 1
    ]
)


validation_end = (
    unique_times.iloc[
        validation_cut_index
        - 1
    ]
)


train_df = ml_df[
    ml_df[
        "timestamp_utc"
    ]
    <= train_end
].copy()


validation_df = ml_df[
    (
        ml_df[
            "timestamp_utc"
        ]
        > train_end
    )
    &
    (
        ml_df[
            "timestamp_utc"
        ]
        <= validation_end
    )
].copy()


test_df = ml_df[
    ml_df[
        "timestamp_utc"
    ]
    > validation_end
].copy()


if (
    train_df.empty
    or validation_df.empty
    or test_df.empty
):

    raise ValueError(
        "Chronological split produced "
        "an empty partition."
    )


print()
print(
    "=============================================="
)

print(
    "CHRONOLOGICAL SPLIT"
)

print(
    "=============================================="
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
    f"Train end:      "
    f"{train_end}"
)


print(
    f"Validation end: "
    f"{validation_end}"
)


# =========================================================
# MODEL SELECTION — VALIDATION ONLY
# =========================================================

X_train = (
    train_df[
        FEATURE_COLUMNS
    ]
)


y_train = (
    train_df[
        TARGET_COLUMN
    ]
)


X_validation = (
    validation_df[
        FEATURE_COLUMNS
    ]
)


y_validation = (
    validation_df[
        TARGET_COLUMN
    ]
)


candidate_results = []


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


for config in (
    MODEL_CANDIDATES
):

    print()
    print(
        f"Testing "
        f"{config['name']}..."
    )


    model = make_model(
        config
    )


    started = (
        time.perf_counter()
    )


    model.fit(
        X_train,
        y_train,
    )


    training_seconds = (
        time.perf_counter()
        - started
    )


    predictions = (
        model.predict(
            X_validation
        )
    )


    result_metrics = (
        calculate_metrics(
            y_validation,
            predictions,
        )
    )


    validation_artifact = (
        MODEL_DIR
        / (
            f"{config['name']}"
            "_19station_validation.joblib"
        )
    )


    joblib.dump(
        model,
        validation_artifact,
        compress=(
            "xz",
            3,
        ),
        protocol=5,
    )


    compressed_size = (
        size_mb(
            validation_artifact
        )
    )


    validation_artifact.unlink(
        missing_ok=True
    )


    result = {
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

        "compressed_model_mb":
            compressed_size,

        "training_seconds":
            training_seconds,
    }


    candidate_results.append(
        result
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
        f"{training_seconds:.2f}s"
    )


# =========================================================
# CHOOSE COMPACT MODEL
#
# Allow a model within 3% of best validation MAE and
# within 0.02 R² of the best validation R².
#
# Among those, choose the smallest compressed model.
# =========================================================

best_validation_mae = min(
    result[
        "validation_mae"
    ]
    for result
    in candidate_results
)


best_validation_r2 = max(
    result[
        "validation_r2"
    ]
    for result
    in candidate_results
)


eligible_candidates = [
    result
    for result
    in candidate_results
    if (
        result[
            "validation_mae"
        ]
        <= (
            best_validation_mae
            * 1.03
        )
        and
        result[
            "validation_r2"
        ]
        >= (
            best_validation_r2
            - 0.02
        )
        and
        result[
            "compressed_model_mb"
        ]
        <= MODEL_SIZE_HARD_LIMIT_MB
    )
]


if not eligible_candidates:

    eligible_candidates = [
        min(
            candidate_results,
            key=lambda item:
                item[
                    "validation_mae"
                ],
        )
    ]


selected_config = min(
    eligible_candidates,
    key=lambda item: (
        item[
            "compressed_model_mb"
        ],

        item[
            "validation_mae"
        ],
    ),
)


print()
print(
    "=============================================="
)

print(
    "SELECTED MODEL"
)

print(
    "=============================================="
)


print(
    f"Profile: "
    f"{selected_config['name']}"
)


print(
    f"Validation MAE: "
    f"{selected_config['validation_mae']:.4f}"
)


print(
    f"Validation RMSE: "
    f"{selected_config['validation_rmse']:.4f}"
)


print(
    f"Validation R²: "
    f"{selected_config['validation_r2']:.4f}"
)


print(
    f"Validation artifact size: "
    f"{selected_config['compressed_model_mb']:.2f} MB"
)


# =========================================================
# HELD-OUT TEST
#
# Only now do we evaluate the selected configuration
# against the untouched test period.
# =========================================================

train_validation_df = pd.concat(
    [
        train_df,
        validation_df,
    ],
    ignore_index=True,
)


evaluation_model = (
    make_model(
        selected_config
    )
)


print()
print(
    "Training selected model on "
    "train + validation..."
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


test_metrics = (
    calculate_metrics(
        test_df[
            TARGET_COLUMN
        ],
        test_predictions,
    )
)


print()
print(
    "=============================================="
)

print(
    "19-STATION HELD-OUT TEST"
)

print(
    "=============================================="
)


print(
    f"MAE:  "
    f"{test_metrics['mae']:.4f} "
    f"µg/m³"
)


print(
    f"RMSE: "
    f"{test_metrics['rmse']:.4f} "
    f"µg/m³"
)


print(
    f"R²:   "
    f"{test_metrics['r2']:.4f}"
)


# =========================================================
# STATION-LEVEL TEST METRICS
# =========================================================

test_results = test_df[
    [
        "timestamp_utc",
        "location_id",
        "location_name",
        TARGET_COLUMN,
    ]
].copy()


test_results[
    "prediction"
] = test_predictions


station_metrics = []


for (
    location_id,
    group,
) in test_results.groupby(
    "location_id"
):


    station_name = str(
        group[
            "location_name"
        ]
        .iloc[0]
    )


    station_mae = (
        mean_absolute_error(
            group[
                TARGET_COLUMN
            ],
            group[
                "prediction"
            ],
        )
    )


    station_rmse = (
        mean_squared_error(
            group[
                TARGET_COLUMN
            ],
            group[
                "prediction"
            ],
        )
        ** 0.5
    )


    if len(
        group
    ) >= 2:

        station_r2 = (
            r2_score(
                group[
                    TARGET_COLUMN
                ],
                group[
                    "prediction"
                ],
            )
        )

    else:

        station_r2 = (
            float(
                "nan"
            )
        )


    station_metrics.append(
        {
            "location_id":
                int(
                    location_id
                ),

            "location_name":
                station_name,

            "test_samples":
                int(
                    len(
                        group
                    )
                ),

            "mae":
                float(
                    station_mae
                ),

            "rmse":
                float(
                    station_rmse
                ),

            "r2":
                float(
                    station_r2
                ),
        }
    )


station_metrics_df = pd.DataFrame(
    station_metrics
)


station_metrics_df = (
    station_metrics_df
    .sort_values(
        "mae"
    )
)


print()
print(
    "STATION TEST PERFORMANCE"
)


print(
    station_metrics_df.to_string(
        index=False,

        formatters={
            "mae":
                lambda x:
                    f"{x:.3f}",

            "rmse":
                lambda x:
                    f"{x:.3f}",

            "r2":
                lambda x:
                    (
                        f"{x:.3f}"
                        if pd.notna(
                            x
                        )
                        else "N/A"
                    ),
        },
    )
)


# =========================================================
# FINAL DEPLOYMENT MODEL
#
# Train on every labelled row AFTER test metrics have been
# fixed and recorded.
# =========================================================

print()
print(
    "Training final 19-station "
    "deployment model on all labelled samples..."
)


deployment_model = (
    make_model(
        selected_config
    )
)


deployment_model.fit(
    ml_df[
        FEATURE_COLUMNS
    ],
    ml_df[
        TARGET_COLUMN
    ],
)


# =========================================================
# STATION METADATA
# =========================================================

station_metadata = []


for _, row in (
    selected.iterrows()
):

    station_metadata.append(
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

            "recent_coverage_pct":
                float(
                    row[
                        "recent_coverage_pct"
                    ]
                ),

            "selection_order":
                int(
                    row[
                        "selection_order"
                    ]
                ),
        }
    )


# =========================================================
# SPATIAL COVERAGE REPORT
# =========================================================

spatial_summary = None


if SPATIAL_REPORT_PATH.exists():

    spatial_report = json.loads(
        SPATIAL_REPORT_PATH
        .read_text(
            encoding="utf-8"
        )
    )


    spatial_summary = {
        "coverage_radius_km":
            spatial_report.get(
                "coverage_radius_km"
            ),

        "service_area_km2":
            spatial_report.get(
                "service_area_km2"
            ),

        "coverage_pct":
            spatial_report.get(
                "final_coverage_pct"
            ),

        "p95_nearest_station_distance_km":
            spatial_report.get(
                "p95_nearest_station_distance_km"
            ),

        "maximum_nearest_station_distance_km":
            spatial_report.get(
                "maximum_nearest_station_distance_km"
            ),
    }


# =========================================================
# MODEL BUNDLE
# =========================================================

bundle = {
    "model":
        deployment_model,

    "model_name":
        "RandomForestRegressor",

    "model_type":
        (
            "compact 19-station "
            "station-aware pooled model"
        ),

    "deployment_profile":
        selected_config[
            "name"
        ],

    "feature_columns":
        FEATURE_COLUMNS,

    "target_column":
        TARGET_COLUMN,

    "forecast_horizon_hours":
        1,

    "coverage_radius_km":
        COVERAGE_RADIUS_KM,

    "stations":
        station_metadata,

    "validation_metrics": {
        "mae":
            selected_config[
                "validation_mae"
            ],

        "rmse":
            selected_config[
                "validation_rmse"
            ],

        "r2":
            selected_config[
                "validation_r2"
            ],
    },

    "held_out_test_metrics":
        test_metrics,

    "spatial_coverage":
        spatial_summary,

    "methodology": (
        "PM2.5 lag and rolling features are "
        "calculated independently for each station. "
        "The target is PM2.5 one hour ahead. "
        "Chronological train, validation and test "
        "periods prevent future observations from "
        "entering earlier model training. "
        "The compact Random Forest configuration "
        "was selected using validation performance "
        "and artifact size only. The held-out test "
        "period was evaluated after model selection."
    ),
}


# =========================================================
# SAVE TEMP MODEL WITH COMPRESSION
# =========================================================

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


final_model_size_mb = (
    size_mb(
        TEMP_MODEL_PATH
    )
)


print()
print(
    "=============================================="
)

print(
    "DEPLOYMENT MODEL SIZE CHECK"
)

print(
    "=============================================="
)


print(
    f"Compressed model size: "
    f"{final_model_size_mb:.2f} MB"
)


print(
    f"Preferred target:      "
    f"< {MODEL_SIZE_TARGET_MB:.0f} MB"
)


print(
    f"Hard model limit:      "
    f"< {MODEL_SIZE_HARD_LIMIT_MB:.0f} MB"
)


if (
    final_model_size_mb
    > MODEL_SIZE_HARD_LIMIT_MB
):

    TEMP_MODEL_PATH.unlink(
        missing_ok=True
    )


    raise RuntimeError(
        "19-station deployment model "
        f"is {final_model_size_mb:.2f} MB, "
        "which exceeds the "
        f"{MODEL_SIZE_HARD_LIMIT_MB:.0f} MB "
        "CityPulse hard deployment limit. "
        "The current deployed model was "
        "NOT overwritten."
    )


if (
    final_model_size_mb
    > MODEL_SIZE_TARGET_MB
):

    print()
    print(
        "WARNING:"
    )

    print(
        "Model is below the hard deployment "
        "limit but above the preferred "
        f"{MODEL_SIZE_TARGET_MB:.0f} MB target."
    )


# Promote only after size check passes.
MODEL_PATH.unlink(
    missing_ok=True
)


TEMP_MODEL_PATH.replace(
    MODEL_PATH
)


# =========================================================
# SAVE REPORTS
# =========================================================

test_results.to_csv(
    TEST_PREDICTIONS_PATH,
    index=False,
)


station_metrics_df.to_csv(
    STATION_METRICS_PATH,
    index=False,
)


report = {
    "generated_at_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "status":
        "PASS",

    "station_count":
        int(
            len(
                selected
            )
        ),

    "stations":
        station_metadata,

    "common_time_range": {
        "start":
            common_start
            .isoformat(),

        "end":
            common_end
            .isoformat(),
    },

    "dataset": {
        "timeline_rows":
            int(
                len(
                    combined_timeline
                )
            ),

        "complete_ml_rows":
            int(
                len(
                    ml_df
                )
            ),

        "feature_count":
            int(
                len(
                    FEATURE_COLUMNS
                )
            ),
    },

    "split": {
        "train_rows":
            int(
                len(
                    train_df
                )
            ),

        "validation_rows":
            int(
                len(
                    validation_df
                )
            ),

        "test_rows":
            int(
                len(
                    test_df
                )
            ),

        "train_end":
            str(
                train_end
            ),

        "validation_end":
            str(
                validation_end
            ),
    },

    "model_selection": {
        "candidate_results":
            candidate_results,

        "selected_profile":
            selected_config[
                "name"
            ],

        "selection_rule":
            (
                "Smallest compressed model "
                "within 3% of the best "
                "validation MAE and within "
                "0.02 R2 of the best "
                "validation R2."
            ),
    },

    "validation_metrics": {
        "mae":
            selected_config[
                "validation_mae"
            ],

        "rmse":
            selected_config[
                "validation_rmse"
            ],

        "r2":
            selected_config[
                "validation_r2"
            ],
    },

    "held_out_test_metrics":
        test_metrics,

    "station_test_metrics":
        station_metrics,

    "spatial_coverage":
        spatial_summary,

    "deployment": {
        "model_path":
            str(
                MODEL_PATH
            ),

        "model_size_mb":
            float(
                final_model_size_mb
            ),

        "preferred_model_size_mb":
            MODEL_SIZE_TARGET_MB,

        "hard_model_limit_mb":
            MODEL_SIZE_HARD_LIMIT_MB,
    },
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
# FINAL VALIDATION
# =========================================================

if (
    latest_df[
        "location_id"
    ].nunique()
    != EXPECTED_STATION_COUNT
):

    raise RuntimeError(
        "Latest feature dataset does not "
        "contain all 19 stations."
    )


if (
    ml_df[
        "location_id"
    ].nunique()
    != EXPECTED_STATION_COUNT
):

    raise RuntimeError(
        "ML dataset does not contain "
        "all 19 stations."
    )


# =========================================================
# FINAL OUTPUT
# =========================================================

print()
print(
    "=============================================="
)

print(
    "19-STATION MODEL PIPELINE: PASS"
)

print(
    "=============================================="
)


print(
    f"Stations:       "
    f"{len(selected)}"
)


print(
    f"ML samples:     "
    f"{len(ml_df):,}"
)


print(
    f"Features:       "
    f"{len(FEATURE_COLUMNS)}"
)


print(
    f"Model profile:  "
    f"{selected_config['name']}"
)


print(
    f"Test MAE:       "
    f"{test_metrics['mae']:.4f}"
)


print(
    f"Test RMSE:      "
    f"{test_metrics['rmse']:.4f}"
)


print(
    f"Test R²:        "
    f"{test_metrics['r2']:.4f}"
)


print(
    f"Model size:     "
    f"{final_model_size_mb:.2f} MB"
)


if spatial_summary:

    print(
        f"5 km coverage:  "
        f"{spatial_summary['coverage_pct']:.2f}%"
    )


    print(
        f"P95 distance:   "
        f"{spatial_summary['p95_nearest_station_distance_km']:.2f} km"
    )


    print(
        f"Max distance:   "
        f"{spatial_summary['maximum_nearest_station_distance_km']:.2f} km"
    )


print()
print(
    "NEW MODEL:"
)

print(
    MODEL_PATH
)


print()
print(
    "NEW LATEST FEATURES:"
)

print(
    LATEST_FEATURES_PATH
)


print()
print(
    "MODEL REPORT:"
)

print(
    REPORT_PATH
)


print()
print(
    "IMPORTANT:"
)

print(
    "The currently deployed 8-station "
    "model has NOT been overwritten."
)

print()
print(
    "NEXT:"
)

print(
    "Validate the 19-station model, "
    "then switch FastAPI to the new "
    "versioned model + feature file."
)
