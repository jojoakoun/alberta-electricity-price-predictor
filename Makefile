SHELL := /bin/bash
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

PYTHON ?= python
PIP ?= pip
PYTEST ?= pytest
NPM ?= npm
CURL ?= curl
SERVER_DIR ?= app/server
CLIENT_DIR ?= app/client
DOTENV ?= $(SERVER_DIR)/node_modules/.bin/dotenv

# All command targets are phony; keep this inventory synchronized with help.
.PHONY: \
	help \
	install \
	verify \
	app-check \
	database-check \
	dev \
	stop \
	sync-history \
	sync-and-predict \
	worker-run \
	research-rebuild \
	research-rebuild-all \
	lifecycle-status \
	lifecycle-run \
	lifecycle-promote \
	lifecycle-rollback \
	release-build \
	models-install \
	hourly-refresh \
	retrain-if-due \
	local-bootstrap \
	db-clean \
	config-check \
	compile-check \
	inference-check \
	test-python \
	test-server \
	test-client \
	refresh-data \
	data-quality \
	features \
	feature-quality \
	training-data \
	regression-models \
	select-best-regression-model \
	classification-models \
	select-best-classification-model \
	spike-definition-analysis \
	spike-regime-analysis \
	decision-window-analysis \
	decision-regime-analysis \
	decision-policy-backtest \
	decision-policy-calibration \
	predicted-decision-stress-test \
	decision-analysis \
	final-regression-evaluation \
	save-selected-regression-models \
	final-classification-evaluation \
	save-selected-classification-models

# ==============================================================================
# Help: complete catalogue grouped by the responsibilities used below.
# ==============================================================================

help:
	@echo ""
	@echo "WattWise commands"
	@echo ""
	@echo "Setup and verification:"
	@echo "  make install              Install Python and Node dependencies"
	@echo "  make verify               Run the complete automated verification"
	@echo "  make app-check            Verify the local API endpoints"
	@echo "  make database-check       Verify local PostgreSQL connectivity"
	@echo ""
	@echo "Application:"
	@echo "  make dev                  Start the API and frontend locally"
	@echo "  make stop                 Stop local application processes"
	@echo "  make sync-and-predict     Refresh data, sync history, and predict"
	@echo "  make worker-run           Run one production worker cycle"
	@echo ""
	@echo "Data and model research:"
	@echo "  make sync-history         Synchronize historical prices to PostgreSQL"
	@echo "  make research-rebuild     Rebuild validation research outputs"
	@echo "  make research-rebuild-all Run the complete approved research rebuild"
	@echo ""
	@echo "Model lifecycle:"
	@echo "  make lifecycle-status     Show current lifecycle state"
	@echo "  make lifecycle-run        Prepare and compare lifecycle candidates"
	@echo "  make lifecycle-promote    Promote an approved candidate"
	@echo "  make lifecycle-rollback   Roll back the active model registry"
	@echo ""
	@echo "Release and scheduling:"
	@echo "  make release-build        Build a versioned model release"
	@echo "  make models-install       Install a prepared model release"
	@echo "  make hourly-refresh       Run the scheduled hourly refresh"
	@echo "  make retrain-if-due       Run lifecycle preparation when due"
	@echo ""
	@echo "Local maintenance:"
	@echo "  make local-bootstrap      Prepare the local database and application"
	@echo "  make db-clean CONFIRM=YES Remove local application data"
	@echo ""
# ==============================================================================
# Configuration and installation
# Install dependencies and validate configuration without running a pipeline.
# ==============================================================================

install:
	# Install Python development/runtime dependencies and both Node workspaces.
	# Writes local dependency environments only; it does not install active models.
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

	# Install backend and frontend dependencies.
	$(NPM) --prefix $(SERVER_DIR) install
	$(NPM) --prefix $(CLIENT_DIR) install

config-check:
	# Verify that the project configuration loads correctly.
	$(PYTHON) -c \
		"from electricity_predictor.config import load_configuration; print(load_configuration()['project']['name'])"


# ==============================================================================
# Project verification
# Run static checks and automated suites without rebuilding research data.
# ==============================================================================

compile-check:
	# Compile Python source files to detect syntax and import problems.
	$(PYTHON) -m compileall -q src

