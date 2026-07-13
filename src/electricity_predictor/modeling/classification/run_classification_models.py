from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.classification.baseline.naive_spike_baseline import (
  run_classification_baseline,
)
from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_classifier import (
  run_gradient_boosting_classifier,
)
from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_tuning import (
  run_tuned_gradient_boosting,
)
from electricity_predictor.modeling.classification.logistic.logistic_regression import (
  run_logistic_regression,
)
from electricity_predictor.modeling.classification.logistic.logistic_tuning import (
  run_tuned_logistic_regression,
)
from electricity_predictor.modeling.classification.random_forest.random_forest_classifier import (
  run_random_forest_classifier,
)
from electricity_predictor.modeling.classification.random_forest.random_forest_tuning import (
  run_tuned_random_forest,
)
from electricity_predictor.modeling.model_results import MODEL_RESULT_COLUMNS
from electricity_predictor.modeling.split import TRAINING_DATASET_PATH


MODEL_RESULTS_PATH = Path("reports/model_results.csv")


def remove_existing_classification_results(results_path: Path) -> None:
  """Remove old classification rows before rebuilding the comparison report."""
  if not results_path.exists():
    return

  results = pd.read_csv(results_path)

  if "task" not in results.columns:
    raise ValueError("Model results file is missing the task column.")

  # Keep regression results while removing old classification rows.
  regression_results = results[results["task"] != "classification"].copy()

  regression_results.to_csv(
    results_path,
    columns=MODEL_RESULT_COLUMNS,
    index=False,
  )


def run_classification_models(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = MODEL_RESULTS_PATH,
) -> Path:
  """Run the current classification model comparison workflow."""
  remove_existing_classification_results(results_path)

  print("Running naive spike baseline")
  print("============================")
  run_classification_baseline(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running Logistic Regression")
  print("===========================")
  run_logistic_regression(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running tuned Logistic Regression")
  print("==================================")
  run_tuned_logistic_regression(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running Random Forest Classifier")
  print("================================")
  run_random_forest_classifier(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running tuned Random Forest Classifier")
  print("======================================")
  run_tuned_random_forest(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running Gradient Boosting Classifier")
  print("====================================")
  run_gradient_boosting_classifier(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running tuned Gradient Boosting Classifier")
  print("==========================================")
  run_tuned_gradient_boosting(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  return results_path


if __name__ == "__main__":
  written_path = run_classification_models()

  print("")
  print("Classification model comparison complete")
  print("========================================")
  print(f"Results written to: {written_path}")
