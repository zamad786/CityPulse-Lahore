from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "citypulse_time_features.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "reports"
    / "eda_plots"
)


def save_and_close(filename):
    output_path = (
        OUTPUT_DIR / filename
    )

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=160,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Saved: {output_path}")


def main():
    print(
        "\nCITYPULSE LAHORE — "
        "DAY 2 STEP 6 EDA PLOTS"
    )

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(INPUT_FILE)

    df["timestamp_utc"] = pd.to_datetime(
        df["timestamp_utc"],
        errors="coerce",
        utc=True,
    )

    observed = (
        df.dropna(
            subset=["pm25_ug_m3"]
        )
        .copy()
    )

    # =====================================================
    # Plot 1 — PM2.5 over time
    # =====================================================

    plt.figure(
        figsize=(14, 6)
    )

    plt.plot(
        observed["timestamp_utc"],
        observed["pm25_ug_m3"],
        linewidth=0.8,
    )

    plt.title(
        "Lahore PM2.5 Over Time"
    )

    plt.xlabel(
        "UTC Timestamp"
    )

    plt.ylabel(
        "PM2.5 (µg/m³)"
    )

    plt.grid(
        alpha=0.25
    )

    save_and_close(
        "01_pm25_over_time.png"
    )

    # =====================================================
    # Plot 2 — Average PM2.5 by Lahore hour
    # =====================================================

    hourly = (
        observed.groupby("hour")[
            "pm25_ug_m3"
        ]
        .mean()
    )

    plt.figure(
        figsize=(10, 5)
    )

    plt.plot(
        hourly.index,
        hourly.values,
        marker="o",
    )

    plt.title(
        "Average PM2.5 by Lahore Hour"
    )

    plt.xlabel(
        "Hour of Day (Asia/Karachi)"
    )

    plt.ylabel(
        "Mean PM2.5 (µg/m³)"
    )

    plt.xticks(
        range(0, 24)
    )

    plt.grid(
        alpha=0.25
    )

    save_and_close(
        "02_pm25_by_hour.png"
    )

    # =====================================================
    # Plot 3 — Average PM2.5 by month
    # =====================================================

    monthly = (
        observed.groupby("month")[
            "pm25_ug_m3"
        ]
        .mean()
    )

    plt.figure(
        figsize=(10, 5)
    )

    plt.bar(
        monthly.index,
        monthly.values,
    )

    plt.title(
        "Average PM2.5 by Month"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Mean PM2.5 (µg/m³)"
    )

    plt.xticks(
        range(1, 13)
    )

    save_and_close(
        "03_pm25_by_month.png"
    )

    # =====================================================
    # Plot 4 — PM2.5 vs temperature
    # =====================================================

    plt.figure(
        figsize=(8, 6)
    )

    plt.scatter(
        observed["temperature_c"],
        observed["pm25_ug_m3"],
        alpha=0.25,
        s=10,
    )

    plt.title(
        "PM2.5 vs Temperature"
    )

    plt.xlabel(
        "Temperature (°C)"
    )

    plt.ylabel(
        "PM2.5 (µg/m³)"
    )

    plt.grid(
        alpha=0.25
    )

    save_and_close(
        "04_pm25_vs_temperature.png"
    )

    # =====================================================
    # Plot 5 — PM2.5 vs humidity
    # =====================================================

    plt.figure(
        figsize=(8, 6)
    )

    plt.scatter(
        observed[
            "relative_humidity_pct"
        ],
        observed["pm25_ug_m3"],
        alpha=0.25,
        s=10,
    )

    plt.title(
        "PM2.5 vs Relative Humidity"
    )

    plt.xlabel(
        "Relative Humidity (%)"
    )

    plt.ylabel(
        "PM2.5 (µg/m³)"
    )

    plt.grid(
        alpha=0.25
    )

    save_and_close(
        "05_pm25_vs_humidity.png"
    )

    # =====================================================
    # Plot 6 — PM2.5 vs wind speed
    # =====================================================

    plt.figure(
        figsize=(8, 6)
    )

    plt.scatter(
        observed["wind_speed_m_s"],
        observed["pm25_ug_m3"],
        alpha=0.25,
        s=10,
    )

    plt.title(
        "PM2.5 vs Wind Speed"
    )

    plt.xlabel(
        "Wind Speed (m/s)"
    )

    plt.ylabel(
        "PM2.5 (µg/m³)"
    )

    plt.grid(
        alpha=0.25
    )

    save_and_close(
        "06_pm25_vs_wind_speed.png"
    )

    # =====================================================
    # Plot 7 — PM2.5 monthly coverage
    # =====================================================

    coverage = (
        df.groupby(
            ["year", "month"]
        )
        .agg(
            total_hours=(
                "timestamp_utc",
                "size",
            ),
            observed_hours=(
                "pm25_observed",
                "sum",
            ),
        )
        .reset_index()
    )

    coverage[
        "coverage_percent"
    ] = (
        coverage["observed_hours"]
        / coverage["total_hours"]
        * 100
    )

    coverage[
        "year_month"
    ] = (
        coverage["year"]
        .astype(str)
        + "-"
        + coverage["month"]
        .astype(str)
        .str.zfill(2)
    )

    plt.figure(
        figsize=(13, 5)
    )

    plt.bar(
        coverage["year_month"],
        coverage["coverage_percent"],
    )

    plt.title(
        "PM2.5 Data Coverage by Month"
    )

    plt.xlabel(
        "Month"
    )

    plt.ylabel(
        "Observed PM2.5 Hours (%)"
    )

    plt.xticks(
        rotation=45,
        ha="right",
    )

    plt.ylim(
        0,
        105,
    )

    save_and_close(
        "07_pm25_monthly_coverage.png"
    )

    print(
        "\nSTEP 6 COMPLETE"
    )

    print(
        f"Plots saved in:\n{OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()