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
	config-check \
	compile-check \
	inference-check \
	test-python \
	test-server \
	test-client \
	verify \
	refresh-data \
	data-quality \
	sync-history \
	features \
	feature-quality \
	training-data \
	baseline \
	linear-regression \
	ridge-regression \
	lasso-regression \
	lasso-tuning \
	elastic-net-regression \
	elastic-net-tuning \
	regression-models \
	select-best-regression-model \
	final-regression-evaluation \
	save-selected-regression-models \
	spike-definition-analysis \
	spike-regime-analysis \
	classification-baseline \
	logistic-regression \
	logistic-tuning \
	random-forest \
	random-forest-tuning \
	gradient-boosting \
	gradient-boosting-tuning \
	classification-models \
	select-best-classification-model \
	final-classification-evaluation \
	save-selected-classification-models \
	decision-window-analysis \
	decision-regime-analysis \
	decision-policy-backtest \
	decision-policy-calibration \
	predicted-decision-stress-test \
	decision-analysis \
	research-rebuild \
	research-rebuild-all \
	lifecycle-status \
	lifecycle-run \
	lifecycle-promote \
	lifecycle-rollback \
	release-build \
	models-install \
	sync-and-predict \
	worker-run \
	dev \
	stop \
	app-check \
	database-check \
	db-clean \
	project-context \
	project-zip \
	project-export \
	project-export-check \
	app-refresh \
	app-dev \
	app-stop \
	refresh-application \
	install-model-release \
	railway-worker \
	rebuild-ml \
	rebuild-all \
	pipeline \
	application-pipeline \
	production-pipeline \
	ml-pipeline \
	pipelines \
	test

# ==============================================================================
# Help: complete catalogue grouped by the responsibilities used below.
# ==============================================================================

