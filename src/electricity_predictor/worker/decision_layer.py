"""Convert horizon predictions into threshold-based consumer decisions."""

from electricity_predictor.worker.decision_context import (
  DecisionContext,
)


def make_recommendation(
  prediction: dict,
  context: DecisionContext,
) -> dict:
  """Convert one prediction into a business recommendation."""
  price = float(prediction["predicted_price"])

  if price >= context.avoid_threshold:
    recommendation = "Avoid"
  elif price <= context.recommended_threshold:
    recommendation = "Recommended"
  else:
    recommendation = "Acceptable"

  if prediction["is_spike"]:
    if recommendation == "Recommended":
      recommendation = "Acceptable"
    elif recommendation == "Acceptable":
      recommendation = "Avoid"

  explanations = {
    "Recommended": (
      "Predicted price is favorable compared with the recent market."
    ),
    "Acceptable": (
      "Predicted price is acceptable but market risk is increasing."
    ),
    "Avoid": (
      "Predicted price is high compared with the recent market."
    ),
  }

  return {
    **prediction,
    "recommended_threshold": context.recommended_threshold,
    "avoid_threshold": context.avoid_threshold,
    "recommendation": recommendation,
    "explanation": explanations[recommendation],
  }


def apply_decision_layer(
  predictions: list[dict],
  context: DecisionContext,
) -> list[dict]:
  """Apply the decision policy to all horizon predictions."""
  return [
    make_recommendation(
      prediction=prediction,
      context=context,
    )
    for prediction in predictions
  ]
