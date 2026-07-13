import pytest

from electricity_predictor.modeling.classification.final_test_evaluation import (
  get_float_parameter,
  get_int_parameter,
  get_optional_int_parameter,
  parse_model_parameters,
  validate_tuned_model_parameters,
)


def test_parse_model_parameters():
  parameters = parse_model_parameters(
    "n_estimators=200; max_depth=None; learning_rate=0.05"
  )

  assert parameters["n_estimators"] == "200"
  assert parameters["max_depth"] == "None"
  assert parameters["learning_rate"] == "0.05"


def test_parameter_helpers_convert_saved_values():
  parameters = {
    "C": "10.0",
    "n_estimators": "200",
    "max_depth": "None",
  }

  assert get_float_parameter(parameters, ["C"], 1.0) == 10.0
  assert get_int_parameter(
    parameters,
    ["n_estimators"],
    100,
  ) == 200
  assert get_optional_int_parameter(
    parameters,
    ["max_depth"],
    5,
  ) is None


def test_validate_tuned_model_parameters_rejects_missing_values():
  with pytest.raises(ValueError, match="missing required parameters"):
    validate_tuned_model_parameters(
      model_name="logistic_regression_tuned",
      parameters={},
    )
