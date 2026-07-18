from electricity_predictor.worker.decision_context import (
  DecisionContext,
)
from electricity_predictor.worker.decision_layer import (
  apply_decision_layer,
)


def test_apply_decision_layer() -> None:
  context = DecisionContext(
    window_hours=720,
    row_count=720,
    q1=50.0,
    q3=100.0,
    iqr=50.0,
    recommended_threshold=50.0,
    avoid_threshold=175.0,
  )

  predictions = [
    {
      "horizon_hours": 1,
      "predicted_price": 40.0,
      "spike_probability": 0.20,
      "is_spike": False,
    },
    {
      "horizon_hours": 3,
      "predicted_price": 80.0,
      "spike_probability": 0.20,
      "is_spike": False,
    },
    {
      "horizon_hours": 6,
      "predicted_price": 200.0,
      "spike_probability": 0.80,
      "is_spike": True,
    },
    {
      "horizon_hours": 12,
      "predicted_price": 40.0,
      "spike_probability": 0.80,
      "is_spike": True,
    },
    {
      "horizon_hours": 24,
      "predicted_price": 80.0,
      "spike_probability": 0.80,
      "is_spike": True,
    },
  ]

  decisions = apply_decision_layer(
    predictions=predictions,
    context=context,
  )

  assert decisions[0]["recommendation"] == "Recommended"
  assert decisions[1]["recommendation"] == "Acceptable"
  assert decisions[2]["recommendation"] == "Avoid"
  assert decisions[3]["recommendation"] == "Acceptable"
  assert decisions[4]["recommendation"] == "Avoid"

  assert decisions[0]["recommended_threshold"] == 50.0
  assert decisions[0]["avoid_threshold"] == 175.0
