"""Evaluate horizon-specific dynamic decision-policy candidates."""

from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import (
  build_target_column_name,
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
from electricity_predictor.modeling.regression.selected_model import (
  BEST_MODEL_PATH,
  load_selected_regression_models,
  predict_selected_regression_model,
  train_selected_regression_model,
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

REGRESSION_SELECTION_PATH = BEST_MODEL_PATH
OUTPUT_PATH = Path(
  "reports/decision_policy_calibration_grid.csv"
)


def generate_predictions(
  train_data: pd.DataFrame,
  data: pd.DataFrame,
  selected_model: dict,
) -> pd.Series:
  """Train on train data and predict the untouched validation rows."""
  horizon_hours = int(selected_model["horizon_hours"])
  target_column = build_target_column_name(horizon_hours)
  model = None

  if selected_model["model_name"] != "naive_baseline":
    model = train_selected_regression_model(
      selected_model=selected_model,
      train_data=train_data,
      target_column=target_column,
    )

  return predict_selected_regression_model(
    selected_model=selected_model,
    model=model,
    data=data,
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


def split_calibration_data(
  data: pd.DataFrame,
  modeling_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
  """Return train and validation data without exposing protected test data."""
  train_data, validation_data, _ = split_time_series_data_from_config(
    data=data,
    modeling_config=modeling_config,
  )

  return train_data, validation_data


def evaluate_candidate(
  data: pd.DataFrame,
  predicted_price: pd.Series,
  actual_price: pd.Series,
  thresholds: pd.DataFrame,
  horizon_hours: int,
  recommended_quantile: float,
  avoid_iqr_multiplier: float,
) -> dict:
  """Evaluate one policy candidate on validation data."""
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
  ).dropna()

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
    "period": "validation",
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
  """Generate decision-policy calibration results from validation data."""
  configuration = load_configuration()
  full_data = load_training_dataset().reset_index(
    drop=True
  )

  train_data, evaluation_data = split_calibration_data(
    data=full_data,
    modeling_config=configuration["modeling"],
  )

  selected_models = load_selected_regression_models(
    REGRESSION_SELECTION_PATH
  )

  results = []

  for selected_model in selected_models.to_dict(
    orient="records"
  ):
    horizon_hours = int(
      selected_model["horizon_hours"]
    )

    predicted_price = generate_predictions(
      train_data=train_data,
      data=evaluation_data,
      selected_model=selected_model,
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

        results.append(
          evaluate_candidate(
            data=evaluation_data,
            predicted_price=predicted_price,
            actual_price=actual_price,
            thresholds=thresholds,
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

  calibration = report.sort_values(
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
