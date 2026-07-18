"""Stress-test dynamic price decisions using protected-test predictions."""

from pathlib import Path

import joblib
import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import (
  build_target_column_name,
)
from electricity_predictor.modeling.split import (
  load_training_dataset,
  split_time_series_data_from_config,
)
from electricity_predictor.serving.inference import (
  parse_feature_columns,
)


WINDOW_HOURS = 720

REGRESSION_METADATA_PATH = Path(
  "models/regression/selected_regression_model_metadata.csv"
)
DETAIL_OUTPUT_PATH = Path(
  "reports/predicted_decision_stress_test.csv"
)
SUMMARY_OUTPUT_PATH = Path(
  "reports/predicted_decision_stress_test_summary.csv"
)


LABEL_ORDER = {
  "Recommended": 0,
  "Acceptable": 1,
  "Avoid": 2,
}


def classify_price(
  price: float,
  recommended_threshold: float,
  avoid_threshold: float,
) -> str:
  """Classify one price using dynamic thresholds."""
  if price >= avoid_threshold:
    return "Avoid"

  if price <= recommended_threshold:
    return "Recommended"

  return "Acceptable"


def build_dynamic_thresholds(
  data: pd.DataFrame,
  window_hours: int,
) -> pd.DataFrame:
  """Calculate leakage-safe thresholds from preceding actual prices."""
  prices = pd.to_numeric(
    data["actual_price"],
    errors="coerce",
  )

  historical = prices.shift(1)

  q1 = historical.rolling(
    window=window_hours,
    min_periods=window_hours,
  ).quantile(0.25)

  q3 = historical.rolling(
    window=window_hours,
    min_periods=window_hours,
  ).quantile(0.75)

  iqr = q3 - q1

  return pd.DataFrame(
    {
      "recommended_threshold": q1,
      "avoid_threshold": q3 + (1.5 * iqr),
    },
    index=data.index,
  )


def generate_regression_predictions(
  data: pd.DataFrame,
  metadata_row: dict,
) -> pd.Series:
  """Generate vectorized predictions from one saved artifact."""
  artifact = joblib.load(
    Path(str(metadata_row["artifact_path"]))
  )

  feature_columns = parse_feature_columns(
    metadata_row["feature_columns"]
  )

  features = data[feature_columns]

  if features.isna().any().any():
    raise ValueError(
      "Protected-test features contain missing values."
    )

  if isinstance(artifact, dict):
    prediction_column = artifact.get("prediction_column")

    if prediction_column not in data.columns:
      raise ValueError(
        f"Baseline requires missing column: {prediction_column}"
      )

    return pd.to_numeric(
      data[prediction_column],
      errors="coerce",
    )

  predictions = artifact.predict(features)

  return pd.Series(
    predictions,
    index=data.index,
    dtype=float,
  )


def build_horizon_results(
  full_data: pd.DataFrame,
  test_indexes: pd.Index,
  metadata_row: dict,
  thresholds: pd.DataFrame,
) -> pd.DataFrame:
  """Compare predicted and actual decisions for one horizon."""
  horizon_hours = int(metadata_row["horizon_hours"])
  target_column = build_target_column_name(horizon_hours)

  evaluation_data = full_data.loc[test_indexes].copy()

  predicted_price = generate_regression_predictions(
    data=evaluation_data,
    metadata_row=metadata_row,
  )

  actual_price = pd.to_numeric(
    evaluation_data[target_column],
    errors="coerce",
  )

  recommended_threshold = thresholds.loc[
    test_indexes,
    "recommended_threshold",
  ]
  avoid_threshold = thresholds.loc[
    test_indexes,
    "avoid_threshold",
  ]

  result = pd.DataFrame(
    {
      "datetime_universal_time": evaluation_data[
        "datetime_universal_time"
      ],
      "horizon_hours": horizon_hours,
      "model_name": metadata_row["model_name"],
      "predicted_price": predicted_price,
      "actual_price": actual_price,
      "recommended_threshold": recommended_threshold,
      "avoid_threshold": avoid_threshold,
    }
  ).dropna()

  result["predicted_recommendation"] = [
    classify_price(
      price=price,
      recommended_threshold=recommended,
      avoid_threshold=avoid,
    )
    for price, recommended, avoid in zip(
      result["predicted_price"],
      result["recommended_threshold"],
      result["avoid_threshold"],
    )
  ]

  result["actual_recommendation"] = [
    classify_price(
      price=price,
      recommended_threshold=recommended,
      avoid_threshold=avoid,
    )
    for price, recommended, avoid in zip(
      result["actual_price"],
      result["recommended_threshold"],
      result["avoid_threshold"],
    )
  ]

  result["label_distance"] = [
    abs(
      LABEL_ORDER[predicted]
      - LABEL_ORDER[actual]
    )
    for predicted, actual in zip(
      result["predicted_recommendation"],
      result["actual_recommendation"],
    )
  ]

  result["false_recommended"] = (
    result["predicted_recommendation"].eq("Recommended")
    & ~result["actual_recommendation"].eq("Recommended")
  )

  result["false_avoid"] = (
    result["predicted_recommendation"].eq("Avoid")
    & ~result["actual_recommendation"].eq("Avoid")
  )

  return result


