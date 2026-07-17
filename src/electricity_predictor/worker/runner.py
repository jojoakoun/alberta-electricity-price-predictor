from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)


def run_worker_cycle():
  """Run one complete application pipeline cycle."""
  modeling_data = prepare_model_features()

  latest_features = modeling_data.tail(1).copy()

  return latest_features


def main() -> None:
  """Run one worker cycle."""
  latest_features = run_worker_cycle()

  print("Worker cycle completed.")
  print(latest_features)


if __name__ == "__main__":
  main()
