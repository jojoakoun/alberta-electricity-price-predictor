import pytest

from electricity_predictor.modeling.decision.price_policy import classify_price


@pytest.mark.parametrize(
  ("price", "expected_label"),
  [
    (9.0, "Recommended"),
    (10.0, "Recommended"),
    (10.01, "Acceptable"),
    (19.99, "Acceptable"),
    (20.0, "Avoid"),
    (21.0, "Avoid"),
  ],
)
def test_classify_price_preserves_labels_and_boundaries(
  price: float,
  expected_label: str,
) -> None:
  assert classify_price(
    price=price,
    recommended_threshold=10.0,
    avoid_threshold=20.0,
  ) == expected_label


def test_avoid_threshold_keeps_precedence_when_thresholds_overlap() -> None:
  assert classify_price(
    price=15.0,
    recommended_threshold=20.0,
    avoid_threshold=10.0,
  ) == "Avoid"
