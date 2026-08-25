import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from backend.main import app


REPORT_PATH = (
    PROJECT_ROOT
    / "reports"
    / "multilocation_final_validation_summary.json"
)


EXPECTED_STATION_COUNT = 8


client = TestClient(app)


results = {}


def record(
    name: str,
    passed: bool,
    detail: str = "",
):
    results[name] = {
        "passed": passed,
        "detail": detail,
    }

    status = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"{name:<35} {status}"
    )

    if (
        detail
        and not passed
    ):
        print(
            f"  {detail}"
        )


print()
print(
    "=== CITYPULSE MULTI-LOCATION FINAL QA ==="
)
print()


# =========================================================
# HEALTH
# =========================================================

try:
    response = client.get(
        "/health"
    )

    record(
        "HEALTH ENDPOINT",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

except Exception as exc:
    record(
        "HEALTH ENDPOINT",
        False,
        str(exc),
    )


# =========================================================
# LOCATIONS
# =========================================================

locations = []


try:
    response = client.get(
        "/locations"
    )

    payload = response.json()

    locations = payload.get(
        "locations",
        [],
    )

    record(
        "LOCATIONS ENDPOINT",
        response.status_code == 200,
        f"HTTP {response.status_code}",
    )

    record(
        "SUPPORTED STATION COUNT",
        len(locations)
        == EXPECTED_STATION_COUNT,
        (
            f"Expected {EXPECTED_STATION_COUNT}, "
            f"received {len(locations)}"
        ),
    )

except Exception as exc:
    record(
        "LOCATIONS ENDPOINT",
        False,
        str(exc),
    )

    record(
        "SUPPORTED STATION COUNT",
        False,
        "Locations could not be loaded.",
    )


# =========================================================
# STATION METADATA
# =========================================================

metadata_valid = True

metadata_errors = []


for station in locations:
    required = [
        "location_id",
        "sensor_id",
        "name",
        "latitude",
        "longitude",
        "provider",
    ]

    missing = [
        field
        for field in required
        if station.get(field)
        in (
            None,
            "",
        )
    ]

    if missing:
        metadata_valid = False

        metadata_errors.append(
            f"{station.get('name')}: "
            f"missing {missing}"
        )


record(
    "STATION METADATA",
    metadata_valid,
    "; ".join(
        metadata_errors
    ),
)


# =========================================================
# ALL LOCATION-SPECIFIC DASHBOARDS
# =========================================================

all_dashboard_pass = True

dashboard_errors = []

predictions = {}


for station in locations:
    location_id = int(
        station[
            "location_id"
        ]
    )

    station_name = station[
        "name"
    ]


    try:
        response = client.get(
            "/dashboard/latest",
            params={
                "location_id":
                    location_id,
            },
        )


        if response.status_code != 200:
            all_dashboard_pass = False

            dashboard_errors.append(
                f"{station_name}: "
                f"HTTP {response.status_code}"
            )

            continue


        payload = response.json()


        returned_id = (
            payload
            .get(
                "station",
                {},
            )
            .get(
                "location_id"
            )
        )


        prediction = (
            payload
            .get(
                "forecast",
                {},
            )
            .get(
                "predicted_pm25_ug_m3"
            )
        )


        horizon = (
            payload
            .get(
                "forecast",
                {},
            )
            .get(
                "horizon_hours"
            )
        )


        risk = payload.get(
            "risk",
            {}
        )


        valid_prediction = (
            isinstance(
                prediction,
                (
                    int,
                    float,
                ),
            )
            and math.isfinite(
                float(
                    prediction
                )
            )
            and float(
                prediction
            ) >= 0
        )


        valid_risk = all(
            [
                risk.get(
                    "level"
                ),
                risk.get(
                    "response_stage"
                ),
                risk.get(
                    "aqi_reference_band"
                ),
                risk.get(
                    "recommendation"
                ),
            ]
        )


        station_pass = all(
            [
                returned_id
                == location_id,

                valid_prediction,

                horizon == 1,

                valid_risk,
            ]
        )


        if not station_pass:
            all_dashboard_pass = False

            dashboard_errors.append(
                f"{station_name}: "
                "invalid dashboard payload"
            )


        if valid_prediction:
            predictions[
                location_id
            ] = round(
                float(
                    prediction
                ),
                2,
            )


    except Exception as exc:
        all_dashboard_pass = False

        dashboard_errors.append(
            f"{station_name}: {exc}"
        )


record(
    "ALL 8 LOCATION DASHBOARDS",
    all_dashboard_pass,
    "; ".join(
        dashboard_errors
    ),
)


# =========================================================
# LOCATION-SPECIFIC PREDICTIONS
# =========================================================

unique_predictions = set(
    predictions.values()
)


record(
    "LOCATION-SPECIFIC PREDICTIONS",
    len(
        unique_predictions
    ) >= 2,
    (
        "Predictions should differ "
        "across supported stations."
    ),
)


# =========================================================
# NEAREST STATION
# =========================================================

try:
    response = client.get(
        "/dashboard/nearest",
        params={
            "lat":
                31.4697,

            "lon":
                74.2728,
        },
    )

    payload = response.json()

    nearest = payload.get(
        "nearest_station",
        {}
    )

    distance = payload.get(
        "distance_km"
    )

    valid_nearest = all(
        [
            response.status_code
            == 200,

            nearest.get(
                "location_id"
            )
            is not None,

            isinstance(
                distance,
                (
                    int,
                    float,
                ),
            ),

            distance >= 0,

            payload.get(
                "coverage_mode"
            )
            == (
                "nearest_supported_station"
            ),
        ]
    )


    record(
        "NEAREST-STATION LOOKUP",
        valid_nearest,
        (
            f"HTTP "
            f"{response.status_code}"
        ),
    )


except Exception as exc:
    record(
        "NEAREST-STATION LOOKUP",
        False,
        str(exc),
    )


# =========================================================
# MODEL METRICS
# =========================================================

try:
    response = client.get(
        "/dashboard/latest",
        params={
            "location_id":
                4618814,
        },
    )

    metrics = (
        response.json()
        .get(
            "model_metrics",
            {}
        )
    )


    metrics_valid = all(
        isinstance(
            metrics.get(
                metric
            ),
            (
                int,
                float,
            ),
        )
        for metric in [
            "mae",
            "rmse",
            "r2",
        ]
    )


    record(
        "MODEL METRICS EXPOSED",
        metrics_valid,
        str(
            metrics
        ),
    )


except Exception as exc:
    record(
        "MODEL METRICS EXPOSED",
        False,
        str(exc),
    )


# =========================================================
# REQUIRED FILES
# =========================================================

required_files = [
    (
        PROJECT_ROOT
        / "models"
        / "citypulse_multilocation_model.joblib"
    ),

    (
        PROJECT_ROOT
        / "data"
        / "processed"
        / "citypulse_multilocation_latest_features.csv"
    ),

    (
        PROJECT_ROOT
        / "reports"
        / "multilocation_model_report.json"
    ),

    (
        PROJECT_ROOT
        / "frontend"
        / "src"
        / "App.tsx"
    ),

    (
        PROJECT_ROOT
        / "frontend"
        / "src"
        / "components"
        / "dashboard"
        / "LahoreMap.tsx"
    ),

    (
        PROJECT_ROOT
        / "frontend"
        / "src"
        / "components"
        / "dashboard"
        / "LocationSelector.tsx"
    ),
]


missing_files = [
    str(
        path.relative_to(
            PROJECT_ROOT
        )
    )
    for path in required_files
    if not path.exists()
]


record(
    "DEPLOYMENT FILES",
    not missing_files,
    (
        ", ".join(
            missing_files
        )
        if missing_files
        else ""
    ),
)


# =========================================================
# FINAL RESULT
# =========================================================

overall_pass = all(
    result[
        "passed"
    ]
    for result
    in results.values()
)


report = {
    "generated_at_utc":
        datetime.now(
            timezone.utc
        ).isoformat(),

    "overall_status":
        (
            "PASS"
            if overall_pass
            else "FAIL"
        ),

    "supported_station_count":
        len(
            locations
        ),

    "station_predictions":
        predictions,

    "checks":
        results,
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


print()
print(
    "----------------------------------------"
)

print(
    "MULTI-LOCATION FINAL QA: "
    + (
        "PASS"
        if overall_pass
        else "FAIL"
    )
)

print(
    f"Report: {REPORT_PATH}"
)

print(
    "----------------------------------------"
)
print()


if not overall_pass:
    sys.exit(1)