import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)

from backend.risk import (
    build_risk_response,
)


TEST_VALUES = [
    10.0,
    25.0,
    50.0,
    100.0,
    200.0,
    300.0,
    500.0,
]


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — "
        "DAY 3 STEP 10 RISK CLASSIFICATION"
    )

    print(
        "Testing representative PM2.5 "
        "forecast concentrations.\n"
    )

    for value in TEST_VALUES:

        result = build_risk_response(
            value
        )

        print(
            f"PM2.5: {value:>6.1f} µg/m³"
        )

        print(
            f"Risk:  "
            f"{result['risk_level']}"
        )

        print(
            f"Band:  "
            f"{result['aqi_reference_band']}"
        )

        print(
            f"Level: "
            f"{result['response_level']}"
        )

        print(
            f"Advice: "
            f"{result['recommendation']}"
        )

        print("-" * 80)

    # -----------------------------------------------------
    # Boundary checks
    # -----------------------------------------------------

    print_section("BOUNDARY TESTS")

    expected = {
        15.0: "Good",
        15.1: "Satisfactory",
        35.0: "Satisfactory",
        35.1: "Moderate",
        70.0: "Moderate",
        70.1: (
            "Unhealthy for Sensitive Groups"
        ),
        140.0: (
            "Unhealthy for Sensitive Groups"
        ),
        140.1: "Unhealthy",
        250.0: "Unhealthy",
        250.1: "Very Unhealthy",
        350.0: "Very Unhealthy",
        350.1: "Hazardous",
    }

    failures = 0

    for value, expected_risk in expected.items():

        result = build_risk_response(
            value
        )

        actual = result[
            "risk_level"
        ]

        passed = (
            actual == expected_risk
        )

        status = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            f"[{status}] "
            f"{value:6.1f} -> "
            f"{actual}"
        )

        if not passed:
            failures += 1

    print_section("STEP 10 RESULT")

    if failures > 0:

        raise SystemExit(
            f"Risk classification failed "
            f"{failures} boundary test(s)."
        )

    print(
        "RISK CLASSIFICATION: PASS"
    )

    print(
        "\nForecast risk logic is ready "
        "for the FastAPI backend."
    )


if __name__ == "__main__":
    main()