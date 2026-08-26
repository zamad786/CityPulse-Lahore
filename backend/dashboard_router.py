import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    tags=["Dashboard"],
)


# =========================================================
# PROJECT PATHS
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


DEFAULT_LOCATION_ID = 4757305

DEFAULT_COVERAGE_RADIUS_KM = 5.0


# =========================================================
# LOAD MODEL
# =========================================================

@lru_cache
def load_model_bundle():

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "19-station CityPulse model not found:\n"
            f"{MODEL_PATH}"
        )

    return joblib.load(
        MODEL_PATH
    )


# =========================================================
# LOAD LATEST FEATURES
# =========================================================

@lru_cache
def load_latest_features():

    if not LATEST_FEATURES_PATH.exists():
        raise FileNotFoundError(
            "19-station latest feature file not found:\n"
            f"{LATEST_FEATURES_PATH}"
        )

    df = pd.read_csv(
        LATEST_FEATURES_PATH
    )

    df[
        "timestamp_utc"
    ] = pd.to_datetime(
        df[
            "timestamp_utc"
        ],
        utc=True,
    )

    df[
        "location_id"
    ] = (
        df[
            "location_id"
        ]
        .astype(int)
    )

    df[
        "sensor_id"
    ] = (
        df[
            "sensor_id"
        ]
        .astype(int)
    )

    return df


# =========================================================
# COVERAGE
# =========================================================

def get_coverage_radius_km() -> float:

    bundle = load_model_bundle()

    radius = bundle.get(
        "coverage_radius_km"
    )

    if radius is not None:
        return float(
            radius
        )

    spatial = (
        bundle.get(
            "spatial_coverage"
        )
        or {}
    )

    radius = spatial.get(
        "coverage_radius_km"
    )

    if radius is not None:
        return float(
            radius
        )

    return DEFAULT_COVERAGE_RADIUS_KM


# =========================================================
# RISK INTELLIGENCE
# =========================================================

def classify_risk(
    pm25: float,
) -> dict[str, Any]:

    if pm25 <= 15:
        return {
            "level":
                "Good",

            "response_stage":
                "Prevention",

            "aqi_reference_band":
                "0-50",

            "severity":
                1,

            "recommendation": (
                "Air-quality conditions are within "
                "the lowest PM2.5 risk band."
            ),
        }

    if pm25 <= 35:
        return {
            "level":
                "Satisfactory",

            "response_stage":
                "Prevention",

            "aqi_reference_band":
                "51-100",

            "severity":
                2,

            "recommendation": (
                "Conditions remain relatively stable. "
                "Continue routine monitoring."
            ),
        }

    if pm25 <= 70:
        return {
            "level":
                "Moderate",

            "response_stage":
                "Preparedness",

            "aqi_reference_band":
                "101-150",

            "severity":
                3,

            "recommendation": (
                "Sensitive citizens should monitor "
                "exposure and consider limiting "
                "prolonged outdoor exertion if they "
                "experience discomfort."
            ),
        }

    if pm25 <= 140:
        return {
            "level":
                "Unhealthy for Sensitive Groups",

            "response_stage":
                "Alert",

            "aqi_reference_band":
                "151-200",

            "severity":
                4,

            "recommendation": (
                "Sensitive groups should consider "
                "reducing prolonged outdoor activity."
            ),
        }

    if pm25 <= 250:
        return {
            "level":
                "Unhealthy",

            "response_stage":
                "Warning",

            "aqi_reference_band":
                "201-300",

            "severity":
                5,

            "recommendation": (
                "Reduce unnecessary outdoor exposure "
                "and continue monitoring local conditions."
            ),
        }

    if pm25 <= 350:
        return {
            "level":
                "Very Unhealthy",

            "response_stage":
                "Emergency",

            "aqi_reference_band":
                "301-400",

            "severity":
                6,

            "recommendation": (
                "Very high pollution risk is predicted. "
                "Strong exposure precautions are advised."
            ),
        }

    return {
        "level":
            "Hazardous",

        "response_stage":
            "Severe",

        "aqi_reference_band":
            "401-500+",

        "severity":
            7,

        "recommendation": (
            "Severe PM2.5 conditions are predicted. "
            "Minimize outdoor exposure where possible."
        ),
    }


# =========================================================
# SUPPORTED STATIONS
# =========================================================