help:
	@echo ""
	@echo "WattWise / Alberta Electricity Predictor"
	@echo ""
	@echo "Configuration and installation"
	@echo "  make install                               "
	@echo "  make config-check                          "
	@echo ""
	@echo "Project verification"
	@echo "  make compile-check                         "
	@echo "  make inference-check                       "
	@echo "  make test-python                           "
	@echo "  make test-server                           "
	@echo "  make test-client                           "
	@echo "  make verify                                "
	@echo ""
	@echo "Historical data"
	@echo "  make refresh-data                          "
	@echo "  make data-quality                          "
	@echo "  make sync-history                          "
	@echo ""
	@echo "Feature engineering"
	@echo "  make features                              "
	@echo "  make feature-quality                       "
	@echo "  make training-data                         "
	@echo ""
	@echo "Regression research"
	@echo "  make baseline                               [trains/evaluates]"
	@echo "  make linear-regression                      [trains/evaluates]"
	@echo "  make ridge-regression                       [trains/evaluates]"
	@echo "  make lasso-regression                       [trains/evaluates]"
	@echo "  make lasso-tuning                           [trains/evaluates]"
	@echo "  make elastic-net-regression                 [trains/evaluates]"
	@echo "  make elastic-net-tuning                     [trains/evaluates]"
	@echo "  make regression-models                      [trains/evaluates]"
	@echo "  make select-best-regression-model          "
	@echo "  make final-regression-evaluation            [trains/evaluates]"
	@echo "  make save-selected-regression-models       "
	@echo ""
	@echo "Classification research"
	@echo "  make spike-definition-analysis             "
	@echo "  make spike-regime-analysis                 "
	@echo "  make classification-baseline                [trains/evaluates]"
	@echo "  make logistic-regression                    [trains/evaluates]"
	@echo "  make logistic-tuning                        [trains/evaluates]"
	@echo "  make random-forest                          [trains/evaluates]"
	@echo "  make random-forest-tuning                   [trains/evaluates]"
	@echo "  make gradient-boosting                      [trains/evaluates]"
	@echo "  make gradient-boosting-tuning               [trains/evaluates]"
	@echo "  make classification-models                  [trains/evaluates]"
	@echo "  make select-best-classification-model      "
	@echo "  make final-classification-evaluation        [trains/evaluates]"
	@echo "  make save-selected-classification-models   "
	@echo ""
	@echo "Decision policy"
	@echo "  make decision-window-analysis              "
	@echo "  make decision-regime-analysis              "
	@echo "  make decision-policy-backtest              "
	@echo "  make decision-policy-calibration           "
	@echo "  make predicted-decision-stress-test         [protected test]"
	@echo "  make decision-analysis                      [validation only]"
	@echo ""
	@echo "Research orchestration"
	@echo "  make research-rebuild                       [validation only]"
	@echo "  make research-rebuild-all                   [protected test/publish]"
	@echo ""
	@echo "Model lifecycle"
	@echo "  make lifecycle-status                      "
	@echo "  make lifecycle-run                          [trains/evaluates]"
	@echo "  make lifecycle-promote                     "
	@echo "  make lifecycle-rollback                    "
	@echo "  make release-build                         "
	@echo "  make models-install                        "
	@echo ""
	@echo "Operational worker"
	@echo "  make sync-and-predict                       [active models]"
	@echo "  make worker-run                             [active models]"
	@echo ""
	@echo "Local application"
	@echo "  make dev                                   "
	@echo "  make stop                                  "
	@echo "  make app-check                             "
	@echo ""
	@echo "Database"
	@echo "  make database-check                        "
	@echo ""
	@echo "Destructive operations"
	@echo "  make db-clean                               [DESTRUCTIVE]"
	@echo ""
	@echo "Exports and maintenance"
	@echo "  make project-context                       "
	@echo "  make project-zip                           "
	@echo "  make project-export                        "
	@echo "  make project-export-check                  "
	@echo ""
	@echo "Compatibility aliases"
	@echo "  make app-refresh                            -> canonical target"
	@echo "  make app-dev                                -> canonical target"
	@echo "  make app-stop                               -> canonical target"
	@echo "  make refresh-application                    -> canonical target"
	@echo "  make install-model-release                  -> canonical target"
	@echo "  make railway-worker                         -> canonical target"
	@echo "  make rebuild-ml                             -> canonical target"
	@echo "  make rebuild-all                            -> canonical target"
	@echo "  make pipeline                               -> canonical target"
	@echo "  make application-pipeline                   -> canonical target"
	@echo "  make production-pipeline                    -> canonical target"
	@echo "  make ml-pipeline                            -> canonical target"
	@echo "  make pipelines                              -> canonical target"
	@echo "  make test                                   -> canonical target"
	@echo ""

# ==============================================================================
# Configuration and installation
# Install dependencies and validate configuration without running a pipeline.
# ==============================================================================

install:
	# Install Python development/runtime dependencies and both Node workspaces.
	# Writes local dependency environments only; it does not install active models.
	$(PIP) install -r requirements-dev.txt
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

baseline:
	# Evaluate the naive regression baseline.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/baseline/naive_baseline.py

linear-regression:
	# Train and evaluate Linear Regression.
	$(PYTHON) -m electricity_predictor.modeling.regression.linear.linear_regression

ridge-regression:
	# Train and evaluate Ridge Regression.
	$(PYTHON) -m electricity_predictor.modeling.regression.ridge.ridge_regression

lasso-regression:
	# Train and evaluate Lasso Regression.
	$(PYTHON) -m electricity_predictor.modeling.regression.lasso.lasso_regression

lasso-tuning:
	# Tune Lasso with chronological TimeSeriesSplit.
	$(PYTHON) -m electricity_predictor.modeling.regression.lasso.lasso_tuning

elastic-net-regression:
	# Train and evaluate Elastic Net Regression.
	$(PYTHON) -m electricity_predictor.modeling.regression.elastic_net.elastic_net_regression

elastic-net-tuning:
	# Tune Elastic Net with chronological TimeSeriesSplit.
	$(PYTHON) -m electricity_predictor.modeling.regression.elastic_net.elastic_net_tuning

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