inference-check:
	# Run focused model-serving and inference tests.
	$(PYTEST) -q tests/serving

test-python:
	# Run the complete Python test suite.
	$(PYTEST)

test-server:
	# Run the Express API test suite.
	NODE_ENV=test $(NPM) --prefix $(SERVER_DIR) test

test-client:
	# Run frontend tests, lint, and the production build.
	$(NPM) --prefix $(CLIENT_DIR) test
	$(NPM) --prefix $(CLIENT_DIR) run lint
	$(NPM) --prefix $(CLIENT_DIR) run build

verify:
	# Verify the project without rebuilding or retraining models.
	$(MAKE) config-check
	$(MAKE) compile-check
	$(MAKE) inference-check
	$(MAKE) test-python
	$(MAKE) test-server
	$(MAKE) test-client
	git diff --check


# ==============================================================================
# Historical data
# Rebuild and inspect clean history; PostgreSQL synchronization remains explicit.
# ==============================================================================

refresh-data:
	# Rebuild canonical research history from the configured CSV and normalized AESO data.
	# Writes interim CSV artifacts; does not touch PostgreSQL or train models.
	$(PYTHON) \
		src/electricity_predictor/data/pipeline.py

data-quality:
	# Inspect the refreshed historical dataset.
	$(PYTHON) \
		src/electricity_predictor/data/data_quality.py

sync-history:
	# Upsert the canonical clean-history CSV into PostgreSQL hourly_prices.
	# Requires DATABASE_URL; does not create predictions or train models.
	$(PYTHON) -m electricity_predictor.worker.research_history_sync


# ==============================================================================
# Feature engineering
# Create, inspect, and finalize chronological model-ready datasets.
# ==============================================================================

features:
	# Build the feature-engineered modeling dataset.
	$(PYTHON) \
		src/electricity_predictor/features/feature_engineering.py

feature-quality:
	# Inspect feature-engineering output quality.
	$(PYTHON) \
		src/electricity_predictor/features/feature_quality.py

training-data:
	# Build the chronological model-ready training dataset.
	$(PYTHON) \
		src/electricity_predictor/features/training_data.py


# ==============================================================================
# Regression research
# Train, tune, compare, select, protected-test evaluate, and save regression artifacts.
# ==============================================================================

regression-models:
	# Run the complete regression-model comparison.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/run_regression_models.py

select-best-regression-model:
	# Select the strongest validation regression model per horizon.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/best_model_selection.py

final-regression-evaluation:
	# Refit selected regression configurations and evaluate on the protected test split.
	# Writes final reports and must not be used for model selection.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/final_test_evaluation.py

save-selected-regression-models:
	# Refit selected regression configurations and serialize artifacts plus metadata.
	# Saves research models but does not activate or promote them.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/save_selected_models.py


# ==============================================================================
# Classification research
# Define spikes, train, tune, select, protected-test evaluate, and save classifiers.
# ==============================================================================

spike-definition-analysis:
	# Compare train-derived spike definitions.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/analyze_spike_definition.py

spike-regime-analysis:
	# Analyze yearly spike rates.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/analyze_spike_regime.py

classification-models:
	# Run the complete classification-model comparison.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/run_classification_models.py

select-best-classification-model:
	# Select the strongest validation classifier per horizon.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/best_model_selection.py

final-classification-evaluation:
	# Refit selected classifiers and evaluate on the protected test split.
	# Writes threshold/uncertainty reports and must not drive model selection.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/final_test_evaluation.py

save-selected-classification-models:
	# Refit selected classifiers and serialize artifacts plus metadata.
	# Saves research models but does not activate or promote them.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/save_selected_models.py


# ==============================================================================
# Decision policy
# Analyze consumer decision rules using PostgreSQL history and saved regression artifacts.
# ==============================================================================

decision-window-analysis:
	# Compare rolling windows and write stability reports.
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.analyze_decision_windows

decision-regime-analysis:
	# Compare decision stability across market regimes.
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.analyze_decision_regimes

decision-policy-backtest:
	# Backtest candidate rolling-window policies.
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.backtest_decision_windows

decision-policy-calibration:
	# Calibrate recommendation quantiles and threshold multipliers.
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.calibrate_decision_policy