def summarize_results(detail: pd.DataFrame) -> pd.DataFrame:
  """Summarize recommendation agreement by horizon."""
  summaries = []

  for horizon_hours, group in detail.groupby("horizon_hours"):
    summaries.append(
      {
        "horizon_hours": int(horizon_hours),
        "row_count": len(group),
        "exact_agreement_rate": (
          group["predicted_recommendation"]
          .eq(group["actual_recommendation"])
          .mean()
        ),
        "false_recommended_rate": (
          group["false_recommended"].mean()
        ),
        "false_avoid_rate": (
          group["false_avoid"].mean()
        ),
        "one_level_error_rate": (
          group["label_distance"].eq(1).mean()
        ),
        "two_level_error_rate": (
          group["label_distance"].eq(2).mean()
        ),
        "predicted_recommended_rate": (
          group["predicted_recommendation"]
          .eq("Recommended")
          .mean()
        ),
        "predicted_acceptable_rate": (
          group["predicted_recommendation"]
          .eq("Acceptable")
          .mean()
        ),
        "predicted_avoid_rate": (
          group["predicted_recommendation"]
          .eq("Avoid")
          .mean()
        ),
        "actual_recommended_rate": (
          group["actual_recommendation"]
          .eq("Recommended")
          .mean()
        ),
        "actual_acceptable_rate": (
          group["actual_recommendation"]
          .eq("Acceptable")
          .mean()
        ),
        "actual_avoid_rate": (
          group["actual_recommendation"]
          .eq("Avoid")
          .mean()
        ),
      }
    )

  return pd.DataFrame(summaries)


def main() -> None:
  """Run the protected-test decision stress test."""
  configuration = load_configuration()
  training_data = load_training_dataset()

  _, _, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=configuration["modeling"],
  )

  full_data = training_data.reset_index(drop=True)
  test_start = test_data["datetime_universal_time"].min()
  test_end = test_data["datetime_universal_time"].max()

  test_indexes = full_data[
    full_data["datetime_universal_time"].between(
      test_start,
      test_end,
    )
  ].index

  thresholds = build_dynamic_thresholds(
    data=full_data,
    window_hours=WINDOW_HOURS,
  )

  metadata = pd.read_csv(
    REGRESSION_METADATA_PATH
  ).sort_values("horizon_hours")

  detail = pd.concat(
    [
      build_horizon_results(
        full_data=full_data,
        test_indexes=test_indexes,
        metadata_row=metadata_row,
        thresholds=thresholds,
      )
      for metadata_row in metadata.to_dict(
        orient="records"
      )
    ],
    ignore_index=True,
  )

  summary = summarize_results(detail)

  DETAIL_OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  detail.to_csv(
    DETAIL_OUTPUT_PATH,
    index=False,
    float_format="%.4f",
  )
  summary.to_csv(
    SUMMARY_OUTPUT_PATH,
    index=False,
    float_format="%.4f",
  )

  print(summary.to_string(index=False))


if __name__ == "__main__":
  main()
