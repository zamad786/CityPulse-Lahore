import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_time_features.csv"
)

REPORT_DIR = (
    PROJECT_ROOT
    / "reports"
)

SUMMARY_FILE = (
    REPORT_DIR
    / "day2_step5_eda_summary.json"
)

HOURLY_FILE = (
    REPORT_DIR
    / "eda_pm25_by_hour.csv"
)

MONTHLY_FILE = (
    REPORT_DIR
    / "eda_pm25_by_month.csv"
)

WEEKDAY_FILE = (
    REPORT_DIR
    / "eda_pm25_by_day_of_week.csv"
)

CORRELATION_FILE = (
    REPORT_DIR
    / "eda_correlation_matrix.csv"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 2 STEP 5 EDA"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(INPUT_FILE)

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    # -----------------------------------------------------
    # Dataset summary
    # -----------------------------------------------------

    print_section("1. DATASET SUMMARY")

    print(f"Rows:    {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print(
        f"Observed PM2.5: "
        f"{df['pm25_ug_m3'].notna().sum():,}"
    )

    print(
        f"Missing PM2.5:  "
        f"{df['pm25_ug_m3'].isna().sum():,}"
    )

    # -----------------------------------------------------
    # Numerical summary
    # -----------------------------------------------------

    print_section("2. NUMERICAL SUMMARY")

    numeric_columns = [
        "pm25_ug_m3",
        "temperature_c",
        "relative_humidity_pct",
        "precipitation_mm",
        "wind_speed_m_s",
        "wind_direction_deg",
        "surface_pressure_hpa",
    ]

    summary = (
        df[numeric_columns]
        .describe(
            percentiles=[
                0.01,
                0.05,
                0.25,
                0.50,
                0.75,
                0.95,
                0.99,
            ]
        )
    )

    print(summary.to_string())

    # -----------------------------------------------------
    # PM2.5 by local hour
    # -----------------------------------------------------

    print_section("3. PM2.5 BY LAHORE HOUR")

    hourly_summary = (
        df.groupby("hour")["pm25_ug_m3"]
        .agg(
            count="count",
            mean="mean",
            median="median",
            minimum="min",
            maximum="max",
        )
        .reset_index()
    )

    print(
        hourly_summary.to_string(
            index=False
        )
    )

    hourly_summary.to_csv(
        HOURLY_FILE,
        index=False,
    )

    # -----------------------------------------------------
    # PM2.5 by month
    # -----------------------------------------------------

    print_section("4. PM2.5 BY MONTH")

    monthly_summary = (
        df.groupby("month")["pm25_ug_m3"]
        .agg(
            count="count",
            mean="mean",
            median="median",
            minimum="min",
            maximum="max",
        )
        .reset_index()
    )

    print(
        monthly_summary.to_string(
            index=False
        )
    )

    monthly_summary.to_csv(
        MONTHLY_FILE,
        index=False,
    )

    # -----------------------------------------------------
    # PM2.5 by weekday
    # -----------------------------------------------------

    print_section("5. PM2.5 BY DAY OF WEEK")

    weekday_summary = (
        df.groupby(
            "day_of_week"
        )["pm25_ug_m3"]
        .agg(
            count="count",
            mean="mean",
            median="median",
        )
        .reset_index()
    )

    print(
        weekday_summary.to_string(
            index=False
        )
    )

    weekday_summary.to_csv(
        WEEKDAY_FILE,
        index=False,
    )

    # -----------------------------------------------------
    # Correlations
    # -----------------------------------------------------

    print_section("6. CORRELATION MATRIX")

    correlation_columns = [
        "pm25_ug_m3",
        "temperature_c",
        "relative_humidity_pct",
        "precipitation_mm",
        "wind_speed_m_s",
        "wind_direction_deg",
        "surface_pressure_hpa",
        "hour",
        "month",
        "day_of_week",
        "is_weekend",
    ]

    correlations = (
        df[correlation_columns]
        .corr(
            method="pearson"
        )
    )

    print(
        correlations
        .round(3)
        .to_string()
    )

    correlations.to_csv(
        CORRELATION_FILE
    )

    # -----------------------------------------------------
    # PM2.5 correlations
    # -----------------------------------------------------

    print_section(
        "7. CORRELATION WITH PM2.5"
    )

    pm25_correlations = (
        correlations["pm25_ug_m3"]
        .drop("pm25_ug_m3")
        .sort_values(
            key=lambda series: (
                series.abs()
            ),
            ascending=False,
        )
    )

    print(
        pm25_correlations
        .round(4)
        .to_string()
    )

    # -----------------------------------------------------
    # Extremes
    # -----------------------------------------------------

    print_section("8. HIGHEST PM2.5 OBSERVATIONS")

    highest = (
        df[
            [
                "timestamp_utc",
                "pm25_ug_m3",
                "temperature_c",
                "relative_humidity_pct",
                "wind_speed_m_s",
                "precipitation_mm",
            ]
        ]
        .dropna(
            subset=["pm25_ug_m3"]
        )
        .sort_values(
            "pm25_ug_m3",
            ascending=False,
        )
        .head(20)
    )

    print(
        highest.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # Missing PM2.5 by month
    # -----------------------------------------------------

    print_section(
        "9. PM2.5 AVAILABILITY BY MONTH"
    )

    availability = (
        df.groupby(
            ["year", "month"]
        )
        .agg(
            calendar_hours=(
                "timestamp_utc",
                "size",
            ),
            observed_pm25=(
                "pm25_observed",
                "sum",
            ),
        )
        .reset_index()
    )

    availability["missing_pm25"] = (
        availability["calendar_hours"]
        - availability["observed_pm25"]
    )

    availability[
        "coverage_percent"
    ] = (
        availability["observed_pm25"]
        / availability["calendar_hours"]
        * 100
    ).round(2)

    print(
        availability.to_string(
            index=False
        )
    )

    # -----------------------------------------------------
    # Save JSON summary
    # -----------------------------------------------------

    report = {
        "project": "CityPulse Lahore",
        "day": 2,
        "step": 5,

        "rows": int(len(df)),

        "pm25": {
            "observed": int(
                df["pm25_ug_m3"]
                .notna()
                .sum()
            ),
            "missing": int(
                df["pm25_ug_m3"]
                .isna()
                .sum()
            ),
            "mean": float(
                df["pm25_ug_m3"]
                .mean()
            ),
            "median": float(
                df["pm25_ug_m3"]
                .median()
            ),
            "minimum": float(
                df["pm25_ug_m3"]
                .min()
            ),
            "maximum": float(
                df["pm25_ug_m3"]
                .max()
            ),
        },

        "strongest_pm25_correlations": {
            key: float(value)
            for key, value
            in pm25_correlations.items()
        },
    }

    with open(
        SUMMARY_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print_section("STEP 5 COMPLETE")

    print("Saved:")
    print(SUMMARY_FILE)
    print(HOURLY_FILE)
    print(MONTHLY_FILE)
    print(WEEKDAY_FILE)
    print(CORRELATION_FILE)


if __name__ == "__main__":
    main()