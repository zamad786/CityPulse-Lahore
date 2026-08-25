import sys
from pathlib import Path

import pandas as pd
from fastapi.testclient import (
    TestClient,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)


from backend.main import app


TEST_DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "splits"
    / "citypulse_test.csv"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():

    print_section(
        "CITYPULSE LAHORE — "
        "DAY 3 STEP 14 FASTAPI TEST"
    )

    client = TestClient(
        app
    )

    # =====================================================
    # 1. Root
    # =====================================================

    print_section("1. TEST ROOT ENDPOINT")

    response = client.get(
        "/"
    )

    print(
        f"Status code: "
        f"{response.status_code}"
    )

    print(
        response.json()
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Root endpoint failed."
        )

    # =====================================================
    # 2. Health
    # =====================================================

    print_section("2. TEST /health")

    response = client.get(
        "/health"
    )

    print(
        f"Status code: "
        f"{response.status_code}"
    )

    health = response.json()

    print(
        health
    )

    if response.status_code != 200:
        raise RuntimeError(
            "/health endpoint failed."
        )

    if not health[
        "model_loaded"
    ]:
        raise RuntimeError(
            "Health endpoint reports "
            "model_loaded=False."
        )

    if (
        health["model_name"]
        != "RandomForestRegressor"
    ):
        raise RuntimeError(
            "Unexpected deployed model."
        )

    print(
        "\n/health: PASS"
    )

    # =====================================================
    # 3. Load one real test-row feature example
    # =====================================================

    print_section(
        "3. BUILD REALISTIC PREDICTION REQUEST"
    )

    if not TEST_DATA_FILE.exists():
        raise FileNotFoundError(
            f"Test file not found:\n"
            f"{TEST_DATA_FILE}"
        )

    test_df = pd.read_csv(
        TEST_DATA_FILE
    )

    sample = test_df.iloc[0]

    payload = {
        "timestamp_utc": (
            sample[
                "timestamp_utc"
            ]
        ),

        "pm25_ug_m3": float(
            sample["pm25_ug_m3"]
        ),

        "pm25_lag_1h": float(
            sample["pm25_lag_1h"]
        ),

        "pm25_lag_2h": float(
            sample["pm25_lag_2h"]
        ),

        "pm25_lag_3h": float(
            sample["pm25_lag_3h"]
        ),

        "pm25_lag_6h": float(
            sample["pm25_lag_6h"]
        ),

        "pm25_lag_12h": float(
            sample["pm25_lag_12h"]
        ),

        "pm25_lag_24h": float(
            sample["pm25_lag_24h"]
        ),

        "pm25_rolling_mean_3h": float(
            sample[
                "pm25_rolling_mean_3h"
            ]
        ),

        "pm25_rolling_mean_6h": float(
            sample[
                "pm25_rolling_mean_6h"
            ]
        ),

        "pm25_rolling_mean_12h": float(
            sample[
                "pm25_rolling_mean_12h"
            ]
        ),

        "pm25_rolling_mean_24h": float(
            sample[
                "pm25_rolling_mean_24h"
            ]
        ),

        "temperature_c": float(
            sample["temperature_c"]
        ),

        "relative_humidity_pct": float(
            sample[
                "relative_humidity_pct"
            ]
        ),

        "precipitation_mm": float(
            sample[
                "precipitation_mm"
            ]
        ),

        "wind_speed_m_s": float(
            sample[
                "wind_speed_m_s"
            ]
        ),

        "wind_direction_deg": float(
            sample[
                "wind_direction_deg"
            ]
        ),

        "surface_pressure_hpa": float(
            sample[
                "surface_pressure_hpa"
            ]
        ),
    }

    print(
        f"Timestamp: "
        f"{payload['timestamp_utc']}"
    )

    print(
        f"Measured PM2.5: "
        f"{payload['pm25_ug_m3']}"
    )

    print(
        f"Actual next-hour PM2.5 "
        f"in historical test row: "
        f"{sample['target_pm25_1h']}"
    )

    # =====================================================
    # 4. Predict
    # =====================================================

    print_section("4. TEST /predict")

    response = client.post(
        "/predict",
        json=payload,
    )

    print(
        f"Status code: "
        f"{response.status_code}"
    )

    if response.status_code != 200:

        print(
            response.text
        )

        raise RuntimeError(
            "/predict endpoint failed."
        )

    result = response.json()

    print(
        "\nPrediction response:"
    )

    for key, value in result.items():
        print(
            f"{key}: {value}"
        )

    predicted = result[
        "predicted_pm25_1h_ug_m3"
    ]

    if predicted < 0:
        raise RuntimeError(
            "Prediction is negative."
        )

    if (
        result[
            "forecast_horizon_hours"
        ]
        != 1
    ):
        raise RuntimeError(
            "Incorrect forecast horizon."
        )

    if (
        result[
            "model_name"
        ]
        != "RandomForestRegressor"
    ):
        raise RuntimeError(
            "Incorrect deployed model."
        )

    if "risk" not in result:
        raise RuntimeError(
            "Risk intelligence missing."
        )

    print(
        "\n/predict: PASS"
    )

    # =====================================================
    # 5. Input validation test
    # =====================================================

    print_section(
        "5. TEST INVALID INPUT HANDLING"
    )

    invalid_payload = dict(
        payload
    )

    invalid_payload[
        "pm25_ug_m3"
    ] = -10

    response = client.post(
        "/predict",
        json=invalid_payload,
    )

    print(
        f"Negative PM2.5 status code: "
        f"{response.status_code}"
    )

    if response.status_code != 422:
        raise RuntimeError(
            "Negative PM2.5 should "
            "produce HTTP 422."
        )

    print(
        "Invalid-input validation: PASS"
    )

    # =====================================================
    # Final
    # =====================================================

    print_section(
        "DAY 3 FASTAPI RESULT"
    )

    print(
        "ROOT ENDPOINT:       PASS"
    )

    print(
        "HEALTH ENDPOINT:     PASS"
    )

    print(
        "PREDICTION ENDPOINT: PASS"
    )

    print(
        "RISK RESPONSE:       PASS"
    )

    print(
        "INPUT VALIDATION:    PASS"
    )

    print(
        "\nDAY 3 API TESTING: PASS"
    )


if __name__ == "__main__":
    main()