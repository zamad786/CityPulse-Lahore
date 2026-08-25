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
    / "day3_model_comparison.csv"
)

OUTPUT_JSON = (
    REPORTS_DIR
    / "day3_model_selection.json"
)


def print_section(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    print_section(
        "CITYPULSE LAHORE — DAY 3 STEP 8 MODEL SELECTION"
    )

    results = []

    # =====================================================
    # Load reports
    # =====================================================

    print_section("1. LOAD VALIDATION RESULTS")

    for path in MODEL_FILES:

        if not path.exists():
            raise FileNotFoundError(
                f"Missing model result:\n{path}"
            )

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            report = json.load(file)

        metrics = report[
            "validation_metrics"
        ]

        results.append(
            {
                "model": report["model"],
                "mae": float(
                    metrics["mae"]
                ),
                "rmse": float(
                    metrics["rmse"]
                ),
                "r2": float(
                    metrics["r2"]
                ),
                "training_time_seconds": float(
                    report[
                        "training_time_seconds"
                    ]
                ),
            }
        )

    comparison = pd.DataFrame(
        results
    )

    print(
        comparison.to_string(
            index=False
        )
    )

    # =====================================================
    # Metric ranking
    # =====================================================

    print_section("2. CALCULATE METRIC RANKS")

    comparison[
        "mae_rank"
    ] = (
        comparison["mae"]
        .rank(
            method="min",
            ascending=True,
        )
        .astype(int)
    )

    comparison[
        "rmse_rank"
    ] = (
        comparison["rmse"]
        .rank(
            method="min",
            ascending=True,
        )
        .astype(int)
    )

    comparison[
        "r2_rank"
    ] = (
        comparison["r2"]
        .rank(
            method="min",
            ascending=False,
        )
        .astype(int)
    )

    comparison[
        "accuracy_rank_sum"
    ] = (
        comparison["mae_rank"]
        + comparison["rmse_rank"]
        + comparison["r2_rank"]
    )

    comparison = (
        comparison
        .sort_values(
            [
                "accuracy_rank_sum",
                "mae",
                "rmse",
                "training_time_seconds",
            ],
            ascending=[
                True,
                True,
                True,
                True,
            ],
        )
        .reset_index(drop=True)
    )

    comparison.insert(
        0,
        "overall_rank",
        range(
            1,
            len(comparison) + 1,
        ),
    )

    print(
        comparison[
            [
                "overall_rank",
                "model",
                "mae",
                "rmse",
                "r2",
                "training_time_seconds",
                "mae_rank",
                "rmse_rank",
                "r2_rank",
                "accuracy_rank_sum",
            ]
        ]
        .to_string(
            index=False
        )
    )

    # =====================================================
    # Winner
    # =====================================================

    print_section("3. SELECT MODEL")

    winner = comparison.iloc[0]

    selected_model = winner[
        "model"
    ]

    print(
        f"Selected model: "
        f"{selected_model}"
    )

    print(
        f"Validation MAE:  "
        f"{winner['mae']:.4f}"
    )

    print(
        f"Validation RMSE: "
        f"{winner['rmse']:.4f}"
    )

    print(
        f"Validation R²:   "
        f"{winner['r2']:.4f}"
    )

    print(
        f"Training time:   "
        f"{winner['training_time_seconds']:.4f} s"
    )

    print(
        "\nSelection reason:"
    )

    print(
        "The model with the strongest combined "
        "validation accuracy is selected."
    )

    print(
        "Training speed is used only as a "
        "secondary consideration."
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "The test set was NOT used for model selection."
    )

    # =====================================================
    # Save
    # =====================================================

    comparison.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    selection_report = {
        "project": "CityPulse Lahore",
        "day": 3,
        "step": 8,

        "selection_dataset": (
            "validation"
        ),

        "selected_model": (
            selected_model
        ),

        "selected_validation_metrics": {
            "mae": float(
                winner["mae"]
            ),
            "rmse": float(
                winner["rmse"]
            ),
            "r2": float(
                winner["r2"]
            ),
            "training_time_seconds": float(
                winner[
                    "training_time_seconds"
                ]
            ),
        },

        "selection_method": {
            "primary": (
                "MAE + RMSE + R2 rank"
            ),
            "secondary": (
                "training time"
            ),
        },

        "test_set_used_for_selection": False,

        "ranking": (
            comparison
            .to_dict(
                orient="records"
            )
        ),
    }

    with open(
        OUTPUT_JSON,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            selection_report,
            file,
            indent=2,
        )

    print_section("STEP 8 COMPLETE")

    print(
        f"Comparison saved:\n{OUTPUT_CSV}"
    )

    print(
        f"\nSelection report saved:\n{OUTPUT_JSON}"
    )


if __name__ == "__main__":
    main()