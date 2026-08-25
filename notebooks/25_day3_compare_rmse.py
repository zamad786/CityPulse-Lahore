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
    / "day3_step6_rmse_comparison.csv"
)

OUTPUT_JSON = (
    REPORTS_DIR
    / "day3_step6_rmse_comparison.json"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 3 STEP 6 RMSE COMPARISON"
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

        rmse = float(
            report[
                "validation_metrics"
            ]["rmse"]
        )

        training_time = float(
            report[
                "training_time_seconds"
            ]
        )

        results.append(
            {
                "model": model_name,
                "rmse": rmse,
                "training_time_seconds": training_time,
            }
        )

        print(
            f"{model_name}: RMSE={rmse:.4f}"
        )

    # -----------------------------------------------------
    # Rank
    # -----------------------------------------------------

    print_section("2. RMSE RANKING")

    comparison = pd.DataFrame(
        results
    )

    comparison = (
        comparison
        .sort_values(
            "rmse",
            ascending=True,
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

    best_rmse = float(
        comparison.iloc[0]["rmse"]
    )

    print(
        f"\nLowest validation RMSE: "
        f"{best_rmse:.4f}"
    )

    print(
        f"Current RMSE leader: "
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
        "step": 6,
        "metric": "RMSE",
        "direction": "lower_is_better",
        "dataset": "validation",
        "leader": {
            "model": best_model,
            "rmse": best_rmse,
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

    print_section("STEP 6 COMPLETE")

    print(
        f"CSV saved:\n{OUTPUT_CSV}"
    )

    print(
        f"\nJSON saved:\n{OUTPUT_JSON}"
    )


if __name__ == "__main__":
    main()