"""Compare rolling market windows across historical monthly reference dates."""

from pathlib import Path

import pandas as pd

from electricity_predictor.storage.postgres import (
  get_database_connection,
)


WINDOWS = [72, 168, 336, 720]

DETAIL_OUTPUT_PATH = Path(
  "reports/decision_window_analysis.csv"
)
SUMMARY_OUTPUT_PATH = Path(
  "reports/decision_window_summary.csv"
)


def load_finalized_hourly_prices() -> pd.DataFrame:
  """Load all finalized hourly prices in chronological order."""
  query = """
    SELECT
      datetime_utc,
      actual_price
    FROM hourly_prices
    WHERE actual_price IS NOT NULL
    ORDER BY datetime_utc;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(query)
      rows = cursor.fetchall()

  data = pd.DataFrame(
    rows,
    columns=[
      "datetime_universal_time",
      "actual_price",
    ],
  )

  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"],
    utc=True,
  )
  data["actual_price"] = pd.to_numeric(
    data["actual_price"],
    errors="coerce",
  )

  data = data.dropna().reset_index(drop=True)

  if data.empty:
    raise RuntimeError(
      "No finalized hourly prices are available in PostgreSQL. "
      "Run `make sync-history` before decision analysis."
    )

  return data


def build_reference_dates(data: pd.DataFrame) -> pd.Series:
  """Select the final available timestamp from every calendar month."""
  minimum_reference = (
    data["datetime_universal_time"].min()
    + pd.Timedelta(hours=max(WINDOWS))
  )

  eligible = data[
    data["datetime_universal_time"] >= minimum_reference
  ].copy()

  return (
    eligible
    .set_index("datetime_universal_time")
    .resample("ME")
    .last()
    .dropna()
    .reset_index()["datetime_universal_time"]
  )


def summarize_window(
  data: pd.DataFrame,
  reference_time: pd.Timestamp,
  window_hours: int,
) -> dict:
  """Calculate decision statistics for one historical window."""
  window_start = (
    reference_time
    - pd.Timedelta(hours=window_hours - 1)
  )

  recent = data.loc[
    data["datetime_universal_time"].between(
      window_start,
      reference_time,
    ),
    "actual_price",
  ]

  q1 = float(recent.quantile(0.25))
  q3 = float(recent.quantile(0.75))
  iqr = q3 - q1

  return {
    "reference_time": reference_time,
    "window_hours": window_hours,
    "row_count": len(recent),
    "coverage_rate": len(recent) / window_hours,
    "minimum": float(recent.min()),
    "mean": float(recent.mean()),
    "median": float(recent.median()),
    "q1": q1,
    "q3": q3,
    "iqr": iqr,
    "iqr_threshold": q3 + (1.5 * iqr),
    "maximum": float(recent.max()),
  }


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
  """Summarize threshold stability for every candidate window."""
  summaries = []

  for window_hours, group in detail.groupby("window_hours"):
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
        "window_hours": int(window_hours),
        "reference_count": len(ordered),
        "average_coverage_rate": ordered[
          "coverage_rate"
        ].mean(),
        "average_q1": ordered["q1"].mean(),
        "q1_standard_deviation": ordered["q1"].std(),
        "median_q1_monthly_change": q1_change.median(),
        "average_iqr_threshold": ordered[
          "iqr_threshold"
        ].mean(),
        "iqr_threshold_standard_deviation": ordered[
          "iqr_threshold"
        ].std(),
        "median_threshold_monthly_change": (
          threshold_change.median()
        ),
        "maximum_threshold_monthly_change": (
          threshold_change.max()
        ),
      }
    )

  return pd.DataFrame(summaries)


def main() -> None:
  """Generate detailed and summarized decision-window reports."""
  data = load_finalized_hourly_prices()
  reference_dates = build_reference_dates(data)

  if reference_dates.empty:
    raise RuntimeError(
      "Not enough finalized hourly prices are available "
      f"to analyze the largest {max(WINDOWS)}-hour window."
    )

  detail = pd.DataFrame(
    [
      summarize_window(
        data=data,
        reference_time=reference_time,
        window_hours=window_hours,
      )
      for reference_time in reference_dates
      for window_hours in WINDOWS
    ]
  )

  summary = build_summary(detail)

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

  print("===== WINDOW STABILITY SUMMARY =====")
  print(summary.to_string(index=False))


if __name__ == "__main__":
  main()
