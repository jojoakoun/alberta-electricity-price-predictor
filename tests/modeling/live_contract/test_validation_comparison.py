"""Tests for validation-only live feature contract comparison."""

import pandas as pd
import pytest

from electricity_predictor.modeling.live_contract.validation_comparison import (
  build_validation_only_splits,
  normalize_utc_timestamp,
  parse_bool,
  parse_parameter_text,
)


def make_hourly_rows() -> pd.DataFrame:
  """Build rows covering train, validation, purge, and protected periods."""
  timestamps = pd.date_range(
    start="2024-01-01T00:00:00Z",
    end="2024-01-05T23:00:00Z",
    freq="h",
  )

  return pd.DataFrame({
    "datetime_universal_time":
      timestamps,
    "value": range(
      len(timestamps)
    ),
  })


def test_validation_only_split_never_returns_test_rows():
  data = make_hourly_rows()

  config = {
    "train_start_utc":
      "2024-01-01T00:00:00Z",
    "validation_start_utc":
      "2024-01-03T00:00:00Z",
    "test_start_utc":
      "2024-01-05T00:00:00Z",
    "purge_hours": 2,
  }

  train_data, validation_data = (
    build_validation_only_splits(
      data=data,
      modeling_config=config,
    )
  )

  assert (
    train_data[
      "datetime_universal_time"
    ].max()
    < pd.Timestamp(
      "2024-01-02T22:00:00Z"
    )
  )

  assert (
    validation_data[
      "datetime_universal_time"
    ].max()
    < pd.Timestamp(
      "2024-01-04T22:00:00Z"
    )
  )

  assert not (
    validation_data[
      "datetime_universal_time"
    ]
    >= pd.Timestamp(
      "2024-01-05T00:00:00Z"
    )
  ).any()


def test_parameter_parser_preserves_recorded_values():
  parameters = parse_parameter_text(
    "learning_rate=0.05; "
    "max_iter=200; "
    "early_stopping=False"
  )

  assert parameters == {
    "learning_rate": "0.05",
    "max_iter": "200",
    "early_stopping": "False",
  }


@pytest.mark.parametrize(
  ("value", "expected"),
  [
    ("True", True),
    ("true", True),
    ("False", False),
    ("false", False),
  ],
)
def test_parse_bool(
  value,
  expected,
):
  assert parse_bool(value) is expected


def test_parse_bool_rejects_unknown_value():
  with pytest.raises(
    ValueError,
    match="Invalid boolean",
  ):
    parse_bool("sometimes")


@pytest.mark.parametrize(
  ("value", "expected"),
  [
    (
      "2024-01-01T00:00:00",
      pd.Timestamp(
        "2024-01-01T00:00:00Z"
      ),
    ),
    (
      "2024-01-01T00:00:00Z",
      pd.Timestamp(
        "2024-01-01T00:00:00Z"
      ),
    ),
    (
      "2023-12-31T17:00:00-07:00",
      pd.Timestamp(
        "2024-01-01T00:00:00Z"
      ),
    ),
  ],
)
def test_normalize_utc_timestamp(
  value,
  expected,
):
  assert normalize_utc_timestamp(
    value,
    "boundary",
  ) == expected


def test_validation_only_split_accepts_naive_configuration_boundaries():
  data = make_hourly_rows()

  config = {
    "train_start_utc":
      "2024-01-01T00:00:00",
    "validation_start_utc":
      "2024-01-03T00:00:00",
    "test_start_utc":
      "2024-01-05T00:00:00",
    "purge_hours": 2,
  }

  train_data, validation_data = (
    build_validation_only_splits(
      data=data,
      modeling_config=config,
    )
  )

  assert not train_data.empty
  assert not validation_data.empty

  assert (
    validation_data[
      "datetime_universal_time"
    ].max()
    < pd.Timestamp(
      "2024-01-05T00:00:00Z"
    )
  )


def test_normalize_utc_timestamp_rejects_invalid_value():
  with pytest.raises(
    ValueError,
    match="must be a valid timestamp",
  ):
    normalize_utc_timestamp(
      None,
      "test_start_utc",
    )
