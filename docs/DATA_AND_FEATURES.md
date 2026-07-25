# Data and Features

## Data source

The project consumes hourly Alberta electricity information from the Alberta
Electric System Operator.

The normalized source fields include:

- UTC datetime
- Alberta local datetime
- actual pool price
- forecast pool price
- Alberta internal load

## Data stages

```text
raw source
  → cleaned historical data
  → engineered modeling data
  → chronological training data
  → lifecycle comparison data
```

Raw source files must not be replaced by generated datasets.

Generated data and model artifacts are reproducible outputs and should not be
treated as hand-maintained source files.

## Time handling

UTC is the canonical ordering key.

Local Alberta time is retained for user-facing interpretation and calendar
features.

Chronological splits use fixed calendar boundaries and a purge gap to reduce
leakage between training, validation, and test periods.

## Shared column contract

`src/electricity_predictor/contracts/columns.py` is the only authoritative
module for shared column names and feature lists.

Modules may define local schemas only when those schemas are specific to that
module and are not shared contracts.

## Live feature contract

The selected live contract contains 14 features:

1. hour
2. day of week
3. month
4. weekend indicator
5. forecast price
6. forecast price lagged by one hour
7. forecast price lagged by 24 hours
8. forecast-price 24-hour mean
9. forecast-price 24-hour maximum
10. forecast-price seven-day mean
11. actual price lagged by 24 hours
12. safe actual-price 24-hour mean
13. safe actual-price 24-hour maximum
14. safe actual-price seven-day mean

The actual-price features are delayed so that the live prediction contract does
not depend on future actual prices.

## Targets

Regression predicts future pool price for supported horizons.

Classification predicts whether the future price belongs to the configured
spike regime.

Target creation, spike thresholds, and decision thresholds must be derived from
approved training or validation data. Protected test results must not influence
feature design, model selection, or threshold tuning.

## Quality checks

The data pipeline checks:

- required columns
- chronological order
- duplicate timestamps
- missing-value expectations
- feature availability
- target availability
- split boundaries
- leakage-sensitive feature behavior
