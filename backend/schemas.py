from datetime import datetime

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class PredictionRequest(BaseModel):
    timestamp_utc: datetime

    # Current measured PM2.5
    pm25_ug_m3: float = Field(ge=0)

    # Historical PM2.5 lags
    pm25_lag_1h: float = Field(ge=0)
    pm25_lag_2h: float = Field(ge=0)
    pm25_lag_3h: float = Field(ge=0)
    pm25_lag_6h: float = Field(ge=0)
    pm25_lag_12h: float = Field(ge=0)
    pm25_lag_24h: float = Field(ge=0)

    # Historical rolling means
    pm25_rolling_mean_3h: float = Field(ge=0)
    pm25_rolling_mean_6h: float = Field(ge=0)
    pm25_rolling_mean_12h: float = Field(ge=0)
    pm25_rolling_mean_24h: float = Field(ge=0)

    # Current weather
    temperature_c: float = Field(
        ge=-30,
        le=60,
    )

    relative_humidity_pct: float = Field(
        ge=0,
        le=100,
    )

    precipitation_mm: float = Field(
        ge=0,
    )

    wind_speed_m_s: float = Field(
        ge=0,
    )

    wind_direction_deg: float = Field(
        ge=0,
        le=360,
    )

    surface_pressure_hpa: float = Field(
        ge=850,
        le=1100,
    )

    @field_validator(
        "timestamp_utc"
    )
    @classmethod
    def timestamp_must_have_timezone(
        cls,
        value: datetime,
    ):
        if (
            value.tzinfo is None
            or value.utcoffset() is None
        ):
            raise ValueError(
                "timestamp_utc must include a timezone, "
                "for example 2026-08-23T05:00:00Z"
            )

        return value


class RiskResponse(BaseModel):
    risk_level: str
    aqi_reference_band: str
    response_level: str
    severity: int
    recommendation: str
    classification_basis: str
    forecast_type: str
    regulatory_note: str


class PredictionResponse(BaseModel):
    station_name: str

    input_timestamp_utc: datetime
    prediction_timestamp_utc: datetime

    current_measured_pm25_ug_m3: float
    predicted_pm25_1h_ug_m3: float

    forecast_horizon_hours: int

    model_name: str

    risk: RiskResponse

    scope_note: str


class HealthResponse(BaseModel):
    status: str

    service: str

    model_loaded: bool

    model_name: str | None = None

    forecast_horizon_hours: int | None = None