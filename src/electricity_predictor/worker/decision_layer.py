def make_recommendation(prediction: dict) -> dict:
  """Convert one model prediction into a business recommendation."""
  recommendation = "Recommended"
  explanation = "Low spike probability."

  if prediction["is_spike"]:
    recommendation = "Avoid"
    explanation = "High spike probability."

  return {
    **prediction,
    "recommendation": recommendation,
    "explanation": explanation,
  }


def apply_decision_layer(
  predictions: list[dict],
) -> list[dict]:
  """Apply business rules to every prediction."""
  return [
    make_recommendation(prediction)
    for prediction in predictions
  ]
