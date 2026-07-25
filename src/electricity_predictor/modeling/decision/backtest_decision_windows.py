"""Backtest candidate price-decision windows without future leakage."""

from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.decision.analyze_decision_windows import (
  load_finalized_hourly_prices,
)
from electricity_predictor.modeling.decision.price_policy import classify_price


WINDOWS = [336, 720]
RECENT_REGIME_START = pd.Timestamp(
  "2024-01-01 00:00:00",
  tz="UTC",
)

DETAIL_OUTPUT_PATH = Path(
  "reports/decision_policy_backtest.csv"
)
SUMMARY_OUTPUT_PATH = Path(
  "reports/decision_policy_backtest_summary.csv"
)


def backtest_window(
  data: pd.DataFrame,
  window_hours: int,
) -> pd.DataFrame:
  """Backtest one rolling window using past prices only."""
  records = []

  prices = data["actual_price"]

  for index in range(window_hours, len(data)):
    timestamp = data.iloc[index]["datetime_universal_time"]

    if timestamp < RECENT_REGIME_START:
      continue

    historical_prices = prices.iloc[
      index - window_hours:index
    ]

    q1 = float(historical_prices.quantile(0.25))
    q3 = float(historical_prices.quantile(0.75))
    iqr = q3 - q1
    avoid_threshold = q3 + (1.5 * iqr)

    actual_price = float(prices.iloc[index])

    records.append(
      {
        "timestamp": timestamp,
        "window_hours": window_hours,
        "actual_price": actual_price,
        "recommended_threshold": q1,
        "avoid_threshold": avoid_threshold,
        "recommendation": classify_price(
          price=actual_price,
          recommended_threshold=q1,
          avoid_threshold=avoid_threshold,
        ),
      }
    )

  return pd.DataFrame(records)


def summarize_backtest(detail: pd.DataFrame) -> pd.DataFrame:
  """Summarize recommendation usefulness and stability."""
  summaries = []

  for window_hours, group in detail.groupby("window_hours"):
    ordered = group.sort_values("timestamp")
    recommendation = ordered["recommendation"]

    summaries.append(
      {
        "window_hours": int(window_hours),
        "row_count": len(ordered),
        "recommended_rate": (
          recommendation.eq("Recommended").mean()
        ),
        "acceptable_rate": (
          recommendation.eq("Acceptable").mean()
        ),
        "avoid_rate": (
          recommendation.eq("Avoid").mean()
        ),
        "label_change_rate": (
          recommendation.ne(recommendation.shift()).iloc[1:].mean()
        ),
        "recommended_threshold_mean": ordered[
          "recommended_threshold"
        ].mean(),
        "recommended_threshold_std": ordered[
          "recommended_threshold"
        ].std(),
        "avoid_threshold_mean": ordered[
          "avoid_threshold"
        ].mean(),
        "avoid_threshold_std": ordered[
          "avoid_threshold"
        ].std(),
      }
    )

  return pd.DataFrame(summaries)


def main() -> None:
  """Run and save candidate-window backtests."""
  data = load_finalized_hourly_prices()

  detail = pd.concat(
    [
      backtest_window(
        data=data,
        window_hours=window_hours,
      )
      for window_hours in WINDOWS
    ],
    ignore_index=True,
  )

  summary = summarize_backtest(detail)

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
