from datetime import datetime

from electricity_predictor.config import load_configuration
from electricity_predictor.worker.decision_context_loader import (
  load_decision_context,
)
from electricity_predictor.worker.decision_layer import (
  apply_decision_layer,
)
from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)
from electricity_predictor.worker.persistence import (
  get_database_time,
)
from electricity_predictor.worker.prediction import (
  generate_horizon_predictions,
)
from electricity_predictor.worker.result_persistence import (
  backfill_prediction_actual_prices,
  save_failed_prediction_run,
  save_prediction_run,
)


def run_worker_cycle() -> dict:
  """Run one complete application prediction cycle."""
  generated_at: datetime | None = None

  try:
    configuration = load_configuration()
    horizons_hours = configuration["modeling"]["horizons_hours"]

    backfilled_rows = backfill_prediction_actual_prices()

    modeling_data = prepare_model_features()
    latest_feature_row = modeling_data.tail(1).copy()

    generated_at = latest_feature_row.iloc[0][
      "datetime_universal_time"
    ].to_pydatetime()

    predictions = generate_horizon_predictions(
      feature_row=latest_feature_row,
      horizons_hours=horizons_hours,
    )

    decision_context = load_decision_context()

    decisions = apply_decision_layer(
      predictions=predictions,
      context=decision_context,
    )

    run_id = save_prediction_run(
      generated_at=generated_at,
      decisions=decisions,
      detail="Application pipeline prediction cycle.",
    )

    return {
      "run_id": run_id,
      "generated_at": generated_at,
      "backfilled_rows": backfilled_rows,
      "decisions": decisions,
    }

  except Exception as error:
    failure_time = generated_at

    if failure_time is None:
      try:
        failure_time = get_database_time()
      except Exception:
        failure_time = datetime.now().astimezone()

    try:
      save_failed_prediction_run(
        generated_at=failure_time,
        detail=(
          f"{type(error).__name__}: {error}"
        ),
      )
    except Exception:
      pass

    raise


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
