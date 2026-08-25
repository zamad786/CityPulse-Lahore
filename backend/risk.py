from typing import Any


# =========================================================
# Punjab EPA PM2.5 reference breakpoint bands
#
# These bands correspond to Punjab EPA AQI categories.
#
# CityPulse applies them to forecast PM2.5 concentration
# to produce predictive risk intelligence.
#
# IMPORTANT:
# This is NOT presented as an official regulatory AQI
# measurement because CityPulse predicts next-hour PM2.5.
# =========================================================


def classify_pm25_risk(
    pm25_ug_m3: float,
) -> dict[str, Any]:

    if pm25_ug_m3 is None:
        raise ValueError(
            "PM2.5 value cannot be None."
        )

    value = float(
        pm25_ug_m3
    )

    if value < 0:
        raise ValueError(
            "PM2.5 cannot be negative."
        )

    # -----------------------------------------------------
    # Punjab EPA PM2.5 breakpoint categories
    # -----------------------------------------------------

    if value <= 15.0:

        return {
            "risk_level": "Good",
            "aqi_reference_band": "0-50",
            "response_level": "Prevention",
            "severity": 1,
            "recommendation": (
                "Air quality conditions are favorable. "
                "Normal outdoor activities can continue."
            ),
        }

    elif value <= 35.0:

        return {
            "risk_level": "Satisfactory",
            "aqi_reference_band": "51-100",
            "response_level": "Prevention",
            "severity": 2,
            "recommendation": (
                "Conditions are generally acceptable. "
                "People unusually sensitive to air "
                "pollution may monitor prolonged "
                "outdoor exposure."
            ),
        }

    elif value <= 70.0:

        return {
            "risk_level": "Moderate",
            "aqi_reference_band": "101-150",
            "response_level": "Preparedness",
            "severity": 3,
            "recommendation": (
                "Sensitive groups should consider "
                "reducing prolonged or strenuous "
                "outdoor activity."
            ),
        }

    elif value <= 140.0:

        return {
            "risk_level": (
                "Unhealthy for Sensitive Groups"
            ),
            "aqi_reference_band": "151-200",
            "response_level": "Alert",
            "severity": 4,
            "recommendation": (
                "Children, older adults, and people "
                "with respiratory or heart conditions "
                "should limit prolonged outdoor "
                "exertion."
            ),
        }

    elif value <= 250.0:

        return {
            "risk_level": "Unhealthy",
            "aqi_reference_band": "201-300",
            "response_level": "Warning",
            "severity": 5,
            "recommendation": (
                "Reduce prolonged outdoor activity. "
                "Sensitive groups should minimize "
                "outdoor exposure where practical."
            ),
        }

    elif value <= 350.0:

        return {
            "risk_level": "Very Unhealthy",
            "aqi_reference_band": "301-400",
            "response_level": "Emergency",
            "severity": 6,
            "recommendation": (
                "Avoid strenuous outdoor activity. "
                "Keep indoor air cleaner where possible "
                "and limit unnecessary exposure."
            ),
        }

    else:

        return {
            "risk_level": "Hazardous",
            "aqi_reference_band": "401-500+",
            "response_level": "Severe",
            "severity": 7,
            "recommendation": (
                "Avoid outdoor activity where possible. "
                "Follow official Punjab health and "
                "air-quality advisories."
            ),
        }


def build_risk_response(
    predicted_pm25: float,
) -> dict[str, Any]:

    risk = classify_pm25_risk(
        predicted_pm25
    )

    return {
        "predicted_pm25_ug_m3": round(
            float(predicted_pm25),
            2,
        ),

        **risk,

        "classification_basis": (
            "Punjab EPA PM2.5 breakpoint bands"
        ),

        "forecast_type": (
            "1-hour-ahead PM2.5 prediction"
        ),

        "regulatory_note": (
            "Forecast risk intelligence, "
            "not an official regulatory AQI reading."
        ),
    }