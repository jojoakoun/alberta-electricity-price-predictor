"""Compare candidate decision windows across market regimes."""

from pathlib import Path

import pandas as pd


INPUT_PATH = Path(
  "reports/decision_window_analysis.csv"
)
OUTPUT_PATH = Path(
  "reports/decision_window_regime_summary.csv"
)


def assign_regime(timestamp: pd.Timestamp) -> str:
  """Assign one historical market regime."""
  if timestamp.year <= 2023:
    return "2020_2023"
  return "2024_2026"


def main() -> None:
  """Generate window-stability statistics by market regime."""
  detail = pd.read_csv(
    INPUT_PATH,
    parse_dates=["reference_time"],
  )

  detail["regime"] = detail[
    "reference_time"
  ].apply(assign_regime)

  summaries = []

  for (regime, window_hours), group in detail.groupby(
    ["regime", "window_hours"]
  ):
    ordered = group.sort_values("reference_time")

    threshold_change = (
      ordered["iqr_threshold"]
      .diff()
      .abs()
      .dropna()
    )

    q1_change = (
      ordered["q1"]
      .diff()
      .abs()
      .dropna()
    )

    summaries.append(
      {
        "regime": regime,
        "window_hours": int(window_hours),
        "reference_count": len(ordered),
        "average_q1": ordered["q1"].mean(),
        "q1_standard_deviation": ordered["q1"].std(),
        "median_q1_change": q1_change.median(),
        "average_iqr_threshold": ordered[
          "iqr_threshold"
        ].mean(),
        "threshold_standard_deviation": ordered[
          "iqr_threshold"
        ].std(),
        "median_threshold_change": (
          threshold_change.median()
        ),
        "maximum_threshold_change": (
          threshold_change.max()
        ),
      }
    )

  report = pd.DataFrame(summaries)

  report.to_csv(
    OUTPUT_PATH,
    index=False,
    float_format="%.4f",
  )

  print(report.to_string(index=False))


if __name__ == "__main__":
  main()
