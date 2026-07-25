import numpy as np
import pytest

from electricity_predictor.modeling.block_bootstrap import (
  calculate_f1_block_bootstrap_interval,
  sample_moving_block_indices,
  validate_block_bootstrap_inputs,
)


def test_sample_moving_block_indices_preserves_requested_length():
  random_generator = np.random.default_rng(42)

  indices = sample_moving_block_indices(
    row_count=10,
    block_size=3,
    random_generator=random_generator,
  )

  assert len(indices) == 10
  assert indices.min() >= 0
  assert indices.max() < 10


def test_calculate_f1_block_bootstrap_interval_returns_valid_bounds():
  result = calculate_f1_block_bootstrap_interval(
    target=[0, 0, 1, 1, 0, 1, 0, 1],
    prediction=[0, 1, 1, 1, 0, 0, 0, 1],
    block_size=2,
    iterations=100,
    confidence_level=0.95,
    random_state=42,
  )

  assert result["metric"] == "f1"
  assert 0.0 <= result["ci_lower"] <= result["ci_upper"] <= 1.0
  assert result["ci_lower"] <= result["estimate"] <= result["ci_upper"]
  assert result["block_size"] == 2
  assert result["iterations"] == 100


def test_calculate_f1_block_bootstrap_interval_is_reproducible():
  arguments = {
    "target": [0, 0, 1, 1, 0, 1, 0, 1],
    "prediction": [0, 1, 1, 1, 0, 0, 0, 1],
    "block_size": 2,
    "iterations": 50,
    "random_state": 42,
  }

  first_result = calculate_f1_block_bootstrap_interval(**arguments)
  second_result = calculate_f1_block_bootstrap_interval(**arguments)

  assert first_result == second_result


def test_block_bootstrap_rejects_mismatched_lengths():
  with pytest.raises(ValueError, match="same number of rows"):
    calculate_f1_block_bootstrap_interval(
      target=[0, 1],
      prediction=[1],
    )


def test_validate_block_bootstrap_inputs_rejects_oversized_block():
  with pytest.raises(ValueError, match="cannot exceed"):
    validate_block_bootstrap_inputs(
      row_count=10,
      block_size=11,
      iterations=100,
      confidence_level=0.95,
    )


def test_validate_block_bootstrap_inputs_rejects_invalid_confidence_level():
  with pytest.raises(ValueError, match="between 0 and 1"):
    validate_block_bootstrap_inputs(
      row_count=10,
      block_size=2,
      iterations=100,
      confidence_level=1.0,
    )
