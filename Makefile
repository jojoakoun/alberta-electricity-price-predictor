SHELL := /bin/bash
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

PYTHON ?= python
PIP ?= pip
PYTEST ?= pytest
NPM ?= npm
CURL ?= curl

.PHONY: \
	help \
	install \
	dev \
	stop \
	app-refresh \
	models-install \
	worker-run \
	lifecycle-status \
	lifecycle-run \
	lifecycle-promote \
	lifecycle-rollback \
	release-build \
	verify \
	compile-check \
	config-check \
	inference-check \
	test-python \
	test-server \
	test-client \
	test \
	app-check \
	database-check \
	refresh-data \
	sync-history \
	sync-and-predict \
	data-quality \
	features \
	feature-quality \
	training-data \
	research-rebuild \
	research-rebuild-all \
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
	db-clean \
	project-context \
	project-zip \
	project-export \
	project-export-check \
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
	pipelines


# ==============================================================================
# Help
# ==============================================================================

help:
	@echo ""
	@echo "WattWise / Alberta Electricity Predictor"
	@echo ""
	@echo "Primary commands"
	@echo "  make dev                         Start the API and frontend locally"
	@echo "  make stop                        Stop local API and frontend processes"
	@echo "  make app-refresh                 Refresh AESO data and publish predictions"
	@echo "  make worker-run                  Run one production worker cycle"
	@echo "  make lifecycle-run               Run only when the 90-day interval is due"
	@echo "  make verify                      Verify the complete project"
	@echo ""
	@echo "Model lifecycle"
	@echo "  make lifecycle-status            Show lifecycle configuration and active models"
	@echo "  make lifecycle-run               Create and evaluate a challenger when due"
	@echo "  make lifecycle-promote TASK=...  Promote regression or classification manually"
	@echo "  make lifecycle-rollback SNAPSHOT=..."
	@echo "                                   Restore a previous active-model registry"
	@echo "  make release-build               Build the active production model release"
	@echo ""
	@echo "Production"
	@echo "  make models-install              Ensure active models are available"
	@echo "  make worker-run                  Install models, refresh data, and predict"
	@echo ""
	@echo "Data and application"
	@echo "  make refresh-data                Refresh the historical AESO dataset"
	@echo "  make sync-history                Synchronize historical rows with PostgreSQL"
	@echo "  make sync-and-predict            Publish one five-horizon prediction run"
	@echo "  make app-check                   Check Health, Now, and Today endpoints"
	@echo "  make database-check              Verify the PostgreSQL connection"
	@echo ""
	@echo "Research"
	@echo "  make research-rebuild            Rebuild historical ML research artifacts"
	@echo "  make research-rebuild-all        Rebuild research artifacts and app predictions"
	@echo ""
	@echo "Maintenance"
	@echo "  make project-context             Export project text context"
	@echo "  make project-zip                 Create the full project ZIP"
	@echo "  make project-export              Generate all project exports"
	@echo "  make db-clean CONFIRM=YES"
	@echo "                                   Remove local application data"
	@echo ""


# ==============================================================================
# Primary workflows
# ==============================================================================

install:
	# Install runtime, research, and test dependencies for local development.
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .

	# Install backend and frontend dependencies.
	$(NPM) --prefix app/server install
	$(NPM) --prefix app/client install


dev:
	# Start Express with Nodemon and React with Vite.
	./scripts/dev-app.sh


stop:
	# Stop local development processes started by make dev.
	pkill -f "nodemon" || true
	pkill -f "vite" || true


app-refresh:
	# Incrementally refresh PostgreSQL from AESO and publish predictions.
	$(PYTHON) -m electricity_predictor.worker.operational_pipeline


models-install:
	# Install a remote release or use the existing local active models.
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


worker-run:
	# Canonical production worker: ensure models, refresh data, and predict.
	$(PYTHON) \
		-m electricity_predictor.worker.production


