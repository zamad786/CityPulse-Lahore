import json
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------
# Make CityPulse project root importable
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from fastapi.testclient import TestClient

from backend.main import app

REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "day4_final_validation_summary.json"
)

FRONTEND_ENV = (
    PROJECT_ROOT
    / "frontend"
    / ".env"
)

FRONTEND_DIST = (
    PROJECT_ROOT
    / "frontend"
    / "dist"
    / "index.html"
)


client = TestClient(app)

checks: dict[str, dict] = {}


def record(
    name: str,
    passed: bool,
    detail: str,
) -> None:
    checks[name] = {
        "passed": passed,
        "detail": detail,
    }

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"{name:<32} {status}"
    )

    if not passed:
        print(
            f"  -> {detail}"
        )


print(
    "\n=== CITYPULSE DAY 4 FINAL VALIDATION ===\n"
)


# ---------------------------------------------------------
# 1. Health endpoint
# ---------------------------------------------------------

health_response = client.get(
    "/health"
)

record(
    "HEALTH ENDPOINT",
    health_response.status_code == 200,
    f"HTTP {health_response.status_code}",
)


# ---------------------------------------------------------
# 2. Dashboard endpoint
# ---------------------------------------------------------

dashboard_response = client.get(
    "/dashboard/latest"
)

record(
    "DASHBOARD ENDPOINT",
    dashboard_response.status_code == 200,
    f"HTTP {dashboard_response.status_code}",
)


payload = (
    dashboard_response.json()
    if dashboard_response.status_code == 200
    else {}
)


# ---------------------------------------------------------
# 3. Required response sections
# ---------------------------------------------------------

required_sections = {
    "station",
    "measurement",
    "forecast",
    "risk",
    "scope_note",
    "regulatory_note",
}

missing_sections = (
    required_sections
    - set(payload.keys())
)

record(
    "DASHBOARD PAYLOAD",
    not missing_sections,
    (
        "Missing: "
        + ", ".join(
            sorted(
                missing_sections
            )
        )
        if missing_sections
        else "Required sections present."
    ),
)


# ---------------------------------------------------------
# 4. Prediction values
# ---------------------------------------------------------

measurement = payload.get(
    "measurement",
    {},
)

forecast = payload.get(
    "forecast",
    {},
)

predicted_pm25 = forecast.get(
    "predicted_pm25_ug_m3"
)

valid_prediction = (
    isinstance(
        predicted_pm25,
        (int, float),
    )
    and predicted_pm25 >= 0
)

record(
    "PM2.5 PREDICTION",
    valid_prediction,
    f"predicted_pm25={predicted_pm25}",
)


# ---------------------------------------------------------
# 5. Exact 1-hour horizon
# ---------------------------------------------------------

horizon_pass = False
horizon_detail = (
    "Missing timestamps."
)

try:
    measurement_time = (
        datetime.fromisoformat(
            measurement[
                "timestamp_utc"
            ]
        )
    )

    forecast_time = (
        datetime.fromisoformat(
            forecast[
                "timestamp_utc"
            ]
        )
    )

    delta_hours = (
        forecast_time
        - measurement_time
    ).total_seconds() / 3600

    horizon_pass = (
        delta_hours == 1
        and forecast.get(
            "horizon_hours"
        ) == 1
    )

    horizon_detail = (
        f"delta_hours={delta_hours}"
    )

except Exception as exc:
    horizon_detail = str(exc)


record(
    "1-HOUR FORECAST HORIZON",
    horizon_pass,
    horizon_detail,
)


# ---------------------------------------------------------
# 6. Risk payload
# ---------------------------------------------------------

risk = payload.get(
    "risk",
    {},
)

required_risk_fields = {
    "level",
    "response_stage",
    "aqi_reference_band",
    "severity",
    "recommendation",
}

missing_risk_fields = (
    required_risk_fields
    - set(risk.keys())
)

record(
    "RISK INTELLIGENCE",
    not missing_risk_fields,
    (
        "Missing: "
        + ", ".join(
            sorted(
                missing_risk_fields
            )
        )
        if missing_risk_fields
        else (
            f"{risk.get('level')} / "
            f"{risk.get('response_stage')}"
        )
    ),
)


# ---------------------------------------------------------
# 7. CORS for Vite frontend
# ---------------------------------------------------------

cors_response = client.get(
    "/dashboard/latest",
    headers={
        "Origin":
            "http://localhost:5173"
    },
)

allowed_origin = (
    cors_response.headers.get(
        "access-control-allow-origin"
    )
)

record(
    "FRONTEND CORS",
    allowed_origin
    == "http://localhost:5173",
    (
        f"allow-origin="
        f"{allowed_origin}"
    ),
)


# ---------------------------------------------------------
# 8. Frontend API configuration
# ---------------------------------------------------------

env_pass = False
env_detail = (
    "frontend/.env not found."
)

if FRONTEND_ENV.exists():
    env_text = (
        FRONTEND_ENV
        .read_text(
            encoding="utf-8"
        )
    )

    env_pass = (
        "VITE_API_BASE_URL="
        in env_text
    )

    env_detail = (
        "VITE_API_BASE_URL configured."
        if env_pass
        else (
            "VITE_API_BASE_URL "
            "missing."
        )
    )


record(
    "FRONTEND API CONFIG",
    env_pass,
    env_detail,
)


# ---------------------------------------------------------
# 9. Production frontend build
# ---------------------------------------------------------

record(
    "FRONTEND BUILD OUTPUT",
    FRONTEND_DIST.exists(),
    (
        str(FRONTEND_DIST)
        if FRONTEND_DIST.exists()
        else (
            "Run npm run build "
            "inside frontend/."
        )
    ),
)


# ---------------------------------------------------------
# Final report
# ---------------------------------------------------------

all_passed = all(
    item["passed"]
    for item in checks.values()
)

report = {
    "day": 4,
    "phase": "UI/UX and Full-Stack Integration",
    "status": (
        "PASS"
        if all_passed
        else "FAIL"
    ),
    "checks": checks,
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


print(
    "\n----------------------------------------"
)

print(
    "DAY 4 FINAL VALIDATION:",
    (
        "PASS"
        if all_passed
        else "FAIL"
    ),
)

print(
    "Report:",
    REPORT_PATH,
)

print(
    "----------------------------------------\n"
)


if not all_passed:
    raise SystemExit(1)