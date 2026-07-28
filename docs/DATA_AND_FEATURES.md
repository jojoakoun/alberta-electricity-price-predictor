# Data and Features

## Source

WattWise consumes hourly Alberta electricity information from the Alberta
Electric System Operator (AESO).

Normalized source fields include:

- UTC datetime;
- Alberta local datetime;
- actual pool price;
- forecast pool price;
- Alberta internal load.

## Data lineage

```text
source API / raw CSV
  → data/raw/
  → cleaning and normalization
  → data/interim/current_historical_prices_clean.csv
  → feature engineering
  → data/processed/modeling_dataset.csv
  → chronological training datasets
  → lifecycle candidate datasets
```

Raw data is source evidence. Interim and processed files are reproducible
outputs and must not be edited by hand.

## Time contract

UTC is the canonical ordering and comparison key. Alberta local time is retained
for user display and calendar features.

Chronological splitting is required because random splitting would allow future
market patterns to leak into earlier training periods. A purge gap reduces
boundary leakage from lagged and rolling features.

## Shared column contract

Authoritative path:

`src/electricity_predictor/contracts/columns.py`

This file owns shared names, supported horizons, feature lists, and required
training columns. Modules may define local schemas only for local-only data.

## Selected live feature contract

The live contract contains 14 features:

1. hour;
2. day of week;
3. month;
4. weekend indicator;
5. forecast price;
6. forecast price lagged one hour;
7. forecast price lagged 24 hours;
8. forecast-price 24-hour mean;
9. forecast-price 24-hour maximum;
10. forecast-price seven-day mean;
11. actual price lagged 24 hours;
12. safe actual-price 24-hour mean;
13. safe actual-price 24-hour maximum;
14. safe actual-price seven-day mean.

The actual-price features are delayed so live predictions do not depend on an
actual value that is unavailable at prediction time.

## Feature intuition

| Feature type | Intuition |
|---|---|
| Calendar | Electricity behaviour changes by hour, weekday, and season |
| Lag | Recent market values often carry predictive information |
| Rolling mean | Describes the recent price level |
| Rolling maximum | Describes recent stress or spike conditions |
| Forecast price | Encodes the system operator's forward expectation |
| Internal load | Describes demand pressure on the grid |

## Targets

Regression predicts a future pool price for supported horizons.
Classification predicts whether the future price belongs to the configured
spike regime.

Thresholds must be derived only from approved training or validation data. The
protected test split cannot influence feature design, candidate selection,
hyperparameters, or decision thresholds.

## Quality controls

The pipeline checks:

- required columns;
- chronological ordering;
- duplicate timestamps;
- missing-value expectations;
- feature and target availability;
- split boundaries;
- leakage-sensitive behaviour;
- live/training feature parity.
