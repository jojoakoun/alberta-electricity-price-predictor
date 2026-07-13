import pandas as pd

def validate_price_series(prices: pd.Series) -> None:
  """Validate a price series before calculating spike thresholds."""
  if prices.empty:
    raise ValueError("Cannot calculate a spike threshold from an empty price series.")

  if prices.isna().any():
    raise ValueError("Spike threshold calculation requires non-missing prices.")

  if not pd.api.types.is_numeric_dtype(prices):
    raise ValueError("Spike threshold calculation requires numeric prices.")
  

def calculate_iqr_spike_threshold(prices: pd.Series, multiplier: float = 1.5) -> float:
  """Calculate the upper IQR fence used to define high-price spikes."""
  validate_price_series(prices)

  if multiplier <= 0:
    raise ValueError("IQR multiplier must be greater than 0.")

  first_quartile = float(prices.quantile(0.25))
  third_quartile = float(prices.quantile(0.75))
  interquartile_range = third_quartile - first_quartile

  # The upper fence identifies unusually high prices without using future splits.
  return third_quartile + multiplier * interquartile_range


def calculate_quantile_spike_threshold(prices: pd.Series, quantile: float) -> float:
  """Calculate a spike threshold from a selected upper quantile."""
  validate_price_series(prices)
  if not 0 < quantile < 1:
    raise ValueError("Quantile must be greater than 0 and less than 1.")
  
  return float(prices.quantile(quantile))

def classify_spikes(prices: pd.Series, threshold: float) -> pd.Series:
  """Classify prices above a fixed threshold as spikes."""
  validate_price_series(prices)

  # Equality is not a spike because the threshold is the upper boundary itself.
  return (prices > threshold).astype(int)


def summarize_spikes(prices: pd.Series,threshold: float ) -> dict[str, float | int]:
  """Summarize spike counts and class balance for one price series."""
  labels = classify_spikes(
    prices=prices,
    threshold=threshold,
  )
  spike_count = int(labels.sum())
  row_count = len(labels)

  return {
    "row_count": row_count,
    "spike_count": spike_count,
    "non_spike_count": row_count - spike_count,
    "spike_rate": spike_count / row_count,
  }