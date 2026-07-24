"""Compare frozen champion and challenger results without promoting models."""

from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd

from electricity_predictor.features.feature_engineering import (
  build_target_column_name,
)
from electricity_predictor.features.feature_columns import (
  parse_model_feature_columns,
)
from electricity_predictor.modeling.classification.decision_threshold import (
  apply_decision_threshold,
)
from electricity_predictor.modeling.lifecycle.candidate_run import (
  read_json_file,
  write_json_file,
)
from electricity_predictor.modeling.lifecycle.frozen_splits import (
  load_frozen_candidate_splits,
  resolve_latest_candidate_manifest_path,
)
from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
  mean_absolute_error_value,
  root_mean_squared_error_value,
)


def load_metadata(
  metadata_path: Path,
  required_columns: set[str],
) -> pd.DataFrame:
  """Load and validate one model metadata table."""
  if not metadata_path.exists():
    raise FileNotFoundError(
      f"Model metadata not found: {metadata_path}"
    )

  metadata = pd.read_csv(
    metadata_path
  )

  missing_columns = (
    required_columns
    - set(metadata.columns)
  )

  if missing_columns:
    raise ValueError(
      f"Metadata {metadata_path} is missing columns: "
      f"{sorted(missing_columns)}"
    )

  return metadata.sort_values(
    "horizon_hours"
  ).reset_index(drop=True)