def get_stations():

    bundle = load_model_bundle()

    raw_stations = bundle.get(
        "stations",
        [],
    )

    latest_df = load_latest_features()

    stations = []


    for raw_station in raw_stations:

        station = dict(
            raw_station
        )

        location_id = int(
            station[
                "location_id"
            ]
        )

        matches = latest_df[
            latest_df[
                "location_id"
            ]
            == location_id
        ]


        if matches.empty:
            raise RuntimeError(
                "Could not match model station "
                f"{location_id} to latest features."
            )


        matched_row = (
            matches
            .sort_values(
                "timestamp_utc"
            )
            .iloc[-1]
        )


        timestamp = pd.Timestamp(
            matched_row[
                "timestamp_utc"
            ]
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(
                "UTC"
            )
        else:
            timestamp = timestamp.tz_convert(
                "UTC"
            )


        station[
            "location_id"
        ] = location_id

        station[
            "sensor_id"
        ] = int(
            matched_row[
                "sensor_id"
            ]
        )

        station[
            "name"
        ] = str(
            station[
                "name"
            ]
        ).strip()

        station[
            "latitude"
        ] = float(
            matched_row[
                "latitude"
            ]
        )

        station[
            "longitude"
        ] = float(
            matched_row[
                "longitude"
            ]
        )

        station[
            "latest_timestamp_utc"
        ] = timestamp.isoformat()

        stations.append(
            station
        )


    return sorted(
        stations,
        key=lambda item:
            item[
                "name"
            ].lower(),
    )


def get_station(
    location_id: int,
):

    for station in get_stations():

        if (
            int(
                station[
                    "location_id"
                ]
            )
            == int(
                location_id
            )
        ):
            return station


    raise HTTPException(
        status_code=404,
        detail=(
            f"Location {location_id} is not supported "
            "by the CityPulse 19-station model."
        ),
    )


# =========================================================
# DISTANCE
# =========================================================

def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:

    radius_km = 6371.0088

    phi1 = math.radians(
        lat1
    )

    phi2 = math.radians(
        lat2
    )

    delta_phi = math.radians(
        lat2
        - lat1
    )

    delta_lambda = math.radians(
        lon2
        - lon1
    )


    a = (
        math.sin(
            delta_phi
            / 2
        )
        ** 2
        +
        math.cos(
            phi1
        )
        * math.cos(
            phi2
        )
        * math.sin(
            delta_lambda
            / 2
        )
        ** 2
    )


    c = 2 * math.atan2(
        math.sqrt(
            a
        ),
        math.sqrt(
            1
            - a
        ),
    )


    return (
        radius_km
        * c
    )


# =========================================================
# LOCATION-SPECIFIC DASHBOARD
# =========================================================

def build_dashboard(
    location_id: int,
):

    bundle = load_model_bundle()

    model = bundle[
        "model"
    ]

    feature_columns = bundle[
        "feature_columns"
    ]

    station = get_station(
        location_id
    )

    latest_df = load_latest_features()


    station_rows = latest_df[
        latest_df[
            "location_id"
        ]
        == int(
            location_id
        )
    ]


    if station_rows.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                "No inference-ready feature row "
                f"for location {location_id}."
            ),
        )


    row = (
        station_rows
        .sort_values(
            "timestamp_utc"
        )
        .iloc[-1]
    )


    missing_features = [
        feature
        for feature
        in feature_columns
        if feature
        not in row.index
    ]


    if missing_features:
        raise HTTPException(
            status_code=500,
            detail=(
                "Latest feature dataset is missing "
                "required model features: "
                + ", ".join(
                    missing_features
                )
            ),
        )


    model_input = pd.DataFrame(
        [
            {
                feature:
                    float(
                        row[
                            feature
                        ]
                    )

                for feature
                in feature_columns
            }
        ],
        columns=feature_columns,
    )


    predicted_pm25 = float(
        model.predict(
            model_input
        )[0]
    )


    predicted_pm25 = max(
        0.0,
        predicted_pm25,
    )


    timestamp = pd.Timestamp(
        row[
            "timestamp_utc"
        ]
    )


    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize(
            "UTC"
        )
    else:
        timestamp = timestamp.tz_convert(
            "UTC"
        )


    forecast_horizon = int(
        bundle.get(
            "forecast_horizon_hours",
            1,
        )
    )


    forecast_timestamp = (
        timestamp
        + pd.Timedelta(
            hours=
                forecast_horizon
        )
    )


    risk = classify_risk(
        predicted_pm25
    )


    coverage_radius = (
        get_coverage_radius_km()
    )


    return {
        "data_mode":
            "latest_available_dataset_observation",

        "station": {
            "location_id":
                int(
                    station[
                        "location_id"
                    ]
                ),

            "sensor_id":
                int(
                    station[
                        "sensor_id"
                    ]
                ),

            "name":
                station[
                    "name"
                ],

            "latitude":
                float(
                    station[
                        "latitude"
                    ]
                ),

            "longitude":
                float(
                    station[
                        "longitude"
                    ]
                ),

            "provider":
                station.get(
                    "provider"
                ),

            "recent_coverage_pct":
                station.get(
                    "recent_coverage_pct"
                ),
        },

        "measurement": {
            "timestamp_utc":
                timestamp.isoformat(),

            "pm25_ug_m3":
                float(
                    row[
                        "pm25_ug_m3"
                    ]
                ),

            "temperature_c":
                float(
                    row[
                        "temperature_c"
                    ]
                ),

            "relative_humidity_pct":
                float(
                    row[
                        "relative_humidity_pct"
                    ]
                ),

            "precipitation_mm":
                float(
                    row[
                        "precipitation_mm"
                    ]
                ),

            "wind_speed_m_s":
                float(
                    row[
                        "wind_speed_m_s"
                    ]
                ),

            "wind_direction_deg":
                float(
                    row[
                        "wind_direction_deg"
                    ]
                ),

            "surface_pressure_hpa":
                float(
                    row[
                        "surface_pressure_hpa"
                    ]
                ),
        },

        "forecast": {
            "timestamp_utc":
                forecast_timestamp
                .isoformat(),

            "horizon_hours":
                forecast_horizon,

            "predicted_pm25_ug_m3":
                round(
                    predicted_pm25,
                    2,
                ),

            "model":
                bundle.get(
                    "model_name",
                    "RandomForestRegressor",
                ),

            "model_type":
                bundle.get(
                    "model_type",
                    (
                        "compact 19-station "
                        "station-aware pooled model"
                    ),
                ),

            "deployment_profile":
                bundle.get(
                    "deployment_profile"
                ),
        },

        "risk":
            risk,

        "model_metrics":
            bundle.get(
                "held_out_test_metrics",
                {},
            ),

        "coverage": {
            "recommended_radius_km":
                coverage_radius,

            "station_count":
                len(
                    bundle.get(
                        "stations",
                        [],
                    )
                ),

            "spatial_summary":
                bundle.get(
                    "spatial_coverage"
                ),
        },

        "scope_note": (
            "Location-specific forecast using the "
            "latest prepared observation from the "
            "supported OpenAQ monitoring station "
            f"'{station['name']}'."
        ),

        "regulatory_note": (
            "Forecast risk intelligence only. "
            "This is not an official regulatory "
            "AQI reading."
        ),
    }


