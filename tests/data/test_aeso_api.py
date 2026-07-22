from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from electricity_predictor.data.aeso_api import (
  fetch_pool_price_report,
  normalize_pool_price_report,
)


def build_pool_price_report(records: list[dict]) -> dict:
  return {
    "return": {
      "Pool Price Report": records,
    }
  }


def test_fetch_pool_price_report_mocks_only_network_boundary(
  monkeypatch,
) -> None:
  monkeypatch.setenv(
    "AESO_API_SUBSCRIPTION_KEY",
    "test-key",
  )

  response = MagicMock()
  response.json.return_value = {"return": {}}

  with patch(
    "electricity_predictor.data.aeso_api.requests.get",
    return_value=response,
  ) as get:
    report = fetch_pool_price_report(
      start_date="2026-07-18",
      end_date="2026-07-20",
    )

  assert report == {"return": {}}
  response.raise_for_status.assert_called_once_with()

  request = get.call_args

  assert request.kwargs["params"] == {
    "startDate": "2026-07-18",
    "endDate": "2026-07-20",
  }
  assert request.kwargs["headers"] == {
    "API-KEY": "test-key",
  }
  assert request.kwargs["timeout"] == 30


def test_normalize_pool_price_report_returns_clean_columns() -> None:
  fake_report = build_pool_price_report([
    {
      "begin_datetime_utc": "2025-07-01 06:00",
      "begin_datetime_mpt": "2025-07-01 00:00",
      "pool_price": "29.06",
      "forecast_pool_price": "28.31",
      "rolling_30day_avg": "46.79",
    }
  ])

  data = normalize_pool_price_report(fake_report)

  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  ]


def test_normalize_pool_price_report_converts_types() -> None:
  fake_report = build_pool_price_report([
    {
      "begin_datetime_utc": "2025-07-01 06:00",
      "begin_datetime_mpt": "2025-07-01 00:00",
      "pool_price": "29.06",
      "forecast_pool_price": "28.31",
      "rolling_30day_avg": "46.79",
    }
  ])

  data = normalize_pool_price_report(fake_report)

  assert pd.api.types.is_datetime64_any_dtype(data["datetime_universal_time"])
  assert pd.api.types.is_datetime64_any_dtype(data["datetime_local_time"])
  assert pd.api.types.is_numeric_dtype(data["actual_price"])
  assert pd.api.types.is_numeric_dtype(data["forecast_price"])


def test_normalize_pool_price_report_rejects_empty_records() -> None:
  fake_report = build_pool_price_report([])

  with pytest.raises(
    ValueError,
    match="does not contain pool price records",
  ):
    normalize_pool_price_report(fake_report)


def test_normalize_pool_price_report_accepts_forecast_only_future_row() -> None:
  fake_report = build_pool_price_report([
    {
      "begin_datetime_utc": "2026-07-21 01:00",
      "begin_datetime_mpt": "2026-07-20 19:00",
      "pool_price": None,
      "forecast_pool_price": "35.40",
    }
  ])

  data = normalize_pool_price_report(fake_report)

  assert pd.isna(data.iloc[0]["actual_price"])
  assert data.iloc[0]["forecast_price"] == 35.40
