import json
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# Project paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

AQ_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openaq_fcc_pm25_hourly.csv"
)

WEATHER_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_hourly.csv"
)

WEATHER_METADATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_metadata.json"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_aq_weather_merged.csv"
)


# ---------------------------------------------------------
# Known OpenAQ station metadata
# ---------------------------------------------------------

STATION_NAME = (
    "Forman Christian College & Chartered University"
)

OPENAQ_LOCATION_ID = 4757305
OPENAQ_SENSOR_ID = 13341452

STATION_LATITUDE = 31.521146
STATION_LONGITUDE = 74.333954


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — EXACT AQ + WEATHER MERGE"
    )

    # -----------------------------------------------------
    # Validate files
    # -----------------------------------------------------

    for path in [
        AQ_FILE,
        WEATHER_FILE,
        WEATHER_METADATA_FILE,
    ]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{path}"
            )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Load datasets
    # -----------------------------------------------------

    print_section("1. LOAD SOURCE DATA")

    aq = pd.read_csv(AQ_FILE)
    weather = pd.read_csv(WEATHER_FILE)

    with open(
        WEATHER_METADATA_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        weather_metadata = json.load(file)

    print(
        f"Air-quality rows loaded: {len(aq):,}"
    )

    print(
        f"Weather rows loaded:     {len(weather):,}"
    )

    # -----------------------------------------------------
    # Parse UTC timestamps
    # -----------------------------------------------------

    print_section("2. PARSE UTC TIMESTAMPS")

    aq["timestamp_utc"] = pd.to_datetime(
        aq["datetime_from_utc"],
        errors="coerce",
        utc=True,
    )

    weather["timestamp_utc"] = pd.to_datetime(
        weather["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    aq_invalid = (
        aq["timestamp_utc"]
        .isna()
        .sum()
    )

    weather_invalid = (
        weather["timestamp_utc"]
        .isna()
        .sum()
    )

    print(
        f"Invalid AQ timestamps: "
        f"{aq_invalid:,}"
    )

    print(
        f"Invalid weather timestamps: "
        f"{weather_invalid:,}"
    )

    if aq_invalid != 0 or weather_invalid != 0:
        raise ValueError(
            "Invalid timestamps detected. "
            "Merge stopped."
        )

    # -----------------------------------------------------
    # Validate merge-key uniqueness
    # -----------------------------------------------------

    print_section("3. VALIDATE MERGE KEYS")

    aq_duplicates = (
        aq["timestamp_utc"]
        .duplicated()
        .sum()
    )

    weather_duplicates = (
        weather["timestamp_utc"]
        .duplicated()
        .sum()
    )

    print(
        f"AQ duplicate timestamps: "
        f"{aq_duplicates:,}"
    )

    print(
        f"Weather duplicate timestamps: "
        f"{weather_duplicates:,}"
    )

    if aq_duplicates != 0:
        raise ValueError(
            "AQ duplicate timestamps detected. "
            "Merge stopped."
        )

    if weather_duplicates != 0:
        raise ValueError(
            "Weather duplicate timestamps detected. "
            "Merge stopped."
        )

    # -----------------------------------------------------
    # Prepare air-quality table
    # -----------------------------------------------------

    print_section("4. PREPARE AIR-QUALITY FIELDS")

    aq["pm25_ug_m3"] = pd.to_numeric(
        aq["value"],
        errors="coerce",
    )

    aq_merge = aq[
        [
            "timestamp_utc",
            "pm25_ug_m3",
            "has_flags",
            "coverage_expected_count",
            "coverage_observed_count",
            "coverage_percent_complete",
            "coverage_percent_coverage",
        ]
    ].copy()

    print(
        f"AQ rows prepared: "
        f"{len(aq_merge):,}"
    )

    print(
        "Missing PM2.5 values:",
        f"{aq_merge['pm25_ug_m3'].isna().sum():,}",
    )

    # -----------------------------------------------------
    # Prepare weather table
    # -----------------------------------------------------

    print_section("5. PREPARE WEATHER FIELDS")

    weather_merge = weather[
        [
            "timestamp_utc",
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "wind_speed_10m",
            "wind_direction_10m",
            "surface_pressure",
        ]
    ].copy()

    weather_merge = weather_merge.rename(
        columns={
            "temperature_2m": "temperature_c",
            "relative_humidity_2m": (
                "relative_humidity_pct"
            ),
            "precipitation": (
                "precipitation_mm"
            ),
            "wind_speed_10m": (
                "wind_speed_m_s"
            ),
            "wind_direction_10m": (
                "wind_direction_deg"
            ),
            "surface_pressure": (
                "surface_pressure_hpa"
            ),
        }
    )

    print(
        f"Weather rows prepared: "
        f"{len(weather_merge):,}"
    )

    # -----------------------------------------------------
    # Exact UTC merge
    #
    # LEFT merge from AQ:
    # one resulting row per observed PM2.5 timestamp.
    #
    # validate="one_to_one" prevents accidental
    # many-to-one or many-to-many joins.
    # -----------------------------------------------------

    print_section("6. EXACT UTC MERGE")

    merged = aq_merge.merge(
        weather_merge,
        on="timestamp_utc",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    merge_counts = (
        merged["_merge"]
        .value_counts()
    )

    print(
        merge_counts.to_string()
    )

    unmatched_rows = (
        merged["_merge"] != "both"
    ).sum()

    print(
        f"\nUnmatched AQ rows: "
        f"{unmatched_rows:,}"
    )

    if unmatched_rows != 0:
        print(
            "\nExample unmatched timestamps:"
        )

        print(
            merged.loc[
                merged["_merge"] != "both",
                ["timestamp_utc", "_merge"],
            ]
            .head(20)
            .to_string(index=False)
        )

        raise ValueError(
            "Not every AQ observation received "
            "an exact weather match."
        )

    merged = merged.drop(
        columns="_merge"
    )

    # -----------------------------------------------------
    # Add provenance metadata
    # -----------------------------------------------------

    print_section("7. ADD SOURCE METADATA")

    returned_coordinates = (
        weather_metadata.get(
            "returned_coordinates",
            {},
        )
    )

    merged.insert(
        1,
        "station_name",
        STATION_NAME,
    )

    merged.insert(
        2,
        "openaq_location_id",
        OPENAQ_LOCATION_ID,
    )

    merged.insert(
        3,
        "openaq_sensor_id",
        OPENAQ_SENSOR_ID,
    )

    merged.insert(
        4,
        "station_latitude",
        STATION_LATITUDE,
    )

    merged.insert(
        5,
        "station_longitude",
        STATION_LONGITUDE,
    )

    merged.insert(
        6,
        "weather_grid_latitude",
        returned_coordinates.get(
            "latitude"
        ),
    )

    merged.insert(
        7,
        "weather_grid_longitude",
        returned_coordinates.get(
            "longitude"
        ),
    )

    # -----------------------------------------------------
    # Sort chronologically
    # -----------------------------------------------------

    merged = (
        merged
        .sort_values("timestamp_utc")
        .reset_index(drop=True)
    )

    # -----------------------------------------------------
    # Pre-save checks
    # -----------------------------------------------------

    print_section("8. PRE-SAVE CHECKS")

    print(
        f"Merged rows: "
        f"{len(merged):,}"
    )

    print(
        f"Merged columns: "
        f"{len(merged.columns)}"
    )

    print(
        "Duplicate merged timestamps:",
        f"{merged['timestamp_utc'].duplicated().sum():,}",
    )

    print(
        "Missing PM2.5:",
        f"{merged['pm25_ug_m3'].isna().sum():,}",
    )

    weather_columns = [
        "temperature_c",
        "relative_humidity_pct",
        "precipitation_mm",
        "wind_speed_m_s",
        "wind_direction_deg",
        "surface_pressure_hpa",
    ]

    print("\nMissing weather values:")

    for column in weather_columns:
        print(
            f"{column}: "
            f"{merged[column].isna().sum():,}"
        )

    print(
        "\nEarliest merged timestamp:",
        merged["timestamp_utc"].min(),
    )

    print(
        "Latest merged timestamp:",
        merged["timestamp_utc"].max(),
    )

    # -----------------------------------------------------
    # Save combined dataset
    # -----------------------------------------------------

    print_section("9. SAVE MERGED DATASET")

    merged.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print(
        "Combined dataset saved to:"
    )

    print(OUTPUT_FILE)

    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    print_section("10. FIRST 5 MERGED ROWS")

    preview_columns = [
        "timestamp_utc",
        "pm25_ug_m3",
        "temperature_c",
        "relative_humidity_pct",
        "precipitation_mm",
        "wind_speed_m_s",
        "wind_direction_deg",
        "surface_pressure_hpa",
    ]

    print(
        merged[
            preview_columns
        ]
        .head()
        .to_string(index=False)
    )

    print_section("11. LAST 5 MERGED ROWS")

    print(
        merged[
            preview_columns
        ]
        .tail()
        .to_string(index=False)
    )

    print_section("MERGE COMPLETE")

    print(
        "Every observed PM2.5 record was matched "
        "to weather using its exact UTC hour."
    )

    print(
        "No missing PM2.5 hours were created, "
        "filled, or interpolated."
    )

    print(
        "No outlier removal or ML preprocessing "
        "has been performed."
    )


if __name__ == "__main__":
    main()