predicted-decision-stress-test:
	# Compare predictions with actual future-price labels.
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.stress_test_predicted_decisions

decision-analysis:
	# Regenerate research and calibration reports without opening the protected test.
	$(MAKE) decision-window-analysis
	$(MAKE) decision-regime-analysis
	$(MAKE) decision-policy-backtest
	$(MAKE) decision-policy-calibration


# ==============================================================================
# Research orchestration
# Run approved research stages sequentially and fail fast; these workflows train models.
# ==============================================================================

research-rebuild:
	# Run repeatable research and validation sequentially without opening protected test data.
	$(MAKE) config-check
	$(MAKE) refresh-data
	$(MAKE) sync-history
	$(MAKE) data-quality
	$(MAKE) features
	$(MAKE) feature-quality
	$(MAKE) training-data
	$(MAKE) spike-definition-analysis
	$(MAKE) spike-regime-analysis
	$(MAKE) regression-models
	$(MAKE) select-best-regression-model
	$(MAKE) classification-models
	$(MAKE) select-best-classification-model
	$(MAKE) decision-analysis
	$(MAKE) compile-check
	$(MAKE) inference-check
	$(MAKE) test-python

research-rebuild-all:
	# Run research, perform the explicitly protected final evaluations, save selected
	# artifacts, and publish predictions. Use only after final evaluation approval.
	$(MAKE) research-rebuild
	$(MAKE) final-regression-evaluation
	$(MAKE) final-classification-evaluation
	$(MAKE) save-selected-regression-models
	$(MAKE) save-selected-classification-models
	$(MAKE) predicted-decision-stress-test
	$(MAKE) sync-and-predict


# ==============================================================================
# Model lifecycle
# Inspect, challenge, promote, restore, package, or install production model releases.
# ==============================================================================

lifecycle-status:
	# Show the scheduler state without training models.
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_retraining_scheduler \
		--status

	@echo ""
	@echo "===== ACTIVE MODEL REGISTRY ====="
	@if [ -f models/production/active_models.json ]; then \
		$(PYTHON) -m json.tool \
			models/production/active_models.json; \
	else \
		echo "No active model registry found."; \
	fi

	@echo ""

lifecycle-run:
	# When due (or FORCE=1), train and evaluate challengers against active champions.
	# Creates candidate artifacts and reports but never promotes automatically.
	@force_flag=""; \
	if [ "$(FORCE)" = "1" ]; then \
		force_flag="--force"; \
	fi; \
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_retraining_scheduler \
		$$force_flag

lifecycle-promote:
	# Promote one manually approved task and snapshot the prior active registry.
	# Requires TASK=regression|classification and changes serving state.
	@if [ "$(TASK)" != "regression" ] && \
		[ "$(TASK)" != "classification" ]; then \
		echo "ERROR: TASK must be regression or classification."; \
		echo "Example:"; \
		echo "  make lifecycle-promote TASK=regression"; \
		exit 1; \
	fi

	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_promotion \
		--task "$(TASK)"

lifecycle-rollback:
	# Restore an explicit active-registry snapshot without retraining models.
	# Requires an existing SNAPSHOT and changes serving state.
	@if [ -z "$(SNAPSHOT)" ]; then \
		echo "ERROR: SNAPSHOT is required."; \
		echo "Example:"; \
		echo "  make lifecycle-rollback \\"; \
		echo "    SNAPSHOT=models/production/history/<snapshot>.json"; \
		exit 1; \
	fi

	@if [ ! -f "$(SNAPSHOT)" ]; then \
		echo "ERROR: Snapshot does not exist: $(SNAPSHOT)"; \
		exit 1; \
	fi

	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_promotion \
		--rollback "$(SNAPSHOT)"

release-build:
	# Package only artifacts referenced by the active registry into a release bundle.
	# Writes dist/model-releases; does not train or promote models.
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.release_bundle

