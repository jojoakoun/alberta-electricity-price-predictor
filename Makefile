SHELL := /bin/bash
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

PYTHON ?= python
PIP ?= pip

.PHONY: \
	help \
	install \
	test \
	test-python \
	test-server \
	test-client \
	verify \
	compile-check \
	config-check \
	app-dev \
	app-stop \
	app-check \
	database-check \
	refresh-data \
	sync-and-predict \
	refresh-application \
	rebuild-ml \
	rebuild-all \
	pipeline \
	application-pipeline \
	production-pipeline \
	ml-pipeline \
	pipelines \
	data-quality \
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
	inference-check \
	project-context \
	project-zip \
	project-export


# ==============================================================================
# Help
# ==============================================================================

help:
	@echo ""
	@echo "WattWise / Alberta Electricity Predictor"
	@echo ""
	@echo "Primary workflows"
	@echo "  make app-dev              Start the API and frontend development servers"
	@echo "  make app-stop             Stop local Nodemon and Vite processes"
	@echo "  make refresh-application Refresh AESO data and create a fresh prediction run"
	@echo "  make rebuild-ml          Rebuild datasets, reports, evaluations, and model artifacts"
	@echo "  make rebuild-all         Rebuild ML artifacts, then create fresh app predictions"
	@echo "  make verify              Run project-wide syntax, tests, lint, and build checks"
	@echo ""
	@echo "Data and application"
	@echo "  make refresh-data         Rebuild the current historical dataset"
	@echo "  make sync-and-predict     Synchronize PostgreSQL and save five predictions"
	@echo "  make database-check       Verify that PostgreSQL is reachable"
	@echo "  make app-check            Check the health, Now, and Today API endpoints"
	@echo ""
	@echo "Exports"
	@echo "  make project-context      Export project files into one text context"
	@echo "  make project-zip          Create a project ZIP archive"
	@echo "  make project-export       Generate both project exports"
	@echo ""


# ==============================================================================
# Installation
# ==============================================================================

install:
	# Install Python dependencies and register the local package.
	$(PIP) install -r requirements.txt
	$(PIP) install -e .

	# Install backend and frontend dependencies.
	npm --prefix app/server install
	npm --prefix app/client install


# ==============================================================================
# Local application development
# ==============================================================================

app-dev:
	# Start Express with Nodemon and React with Vite.
	./scripts/dev-app.sh

app-stop:
	# Stop local development processes started by app-dev.
	pkill -f "nodemon" || true
	pkill -f "vite" || true

app-check:
	# Verify the public application endpoints while the API is running.
	@echo "===== HEALTH ====="
	curl -fsS http://127.0.0.1:8000/api/v1/health
	@echo ""
	@echo "===== NOW ====="
	curl -fsS http://127.0.0.1:8000/api/v1/now
	@echo ""
	@echo "===== TODAY ====="
	curl -fsS http://127.0.0.1:8000/api/v1/today
	@echo ""

database-check:
	# Load DATABASE_URL from the root .env file and verify PostgreSQL.
	./app/server/node_modules/.bin/dotenv -e .env -- \
		sh -c 'psql "$$DATABASE_URL" -c "SELECT current_database(), current_user, NOW() AS database_time;"'


# ==============================================================================
# Fast operational application refresh
# ==============================================================================

refresh-data:
	# Refresh the historical dataset from CSV and the latest AESO API data.
	$(PYTHON) src/electricity_predictor/data/pipeline.py

sync-and-predict:
	# Synchronize PostgreSQL and create one fresh five-horizon prediction run.
	$(PYTHON) -m electricity_predictor.application_pipeline

refresh-application:
	# Normal operational workflow: refresh data, then publish fresh predictions.
	$(MAKE) refresh-data
	$(MAKE) sync-and-predict


# ==============================================================================
# Data preparation and quality
# ==============================================================================

data-quality:
	# Inspect the refreshed historical dataset before feature engineering.
	$(PYTHON) src/electricity_predictor/data/data_quality.py

features:
	# Build the feature-engineered modeling dataset.
	$(PYTHON) src/electricity_predictor/features/feature_engineering.py

feature-quality:
	# Inspect missing values and feature-engineering output quality.
	$(PYTHON) src/electricity_predictor/features/feature_quality.py

training-data:
	# Build the chronological model-ready training dataset.
	$(PYTHON) src/electricity_predictor/features/training_data.py


# ==============================================================================
# Regression modeling
# ==============================================================================

baseline:
	# Evaluate the naive regression baseline.
	$(PYTHON) src/electricity_predictor/modeling/regression/baseline/naive_baseline.py

linear-regression:
	# Train and evaluate Linear Regression on the validation split.
	$(PYTHON) src/electricity_predictor/modeling/regression/linear/linear_regression.py