# =========================================================
# ROUTES
# =========================================================

@router.get(
    "/locations"
)
def locations():

    stations = get_stations()

    bundle = load_model_bundle()

    return {
        "count":
            len(
                stations
            ),

        "forecast_horizon_hours":
            int(
                bundle.get(
                    "forecast_horizon_hours",
                    1,
                )
            ),

        "coverage_radius_km":
            get_coverage_radius_km(),

        "locations":
            stations,
    }


@router.get(
    "/dashboard/latest"
)
def dashboard_latest(
    location_id: int = Query(
        default=
            DEFAULT_LOCATION_ID,

        description=(
            "Supported OpenAQ "
            "location ID."
        ),
    ),
):

    return build_dashboard(
        location_id
    )


@router.get(
    "/dashboard/nearest"
)
def dashboard_nearest(

    lat: float = Query(
        ...,
        ge=-90,
        le=90,
    ),

    lon: float = Query(
        ...,
        ge=-180,
        le=180,
    ),
):

    stations = get_stations()


    if not stations:
        raise HTTPException(
            status_code=500,
            detail=(
                "No supported stations available."
            ),
        )


    nearest_station = None

    nearest_distance = None


    for station in stations:

        distance = haversine_km(
            lat,
            lon,
            float(
                station[
                    "latitude"
                ]
            ),
            float(
                station[
                    "longitude"
                ]
            ),
        )


        if (
            nearest_distance is None
            or distance
            < nearest_distance
        ):

            nearest_distance = distance

            nearest_station = station


    if (
        nearest_station is None
        or nearest_distance is None
    ):

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to determine "
                "nearest supported station."
            ),
        )


    coverage_radius = (
        get_coverage_radius_km()
    )


    within_supported_radius = (
        nearest_distance
        <= coverage_radius
    )


    if within_supported_radius:

        coverage_status = (
            "within_recommended_coverage"
        )

        coverage_note = (
            "The selected point is within "
            f"{coverage_radius:.1f} km of a "
            "supported monitoring station. "
            "CityPulse will use the nearest "
            "station as the observation and "
            "forecast reference."
        )

    else:

        coverage_status = (
            "outside_recommended_coverage"
        )

        coverage_note = (
            "The selected point is more than "
            f"{coverage_radius:.1f} km from the "
            "nearest supported monitoring station. "
            "The nearest station is shown for "
            "reference, but the clicked point "
            "should not be treated as having an "
            "exact local measurement."
        )


    return {
        "selected_point": {
            "latitude":
                lat,

            "longitude":
                lon,
        },

        "nearest_station":
            nearest_station,

        "distance_km":
            round(
                nearest_distance,
                2,
            ),

        "coverage_radius_km":
            coverage_radius,

        "within_supported_radius":
            within_supported_radius,

        "coverage_status":
            coverage_status,

        # Kept for compatibility with the
        # existing frontend.
        "coverage_mode":
            "nearest_supported_station",

        "coverage_note":
            coverage_note,
    }
