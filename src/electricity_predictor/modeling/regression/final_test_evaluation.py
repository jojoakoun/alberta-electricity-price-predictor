from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import build_target_column_name
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.model_results import build_model_result_row, write_model_results
from electricity_predictor.modeling.regression.selected_model import (
  BEST_MODEL_PATH,
  load_selected_regression_models,
  predict_selected_regression_model,
  train_selected_regression_model,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


FINAL_TEST_RESULTS_PATH = Path("reports/final_regression_test_results.csv")


def evaluate_trained_selected_regression_model(
  selected_model: dict,
  model,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Score one fitted selected model on protected evaluation rows."""
  predictions = predict_selected_regression_model(
    selected_model=selected_model,
    model=model,
    data=evaluation_data,
  )
  target = evaluation_data[target_column]

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def evaluate_selected_regression_model(
  selected_model: dict,
  train_data: pd.DataFrame,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Fit when required and score one validation-selected design."""
  model = None

  if selected_model["model_name"] != "naive_baseline":
    model = train_selected_regression_model(
      selected_model=selected_model,
      train_data=train_data,
      target_column=target_column,
    )

  return evaluate_trained_selected_regression_model(
    selected_model=selected_model,
    model=model,
    evaluation_data=evaluation_data,
    target_column=target_column,
  )


def build_final_test_result(
  selected_model: dict,
  scores: dict[str, float],
  row_count: int,
) -> dict:
  """Build one final protected test result row."""
  horizon_hours = int(selected_model["horizon_hours"])

  return build_model_result_row(
    model_name=selected_model["model_name"],
    task="regression",
    horizon_hours=horizon_hours,
    split="test",
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=selected_model.get("model_parameters", ""),
    notes=(
      "Final protected test evaluation after validation selection "
      f"for the {horizon_hours}h horizon."
    ),
  )


def run_final_regression_test_evaluation() -> Path:
  """Evaluate validation-selected regression models on the protected test split."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]

  selected_models = load_selected_regression_models(BEST_MODEL_PATH)
  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
  )

  # After model selection, train on train + validation before the one-time test evaluation.
  final_training_data = pd.concat([train_data, validation_data], ignore_index=True)

  final_results = []

  for selected_model in selected_models.to_dict(orient="records"):
    horizon_hours = int(selected_model["horizon_hours"])
    target_column = build_target_column_name(horizon_hours)

    print("")
    print(f"Final test evaluation: {horizon_hours}h")
    print("=" * 34)
    print(f"Selected model: {selected_model['model_name']}")
    print(f"Target column: {target_column}")

    scores = evaluate_selected_regression_model(
      selected_model=selected_model,
      train_data=final_training_data,
      evaluation_data=test_data,
      target_column=target_column,
    )

    final_results.append(
      build_final_test_result(
        selected_model=selected_model,
        scores=scores,
        row_count=len(test_data),
      )
    )

  return write_model_results(
    results=final_results,
    output_path=FINAL_TEST_RESULTS_PATH,
  )


def print_final_test_summary(results_path: Path) -> None:
  """Print the final protected test results."""
  results = pd.read_csv(results_path)

  print("")
  print("Final protected regression test results")
  print("=======================================")

  for _, result in results.iterrows():
    print(
      f"{int(result['horizon_hours'])}h | "
      f"{result['model_name']} | "
      f"MAE: {result['mae']:.4f} | "
      f"RMSE: {result['rmse']:.4f}"
    )

  print("")
  print(f"Final test results written to: {results_path}")


if __name__ == "__main__":
  written_path = run_final_regression_test_evaluation()
  print_final_test_summary(written_path)
