# Project Decisions

This file records the main technical and product decisions for the Alberta Electricity Price Predictor.

Each entry explains:

- what we chose
- why we chose it
- what we rejected
- what comes next

## Phase 0 — Repository Setup

### Decision 1 — Build a clean public-first project

We chose to build the project from zero with a clean public repository structure.

Why: the repository must be easy to understand, easy to run, and easy to maintain.

Rejected: starting with unnecessary complexity before the core product works.

Next: create the project foundation, then add data engineering in Phase 1.

### Decision 2 — Keep the public product name simple

We chose to use `Alberta Electricity Price Predictor` as the project name for now.

Why: this name is clear and describes the project directly.

Rejected: using a separate brand name before the product direction is stable.

Next: revisit branding only after the core product works.