ridge-regression:
	# Train and evaluate Ridge Regression on the validation split.
	$(PYTHON) src/electricity_predictor/modeling/regression/ridge/ridge_regression.py

lasso-regression:
	# Train and evaluate Lasso Regression on the validation split.
	$(PYTHON) src/electricity_predictor/modeling/regression/lasso/lasso_regression.py

lasso-tuning:
	# Tune Lasso with chronological TimeSeriesSplit.
	$(PYTHON) src/electricity_predictor/modeling/regression/lasso/lasso_tuning.py

elastic-net-regression:
	# Train and evaluate Elastic Net Regression.
	$(PYTHON) src/electricity_predictor/modeling/regression/elastic_net/elastic_net_regression.py

elastic-net-tuning:
	# Tune Elastic Net with chronological TimeSeriesSplit.
	$(PYTHON) src/electricity_predictor/modeling/regression/elastic_net/elastic_net_tuning.py

regression-models:
	# Run the complete regression-model comparison workflow.
	$(PYTHON) src/electricity_predictor/modeling/regression/run_regression_models.py

select-best-regression-model:
	# Select the strongest validation regression model for each horizon.
	$(PYTHON) src/electricity_predictor/modeling/regression/best_model_selection.py

final-regression-evaluation:
	# Evaluate selected regression models on the protected test split.
	$(PYTHON) src/electricity_predictor/modeling/regression/final_test_evaluation.py

save-selected-regression-models:
	# Train and save selected regression models as joblib artifacts.
	$(PYTHON) src/electricity_predictor/modeling/regression/save_selected_models.py


# ==============================================================================
# Spike classification modeling
# ==============================================================================

spike-definition-analysis:
	# Compare train-derived spike definitions across chronological splits.
	$(PYTHON) src/electricity_predictor/modeling/classification/analyze_spike_definition.py

spike-regime-analysis:
	# Analyze yearly spike rates using the frozen train-derived threshold.
	$(PYTHON) src/electricity_predictor/modeling/classification/analyze_spike_regime.py

classification-baseline:
	# Evaluate the naive spike-classification baseline.
	$(PYTHON) src/electricity_predictor/modeling/classification/baseline/naive_spike_baseline.py

logistic-regression:
	# Train and evaluate Logistic Regression for every horizon.
	$(PYTHON) src/electricity_predictor/modeling/classification/logistic/logistic_regression.py

logistic-tuning:
	# Tune Logistic Regression with chronological TimeSeriesSplit.
	$(PYTHON) src/electricity_predictor/modeling/classification/logistic/logistic_tuning.py

random-forest:
	# Train and evaluate Random Forest classification.
	$(PYTHON) src/electricity_predictor/modeling/classification/random_forest/random_forest_classifier.py

random-forest-tuning:
	# Tune Random Forest with chronological TimeSeriesSplit.
	$(PYTHON) src/electricity_predictor/modeling/classification/random_forest/random_forest_tuning.py

gradient-boosting:
	# Train and evaluate Gradient Boosting classification.
	$(PYTHON) src/electricity_predictor/modeling/classification/gradient_boosting/gradient_boosting_classifier.py

gradient-boosting-tuning:
	# Tune Gradient Boosting with chronological TimeSeriesSplit.
	$(PYTHON) src/electricity_predictor/modeling/classification/gradient_boosting/gradient_boosting_tuning.py

classification-models:
	# Run the complete multi-horizon classification comparison workflow.
	$(PYTHON) src/electricity_predictor/modeling/classification/run_classification_models.py

select-best-classification-model:
	# Select the strongest validation classifier for each horizon.
	$(PYTHON) src/electricity_predictor/modeling/classification/best_model_selection.py

final-classification-evaluation:
	# Evaluate selected classifiers on the protected test split.
	$(PYTHON) src/electricity_predictor/modeling/classification/final_test_evaluation.py

save-selected-classification-models:
	# Train and save selected classification models as joblib artifacts.
	$(PYTHON) src/electricity_predictor/modeling/classification/save_selected_models.py


# ==============================================================================
# Decision-policy analysis
# ==============================================================================

decision-window-analysis:
	# Compare rolling windows and write detailed stability reports.
	$(PYTHON) -m electricity_predictor.modeling.decision.analyze_decision_windows

decision-regime-analysis:
	# Compare decision stability across historical market regimes.
	$(PYTHON) -m electricity_predictor.modeling.decision.analyze_decision_regimes

decision-policy-backtest:
	# Backtest candidate rolling-window policies.
	$(PYTHON) -m electricity_predictor.modeling.decision.backtest_decision_windows

decision-policy-calibration:
	# Calibrate recommendation quantiles and avoid-threshold multipliers.
	$(PYTHON) -m electricity_predictor.modeling.decision.calibrate_decision_policy

predicted-decision-stress-test:
	# Compare predicted recommendations with actual future-price labels.
	$(PYTHON) -m electricity_predictor.modeling.decision.stress_test_predicted_decisions

