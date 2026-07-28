# Model Lifecycle

## Core rule

A trained model is not automatically a production model.

```text
training
  → candidate
  → validation and comparison
  → human review
  → explicit promotion
  → active registry
```

## Rebuild

```bash
make rebuild
```

The rebuild reconstructs data, features, regression and classification results,
decision-policy analysis, live candidate models, and lifecycle evidence.

It does **not**:

- execute protected final-evaluation tests;
- activate the candidate;
- replace the active registry automatically.

## Candidate preparation

Internal lifecycle modules record:

- candidate identifier;
- source-data and split metadata;
- feature contract;
- model families and parameters;
- validation metrics;
- model artifact paths;
- comparison and promotion readiness.

Primary path:

`src/electricity_predictor/modeling/lifecycle/`

## Review

Before activation, review regression, classification, decision-policy, and
champion/challenger reports. Confirm that both technical quality and product
behaviour are acceptable.

## Activation

```bash
make activate
```

Activation validates the latest candidate and promotes the approved regression
and classification models. It is the only public command that may create or
change:

`models/production/active_models.json`

Immediately afterward:

```bash
make sync
```

## First activation

A clean repository may contain no active model. This is a valid initial state.
The first production model follows the same review and promotion boundary as
later replacements.

## Rollback principle

Rollback restores a previously approved registry/release. It must not retrain a
model. After restoring the previous version, run `make sync` to generate fresh
predictions with that version.

## Protected final evaluation

Routine verification excludes:

- `tests/modeling/regression/test_final_test_evaluation.py`
- `tests/modeling/classification/test_final_test_evaluation.py`

These tests may run only during an explicitly authorized final evaluation. Their
results must never feed training, tuning, feature design, or threshold selection.

## Release boundary

Deployment must use an approved active release. Deployment itself cannot train,
select, or promote a model.
