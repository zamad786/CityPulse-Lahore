import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import requests

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


# =========================================================
# PROJECT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CANDIDATES_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "lahore_multilocation_station_candidates.csv"
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
# SELECTED MVP STATIONS
# =========================================================

SELECTED_LOCATION_IDS = [
    4757305,  # FCC University
    4527035,  # Civil Secretariat
    4527173,  # Learning Alliance Intl. DHA
    4515157,  # Barki
    4609353,  # Kahna Hospital
    4618814,  # Gulberg III
    4568423,  # Model Town
    4555745,  # Ravi Road
]


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
# API KEY
# =========================================================

def read_api_key():
    key = os.getenv(
        "OPENAQ_API_KEY"
    )

    if key:
        return key

    for env_path in [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT / "backend" / ".env",
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

            name, value = line.split(
                "=",
                1,
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


OPENAQ_API_KEY = read_api_key()


if not OPENAQ_API_KEY:
    print(
        "\nERROR: OPENAQ_API_KEY missing."
    )

    print(
        'Set it with:\n'
        '$env:OPENAQ_API_KEY="YOUR_KEY"'
    )

    sys.exit(1)


OPENAQ_HEADERS = {
    "X-API-Key":
        OPENAQ_API_KEY,
}


# =========================================================
# HELPERS
# =========================================================

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

            return response.json()

        except Exception as exc:
            last_error = exc

            print(
                f"  Request attempt "
                f"{attempt}/{retries} failed: "
                f"{exc}"
            )

            if attempt < retries:
                time.sleep(
                    attempt * 2
                )

    raise RuntimeError(
        f"Request failed after "
        f"{retries} attempts: "
        f"{last_error}"
    )


def parse_openaq_timestamp(
    record,
):
    period = (
        record.get("period")
        or {}
    )

    datetime_from = (
        period.get("datetimeFrom")
        or record.get("datetimeFrom")
        or record.get("datetime")
    )

    if isinstance(
        datetime_from,
        dict,
    ):
        datetime_from = (
            datetime_from.get("utc")
            or datetime_from.get("local")
        )

    return pd.to_datetime(
        datetime_from,
        utc=True,
        errors="coerce",
    )


# =========================================================
# READ STATIONS
# =========================================================

if not CANDIDATES_PATH.exists():
    raise FileNotFoundError(
        f"Missing station file:\n"
        f"{CANDIDATES_PATH}"
    )


candidate_df = pd.read_csv(
    CANDIDATES_PATH
)


selected = candidate_df[
    candidate_df[
        "location_id"
    ].isin(
        SELECTED_LOCATION_IDS
    )
].copy()


selected = (
    selected
    .sort_values(
        "location_id"
    )
    .drop_duplicates(
        subset=[
            "location_id"
        ]
    )
)


missing_locations = (
    set(
        SELECTED_LOCATION_IDS
    )
    - set(
        selected[
            "location_id"
        ].astype(int)
    )
)


if missing_locations:
    raise ValueError(
        "Selected location IDs missing "
        f"from candidate file: "
        f"{sorted(missing_locations)}"
    )


if len(selected) != len(
    SELECTED_LOCATION_IDS
):
    raise ValueError(
        "Expected one PM2.5 sensor "
        "per selected station."
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


# Common time range shared by all stations.
common_start = (
    selected[
        "sensor_datetime_first_utc"
    ]
    .max()
    .ceil("h")
)


common_end = (
    selected[
        "sensor_datetime_last_utc"
    ]
    .min()
    .floor("h")
)


print(
    "\n=============================================="
)

print(
    "CITYPULSE MULTI-LOCATION MODEL PIPELINE"
)

print(
    "=============================================="
)

print(
    f"Stations:       {len(selected)}"
)

print(
    f"Common start:   {common_start}"
)

print(
    f"Common end:     {common_end}"
)


print(
    "\nSelected locations:"
)


for _, station in selected.iterrows():
    print(
        f"  {int(station['location_id'])} | "
        f"{station['location_name']} | "
        f"sensor={int(station['sensor_id'])}"
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
        / f"openaq_{location_id}_pm25_hourly.csv"
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
                f"/sensors/{sensor_id}/hours"
            ),
            headers=OPENAQ_HEADERS,
            params={
                "datetime_from":
                    common_start.isoformat(),

                "datetime_to":
                    common_end.isoformat(),

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


        if len(results) < 1000:
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
            f"No OpenAQ data for "
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
        / f"openmeteo_{location_id}_weather_hourly.csv"
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
                common_start.date().isoformat(),

            "end_date":
                common_end.date().isoformat(),

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
            f"missing hourly data for "
            f"{location_id}"
        )


    weather = pd.DataFrame(
        {
            "timestamp_utc":
                pd.to_datetime(
                    hourly["time"],
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
# ENGINEER ONE STATION
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

    station_name = (
        station[
            "location_name"
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


    print(
        "\n----------------------------------------------"
    )

    print(
        f"[{station_number}/{len(selected)}] "
        f"{station_name}"
    )

    print(
        "----------------------------------------------"
    )


    aq = download_openaq(
        station
    )

    weather = download_weather(
        station
    )


    timeline = pd.DataFrame(
        {
            "timestamp_utc":
                pd.date_range(
                    start=common_start,
                    end=common_end,
                    freq="h",
                    tz="UTC",
                )
        }
    )


    timeline = timeline.merge(
        aq,
        how="left",
        on="timestamp_utc",
    )


    timeline = timeline.merge(
        weather,
        how="left",
        on="timestamp_utc",
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


    # ----------------------------------------------
    # Lahore-local time features
    # ----------------------------------------------

    local_time = (
        timeline[
            "timestamp_utc"
        ]
        .dt.tz_convert(
            "Asia/Karachi"
        )
    )


    timeline[
        "timestamp_lahore"
    ] = local_time

    timeline[
        "hour"
    ] = local_time.dt.hour

    timeline[
        "day_of_week"
    ] = local_time.dt.dayofweek

    timeline[
        "month"
    ] = local_time.dt.month

    timeline[
        "is_weekend"
    ] = (
        local_time
        .dt.dayofweek
        .isin(
            [5, 6]
        )
        .astype(int)
    )


    # ----------------------------------------------
    # Leakage-safe lag features
    # ----------------------------------------------

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


    # ----------------------------------------------
    # Rolling means
    # Includes current t and previous hours only.
    # Valid for forecasting t+1.
    # ----------------------------------------------

    for window in ROLLING_WINDOWS:
        timeline[
            f"pm25_rolling_mean_{window}h"
        ] = (
            timeline[
                "pm25_ug_m3"
            ]
            .rolling(
                window=window,
                min_periods=window,
            )
            .mean()
        )


    # ----------------------------------------------
    # Future target
    # ----------------------------------------------

    timeline[
        TARGET_COLUMN
    ] = (
        timeline[
            "pm25_ug_m3"
        ]
        .shift(-1)
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


    # ----------------------------------------------
    # Station identity
    # ----------------------------------------------

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


    # Latest inference-ready feature row.
    feature_ready = (
        timeline
        .dropna(
            subset=FEATURE_COLUMNS
        )
    )


    if feature_ready.empty:
        raise ValueError(
            f"No complete feature row "
            f"for {station_name}"
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
# COMBINE
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


timeline_path = (
    PROCESSED_DIR
    / "citypulse_multilocation_hourly.csv"
)


combined_timeline.to_csv(
    timeline_path,
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


ml_path = (
    PROCESSED_DIR
    / "citypulse_multilocation_ml_dataset.csv"
)


ml_df.to_csv(
    ml_path,
    index=False,
)


latest_df = pd.DataFrame(
    latest_feature_rows
)


latest_path = (
    PROCESSED_DIR
    / "citypulse_multilocation_latest_features.csv"
)


latest_df.to_csv(
    latest_path,
    index=False,
)


print(
    "\n=============================================="
)

print(
    "COMBINED DATASET"
)

print(
    "=============================================="
)

print(
    f"Timeline rows: "
    f"{len(combined_timeline):,}"
)

print(
    f"Complete ML rows: "
    f"{len(ml_df):,}"
)

print(
    f"Stations: "
    f"{ml_df['location_id'].nunique()}"
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
        train_cut_index - 1
    ]
)


validation_end = (
    unique_times.iloc[
        validation_cut_index - 1
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


print(
    "\n=============================================="
)

print(
    "CHRONOLOGICAL SPLIT"
)

print(
    "=============================================="
)

print(
    f"Train:      "
    f"{len(train_df):,} rows"
)

print(
    f"Validation: "
    f"{len(validation_df):,} rows"
)

print(
    f"Test:       "
    f"{len(test_df):,} rows"
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
# TRAIN RANDOM FOREST
# =========================================================

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


print(
    "\nTraining station-aware "
    "Random Forest..."
)


start_time = time.perf_counter()


validation_model = (
    RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
)


validation_model.fit(
    X_train,
    y_train,
)


training_seconds = (
    time.perf_counter()
    - start_time
)


validation_predictions = (
    validation_model.predict(
        X_validation
    )
)


validation_mae = (
    mean_absolute_error(
        y_validation,
        validation_predictions,
    )
)


validation_rmse = (
    mean_squared_error(
        y_validation,
        validation_predictions,
    )
    ** 0.5
)


validation_r2 = (
    r2_score(
        y_validation,
        validation_predictions,
    )
)


print(
    "\nVALIDATION"
)

print(
    f"MAE:  "
    f"{validation_mae:.4f}"
)

print(
    f"RMSE: "
    f"{validation_rmse:.4f}"
)

print(
    f"R²:   "
    f"{validation_r2:.4f}"
)

print(
    f"Train time: "
    f"{training_seconds:.2f}s"
)


# =========================================================
# FINAL HELD-OUT TEST
# =========================================================

train_validation_df = pd.concat(
    [
        train_df,
        validation_df,
    ],
    ignore_index=True,
)


evaluation_model = (
    RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
    )
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


test_mae = (
    mean_absolute_error(
        test_df[
            TARGET_COLUMN
        ],
        test_predictions,
    )
)


test_rmse = (
    mean_squared_error(
        test_df[
            TARGET_COLUMN
        ],
        test_predictions,
    )
    ** 0.5
)


test_r2 = (
    r2_score(
        test_df[
            TARGET_COLUMN
        ],
        test_predictions,
    )
)


print(
    "\n=============================================="
)

print(
    "HELD-OUT TEST RESULTS"
)

print(
    "=============================================="
)

print(
    f"MAE:  {test_mae:.4f} µg/m³"
)

print(
    f"RMSE: {test_rmse:.4f} µg/m³"
)

print(
    f"R²:   {test_r2:.4f}"
)


# =========================================================
# STATION-LEVEL TEST PERFORMANCE
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

    station_name = (
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


    station_metrics.append(
        {
            "location_id":
                int(location_id),

            "location_name":
                station_name,

            "test_samples":
                len(group),

            "mae":
                station_mae,

            "rmse":
                station_rmse,

            "r2":
                station_r2,
        }
    )


station_metrics_df = pd.DataFrame(
    station_metrics
).sort_values(
    "mae"
)


print(
    "\nSTATION TEST PERFORMANCE"
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
                    f"{x:.3f}",
        },
    )
)


# =========================================================
# DEPLOYMENT MODEL
# =========================================================

print(
    "\nTraining final deployment model "
    "on all labelled samples..."
)


deployment_model = (
    RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        max_features=0.8,
        random_state=42,
        n_jobs=-1,
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


station_metadata = []


for _, row in selected.iterrows():
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
                row[
                    "location_name"
                ],

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
                row[
                    "provider"
                ],
        }
    )


bundle = {
    "model":
        deployment_model,

    "model_name":
        "RandomForestRegressor",

    "model_type":
        "station-aware pooled model",

    "feature_columns":
        FEATURE_COLUMNS,

    "target_column":
        TARGET_COLUMN,

    "forecast_horizon_hours":
        1,

    "stations":
        station_metadata,

    "validation_metrics": {
        "mae":
            validation_mae,

        "rmse":
            validation_rmse,

        "r2":
            validation_r2,
    },

    "held_out_test_metrics": {
        "mae":
            test_mae,

        "rmse":
            test_rmse,

        "r2":
            test_r2,
    },

    "methodology": (
        "PM2.5 lags and rolling features are "
        "calculated independently within each "
        "station. Chronological splitting is "
        "performed by timestamp across all stations "
        "to prevent future observations from "
        "entering earlier training periods."
    ),
}


model_path = (
    MODEL_DIR
    / "citypulse_multilocation_model.joblib"
)


joblib.dump(
    bundle,
    model_path,
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

    "station_count":
        len(selected),

    "stations":
        station_metadata,

    "common_time_range": {
        "start":
            common_start.isoformat(),

        "end":
            common_end.isoformat(),
    },

    "dataset": {
        "timeline_rows":
            len(
                combined_timeline
            ),

        "complete_ml_rows":
            len(
                ml_df
            ),

        "feature_count":
            len(
                FEATURE_COLUMNS
            ),
    },

    "split": {
        "train_rows":
            len(
                train_df
            ),

        "validation_rows":
            len(
                validation_df
            ),

        "test_rows":
            len(
                test_df
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

    "validation_metrics": {
        "mae":
            validation_mae,

        "rmse":
            validation_rmse,

        "r2":
            validation_r2,
    },

    "held_out_test_metrics": {
        "mae":
            test_mae,

        "rmse":
            test_rmse,

        "r2":
            test_r2,
    },

    "station_test_metrics":
        station_metrics,
}


report_path = (
    REPORT_DIR
    / "multilocation_model_report.json"
)


report_path.write_text(
    json.dumps(
        report,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)


station_metrics_df.to_csv(
    (
        REPORT_DIR
        / "multilocation_station_test_metrics.csv"
    ),
    index=False,
)


test_results.to_csv(
    (
        REPORT_DIR
        / "multilocation_test_predictions.csv"
    ),
    index=False,
)


# =========================================================
# FINAL
# =========================================================

print(
    "\n=============================================="
)

print(
    "MULTI-LOCATION MODEL PIPELINE: PASS"
)

print(
    "=============================================="
)

print(
    f"Stations:       {len(selected)}"
)

print(
    f"ML samples:     {len(ml_df):,}"
)

print(
    f"Features:       {len(FEATURE_COLUMNS)}"
)

print(
    f"Test MAE:       {test_mae:.4f}"
)

print(
    f"Test RMSE:      {test_rmse:.4f}"
)

print(
    f"Test R²:        {test_r2:.4f}"
)

print(
    f"\nModel:"
    f"\n{model_path}"
)

print(
    f"\nLatest features:"
    f"\n{latest_path}"
)

print(
    f"\nReport:"
    f"\n{report_path}"
)

print(
    "\nNEXT: make FastAPI + React location-aware."
)