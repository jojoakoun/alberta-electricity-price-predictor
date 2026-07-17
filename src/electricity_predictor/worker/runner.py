from electricity_predictor.config import load_configuration
from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)
from electricity_predictor.worker.prediction import (
  generate_horizon_predictions,
)


def run_worker_cycle() -> list[dict]:
  """Run one application prediction cycle."""
  configuration = load_configuration()
  horizons_hours = configuration["modeling"]["horizons_hours"]

  modeling_data = prepare_model_features()
  latest_feature_row = modeling_data.tail(1).copy()

  return generate_horizon_predictions(
    feature_row=latest_feature_row,
    horizons_hours=horizons_hours,
  )


def main() -> None:
  """Run one worker prediction cycle."""
  predictions = run_worker_cycle()

  print("Worker cycle completed.")

  for prediction in predictions:
    print(
      f"{prediction['horizon_hours']}h | "
      f"price={prediction['predicted_price']:.2f} | "
      f"spike_probability={prediction['spike_probability']:.4f} | "
      f"is_spike={prediction['is_spike']}"
    )


if __name__ == "__main__":
  main()