classification-baseline:
	# Evaluate the naive spike-classification baseline.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/baseline/naive_spike_baseline.py

logistic-regression:
	# Train and evaluate Logistic Regression.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/logistic/logistic_regression.py

logistic-tuning:
	# Tune Logistic Regression.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/logistic/logistic_tuning.py

random-forest:
	# Train and evaluate Random Forest classification.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/random_forest/random_forest_classifier.py

random-forest-tuning:
	# Tune Random Forest classification.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/random_forest/random_forest_tuning.py

gradient-boosting:
	# Train and evaluate Gradient Boosting classification.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/gradient_boosting/gradient_boosting_classifier.py

gradient-boosting-tuning:
	# Tune Gradient Boosting classification.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/gradient_boosting/gradient_boosting_tuning.py

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
		-m electricity_predictor.modeling.lifecycle.runner \
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
		-m electricity_predictor.modeling.lifecycle.runner \
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
		-m electricity_predictor.modeling.lifecycle.promotion \
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
		-m electricity_predictor.modeling.lifecycle.promotion \
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
	$(PYTHON) -m electricity_predictor.worker.operational_pipeline

worker-run:
	# Production entrypoint: ensure active models, refresh AESO/PostgreSQL data,
	# generate five horizons, and persist the run; never trains models.
	$(PYTHON) \
		-m electricity_predictor.worker.production


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

project-context:
	# Export relevant text files and inventory binary files.
	$(PYTHON) \
		scripts/export_project_context.py \
		--mode context

project-zip:
	# Archive relevant project files, data, and model assets.
	$(PYTHON) \
		scripts/export_project_context.py \
		--mode zip

project-export:
	# Generate the complete context, ZIP archive, and manifests.
	$(PYTHON) \
		scripts/export_project_context.py \
		--mode all

	$(MAKE) project-export-check

project-export-check:
	@echo "===== PROJECT EXPORT ====="
	$(PYTHON) \
		scripts/verify_project_export.py
	@du -h \
		context_exports/project_context_full.txt
	@du -h \
		context_exports/alberta-electricity-price-predictor.zip


# ==============================================================================
# Compatibility aliases
# Keep legacy names separate; every target delegates to a canonical command.
# ==============================================================================

app-refresh:
	@echo "NOTICE: 'app-refresh' is a compatibility alias for 'sync-and-predict'."
	$(MAKE) sync-and-predict

app-dev:
	@echo "NOTICE: use 'make dev'."
	$(MAKE) dev

app-stop:
	@echo "NOTICE: use 'make stop'."
	$(MAKE) stop

refresh-application:
	@echo "NOTICE: use 'make app-refresh'."
	$(MAKE) app-refresh

install-model-release:
	@echo "NOTICE: use 'make models-install'."
	$(MAKE) models-install

railway-worker:
	@echo "NOTICE: use 'make worker-run'."
	$(MAKE) worker-run

rebuild-ml:
	@echo "NOTICE: use 'make research-rebuild'."
	$(MAKE) research-rebuild

rebuild-all:
	@echo "NOTICE: use 'make research-rebuild-all'."
	$(MAKE) research-rebuild-all

pipeline:
	@echo "NOTICE: use 'make refresh-data'."
	$(MAKE) refresh-data

application-pipeline:
	@echo "NOTICE: use 'make sync-and-predict'."
	$(MAKE) sync-and-predict

production-pipeline:
	@echo "NOTICE: use 'make app-refresh'."
	$(MAKE) app-refresh

ml-pipeline:
	@echo "NOTICE: use 'make research-rebuild'."
	$(MAKE) research-rebuild

pipelines:
	@echo "NOTICE: use 'make research-rebuild-all'."
	$(MAKE) research-rebuild-all

test:
	@echo "NOTICE: use 'make test-python' or 'make verify'."
	$(MAKE) test-python
