"""Estimate classification uncertainty while preserving temporal blocks."""

import numpy as np
from sklearn.metrics import f1_score


DEFAULT_BOOTSTRAP_ITERATIONS = 1000
DEFAULT_BLOCK_SIZE = 24
DEFAULT_CONFIDENCE_LEVEL = 0.95
DEFAULT_RANDOM_STATE = 42


def validate_block_bootstrap_inputs(
  row_count: int,
  block_size: int,
  iterations: int,
  confidence_level: float,
) -> None:
  """Validate shared block-bootstrap parameters."""
  if row_count <= 0:
    raise ValueError("Block bootstrap requires non-empty data.")

  if block_size <= 0:
    raise ValueError("Block size must be greater than 0.")

  if block_size > row_count:
    raise ValueError("Block size cannot exceed the number of rows.")

  if iterations <= 0:
    raise ValueError("Bootstrap iterations must be greater than 0.")

  if not 0.0 < confidence_level < 1.0:
    raise ValueError("Confidence level must be between 0 and 1.")


def sample_moving_block_indices(
  row_count: int,
  block_size: int,
  random_generator: np.random.Generator,
) -> np.ndarray:
  """Sample consecutive blocks until one bootstrap dataset is complete."""
  maximum_start = row_count - block_size
  sampled_indices = []

  while len(sampled_indices) < row_count:
    block_start = int(
      random_generator.integers(
        low=0,
        high=maximum_start + 1,
      )
    )

    sampled_indices.extend(
      range(
        block_start,
        block_start + block_size,
      )
    )

  # Trim the final block so every bootstrap sample matches the original size.
  return np.asarray(sampled_indices[:row_count])


def calculate_f1_block_bootstrap_interval(
  target,
  prediction,
  block_size: int = DEFAULT_BLOCK_SIZE,
  iterations: int = DEFAULT_BOOTSTRAP_ITERATIONS,
  confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
  random_state: int = DEFAULT_RANDOM_STATE,
) -> dict[str, float | int]:
  """Estimate a confidence interval for F1 with moving block bootstrap."""
  target_array = np.asarray(target)
  prediction_array = np.asarray(prediction)

  if len(target_array) != len(prediction_array):
    raise ValueError(
      "Target and prediction must contain the same number of rows."
    )

  validate_block_bootstrap_inputs(
    row_count=len(target_array),
    block_size=block_size,
    iterations=iterations,
    confidence_level=confidence_level,
  )

  random_generator = np.random.default_rng(random_state)
  bootstrap_scores = []

  for _ in range(iterations):
    sampled_indices = sample_moving_block_indices(
      row_count=len(target_array),
      block_size=block_size,
      random_generator=random_generator,
    )

    bootstrap_scores.append(
      f1_score(
        target_array[sampled_indices],
        prediction_array[sampled_indices],
        zero_division=0,
      )
    )

  alpha = 1.0 - confidence_level
  lower_percentile = 100.0 * alpha / 2.0
  upper_percentile = 100.0 * (1.0 - alpha / 2.0)

  return {
    "metric": "f1",
    "estimate": float(
      f1_score(
        target_array,
        prediction_array,
        zero_division=0,
      )
    ),
    "confidence_level": confidence_level,
    "ci_lower": float(
      np.percentile(
        bootstrap_scores,
        lower_percentile,
      )
    ),
    "ci_upper": float(
      np.percentile(
        bootstrap_scores,
        upper_percentile,
      )
    ),
    "block_size": block_size,
    "iterations": iterations,
  }