decision-analysis:
	# Regenerate all decision-policy reports in dependency order.
	$(MAKE) decision-window-analysis
	$(MAKE) decision-regime-analysis
	$(MAKE) decision-policy-backtest
	$(MAKE) decision-policy-calibration
	$(MAKE) predicted-decision-stress-test


# ==============================================================================
# Full machine-learning rebuild
# ==============================================================================

rebuild-ml:
	# Rebuild data, reports, evaluations, and all selected model artifacts.
	$(MAKE) config-check
	$(MAKE) refresh-data
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

rebuild-all:
	# Full rebuild: retrain ML artifacts, then publish a fresh app prediction run.
	$(MAKE) rebuild-ml
	$(MAKE) sync-and-predict


# ==============================================================================
# Verification
# ==============================================================================

compile-check:
	# Compile Python source files to detect syntax and import problems.
	$(PYTHON) -m compileall -q src

config-check:
	# Verify that the project configuration loads correctly.
	$(PYTHON) -c "from electricity_predictor.config import load_configuration; print(load_configuration()['project']['name'])"

inference-check:
	# Run focused serving and inference tests.
	pytest -q tests/serving

test-python:
	# Run the complete Python test suite.
	pytest

test-server:
	# Run the Express API test suite.
	NODE_ENV=test npm --prefix app/server test

test-client:
	# Run frontend tests, lint, and the production build.
	npm --prefix app/client test
	npm --prefix app/client run lint
	npm --prefix app/client run build

test:
	# Backward-compatible alias for the Python test suite.
	$(MAKE) test-python

verify:
	# Run project-wide verification without retraining models.
	$(MAKE) config-check
	$(MAKE) compile-check
	$(MAKE) inference-check
	$(MAKE) test-python
	$(MAKE) test-server
	$(MAKE) test-client
	git diff --check


# ==============================================================================
# Backward-compatible aliases
# ==============================================================================

pipeline:
	# Legacy alias: rebuild the current historical dataset.
	$(MAKE) refresh-data

application-pipeline:
	# Legacy alias: synchronize PostgreSQL and create predictions.
	$(MAKE) sync-and-predict

production-pipeline:
	# Legacy alias: perform the normal operational application refresh.
	$(MAKE) refresh-application

ml-pipeline:
	# Legacy alias: perform the full machine-learning rebuild.
	$(MAKE) rebuild-ml

pipelines:
	# Legacy alias: perform the complete ML and application rebuild.
	@echo "NOTICE: 'pipelines' is a legacy name. Prefer 'make rebuild-all'."
	$(MAKE) rebuild-all


# ==============================================================================
# Project exports
# ==============================================================================

project-context:
	# Export tracked and non-ignored text files without running pipelines.
	mkdir -p context_exports
	git ls-files --cached --others --exclude-standard \
		| grep -v '^context_exports/' \
		| sort > context_exports/.project_files.txt
	{ \
		echo "===== PROJECT CONTEXT GENERATED AT ====="; \
		date; \
		echo ""; \
		echo "===== BRANCH ====="; \
		git branch --show-current; \
		echo ""; \
		echo "===== GIT STATUS ====="; \
		git status --short; \
		echo ""; \
		echo "===== GIT DIFF STAT ====="; \
		git diff --stat; \
		echo ""; \
		echo "===== GIT DIFF ====="; \
		git diff -- . ':(exclude)reports/*.csv'; \
		echo ""; \
		echo "===== RECENT COMMITS ====="; \
		git log --oneline -10; \
		echo ""; \
		echo "===== FILE INVENTORY ====="; \
		cat context_exports/.project_files.txt; \
		echo ""; \
		while IFS= read -r file; do \
			if [ -f "$$file" ] && { grep -Iq . "$$file" || [ ! -s "$$file" ]; }; then \
				echo ""; \
				echo "===== $$file ====="; \
				cat "$$file"; \
				echo ""; \
			fi; \
		done < context_exports/.project_files.txt; \
	} > context_exports/project_context_full.txt
	rm -f context_exports/.project_files.txt
	@echo "Project context created: context_exports/project_context_full.txt"

project-zip:
	# Archive tracked and non-ignored files without running pipelines.
	mkdir -p context_exports
	rm -f context_exports/alberta-electricity-price-predictor.zip
	git ls-files --cached --others --exclude-standard \
		| grep -v '^context_exports/' \
		| sort > context_exports/.project_files.txt
	test -s context_exports/.project_files.txt
	cat context_exports/.project_files.txt \
		| zip -q context_exports/alberta-electricity-price-predictor.zip -@
	rm -f context_exports/.project_files.txt
	@echo "Project archive created: context_exports/alberta-electricity-price-predictor.zip"

project-export:
	# Generate both the text context and ZIP archive.
	$(MAKE) project-context
	$(MAKE) project-zip
