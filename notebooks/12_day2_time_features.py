from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_hourly_timeline.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_time_features.csv"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 4 TIME FEATURES"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print_section("1. LOAD DATA")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    # -----------------------------------------------------
    # Parse UTC timestamp
    # -----------------------------------------------------

    print_section("2. PARSE UTC TIMESTAMP")

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    invalid_timestamps = int(
        df["timestamp_utc"].isna().sum()
    )

    print(
        f"Invalid timestamps: "
        f"{invalid_timestamps:,}"
    )

    if invalid_timestamps > 0:
        raise ValueError(
            "Invalid timestamps detected."
        )

    # -----------------------------------------------------
    # Convert to Lahore local time
    # -----------------------------------------------------

    print_section("3. CREATE LAHORE LOCAL TIME")

    df["timestamp_lahore"] = (
        df["timestamp_utc"]
        .dt.tz_convert("Asia/Karachi")
    )

    print(
        "First UTC timestamp:   ",
        df["timestamp_utc"].iloc[0],
    )

    print(
        "First Lahore timestamp:",
        df["timestamp_lahore"].iloc[0],
    )

    # -----------------------------------------------------
    # Time-based features
    # -----------------------------------------------------

    print_section("4. CREATE TIME FEATURES")

    local_time = df["timestamp_lahore"]

    df["year"] = local_time.dt.year
    df["month"] = local_time.dt.month
    df["day"] = local_time.dt.day
    df["hour"] = local_time.dt.hour

    df["day_of_week"] = (
        local_time.dt.dayofweek
    )

    df["day_of_year"] = (
        local_time.dt.dayofyear
    )

    df["week_of_year"] = (
        local_time.dt.isocalendar()
        .week
        .astype(int)
    )

    df["is_weekend"] = (
        df["day_of_week"]
        .isin([5, 6])
        .astype(int)
    )

    print("Created:")
    print("- timestamp_lahore")
    print("- year")
    print("- month")
    print("- day")
    print("- hour")
    print("- day_of_week")
    print("- day_of_year")
    print("- week_of_year")
    print("- is_weekend")

    # -----------------------------------------------------
    # Validate
    # -----------------------------------------------------

    print_section("5. VALIDATE FEATURES")

    new_columns = [
        "timestamp_lahore",
        "year",
        "month",
        "day",
        "hour",
        "day_of_week",
        "day_of_year",
        "week_of_year",
        "is_weekend",
    ]

    for column in new_columns:
        print(
            f"{column}: "
            f"{df[column].isna().sum():,} missing"
        )

    print(
        "\nHour range:",
        df["hour"].min(),
        "to",
        df["hour"].max(),
    )

    print(
        "Month range:",
        df["month"].min(),
        "to",
        df["month"].max(),
    )

    print(
        "Day-of-week range:",
        df["day_of_week"].min(),
        "to",
        df["day_of_week"].max(),
    )

    print(
        "Weekend values:",
        sorted(
            df["is_weekend"]
            .unique()
            .tolist()
        ),
    )

    print(
        "\nPM2.5 missing before save:",
        f"{df['pm25_ug_m3'].isna().sum():,}",
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    print_section("6. SAVE DATASET")

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8",
    )

    print(
        "Saved to:"
    )

    print(OUTPUT_FILE)

    print_section("STEP 4 COMPLETE")

    print(
        f"Rows preserved: {len(df):,}"
    )

    print(
        "PM2.5 gaps remain unchanged."
    )


if __name__ == "__main__":
    main()