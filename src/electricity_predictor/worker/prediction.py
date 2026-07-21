"""Run active regression and classification artifacts for every horizon."""

import pandas as pd

from electricity_predictor.serving.inference import predict_horizon


def generate_horizon_predictions(
  feature_row: pd.DataFrame,
  horizons_hours: list[int],
) -> list[dict]:
  """Generate one prediction result for each configured horizon."""
  if len(feature_row) != 1:
    raise ValueError("Prediction requires exactly one feature row.")

  features = feature_row.iloc[0].to_dict()

  return [
    predict_horizon(
      horizon_hours=horizon_hours,
      features=features,
    )
    for horizon_hours in horizons_hours
  ]