def validate_features(
  data: pd.DataFrame,
  feature_columns: list[str],
) -> pd.DataFrame:
  """Return complete features in artifact order."""
  missing_columns = (
    set(feature_columns)
    - set(data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Evaluation data is missing model features: "
      f"{sorted(missing_columns)}"
    )

  features = data[
    feature_columns
  ]

  if features.isna().any().any():
    raise ValueError(
      "Evaluation features contain missing values."
    )

  return features


def generate_regression_predictions(
  metadata_row: dict,
  evaluation_data: pd.DataFrame,
) -> pd.Series:
  """Generate predictions from one regression artifact."""
  artifact = joblib.load(
    Path(
      str(
        metadata_row[
          "artifact_path"
        ]
      )
    )
  )

  if isinstance(artifact, dict):
    prediction_column = artifact.get(
      "prediction_column"
    )

    if prediction_column not in evaluation_data.columns:
      raise ValueError(
        "Regression baseline requires missing column: "
        f"{prediction_column}"
      )

    return pd.to_numeric(
      evaluation_data[
        prediction_column
      ],
      errors="coerce",
    )

  feature_columns = parse_model_feature_columns(
    metadata_row[
      "feature_columns"
    ]
  )

  features = validate_features(
    data=evaluation_data,
    feature_columns=feature_columns,
  )

  return pd.Series(
    artifact.predict(features),
    index=evaluation_data.index,
    dtype=float,
  )


def evaluate_regression_metadata(
  metadata_path: Path,
  evaluation_data: pd.DataFrame,
  source: str,
  model_version: str,
) -> pd.DataFrame:
  """Evaluate one regression model collection."""
  metadata = load_metadata(
    metadata_path=metadata_path,
    required_columns={
      "model_name",
      "horizon_hours",
      "artifact_path",
      "feature_columns",
    },
  )

  rows = []

  for metadata_row in metadata.to_dict(
    orient="records"
  ):
    horizon_hours = int(
      metadata_row[
        "horizon_hours"
      ]
    )

    target_column = build_target_column_name(
      horizon_hours
    )

    target = pd.to_numeric(
      evaluation_data[
        target_column
      ],
      errors="coerce",
    )

    prediction = generate_regression_predictions(
      metadata_row=metadata_row,
      evaluation_data=evaluation_data,
    )

    if target.isna().any():
      raise ValueError(
        f"Regression target contains missing values: "
        f"{target_column}"
      )

    if prediction.isna().any():
      raise ValueError(
        f"Regression predictions contain missing values: "
        f"{horizon_hours}h"
      )

    rows.append(
      {
        "source": source,
        "model_version": model_version,
        "horizon_hours": horizon_hours,
        "model_name": metadata_row[
          "model_name"
        ],
        "evaluation_rows": len(
          evaluation_data
        ),
        "mae": mean_absolute_error_value(
          target,
          prediction,
        ),
        "rmse": root_mean_squared_error_value(
          target,
          prediction,
        ),
      }
    )

  return pd.DataFrame(rows)


def extract_single_spike_threshold(
  metadata: pd.DataFrame,
  source: str,
) -> float:
  """Read one shared spike definition from metadata."""
  thresholds = (
    pd.to_numeric(
      metadata[
        "spike_threshold"
      ],
      errors="coerce",
    )
    .dropna()
    .unique()
  )

  if len(thresholds) != 1:
    raise ValueError(
      f"{source} must contain exactly one "
      "shared spike threshold."
    )

  return float(
    thresholds[0]
  )


def generate_classification_predictions(
  metadata_row: dict,
  evaluation_data: pd.DataFrame,
  reference_spike_threshold: float,
) -> tuple[pd.Series, pd.Series | None]:
  """Generate classification decisions and probabilities."""
  artifact = joblib.load(
    Path(
      str(
        metadata_row[
          "artifact_path"
        ]
      )
    )
  )

  if isinstance(artifact, dict):
    prediction_column = artifact.get(
      "prediction_column"
    )

    if prediction_column not in evaluation_data.columns:
      raise ValueError(
        "Classification baseline requires missing column: "
        f"{prediction_column}"
      )

    spike_threshold = float(
      reference_spike_threshold
    )

    prediction = (
      pd.to_numeric(
        evaluation_data[
          prediction_column
        ],
        errors="coerce",
      )
      > spike_threshold
    ).astype(int)

    return prediction, None

  feature_columns = parse_model_feature_columns(
    metadata_row[
      "feature_columns"
    ]
  )

  features = validate_features(
    data=evaluation_data,
    feature_columns=feature_columns,
  )

  decision_threshold = pd.to_numeric(
    pd.Series(
      [
        metadata_row.get(
          "decision_threshold"
        )
      ]
    ),
    errors="coerce",
  ).iloc[0]

  if pd.isna(
    decision_threshold
  ):
    raise ValueError(
      "Learned classifier is missing its "
      "decision threshold."
    )

  probability = pd.Series(
    artifact.predict_proba(
      features
    )[:, 1],
    index=evaluation_data.index,
    dtype=float,
  )

  prediction = pd.Series(
    apply_decision_threshold(
      probability=probability,
      threshold=float(
        decision_threshold
      ),
    ),
    index=evaluation_data.index,
    dtype=int,
  )

  return prediction, probability


def evaluate_classification_metadata(
  metadata_path: Path,
  evaluation_data: pd.DataFrame,
  source: str,
  model_version: str,
  reference_spike_threshold: float,
) -> pd.DataFrame:
  """Evaluate classifiers using one common spike definition."""
  metadata = load_metadata(
    metadata_path=metadata_path,
    required_columns={
      "model_name",
      "horizon_hours",
      "spike_threshold",
      "decision_threshold",
      "artifact_path",
      "feature_columns",
    },
  )

  rows = []

  for metadata_row in metadata.to_dict(
    orient="records"
  ):
    horizon_hours = int(
      metadata_row[
        "horizon_hours"
      ]
    )

    price_target_column = (
      build_target_column_name(
        horizon_hours
      )
    )

    future_price = pd.to_numeric(
      evaluation_data[
        price_target_column
      ],
      errors="coerce",
    )

    if future_price.isna().any():
      raise ValueError(
        "Classification price target contains "
        f"missing values: {price_target_column}"
      )

    reference_target = (
      future_price
      > reference_spike_threshold
    ).astype(int)

    (
      prediction,
      probability,
    ) = generate_classification_predictions(
      metadata_row=metadata_row,
      evaluation_data=evaluation_data,
      reference_spike_threshold=(
        reference_spike_threshold
      ),
    )

    scores = calculate_classification_metrics(
      target=reference_target,
      prediction=prediction,
      probability=probability,
    )

    rows.append(
      {
        "source": source,
        "model_version": model_version,
        "horizon_hours": horizon_hours,
        "model_name": metadata_row[
          "model_name"
        ],
        "evaluation_rows": len(
          evaluation_data
        ),
        "reference_spike_threshold": (
          reference_spike_threshold
        ),
        "operational_spike_threshold": float(
          metadata_row[
            "spike_threshold"
          ]
        ),
        "decision_threshold": (
          metadata_row.get(
            "decision_threshold"
          )
        ),
        "accuracy": scores.get(
          "accuracy"
        ),
        "precision": scores.get(
          "precision"
        ),
        "recall": scores.get(
          "recall"
        ),
        "f1": scores.get(
          "f1"
        ),
        "pr_auc": scores.get(
          "pr_auc"
        ),
      }
    )

  return pd.DataFrame(rows)


def build_regression_comparison(
  champion_results: pd.DataFrame,
  candidate_results: pd.DataFrame,
) -> pd.DataFrame:
  """Compare regression metrics horizon by horizon."""
  champion = champion_results.rename(
    columns={
      "model_name":
        "champion_model_name",
      "mae":
        "champion_mae",
      "rmse":
        "champion_rmse",
    }
  )[
    [
      "horizon_hours",
      "champion_model_name",
      "champion_mae",
      "champion_rmse",
    ]
  ]

  candidate = candidate_results.rename(
    columns={
      "model_name":
        "candidate_model_name",
      "mae":
        "candidate_mae",
      "rmse":
        "candidate_rmse",
    }
  )[
    [
      "horizon_hours",
      "candidate_model_name",
      "candidate_mae",
      "candidate_rmse",
    ]
  ]

  comparison = champion.merge(
    candidate,
    on="horizon_hours",
    how="outer",
    validate="one_to_one",
  )

  comparison[
    "mae_delta"
  ] = (
    comparison[
      "candidate_mae"
    ]
    - comparison[
      "champion_mae"
    ]
  )

  comparison[
    "rmse_delta"
  ] = (
    comparison[
      "candidate_rmse"
    ]
    - comparison[
      "champion_rmse"
    ]
  )

  comparison[
    "mae_improvement_percent"
  ] = (
    (
      comparison[
        "champion_mae"
      ]
      - comparison[
        "candidate_mae"
      ]
    )
    / comparison[
      "champion_mae"
    ]
    * 100
  )

  comparison[
    "rmse_improvement_percent"
  ] = (
    (
      comparison[
        "champion_rmse"
      ]
      - comparison[
        "candidate_rmse"
      ]
    )
    / comparison[
      "champion_rmse"
    ]
    * 100
  )

  comparison[
    "promotion_gate_pass"
  ] = (
    comparison[
      "candidate_mae"
    ]
    <= comparison[
      "champion_mae"
    ]
  ) & (
    comparison[
      "candidate_rmse"
    ]
    <= comparison[
      "champion_rmse"
    ]
  )

  return comparison


def build_classification_comparison(
  champion_results: pd.DataFrame,
  candidate_results: pd.DataFrame,
) -> pd.DataFrame:
  """Compare classification metrics on one reference target."""
  champion = champion_results.rename(
    columns={
      "model_name":
        "champion_model_name",
      "precision":
        "champion_precision",
      "recall":
        "champion_recall",
      "f1":
        "champion_f1",
      "pr_auc":
        "champion_pr_auc",
      "operational_spike_threshold":
        "champion_operational_threshold",
      "decision_threshold":
        "champion_decision_threshold",
    }
  )[
    [
      "horizon_hours",
      "reference_spike_threshold",
      "champion_model_name",
      "champion_operational_threshold",
      "champion_decision_threshold",
      "champion_precision",
      "champion_recall",
      "champion_f1",
      "champion_pr_auc",
    ]
  ]

  candidate = candidate_results.rename(
    columns={
      "model_name":
        "candidate_model_name",
      "precision":
        "candidate_precision",
      "recall":
        "candidate_recall",
      "f1":
        "candidate_f1",
      "pr_auc":
        "candidate_pr_auc",
      "operational_spike_threshold":
        "candidate_operational_threshold",
      "decision_threshold":
        "candidate_decision_threshold",
    }
  )[
    [
      "horizon_hours",
      "candidate_model_name",
      "candidate_operational_threshold",
      "candidate_decision_threshold",
      "candidate_precision",
      "candidate_recall",
      "candidate_f1",
      "candidate_pr_auc",
    ]
  ]

  comparison = champion.merge(
    candidate,
    on="horizon_hours",
    how="outer",
    validate="one_to_one",
  )

  comparison[
    "recall_delta"
  ] = (
    comparison[
      "candidate_recall"
    ]
    - comparison[
      "champion_recall"
    ]
  )

  comparison[
    "f1_delta"
  ] = (
    comparison[
      "candidate_f1"
    ]
    - comparison[
      "champion_f1"
    ]
  )

  comparison[
    "pr_auc_delta"
  ] = (
    comparison[
      "candidate_pr_auc"
    ]
    - comparison[
      "champion_pr_auc"
    ]
  )

  comparison[
    "metric_gate_pass"
  ] = (
    comparison[
      "candidate_recall"
    ]
    >= comparison[
      "champion_recall"
    ]
  ) & (
    comparison[
      "candidate_f1"
    ]
    >= comparison[
      "champion_f1"
    ]
  ) & (
    comparison[
      "candidate_pr_auc"
    ]
    >= comparison[
      "champion_pr_auc"
    ]
  )

  comparison[
    "promotion_gate_pass"
  ] = comparison[
    "metric_gate_pass"
  ]

  return comparison


def build_promotion_summary(
  regression_comparison: pd.DataFrame,
  classification_comparison: pd.DataFrame,
  champion_spike_threshold: float,
  candidate_spike_threshold: float,
) -> dict:
  """Build the final manual-promotion recommendation."""
  threshold_changed = (
    abs(
      candidate_spike_threshold
      - champion_spike_threshold
    )
    > 1e-9
  )

  regression_pass = bool(
    regression_comparison[
      "promotion_gate_pass"
    ].all()
  )

  classification_metric_pass = bool(
    classification_comparison[
      "metric_gate_pass"
    ].all()
  )

  classification_pass = (
    classification_metric_pass
  )

  return {
    "schema_version": 1,
    "evaluated_at_utc": datetime.now(
      UTC
    ).isoformat(),
    "regression_gate_pass": (
      regression_pass
    ),
    "classification_metric_gate_pass": (
      classification_metric_pass
    ),
    "classification_gate_pass": (
      classification_pass
    ),
    "champion_spike_threshold": (
      champion_spike_threshold
    ),
    "candidate_spike_threshold": (
      candidate_spike_threshold
    ),
    "spike_threshold_delta": (
      candidate_spike_threshold
      - champion_spike_threshold
    ),
    "spike_threshold_changed": (
      threshold_changed
    ),
    "spike_threshold_update_mode": (
      "automatic_train_derived"
    ),
    "promotion_ready": (
      regression_pass
      and classification_pass
    ),
    "promotion_mode": "manual",
  }


def compare_challenger_with_active_models(
  candidate_manifest_path: Path,
) -> tuple[Path, Path, Path, dict]:
  """Evaluate champion and candidate on the same frozen test."""
  candidate_manifest = read_json_file(
    candidate_manifest_path
  )

  if candidate_manifest.get(
    "status"
  ) not in {
    "trained",
    "evaluated",
  }:
    raise ValueError(
      "Candidate must be fully trained before comparison."
    )

  (
    _,
    _,
    test_data,
    _,
  ) = load_frozen_candidate_splits(
    candidate_manifest
  )

  champion_regression_metadata_path = Path(
    candidate_manifest[
      "current_champion"
    ][
      "regression_metadata_path"
    ]
  )

  champion_classification_metadata_path = Path(
    candidate_manifest[
      "current_champion"
    ][
      "classification_metadata_path"
    ]
  )

  candidate_regression_metadata_path = Path(
    candidate_manifest[
      "tasks"
    ][
      "regression"
    ][
      "metadata_path"
    ]
  )

  candidate_classification_metadata_path = Path(
    candidate_manifest[
      "tasks"
    ][
      "classification"
    ][
      "metadata_path"
    ]
  )

  champion_classification_metadata = (
    load_metadata(
      metadata_path=(
        champion_classification_metadata_path
      ),
      required_columns={
        "spike_threshold",
      },
    )
  )

  candidate_classification_metadata = (
    load_metadata(
      metadata_path=(
        candidate_classification_metadata_path
      ),
      required_columns={
        "spike_threshold",
      },
    )
  )

  champion_spike_threshold = (
    extract_single_spike_threshold(
      metadata=(
        champion_classification_metadata
      ),
      source="Champion",
    )
  )

  candidate_spike_threshold = (
    extract_single_spike_threshold(
      metadata=(
        candidate_classification_metadata
      ),
      source="Candidate",
    )
  )

  champion_regression_results = (
    evaluate_regression_metadata(
      metadata_path=(
        champion_regression_metadata_path
      ),
      evaluation_data=test_data,
      source="champion",
      model_version=(
        "legacy-unversioned"
      ),
    )
  )

  candidate_regression_results = (
    evaluate_regression_metadata(
      metadata_path=(
        candidate_regression_metadata_path
      ),
      evaluation_data=test_data,
      source="candidate",
      model_version=(
        candidate_manifest[
          "model_version"
        ]
      ),
    )
  )

  champion_classification_results = (
    evaluate_classification_metadata(
      metadata_path=(
        champion_classification_metadata_path
      ),
      evaluation_data=test_data,
      source="champion",
      model_version=(
        "legacy-unversioned"
      ),
      reference_spike_threshold=(
        candidate_spike_threshold
      ),
    )
  )

  candidate_classification_results = (
    evaluate_classification_metadata(
      metadata_path=(
        candidate_classification_metadata_path
      ),
      evaluation_data=test_data,
      source="candidate",
      model_version=(
        candidate_manifest[
          "model_version"
        ]
      ),
      reference_spike_threshold=(
        candidate_spike_threshold
      ),
    )
  )

  regression_comparison = (
    build_regression_comparison(
      champion_results=(
        champion_regression_results
      ),
      candidate_results=(
        candidate_regression_results
      ),
    )
  )

  classification_comparison = (
    build_classification_comparison(
      champion_results=(
        champion_classification_results
      ),
      candidate_results=(
        candidate_classification_results
      ),
    )
  )

  summary = build_promotion_summary(
    regression_comparison=(
      regression_comparison
    ),
    classification_comparison=(
      classification_comparison
    ),
    champion_spike_threshold=(
      champion_spike_threshold
    ),
    candidate_spike_threshold=(
      candidate_spike_threshold
    ),
  )

  comparison_directory = (
    Path(
      candidate_manifest[
        "candidate_directory"
      ]
    )
    / "reports"
    / "comparison"
  )

  comparison_directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  regression_path = (
    comparison_directory
    / "regression_champion_candidate.csv"
  )

  classification_path = (
    comparison_directory
    / "classification_champion_candidate.csv"
  )

  summary_path = (
    comparison_directory
    / "promotion_summary.json"
  )

  regression_comparison.to_csv(
    regression_path,
    index=False,
  )

  classification_comparison.to_csv(
    classification_path,
    index=False,
  )

  write_json_file(
    content=summary,
    file_path=summary_path,
  )

  candidate_manifest[
    "comparison"
  ] = {
    "status": "completed",
    "regression_report_path": str(
      regression_path
    ),
    "classification_report_path": str(
      classification_path
    ),
    "promotion_summary_path": str(
      summary_path
    ),
    **summary,
  }

  candidate_manifest[
    "status"
  ] = "evaluated"

  write_json_file(
    content=candidate_manifest,
    file_path=candidate_manifest_path,
  )

  return (
    regression_path,
    classification_path,
    summary_path,
    summary,
  )


def main() -> None:
  """Compare the latest candidate with the active champion."""
  candidate_manifest_path = (
    resolve_latest_candidate_manifest_path()
  )

  (
    regression_path,
    classification_path,
    summary_path,
    summary,
  ) = compare_challenger_with_active_models(
    candidate_manifest_path=(
      candidate_manifest_path
    )
  )

  print("Champion / candidate comparison")
  print("===============================")

  print("")
  print("Regression")
  print("----------")

  regression = pd.read_csv(
    regression_path
  )

  print(
    regression[
      [
        "horizon_hours",
        "champion_mae",
        "candidate_mae",
        "mae_improvement_percent",
        "champion_rmse",
        "candidate_rmse",
        "rmse_improvement_percent",
        "promotion_gate_pass",
      ]
    ].to_string(
      index=False
    )
  )

  print("")
  print("Classification")
  print("--------------")

  classification = pd.read_csv(
    classification_path
  )

  print(
    classification[
      [
        "horizon_hours",
        "champion_recall",
        "candidate_recall",
        "champion_f1",
        "candidate_f1",
        "champion_pr_auc",
        "candidate_pr_auc",
        "metric_gate_pass",
        "promotion_gate_pass",
      ]
    ].to_string(
      index=False
    )
  )

  print("")
  print("Promotion summary")
  print("-----------------")

  for key, value in summary.items():
    print(
      f"{key}: {value}"
    )

  print("")
  print(
    f"Regression report: {regression_path}"
  )
  print(
    f"Classification report: {classification_path}"
  )
  print(
    f"Summary: {summary_path}"
  )


if __name__ == "__main__":
  main()
