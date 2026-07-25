from pathlib import Path

from electricity_predictor.modeling.classification.baseline.naive_spike_baseline import (
  run_classification_baseline,
)
from electricity_predictor.modeling.classification.baseline.rule_spike_baseline import (
  run_aeso_forecast_spike_baseline,
  run_previous_day_spike_baseline,
)
from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_classifier import (
  run_gradient_boosting_classifier,
)
from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_tuning import (
  run_tuned_gradient_boosting,
)
from electricity_predictor.modeling.classification.hist_gradient_boosting.hist_gradient_boosting_classifier import (
  run_hist_gradient_boosting_classifier,
)
from electricity_predictor.modeling.classification.hist_gradient_boosting.hist_gradient_boosting_tuning import (
  run_tuned_hist_gradient_boosting,
)
from electricity_predictor.modeling.classification.extra_trees.extra_trees_classifier import (
  run_extra_trees_classifier,
)
from electricity_predictor.modeling.classification.extra_trees.extra_trees_tuning import (
  run_tuned_extra_trees,
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
from electricity_predictor.modeling.model_results import (
  CLASSIFICATION_VALIDATION_RESULTS_PATH,
  write_model_results,
)
from electricity_predictor.modeling.split import TRAINING_DATASET_PATH


def run_classification_models(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Run the current classification model comparison workflow."""
  # Each task owns a complete validation report, so a rerun starts from headers
  # rather than filtering rows that belong to another model lineage.
  write_model_results(results=[], output_path=results_path)

  print("Running naive spike baseline")
  print("============================")
  run_classification_baseline(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running AESO forecast spike baseline")
  print("====================================")
  run_aeso_forecast_spike_baseline(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running previous-day spike baseline")
  print("===================================")
  run_previous_day_spike_baseline(
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

  print("")
  print("Running HistGradientBoosting Classifier")
  print("=======================================")
  run_hist_gradient_boosting_classifier(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running tuned HistGradientBoosting Classifier")
  print("=============================================")
  run_tuned_hist_gradient_boosting(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running ExtraTrees Classifier")
  print("=============================")
  run_extra_trees_classifier(
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )

  print("")
  print("Running tuned ExtraTrees Classifier")
  print("===================================")
  run_tuned_extra_trees(
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
