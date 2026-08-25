import os
import sys
import requests


API_URL = "https://api.openaq.org/v3/locations"

# Approximate central Lahore coordinate.
LAHORE_LATITUDE = 31.5204
LAHORE_LONGITUDE = 74.3587

# OpenAQ v3 allows a maximum radius of 25,000 metres.
SEARCH_RADIUS_METERS = 25000


def main():
    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        print("ERROR: OPENAQ_API_KEY is not set.")
        print("Set it in PowerShell before running this script.")
        sys.exit(1)

    headers = {
        "X-API-Key": api_key
    }

    params = {
        "coordinates": f"{LAHORE_LATITUDE},{LAHORE_LONGITUDE}",
        "radius": SEARCH_RADIUS_METERS,
        "limit": 100,
        "page": 1,
    }

    print("Testing OpenAQ API v3...")
    print(
        f"Searching within {SEARCH_RADIUS_METERS / 1000:.0f} km "
        f"of Lahore ({LAHORE_LATITUDE}, {LAHORE_LONGITUDE})"
    )

    try:
        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=30,
        )
    except requests.RequestException as exc:
        print("\nREQUEST FAILED")
        print(type(exc).__name__, exc)
        sys.exit(1)

    print(f"\nHTTP status: {response.status_code}")

    if response.status_code != 200:
        print("\nOpenAQ returned an error:")
        print(response.text[:2000])
        sys.exit(1)

    payload = response.json()

    meta = payload.get("meta", {})
    results = payload.get("results", [])

    print(f"Locations reported by API: {meta.get('found')}")
    print(f"Locations returned on this page: {len(results)}")

    if not results:
        print("\nNo monitoring locations were returned in this search.")
        print("Do not conclude yet that Lahore has no usable OpenAQ data.")
        sys.exit(0)

    print("\n--- RETURNED LOCATIONS ---")

    for location in results:
        print("\n" + "=" * 70)

        print("Location ID:", location.get("id"))
        print("Name:", location.get("name"))
        print("Locality:", location.get("locality"))
        print("Timezone:", location.get("timezone"))

        coordinates = location.get("coordinates") or {}
        print(
            "Coordinates:",
            coordinates.get("latitude"),
            coordinates.get("longitude"),
        )

        provider = location.get("provider") or {}
        print("Provider:", provider.get("name"))

        print("First datetime:", location.get("datetimeFirst"))
        print("Last datetime:", location.get("datetimeLast"))

        sensors = location.get("sensors") or []

        print(f"Sensors ({len(sensors)}):")

        if not sensors:
            print("  None listed")
            continue

        for sensor in sensors:
            parameter = sensor.get("parameter") or {}

            print(
                " ",
                {
                    "sensor_id": sensor.get("id"),
                    "parameter": parameter.get("name"),
                    "display_name": parameter.get("displayName"),
                    "units": parameter.get("units"),
                },
            )


if __name__ == "__main__":
    main()