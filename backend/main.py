import os

from fastapi import (
    FastAPI,
    HTTPException,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from pydantic import (
    BaseModel,
    Field,
)

from backend.dashboard_router import (
    DEFAULT_LOCATION_ID,
    MODEL_PATH,
    build_dashboard,
    get_coverage_radius_km,
    get_stations,
    load_model_bundle,
    router as dashboard_router,
)


# =========================================================
# REQUEST SCHEMA
# =========================================================

class PredictionRequest(
    BaseModel
):

    location_id: int = Field(
        default=
            DEFAULT_LOCATION_ID,

        description=(
            "Supported CityPulse "
            "OpenAQ location ID."
        ),
    )


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="CityPulse Lahore API",

    description=(
        "AI-powered next-hour PM2.5 prediction "
        "and Lahore urban air-quality "
        "risk intelligence."
    ),

    version="1.1.0",
)


app.include_router(
    dashboard_router
)


# =========================================================
# CORS
# =========================================================

cors_env = os.getenv(
    "CITYPULSE_CORS_ORIGINS",
    (
        "http://localhost:5173,"
        "http://127.0.0.1:5173"
    ),
)


allowed_origins = [
    origin.strip()
    for origin
    in cors_env.split(",")
    if origin.strip()
]


app.add_middleware(
    CORSMiddleware,

    allow_origins=
        allowed_origins,

    allow_credentials=
        True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "service":
            "CityPulse Lahore API",

        "status":
            "running",

        "version":
            "1.1.0",

        "docs":
            "/docs",

        "health":
            "/health",

        "locations":
            "/locations",

        "dashboard":
            "/dashboard/latest",

        "nearest":
            "/dashboard/nearest",

        "predict":
            "/predict",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health"
)
def health():

    try:

        bundle = (
            load_model_bundle()
        )

        stations = (
            get_stations()
        )


        model_size_mb = (
            MODEL_PATH
            .stat()
            .st_size
            / 1024
            / 1024
        )


        return {
            "status":
                "ok",

            "service":
                "CityPulse Lahore API",

            "version":
                "1.1.0",

            "model_loaded":
                True,

            "model_name":
                bundle.get(
                    "model_name"
                ),

            "model_type":
                bundle.get(
                    "model_type"
                ),

            "deployment_profile":
                bundle.get(
                    "deployment_profile"
                ),

            "forecast_horizon_hours":
                int(
                    bundle.get(
                        "forecast_horizon_hours",
                        1,
                    )
                ),

            "station_count":
                len(
                    stations
                ),

            "feature_count":
                len(
                    bundle.get(
                        "feature_columns",
                        [],
                    )
                ),

            "coverage_radius_km":
                get_coverage_radius_km(),

            "model_size_mb":
                round(
                    model_size_mb,
                    2,
                ),

            "held_out_test_metrics":
                bundle.get(
                    "held_out_test_metrics",
                    {},
                ),

            "spatial_coverage":
                bundle.get(
                    "spatial_coverage"
                ),
        }


    except Exception as exc:

        return {
            "status":
                "degraded",

            "service":
                "CityPulse Lahore API",

            "version":
                "1.1.0",

            "model_loaded":
                False,

            "error":
                str(
                    exc
                ),
        }


# =========================================================
# PREDICTION
#
# Uses the selected station's latest prepared feature row.
# The frontend does not send raw future-sensitive features.
# =========================================================

@app.post(
    "/predict"
)
def predict(
    payload: PredictionRequest,
):

    try:

        return build_dashboard(
            payload.location_id
        )


    except HTTPException:
        raise


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Prediction failed: "
                f"{exc}"
            ),
        ) from exc
