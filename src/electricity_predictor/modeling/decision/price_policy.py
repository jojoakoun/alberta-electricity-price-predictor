"""Shared price-only recommendation policy for decision research."""


def classify_price(
  price: float,
  recommended_threshold: float,
  avoid_threshold: float,
) -> str:
  """Classify one price using the established threshold precedence."""
  # Avoid takes precedence if unusual thresholds overlap at the boundary.
  if price >= avoid_threshold:
    return "Avoid"

  if price <= recommended_threshold:
    return "Recommended"

  return "Acceptable"
