"""Evaluate horizon-specific dynamic decision-policy candidates."""

from pathlib import Path

import joblib
import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import (
  build_target_column_name,
)
from electricity_predictor.features.feature_columns import (
  parse_model_feature_columns,
)
from electricity_predictor.modeling.decision.price_policy import classify_price
from electricity_predictor.modeling.decision.thresholds import (
  DECISION_WINDOW_HOURS,
  build_rolling_price_thresholds,
)
from electricity_predictor.modeling.split import (
  load_training_dataset,
  split_time_series_data_from_config,
)


WINDOW_HOURS = DECISION_WINDOW_HOURS

RECOMMENDED_QUANTILES = [
  0.10,
  0.15,
  0.20,
  0.25,
]

AVOID_IQR_MULTIPLIERS = [
  1.5,
  2.0,
  2.5,
  3.0,
]

REGRESSION_METADATA_PATH = Path(
  "models/regression/selected_regression_model_metadata.csv"
)
OUTPUT_PATH = Path(
  "reports/decision_policy_calibration_grid.csv"
)


def generate_predictions(
  data: pd.DataFrame,
  metadata_row: dict,
) -> pd.Series:
  """Generate predictions from one saved regression artifact."""
  artifact = joblib.load(
    Path(str(metadata_row["artifact_path"]))
  )

  feature_columns = parse_model_feature_columns(
    metadata_row["feature_columns"]
  )

  if isinstance(artifact, dict):
    prediction_column = artifact["prediction_column"]

    return pd.to_numeric(
      data[prediction_column],
      errors="coerce",
    )

  return pd.Series(
    artifact.predict(data[feature_columns]),
    index=data.index,
    dtype=float,
  )


def build_thresholds(
  prices: pd.Series,
  recommended_quantile: float,
  avoid_iqr_multiplier: float,
) -> pd.DataFrame:
  """Build leakage-safe rolling thresholds."""
  return build_rolling_price_thresholds(
    prices=prices,
    window_hours=WINDOW_HOURS,
    recommended_quantile=recommended_quantile,
    avoid_iqr_multiplier=avoid_iqr_multiplier,
  )


def evaluate_candidate(
  data: pd.DataFrame,
  predicted_price: pd.Series,
  actual_price: pd.Series,
  thresholds: pd.DataFrame,
  period: str,
  horizon_hours: int,
  recommended_quantile: float,
  avoid_iqr_multiplier: float,
) -> dict:
  """Evaluate one policy candidate in one time period."""
  if period == "calibration_2025":
    mask = data[
      "datetime_universal_time"
    ].dt.year.eq(2025)
  else:
    mask = data[
      "datetime_universal_time"
    ].dt.year.eq(2026)

  evaluation = pd.DataFrame(
    {
      "predicted_price": predicted_price,
      "actual_price": actual_price,
      "recommended_threshold": thresholds[
        "recommended_threshold"
      ],
      "avoid_threshold": thresholds[
        "avoid_threshold"
      ],
    }
  ).loc[mask].dropna()

  predicted_label = pd.Series(
    [
      classify_price(
        price=row.predicted_price,
        recommended_threshold=row.recommended_threshold,
        avoid_threshold=row.avoid_threshold,
      )
      for row in evaluation.itertuples()
    ],
    index=evaluation.index,
  )

  actual_label = pd.Series(
    [
      classify_price(
        price=row.actual_price,
        recommended_threshold=row.recommended_threshold,
        avoid_threshold=row.avoid_threshold,
      )
      for row in evaluation.itertuples()
    ],
    index=evaluation.index,
  )

  false_recommended = (
    predicted_label.eq("Recommended")
    & ~actual_label.eq("Recommended")
  )

  false_avoid = (
    predicted_label.eq("Avoid")
    & ~actual_label.eq("Avoid")
  )

  return {
    "period": period,
    "horizon_hours": horizon_hours,
    "recommended_quantile": recommended_quantile,
    "avoid_iqr_multiplier": avoid_iqr_multiplier,
    "row_count": len(evaluation),
    "exact_agreement_rate": (
      predicted_label.eq(actual_label).mean()
    ),
    "false_recommended_rate": (
      false_recommended.mean()
    ),
    "false_avoid_rate": false_avoid.mean(),
    "predicted_recommended_rate": (
      predicted_label.eq("Recommended").mean()
    ),
    "predicted_acceptable_rate": (
      predicted_label.eq("Acceptable").mean()
    ),
    "predicted_avoid_rate": (
      predicted_label.eq("Avoid").mean()
    ),
  }


def main() -> None:
  """Generate calibration-grid results for 2025 and 2026."""
  configuration = load_configuration()
  full_data = load_training_dataset().reset_index(
    drop=True
  )

  _, _, test_data = split_time_series_data_from_config(
    data=full_data,
    modeling_config=configuration["modeling"],
  )

  start = test_data[
    "datetime_universal_time"
  ].min()
  end = test_data[
    "datetime_universal_time"
  ].max()

  evaluation_data = full_data[
    full_data["datetime_universal_time"].between(
      start,
      end,
    )
  ].copy()

  metadata = pd.read_csv(
    REGRESSION_METADATA_PATH
  ).sort_values("horizon_hours")

  results = []

  for metadata_row in metadata.to_dict(
    orient="records"
  ):
    horizon_hours = int(
      metadata_row["horizon_hours"]
    )

    predicted_price = generate_predictions(
      data=evaluation_data,
      metadata_row=metadata_row,
    )

    actual_price = pd.to_numeric(
      evaluation_data[
        build_target_column_name(horizon_hours)
      ],
      errors="coerce",
    )

    for recommended_quantile in (
      RECOMMENDED_QUANTILES
    ):
      for avoid_multiplier in (
        AVOID_IQR_MULTIPLIERS
      ):
        thresholds = build_thresholds(
          prices=evaluation_data[
            "actual_price"
          ],
          recommended_quantile=(
            recommended_quantile
          ),
          avoid_iqr_multiplier=(
            avoid_multiplier
          ),
        )

        for period in [
          "calibration_2025",
          "holdout_2026",
        ]:
          results.append(
            evaluate_candidate(
              data=evaluation_data,
              predicted_price=predicted_price,
              actual_price=actual_price,
              thresholds=thresholds,
              period=period,
              horizon_hours=horizon_hours,
              recommended_quantile=(
                recommended_quantile
              ),
              avoid_iqr_multiplier=(
                avoid_multiplier
              ),
            )
          )

  report = pd.DataFrame(results)

  OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  report.to_csv(
    OUTPUT_PATH,
    index=False,
    float_format="%.4f",
  )

  calibration = report[
    report["period"].eq("calibration_2025")
  ].sort_values(
    [
      "horizon_hours",
      "false_recommended_rate",
      "false_avoid_rate",
      "exact_agreement_rate",
    ],
    ascending=[True, True, True, False],
  )

  print(
    calibration.groupby(
      "horizon_hours"
    ).head(5).to_string(index=False)
  )


if __name__ == "__main__":
  main()