models-install:
	# Install a checksum-pinned remote release or validate the local active registry.
	# May write production model files; does not train models.
	@release_url="$${MODEL_RELEASE_URL:-}"; \
	release_sha256="$${MODEL_RELEASE_SHA256:-}"; \
	if [ -n "$$release_url" ] || [ -n "$$release_sha256" ]; then \
		if [ -z "$$release_url" ] || [ -z "$$release_sha256" ]; then \
			echo "ERROR: MODEL_RELEASE_URL and MODEL_RELEASE_SHA256 must be set together."; \
			exit 1; \
		fi; \
		echo "Installing configured production model release."; \
		$(PYTHON) -m electricity_predictor.serving.release_installer; \
	elif [ -f models/production/active_models.json ]; then \
		echo "No remote model release configured."; \
		echo "Using local active model registry:"; \
		echo "  models/production/active_models.json"; \
	else \
		echo "ERROR: No active models are available."; \
		echo "Local development requires:"; \
		echo "  models/production/active_models.json"; \
		echo "Production requires:"; \
		echo "  MODEL_RELEASE_URL"; \
		echo "  MODEL_RELEASE_SHA256"; \
		exit 1; \
	fi


# ==============================================================================
# Operational worker
# Refresh AESO/PostgreSQL state and publish predictions with active models; never train.
# ==============================================================================

sync-and-predict:
	# Canonical operational pipeline: refresh AESO/PostgreSQL state, build inference
	# features, load active models, and persist one five-horizon prediction run.
	$(PYTHON) -m electricity_predictor.worker.application_prediction_pipeline

worker-run:
	# Production entrypoint: ensure active models, refresh AESO/PostgreSQL data,
	# generate five horizons, and persist the run; never trains models.
	$(PYTHON) \
		-m electricity_predictor.worker.production_worker


# ==============================================================================
# Local application
# Start, stop, and probe the local Express and React application.
# ==============================================================================

dev:
	# Start local Express/Nodemon and React/Vite processes. The application reads
	# PostgreSQL but this target does not refresh data or create predictions.
	./scripts/dev-app.sh

stop:
	# Stop Nodemon and Vite processes started for local development.
	# Retains the existing broad process match and does not modify PostgreSQL.
	pkill -f "nodemon" || true
	pkill -f "vite" || true

app-check:
	# Verify public application endpoints while the API is running.
	@echo "===== HEALTH ====="
	$(CURL) -fsS \
		http://127.0.0.1:8000/api/v1/health

	@echo ""
	@echo "===== NOW ====="
	$(CURL) -fsS \
		http://127.0.0.1:8000/api/v1/now

	@echo ""
	@echo "===== TODAY ====="
	$(CURL) -fsS \
		http://127.0.0.1:8000/api/v1/today

	@echo ""


# ==============================================================================
# Database
# Perform a read-only PostgreSQL connectivity check through the root environment.
# ==============================================================================

database-check:
	# Load DATABASE_URL from root .env and issue a read-only PostgreSQL identity/time query.
	# Requires the server dotenv executable and psql.
	$(DOTENV) \
		-e .env \
		-- sh -c \
		'psql "$$DATABASE_URL" -c \
		"SELECT current_database(), current_user, NOW() AS database_time;"'


# ==============================================================================
# Destructive operations
# Isolate confirmation-gated local database deletion from ordinary maintenance.
# ==============================================================================

db-clean:
	# DESTRUCTIVE local-only operation. Truncates application tables while preserving
	# schema/migrations; requires CONFIRM=YES and rejects non-local DATABASE_URL values.
	@CONFIRM_DB_CLEANUP="$(CONFIRM)" \
		./scripts/cleanup_local_database.sh


# ==============================================================================
# Exports and maintenance
# Build and verify project context and archive outputs.
# ==============================================================================

# ==============================================================================
# Compatibility aliases
# Keep legacy names separate; every target delegates to a canonical command.
# ==============================================================================

# ==============================================================================
# Final local and scheduled workflows
# ==============================================================================


hourly-refresh:
	# Refresh AESO/PostgreSQL state and publish one current-hour five-horizon run.
	$(MAKE) sync-and-predict

retrain-if-due:
	# Run the lifecycle checker; candidate training occurs only when the interval is due.
	# Promotion remains manual.
	$(MAKE) lifecycle-run

local-bootstrap:
	# Rebuild the local operational state without retraining or protected evaluation.
	$(MAKE) models-install
	$(MAKE) database-check
	$(MAKE) sync-history
	$(MAKE) hourly-refresh
