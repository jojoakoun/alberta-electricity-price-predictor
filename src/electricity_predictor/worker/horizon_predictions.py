"""Generate price and spike-risk predictions for every configured horizon."""

import pandas as pd

from electricity_predictor.serving.active_model_predictions import predict_price_and_spike_for_horizon


def generate_horizon_predictions(
  feature_row: pd.DataFrame,
  horizons_hours: list[int],
) -> list[dict]:
  """Generate one prediction result for each configured horizon."""
  if len(feature_row) != 1:
    raise ValueError("Prediction requires exactly one feature row.")

  features = feature_row.iloc[0].to_dict()

  return [
    predict_price_and_spike_for_horizon(
      horizon_hours=horizon_hours,
      features=features,
    )
    for horizon_hours in horizons_hours
  ]
