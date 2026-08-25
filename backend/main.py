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
    router as dashboard_router,
    build_dashboard,
    get_stations,
    load_model_bundle,
)


# =========================================================
# CONSTANTS
# =========================================================

DEFAULT_LOCATION_ID = 4757305


# =========================================================
# REQUEST SCHEMA
# =========================================================

class PredictionRequest(BaseModel):
    location_id: int = Field(
        default=DEFAULT_LOCATION_ID,
        gt=0,
        description=(
            "Supported OpenAQ Lahore location ID."
        ),
    )


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="CityPulse Lahore API",
    description=(
        "AI-powered multi-location next-hour PM2.5 "
        "prediction and urban air-quality "
        "risk intelligence."
    ),
    version="2.0.0",
)


# =========================================================
# DASHBOARD / MULTI-LOCATION ROUTES
# =========================================================

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
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
            "2.0.0",

        "architecture":
            "multi-location station-aware forecasting",

        "endpoints": {
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

            "docs":
                "/docs",
        },
    }


# =========================================================
# HEALTH
#
# Checks the CURRENT compact multi-location model,
# not the removed legacy FCC-only model.
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


        model = bundle.get(
            "model"
        )

        feature_columns = bundle.get(
            "feature_columns"
        )


        if (
            model is None
            or not feature_columns
        ):
            raise RuntimeError(
                "Multi-location model bundle "
                "is incomplete."
            )


        return {
            "status":
                "ok",

            "service":
                "CityPulse Lahore API",

            "model_loaded":
                True,

            "model_name":
                bundle.get(
                    "model_name",
                    type(model).__name__,
                ),

            "model_type":
                bundle.get(
                    "model_type",
                    (
                        "station-aware "
                        "multi-location model"
                    ),
                ),

            "forecast_horizon_hours":
                int(
                    bundle.get(
                        "forecast_horizon_hours",
                        1,
                    )
                ),

            "supported_station_count":
                len(
                    stations
                ),

            "deployment_profile":
                bundle.get(
                    "deployment_profile",
                    "multi-location",
                ),
        }


    except Exception as exc:

        return {
            "status":
                "degraded",

            "service":
                "CityPulse Lahore API",

            "model_loaded":
                False,

            "model_name":
                None,

            "model_type":
                None,

            "forecast_horizon_hours":
                None,

            "supported_station_count":
                0,

            "error":
                str(
                    exc
                ),
        }


# =========================================================
# PREDICT
#
# The prediction endpoint now uses exactly the same
# compact multi-location forecasting pipeline as the
# dashboard.
#
# Example JSON:
#
# {
#     "location_id": 4618814
# }
# =========================================================

@app.post(
    "/predict"
)
def predict(
    payload: PredictionRequest,
):

    try:

        result = (
            build_dashboard(
                payload.location_id
            )
        )


        return result


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