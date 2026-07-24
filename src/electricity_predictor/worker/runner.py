"""Orchestrate one idempotent forecast cycle from PostgreSQL features."""

from datetime import datetime

from electricity_predictor.config import load_configuration
from electricity_predictor.logger import get_logger
from electricity_predictor.worker.decision_context_loader import (
  load_decision_context,
)
from electricity_predictor.worker.decision_layer import (
  apply_decision_layer,
)
from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)
from electricity_predictor.worker.hourly_price_database import (
  get_current_database_time,
)
from electricity_predictor.worker.horizon_predictions import (
  generate_horizon_predictions,
)
from electricity_predictor.worker.prediction_run_database import (
  update_predictions_with_final_actual_prices,
  save_failed_prediction_run,
  save_successful_prediction_run,
)


LOGGER = get_logger(__name__)


def run_worker_cycle() -> dict:
  """Backfill outcomes, predict five horizons, and persist one source hour."""
  forecast_source_at: datetime | None = None

  try:
    configuration = load_configuration()
    horizons_hours = configuration["modeling"]["horizons_hours"]

    # Refresh runs before this cycle, so backfill can attach newly finalized
    # observations without replacing any outcome already recorded.
    backfilled_rows = update_predictions_with_final_actual_prices()

    candidate_features = prepare_model_features()

    # The database field is named generated_at, but it stores the forecast's
    # source market-data hour rather than worker wall-clock execution time.
    forecast_source_at = candidate_features.iloc[0][
      "datetime_universal_time"
    ].to_pydatetime()

    predictions = generate_horizon_predictions(
      feature_row=candidate_features,
      horizons_hours=horizons_hours,
    )

    decision_context = load_decision_context()

    decisions = apply_decision_layer(
      predictions=predictions,
      context=decision_context,
    )

    run_id = save_successful_prediction_run(
      generated_at=forecast_source_at,
      decisions=decisions,
      detail="Application pipeline prediction cycle.",
    )

    return {
      "run_id": run_id,
      "generated_at": forecast_source_at,
      "backfilled_rows": backfilled_rows,
      "decisions": decisions,
    }

  except Exception as error:
    # Once selected, the source hour identifies the failed attempt. Earlier
    # failures use database time and remain excluded from successful-run freshness.
    failure_time = forecast_source_at

    if failure_time is None:
      try:
        failure_time = get_current_database_time()
      except Exception:
        # A pre-candidate failure has no source hour. Preserve a useful failure
        # timestamp even when PostgreSQL itself is unavailable.
        failure_time = datetime.now().astimezone()

    try:
      save_failed_prediction_run(
        generated_at=failure_time,
        detail=(
          f"{type(error).__name__}: {error}"
        ),
      )
    except Exception:
      # Failure recording is secondary: report it, then preserve the original
      # worker exception for the scheduler and operator.
      LOGGER.exception("Could not persist the failed worker run.")

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
