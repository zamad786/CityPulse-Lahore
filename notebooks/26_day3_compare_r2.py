import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REPORTS_DIR = PROJECT_ROOT / "reports"

MODEL_FILES = [
    REPORTS_DIR / "day3_linear_regression_results.json",
    REPORTS_DIR / "day3_random_forest_results.json",
    REPORTS_DIR / "day3_gradient_boosting_results.json",
    REPORTS_DIR / "day3_xgboost_results.json",
]

OUTPUT_CSV = (
    REPORTS_DIR
    / "day3_step7_r2_comparison.csv"
)

OUTPUT_JSON = (
    REPORTS_DIR
    / "day3_step7_r2_comparison.json"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 3 STEP 7 R2 COMPARISON"
    )

    results = []

    print_section("1. LOAD MODEL RESULTS")

    for file_path in MODEL_FILES:
        if not file_path.exists():
            raise FileNotFoundError(
                f"Missing model report:\n{file_path}"
            )

        with open(
            file_path,
            "r",
            encoding="utf-8",
        ) as file:
            report = json.load(file)

        model_name = report["model"]

        r2 = float(
            report[
                "validation_metrics"
            ]["r2"]
        )

        training_time = float(
            report[
                "training_time_seconds"
            ]
        )

        results.append(
            {
                "model": model_name,
                "r2": r2,
                "training_time_seconds": training_time,
            }
        )

        print(
            f"{model_name}: R²={r2:.4f}"
        )

    # -----------------------------------------------------
    # Rank
    # -----------------------------------------------------

    print_section("2. R2 RANKING")

    comparison = pd.DataFrame(
        results
    )

    comparison = (
        comparison
        .sort_values(
            "r2",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    comparison.insert(
        0,
        "rank",
        range(
            1,
            len(comparison) + 1,
        ),
    )

    print(
        comparison.to_string(
            index=False
        )
    )

    best_model = (
        comparison.iloc[0]["model"]
    )

    best_r2 = float(
        comparison.iloc[0]["r2"]
    )

    print(
        f"\nHighest validation R²: "
        f"{best_r2:.4f}"
    )

    print(
        f"Current R² leader: "
        f"{best_model}"
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    comparison.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    report = {
        "project": "CityPulse Lahore",
        "day": 3,
        "step": 7,
        "metric": "R2",
        "direction": "higher_is_better",
        "dataset": "validation",
        "leader": {
            "model": best_model,
            "r2": best_r2,
        },
        "ranking": (
            comparison
            .to_dict(
                orient="records"
            )
        ),
        "test_set_used": False,
    }

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    print_section("STEP 7 COMPLETE")

    print(
        f"CSV saved:\n{OUTPUT_CSV}"
    )

    print(
        f"\nJSON saved:\n{OUTPUT_JSON}"
    )


if __name__ == "__main__":
    main()