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


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — AQ + WEATHER ALIGNMENT CHECK"
    )

    # ---------------------------------------------------------
    # Load datasets
    # ---------------------------------------------------------

    if not AQ_FILE.exists():
        raise FileNotFoundError(
            f"Air-quality file not found:\n{AQ_FILE}"
        )

    if not WEATHER_FILE.exists():
        raise FileNotFoundError(
            f"Weather file not found:\n{WEATHER_FILE}"
        )

    aq = pd.read_csv(AQ_FILE)
    weather = pd.read_csv(WEATHER_FILE)

    print_section("1. RAW DATASET SIZES")

    print(f"Air-quality rows: {len(aq):,}")
    print(f"Weather rows:     {len(weather):,}")

    # ---------------------------------------------------------
    # Parse timestamps
    # ---------------------------------------------------------

    aq["timestamp"] = pd.to_datetime(
        aq["datetime_from_utc"],
        errors="coerce",
        utc=True,
    )

    weather["timestamp"] = pd.to_datetime(
        weather["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    print_section("2. TIMESTAMP PARSING")

    print(
        "Invalid AQ timestamps:",
        f"{aq['timestamp'].isna().sum():,}",
    )

    print(
        "Invalid weather timestamps:",
        f"{weather['timestamp'].isna().sum():,}",
    )

    aq_valid = (
        aq.dropna(subset=["timestamp"])
        .copy()
    )

    weather_valid = (
        weather.dropna(subset=["timestamp"])
        .copy()
    )

    # ---------------------------------------------------------
    # Date ranges
    # ---------------------------------------------------------

    print_section("3. DATE RANGES")

    aq_start = aq_valid["timestamp"].min()
    aq_end = aq_valid["timestamp"].max()

    weather_start = weather_valid["timestamp"].min()
    weather_end = weather_valid["timestamp"].max()

    print("AQ start:      ", aq_start)
    print("AQ end:        ", aq_end)

    print("Weather start: ", weather_start)
    print("Weather end:   ", weather_end)

    print()

    weather_covers_aq_start = (
        weather_start <= aq_start
    )

    weather_covers_aq_end = (
        weather_end >= aq_end
    )

    print(
        "Weather covers AQ start:",
        weather_covers_aq_start,
    )

    print(
        "Weather covers AQ end:",
        weather_covers_aq_end,
    )

    # ---------------------------------------------------------
    # Duplicate merge-key checks
    # ---------------------------------------------------------

    print_section("4. TIMESTAMP UNIQUENESS")

    aq_duplicate_timestamps = (
        aq_valid["timestamp"]
        .duplicated()
        .sum()
    )

    weather_duplicate_timestamps = (
        weather_valid["timestamp"]
        .duplicated()
        .sum()
    )

    print(
        "AQ duplicate timestamps:",
        f"{aq_duplicate_timestamps:,}",
    )

    print(
        "Weather duplicate timestamps:",
        f"{weather_duplicate_timestamps:,}",
    )

    # ---------------------------------------------------------
    # Basic frequency
    # ---------------------------------------------------------

    print_section("5. DATASET FREQUENCIES")

    aq_times = (
        aq_valid["timestamp"]
        .drop_duplicates()
        .sort_values()
    )

    weather_times = (
        weather_valid["timestamp"]
        .drop_duplicates()
        .sort_values()
    )

    aq_diffs = aq_times.diff()
    weather_diffs = weather_times.diff()

    print("AQ most common intervals:")

    print(
        aq_diffs
        .value_counts()
        .head(10)
        .to_string()
    )

    print("\nWeather most common intervals:")

    print(
        weather_diffs
        .value_counts()
        .head(10)
        .to_string()
    )

    # ---------------------------------------------------------
    # Exact timestamp overlap
    # ---------------------------------------------------------

    print_section("6. EXACT TIMESTAMP OVERLAP")

    aq_index = pd.DatetimeIndex(
        aq_times
    )

    weather_index = pd.DatetimeIndex(
        weather_times
    )

    exact_overlap = (
        aq_index.intersection(
            weather_index
        )
    )

    aq_without_weather = (
        aq_index.difference(
            weather_index
        )
    )

    print(
        "Unique AQ timestamps:",
        f"{len(aq_index):,}",
    )

    print(
        "Unique weather timestamps:",
        f"{len(weather_index):,}",
    )

    print(
        "Exact matching timestamps:",
        f"{len(exact_overlap):,}",
    )

    print(
        "AQ timestamps with no exact weather match:",
        f"{len(aq_without_weather):,}",
    )

    if len(aq_index) > 0:
        exact_match_percent = (
            len(exact_overlap)
            / len(aq_index)
            * 100
        )

        print(
            "AQ → weather exact match rate:",
            f"{exact_match_percent:.2f}%"
        )

    if len(aq_without_weather) > 0:
        print(
            "\nFirst 20 AQ timestamps "
            "without weather:"
        )

        for timestamp in aq_without_weather[:20]:
            print(timestamp)

    # ---------------------------------------------------------
    # Weather coverage specifically inside AQ date range
    # ---------------------------------------------------------

    print_section(
        "7. WEATHER COVERAGE INSIDE AQ PERIOD"
    )

    expected_aq_period_hours = pd.date_range(
        start=aq_start,
        end=aq_end,
        freq="h",
        tz="UTC",
    )

    weather_inside_aq_period = (
        weather_index[
            (weather_index >= aq_start)
            & (weather_index <= aq_end)
        ]
    )

    print(
        "Calendar hours in AQ date range:",
        f"{len(expected_aq_period_hours):,}",
    )

    print(
        "Weather hours inside AQ date range:",
        f"{len(weather_inside_aq_period):,}",
    )

    missing_weather_inside_period = (
        expected_aq_period_hours
        .difference(
            weather_inside_aq_period
        )
    )

    print(
        "Missing weather hours inside AQ period:",
        f"{len(missing_weather_inside_period):,}",
    )

    # ---------------------------------------------------------
    # Missing AQ hours that DO have weather
    # ---------------------------------------------------------

    print_section(
        "8. AQ GAPS VS AVAILABLE WEATHER"
    )

    missing_aq_hours = (
        expected_aq_period_hours
        .difference(
            aq_index
        )
    )

    missing_aq_but_weather_exists = (
        missing_aq_hours
        .intersection(
            weather_index
        )
    )

    print(
        "Missing AQ hours in calendar range:",
        f"{len(missing_aq_hours):,}",
    )

    print(
        "Of those, weather is available:",
        f"{len(missing_aq_but_weather_exists):,}",
    )

    # ---------------------------------------------------------
    # Check weather values specifically at AQ timestamps
    # ---------------------------------------------------------

    print_section(
        "9. WEATHER COMPLETENESS AT AQ TIMESTAMPS"
    )

    weather_columns = [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m",
        "wind_direction_10m",
        "surface_pressure",
    ]

    weather_subset = (
        weather_valid[
            ["timestamp"] + weather_columns
        ]
        .copy()
    )

    aligned_weather = (
        weather_subset[
            weather_subset["timestamp"]
            .isin(aq_index)
        ]
        .copy()
    )

    print(
        "Weather rows matching AQ timestamps:",
        f"{len(aligned_weather):,}",
    )

    for column in weather_columns:
        missing_count = (
            aligned_weather[column]
            .isna()
            .sum()
        )

        print(
            f"{column}: "
            f"{missing_count:,} missing"
        )

    # ---------------------------------------------------------
    # Preliminary alignment assessment
    # ---------------------------------------------------------

    print_section(
        "10. ALIGNMENT ASSESSMENT"
    )

    exact_merge_possible = (
        len(aq_without_weather) == 0
        and aq_duplicate_timestamps == 0
        and weather_duplicate_timestamps == 0
        and weather_covers_aq_start
        and weather_covers_aq_end
    )

    if exact_merge_possible:
        print(
            "RESULT: Exact UTC hourly alignment "
            "appears possible."
        )

        print(
            "Every observed AQ timestamp has an "
            "exact corresponding weather timestamp."
        )

        print(
            "A tolerance-based/asof merge is not "
            "necessary based on timestamp alignment."
        )

    else:
        print(
            "RESULT: Exact alignment is not fully "
            "supported yet."
        )

        print(
            "Review the unmatched timestamps above "
            "before choosing the merge method."
        )

    print_section("COMPARISON COMPLETE")

    print(
        "No rows were merged, removed, filled, "
        "or modified."
    )


if __name__ == "__main__":
    main()