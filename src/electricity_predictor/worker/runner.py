from electricity_predictor.config import load_configuration
from electricity_predictor.worker.decision_layer import (
  apply_decision_layer,
)
from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)
from electricity_predictor.worker.prediction import (
  generate_horizon_predictions,
)
from electricity_predictor.worker.result_persistence import (
  save_prediction_run,
)


def run_worker_cycle() -> dict:
  """Run one complete application prediction cycle."""
  configuration = load_configuration()
  horizons_hours = configuration["modeling"]["horizons_hours"]

  modeling_data = prepare_model_features()
  latest_feature_row = modeling_data.tail(1).copy()

  predictions = generate_horizon_predictions(
    feature_row=latest_feature_row,
    horizons_hours=horizons_hours,
  )

  decisions = apply_decision_layer(predictions)

  generated_at = latest_feature_row.iloc[0][
    "datetime_universal_time"
  ].to_pydatetime()

  run_id = save_prediction_run(
    generated_at=generated_at,
    decisions=decisions,
    detail="Application pipeline prediction cycle.",
  )

  return {
    "run_id": run_id,
    "generated_at": generated_at,
    "decisions": decisions,
  }


def main() -> None:
  """Run one complete application pipeline cycle."""
  result = run_worker_cycle()

  print(f"Worker cycle completed. Run ID: {result['run_id']}")

  for decision in result["decisions"]:
    print(
      f"{decision['horizon_hours']}h | "
      f"price={decision['predicted_price']:.2f} | "
      f"spike_probability={decision['spike_probability']:.4f} | "
      f"recommendation={decision['recommendation']}"
    )


if __name__ == "__main__":
  main()
