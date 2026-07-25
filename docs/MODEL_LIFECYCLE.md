# Model Lifecycle

## Purpose

The lifecycle separates model construction from model activation.

A model is not active merely because it was trained successfully.

## Lifecycle stages

### 1. Research

Research pipelines prepare datasets, train model families, tune supported
algorithms, and select validation candidates.

```bash
make research-rebuild
```

A full approved rebuild is available through:

```bash
make research-rebuild-all
```

The full rebuild must be intentional because it can include final evaluation
and publication-oriented outputs.

### 2. Candidate preparation

Lifecycle preparation creates candidate bundles and records the exact data,
features, configuration, and model metadata used to create them.

```bash
make lifecycle-run
```

### 3. Comparison

Candidates are compared against the actual currently active model version.

Comparison and promotion are separate actions.

### 4. Promotion

Promotion is explicit:

```bash
make lifecycle-promote
```

Promotion owns active registry writes, including the first activation when no
active model exists.

### 5. Rollback

Rollback restores a previously registered active version:

```bash
make lifecycle-rollback
```

### 6. Status

```bash
make lifecycle-status
```

## Initial state

The repository may legitimately contain no active model after a cleanup or
fresh installation.

In that state:

- application prediction cannot invent a model;
- the lifecycle can prepare and compare candidates;
- the first activation remains manual;
- the active registry is created only through approved promotion.

## Protected final evaluation

These tests are excluded from routine verification:

- `tests/modeling/regression/test_final_test_evaluation.py`
- `tests/modeling/classification/test_final_test_evaluation.py`

The protected test split is used only for an explicitly authorized final
evaluation. It must not be used to fit models, select candidates, tune
hyperparameters, or choose thresholds.

## Release flow

After an approved promotion:

```bash
make release-build
make models-install
```

A live refit may update a candidate bundle, but it must not directly activate
the result.
