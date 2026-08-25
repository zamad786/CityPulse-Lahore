import json
from pathlib import Path

import pandas as pd


# =========================================================
# Paths
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CLEANED_AQ_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_cleaned.csv"
)

RAW_WEATHER_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "openmeteo_fcc_weather_hourly.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_hourly_timeline.csv"
)

REPORT_FILE = (
    PROJECT_ROOT
    / "reports"
    / "day2_step3_hourly_timeline_summary.json"
)


WEATHER_COLUMNS = [
    "temperature_c",
    "relative_humidity_pct",
    "precipitation_mm",
    "wind_speed_m_s",
    "wind_direction_deg",
    "surface_pressure_hpa",
]


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 3 COMPLETE HOURLY TIMELINE"
    )

    # -----------------------------------------------------
    # 1. Validate files
    # -----------------------------------------------------

    if not CLEANED_AQ_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found:\n{CLEANED_AQ_FILE}"
        )

    if not RAW_WEATHER_FILE.exists():
        raise FileNotFoundError(
            f"Weather dataset not found:\n{RAW_WEATHER_FILE}"
        )

    # -----------------------------------------------------
    # 2. Load datasets
    # -----------------------------------------------------

    print_section("1. LOAD DATA")

    aq = pd.read_csv(CLEANED_AQ_FILE)
    weather = pd.read_csv(RAW_WEATHER_FILE)

    print(
        f"Cleaned AQ rows: {len(aq):,}"
    )

    print(
        f"Weather rows:    {len(weather):,}"
    )

    # -----------------------------------------------------
    # 3. Parse timestamps
    # -----------------------------------------------------

    print_section("2. PARSE TIMESTAMPS")

    aq["timestamp_utc"] = pd.to_datetime(
        aq["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    weather["timestamp_utc"] = pd.to_datetime(
        weather["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    aq_invalid = int(
        aq["timestamp_utc"]
        .isna()
        .sum()
    )

    weather_invalid = int(
        weather["timestamp_utc"]
        .isna()
        .sum()
    )

    print(
        f"Invalid AQ timestamps:      {aq_invalid:,}"
    )

    print(
        f"Invalid weather timestamps: {weather_invalid:,}"
    )

    if aq_invalid > 0 or weather_invalid > 0:
        raise ValueError(
            "Invalid timestamps detected."
        )

    aq_duplicate_timestamps = int(
        aq["timestamp_utc"]
        .duplicated()
        .sum()
    )

    weather_duplicate_timestamps = int(
        weather["timestamp_utc"]
        .duplicated()
        .sum()
    )

    print(
        f"AQ duplicate timestamps:      "
        f"{aq_duplicate_timestamps:,}"
    )

    print(
        f"Weather duplicate timestamps: "
        f"{weather_duplicate_timestamps:,}"
    )

    if (
        aq_duplicate_timestamps > 0
        or weather_duplicate_timestamps > 0
    ):
        raise ValueError(
            "Duplicate timestamp keys detected."
        )

    # -----------------------------------------------------
    # 4. Determine AQ modelling period
    # -----------------------------------------------------

    print_section("3. DEFINE HOURLY MODELLING PERIOD")

    start_timestamp = (
        aq["timestamp_utc"].min()
    )

    end_timestamp = (
        aq["timestamp_utc"].max()
    )

    print(
        f"Start: {start_timestamp}"
    )

    print(
        f"End:   {end_timestamp}"
    )

    full_hourly_index = pd.date_range(
        start=start_timestamp,
        end=end_timestamp,
        freq="h",
        tz="UTC",
    )

    timeline = pd.DataFrame(
        {
            "timestamp_utc": (
                full_hourly_index
            )
        }
    )

    print(
        f"Complete calendar hours: "
        f"{len(timeline):,}"
    )

    # -----------------------------------------------------
    # 5. Prepare AQ measurements
    # -----------------------------------------------------

    print_section("4. PREPARE PM2.5 OBSERVATIONS")

    aq_columns = [
        "timestamp_utc",
        "pm25_ug_m3",
        "has_flags",
        "coverage_expected_count",
        "coverage_observed_count",
        "coverage_percent_complete",
        "coverage_percent_coverage",
    ]

    aq_measurements = (
        aq[aq_columns]
        .copy()
    )

    print(
        f"Observed PM2.5 timestamps: "
        f"{len(aq_measurements):,}"
    )

    # -----------------------------------------------------
    # 6. Prepare full weather series
    # -----------------------------------------------------

    print_section("5. PREPARE WEATHER SERIES")

    weather = weather.rename(
        columns={
            "temperature_2m": (
                "temperature_c"
            ),
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

    weather_subset = weather[
        [
            "timestamp_utc",
            "temperature_c",
            "relative_humidity_pct",
            "precipitation_mm",
            "wind_speed_m_s",
            "wind_direction_deg",
            "surface_pressure_hpa",
        ]
    ].copy()

    weather_subset = (
        weather_subset[
            (
                weather_subset["timestamp_utc"]
                >= start_timestamp
            )
            &
            (
                weather_subset["timestamp_utc"]
                <= end_timestamp
            )
        ]
        .copy()
    )

    print(
        f"Weather rows inside AQ period: "
        f"{len(weather_subset):,}"
    )

    # -----------------------------------------------------
    # 7. Merge complete clock + AQ + weather
    # -----------------------------------------------------

    print_section("6. BUILD COMPLETE HOURLY TIMELINE")

    timeline = timeline.merge(
        aq_measurements,
        on="timestamp_utc",
        how="left",
        validate="one_to_one",
    )

    timeline = timeline.merge(
        weather_subset,
        on="timestamp_utc",
        how="left",
        validate="one_to_one",
    )

    # Explicit observation indicator.
    timeline["pm25_observed"] = (
        timeline["pm25_ug_m3"]
        .notna()
    )

    # -----------------------------------------------------
    # 8. Add static station metadata
    # -----------------------------------------------------

    print_section("7. ADD STATION METADATA")

    static_columns = [
        "station_name",
        "openaq_location_id",
        "openaq_sensor_id",
        "station_latitude",
        "station_longitude",
        "weather_grid_latitude",
        "weather_grid_longitude",
    ]

    for column in static_columns:
        unique_values = (
            aq[column]
            .drop_duplicates()
        )

        if len(unique_values) != 1:
            raise ValueError(
                f"{column} does not contain "
                "exactly one unique value."
            )

        timeline[column] = (
            unique_values.iloc[0]
        )

    # -----------------------------------------------------
    # 9. Reorder columns
    # -----------------------------------------------------

    final_columns = [
        "timestamp_utc",

        "station_name",
        "openaq_location_id",
        "openaq_sensor_id",
        "station_latitude",
        "station_longitude",
        "weather_grid_latitude",
        "weather_grid_longitude",

        "pm25_observed",
        "pm25_ug_m3",

        "has_flags",
        "coverage_expected_count",
        "coverage_observed_count",
        "coverage_percent_complete",
        "coverage_percent_coverage",

        "temperature_c",
        "relative_humidity_pct",
        "precipitation_mm",
        "wind_speed_m_s",
        "wind_direction_deg",
        "surface_pressure_hpa",
    ]

    timeline = timeline[
        final_columns
    ].copy()

    # -----------------------------------------------------
    # 10. Validation
    # -----------------------------------------------------

    print_section("8. VALIDATE HOURLY TIMELINE")

    total_rows = len(timeline)

    observed_pm25 = int(
        timeline["pm25_observed"]
        .sum()
    )

    missing_pm25 = int(
        timeline["pm25_ug_m3"]
        .isna()
        .sum()
    )

    duplicate_timestamps = int(
        timeline["timestamp_utc"]
        .duplicated()
        .sum()
    )

    hourly_differences = (
        timeline["timestamp_utc"]
        .diff()
    )

    non_hourly_intervals = int(
        (
            hourly_differences
            .dropna()
            != pd.Timedelta(hours=1)
        ).sum()
    )

    print(
        f"Timeline rows:              "
        f"{total_rows:,}"
    )

    print(
        f"Observed PM2.5 hours:       "
        f"{observed_pm25:,}"
    )

    print(
        f"Missing PM2.5 hours:        "
        f"{missing_pm25:,}"
    )

    print(
        f"Duplicate timestamps:       "
        f"{duplicate_timestamps:,}"
    )

    print(
        f"Non-1-hour intervals:       "
        f"{non_hourly_intervals:,}"
    )

    print("\nMissing weather values:")

    weather_missing = {}

    for column in WEATHER_COLUMNS:
        count = int(
            timeline[column]
            .isna()
            .sum()
        )

        weather_missing[column] = count

        print(
            f"{column}: "
            f"{count:,}"
        )

    # -----------------------------------------------------
    # Expected integrity checks
    # -----------------------------------------------------

    if total_rows != len(
        full_hourly_index
    ):
        raise ValueError(
            "Timeline row count does not match "
            "the complete hourly range."
        )

    if observed_pm25 != len(aq):
        raise ValueError(
            "Observed PM2.5 count changed."
        )

    if duplicate_timestamps != 0:
        raise ValueError(
            "Duplicate timeline timestamps detected."
        )

    if non_hourly_intervals != 0:
        raise ValueError(
            "Timeline is not strictly hourly."
        )

    if any(
        value > 0
        for value in weather_missing.values()
    ):
        raise ValueError(
            "Weather is missing on one or more "
            "timeline hours."
        )

    # -----------------------------------------------------
    # 11. Show missing PM2.5 examples
    # -----------------------------------------------------

    print_section("9. EXAMPLE MISSING PM2.5 HOURS")

    missing_examples = (
        timeline.loc[
            ~timeline["pm25_observed"],
            [
                "timestamp_utc",
                "pm25_ug_m3",
                "temperature_c",
                "relative_humidity_pct",
            ],
        ]
        .head(20)
    )

    print(
        missing_examples
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # 12. Show observed examples
    # -----------------------------------------------------

    print_section("10. FIRST 10 TIMELINE ROWS")

    print(
        timeline[
            [
                "timestamp_utc",
                "pm25_observed",
                "pm25_ug_m3",
                "temperature_c",
                "relative_humidity_pct",
            ]
        ]
        .head(10)
        .to_string(index=False)
    )

    # -----------------------------------------------------
    # 13. Save timeline
    # -----------------------------------------------------

    print_section("11. SAVE HOURLY TIMELINE")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    timeline.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print(
        "Hourly timeline saved to:"
    )

    print(OUTPUT_FILE)

    # -----------------------------------------------------
    # 14. Save report
    # -----------------------------------------------------

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 3,

        "input_cleaned_dataset": str(
            CLEANED_AQ_FILE
        ),

        "input_weather_dataset": str(
            RAW_WEATHER_FILE
        ),

        "output_file": str(
            OUTPUT_FILE
        ),

        "timeline": {
            "start_timestamp_utc": str(
                start_timestamp
            ),
            "end_timestamp_utc": str(
                end_timestamp
            ),
            "total_calendar_hours": int(
                total_rows
            ),
            "observed_pm25_hours": int(
                observed_pm25
            ),
            "missing_pm25_hours": int(
                missing_pm25
            ),
            "duplicate_timestamps": int(
                duplicate_timestamps
            ),
            "non_hourly_intervals": int(
                non_hourly_intervals
            ),
        },

        "weather_missing": (
            weather_missing
        ),

        "methodology": {
            "frequency": "1 hour",
            "pm25_interpolated": False,
            "pm25_forward_filled": False,
            "weather_complete": True,
            "purpose": (
                "Ensure future lag and target "
                "features represent actual clock hours"
            ),
        },
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        REPORT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nTimeline report saved to:"
    )

    print(REPORT_FILE)

    # -----------------------------------------------------
    # Finish
    # -----------------------------------------------------

    print_section("STEP 3 COMPLETE")

    print(
        "Complete hourly timeline created successfully."
    )

    print(
        "PM2.5 gaps remain explicit NaN values."
    )

    print(
        "Weather remains available for every hour."
    )

    print(
        "The dataset is now safe for clock-based "
        "lag and target construction later."
    )


if __name__ == "__main__":
    main()