# ==============================================================================
# Model lifecycle
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
	# Refresh data and evaluate a challenger only when retraining is due.
	@force_flag=""; \
	if [ "$(FORCE)" = "1" ]; then \
		force_flag="--force"; \
	fi; \
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.runner \
		$$force_flag


lifecycle-promote:
	# Promote one task only after manual review of the comparison report.
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
	# Restore a previous active-model registry snapshot.
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
	# Package only the currently active production models.
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.release_bundle


# ==============================================================================
# Verification
# ==============================================================================

config-check:
	# Verify that the project configuration loads correctly.
	$(PYTHON) -c \
		"from electricity_predictor.config import load_configuration; print(load_configuration()['project']['name'])"


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
	NODE_ENV=test $(NPM) --prefix app/server test


test-client:
	# Run frontend tests, lint, and the production build.
	$(NPM) --prefix app/client test
	$(NPM) --prefix app/client run lint
	$(NPM) --prefix app/client run build


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
# Local application checks
# ==============================================================================

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


database-check:
	# Load DATABASE_URL from the root .env and verify PostgreSQL.
	./app/server/node_modules/.bin/dotenv \
		-e .env \
		-- sh -c \
		'psql "$$DATABASE_URL" -c \
		"SELECT current_database(), current_user, NOW() AS database_time;"'


# ==============================================================================
# Data refresh and prediction internals
# ==============================================================================

refresh-data:
	# Refresh historical data from CSV and the latest AESO API data.
	$(PYTHON) \
		src/electricity_predictor/data/pipeline.py



sync-history:
	# Synchronize the complete refreshed research history with PostgreSQL.
	$(PYTHON) -m electricity_predictor.worker.research_history_sync


sync-and-predict:
	# Synchronize PostgreSQL and create one five-horizon prediction run.
	$(PYTHON) -m electricity_predictor.worker.operational_pipeline


data-quality:
	# Inspect the refreshed historical dataset.
	$(PYTHON) \
		src/electricity_predictor/data/data_quality.py


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
# Historical research rebuild
#
# These targets reproduce the original research workflow.
# They are not production schedulers and do not use champion-challenger promotion.
# ==============================================================================

research-rebuild:
	# Rebuild historical datasets, reports, evaluations, and model artifacts.
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
	$(MAKE) final-regression-evaluation
	$(MAKE) save-selected-regression-models
	$(MAKE) classification-models
	$(MAKE) select-best-classification-model
	$(MAKE) final-classification-evaluation
	$(MAKE) save-selected-classification-models
	$(MAKE) decision-analysis
	$(MAKE) compile-check
	$(MAKE) inference-check
	$(MAKE) test-python


research-rebuild-all:
	# Rebuild research artifacts, then create fresh application predictions.
	$(MAKE) research-rebuild
	$(MAKE) sync-and-predict


# ==============================================================================
# Regression research commands
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
	# Evaluate selected regression models on the protected test split.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/final_test_evaluation.py


save-selected-regression-models:
	# Save selected historical regression artifacts.
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/save_selected_models.py


# ==============================================================================
# Classification research commands
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
	# Evaluate selected classifiers on the protected test split.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/final_test_evaluation.py


save-selected-classification-models:
	# Save selected historical classification artifacts.
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/save_selected_models.py


# ==============================================================================
# Decision-policy research
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
	# Regenerate all decision-policy reports in dependency order.
	$(MAKE) decision-window-analysis
	$(MAKE) decision-regime-analysis
	$(MAKE) decision-policy-backtest
	$(MAKE) decision-policy-calibration
	$(MAKE) predicted-decision-stress-test


# ==============================================================================
# Maintenance and exports
# ==============================================================================

db-clean:
	# Delete local application data while preserving schema and migrations.
	@CONFIRM_DB_CLEANUP="$(CONFIRM)" \
		./scripts/cleanup_local_database.sh


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
# Backward-compatible aliases
#
# Keep temporarily so existing documentation and commands do not break.
# New workflows should use the canonical names shown by make help.
# ==============================================================================

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
