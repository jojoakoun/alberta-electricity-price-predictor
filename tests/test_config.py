from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)


def test_load_configuration_returns_project_name() -> None:
  # The configuration file should load the official project name.
  configuration = load_configuration()

  assert configuration["project"]["name"] == "Alberta Electricity Price Predictor"


def test_load_configuration_contains_consumed_data_paths() -> None:
  configuration = load_configuration()

  assert "raw_data_dir" in configuration["paths"]
  assert "interim_data_dir" in configuration["paths"]


def test_configured_horizons_match_the_shared_production_contract() -> None:
  configuration = load_configuration()

  assert tuple(
    configuration["modeling"]["horizons_hours"]
  ) == SUPPORTED_FORECAST_HORIZONS_HOURS
