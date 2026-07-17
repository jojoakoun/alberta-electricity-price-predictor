from electricity_predictor.worker.decision_layer import (
  apply_decision_layer,
)


def test_apply_decision_layer() -> None:
  predictions = [
    {
      "horizon_hours": 1,
      "predicted_price": 80.0,
      "spike_probability": 0.20,
      "is_spike": False,
    },
    {
      "horizon_hours": 3,
      "predicted_price": 200.0,
      "spike_probability": 0.80,
      "is_spike": True,
    },
  ]

  decisions = apply_decision_layer(predictions)

  assert decisions[0]["recommendation"] == "Recommended"
  assert decisions[1]["recommendation"] == "Avoid"
