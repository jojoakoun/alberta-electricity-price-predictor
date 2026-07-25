SHELL := /bin/bash
.DEFAULT_GOAL := help
MAKEFLAGS += --no-print-directory

PYTHON ?= python
PIP ?= pip
PYTEST ?= pytest
NPM ?= npm
CURL ?= curl

SERVER_DIR := app/server
CLIENT_DIR := app/client
DOTENV := $(SERVER_DIR)/node_modules/.bin/dotenv

GENERATED_DIRECTORIES := \
	data/interim \
	data/processed \
	reports \
	models/candidates \
	models/production \
	dist/model-releases

PROTECTED_REGRESSION_TEST := \
	tests/modeling/regression/test_final_test_evaluation.py

PROTECTED_CLASSIFICATION_TEST := \
	tests/modeling/classification/test_final_test_evaluation.py


# ==============================================================================
# ==============================================================================
#
#                    WATTWISE — MAIN COMMANDS
#
#                   USE THIS SECTION NORMALLY
#
# ==============================================================================
# ==============================================================================

.PHONY: \
	help \
	install \
	reset \
	rebuild \
	activate \
	sync \
	start \
	restart \
	stop \
	check \
	status \
	verify

help:
	@echo ""
	@echo "WattWise — main commands"
	@echo "========================"
	@echo ""
	@echo "Installation:"
	@echo "  make install"
	@echo "      Install Python, API, and frontend dependencies."
	@echo ""
	@echo "Complete rebuild:"
	@echo "  make reset CONFIRM=YES"
	@echo "      Delete generated files and reset the local database."
	@echo "      Preserve the raw CSV source and PostgreSQL schema."
	@echo ""
	@echo "  make rebuild"
	@echo "      Rebuild data, reports, models, and the lifecycle candidate."
	@echo "      Does not run protected final-test evaluations."
	@echo "      Does not activate models automatically."
	@echo ""
	@echo "  make activate"
	@echo "      Manually activate the latest approved candidate."
	@echo ""
	@echo "Normal application update:"
	@echo "  make sync"
	@echo "      Refresh AESO/PostgreSQL data and generate predictions."
	@echo "      Does not retrain models."
	@echo ""
	@echo "Local application:"
	@echo "  make start"
	@echo "      Start the API and frontend."
	@echo ""
	@echo "  make restart"
	@echo "      Restart the API and frontend."
	@echo ""
	@echo "  make stop"
	@echo "      Stop the API and frontend."
	@echo ""
	@echo "  make check"
	@echo "      Check the health, now, and today endpoints."
	@echo ""
	@echo "Verification:"
	@echo "  make status"
	@echo "      Show Git, PostgreSQL, model, and generated-file status."
	@echo ""
	@echo "  make verify"
	@echo "      Run allowed tests, lint, and the production build."
	@echo ""


install:
	@echo ""
	@echo "=== Installing dependencies ==="
	$(PIP) install -r requirements.txt
	$(PIP) install -e .
	$(NPM) --prefix $(SERVER_DIR) install
	$(NPM) --prefix $(CLIENT_DIR) install
	@echo ""
	@echo "INSTALL=PASS"


reset:
	@if [ "$(CONFIRM)" != "YES" ]; then \
		echo ""; \
		echo "ERROR: this command deletes generated files"; \
		echo "and clears local application tables."; \
		echo ""; \
		echo "Correct command:"; \
		echo "  make reset CONFIRM=YES"; \
		echo ""; \
		exit 1; \
	fi
	@echo ""
	@echo "============================================================"
	@echo "WattWise — local reset"
	@echo "============================================================"
	$(MAKE) internal-stop
	$(MAKE) internal-clean-generated CONFIRM=YES
	$(MAKE) internal-reset-database CONFIRM=YES
	@echo ""
	@echo "RESET=PASS"
	@echo "The raw CSV source and PostgreSQL schema were preserved."
	@echo ""
	@echo "Next command:"
	@echo "  make rebuild"


rebuild:
	@echo ""
	@echo "============================================================"
	@echo "WattWise — complete reconstruction"
	@echo "============================================================"
	@echo ""
	@echo "This command will:"
	@echo "  1. check PostgreSQL;"
	@echo "  2. rebuild and synchronize data;"
	@echo "  3. rebuild features;"
	@echo "  4. train and select models;"
	@echo "  5. rebuild the decision policy;"
	@echo "  6. create and evaluate the operational candidate."
	@echo ""
	@echo "Protected final-test evaluations will not run."
	@echo "No model will be activated automatically."
	@echo ""
	$(MAKE) internal-database-check
	$(MAKE) internal-refresh-data
	$(MAKE) internal-data-quality
	$(MAKE) internal-sync-history
	$(MAKE) internal-features
	$(MAKE) internal-feature-quality
	$(MAKE) internal-training-data
	$(MAKE) internal-spike-definition
	$(MAKE) internal-spike-regime
	$(MAKE) internal-regression-models
	$(MAKE) internal-select-regression
	$(MAKE) internal-classification-models
	$(MAKE) internal-select-classification
	$(MAKE) internal-decision-analysis
	$(MAKE) internal-live-datasets
	$(MAKE) internal-live-validations
	$(MAKE) internal-lifecycle-run FORCE=1
	@echo ""
	@echo "REBUILD=PASS"
	@echo ""
	@echo "Next command after candidate review:"
	@echo "  make activate"


activate:
	@echo ""
	@echo "============================================================"
	@echo "WattWise — manual activation"
	@echo "============================================================"
	$(MAKE) internal-validate-candidate
	$(MAKE) internal-promote-models
	@test -f models/production/active_models.json || \
		(echo "ERROR: active_models.json was not created."; exit 1)
	@echo ""
	@echo "ACTIVATION=PASS"
	@echo ""
	@echo "Next command:"
	@echo "  make sync"


sync:
	@echo ""
	@echo "============================================================"
	@echo "WattWise — operational synchronization"
	@echo "============================================================"
	@test -f models/production/active_models.json || \
		(echo ""; \
		 echo "ERROR: no active model registry exists."; \
		 echo "Run first: make activate"; \
		 echo ""; \
		 exit 1)
	$(MAKE) internal-sync-and-predict
	@echo ""
	@echo "SYNC=PASS"
	@echo "The Now and Today pages can use the latest prediction run."


start:
	$(MAKE) internal-start


restart:
	$(MAKE) internal-stop
	$(MAKE) internal-start


stop:
	$(MAKE) internal-stop


check:
	$(MAKE) internal-app-check


status:
	@echo ""
	@echo "============================================================"
	@echo "WattWise — project status"
	@echo "============================================================"
	@echo ""
	@echo "===== Git ====="
	@git branch --show-current
	@git rev-parse --short HEAD
	@git status --short
	@echo ""
	@echo "===== PostgreSQL ====="
	@$(MAKE) internal-database-check
	@echo ""
	@echo "===== Active models ====="
	@if [ -f models/production/active_models.json ]; then \
		$(PYTHON) -m json.tool models/production/active_models.json; \
	else \
		echo "No active model registry exists."; \
	fi
	@echo ""
	@echo "===== Generated files ====="
	@for directory in $(GENERATED_DIRECTORIES); do \
		mkdir -p "$$directory"; \
		count=$$(find "$$directory" -type f | wc -l | tr -d ' '); \
		echo "$$directory: $$count file(s)"; \
	done
	@echo ""


verify:
	@echo ""
	@echo "============================================================"
	@echo "WattWise — automated verification"
	@echo "============================================================"
	$(MAKE) internal-config-check
	$(MAKE) internal-compile-check
	$(PYTEST) -q \
		--ignore=$(PROTECTED_REGRESSION_TEST) \
		--ignore=$(PROTECTED_CLASSIFICATION_TEST)
	NODE_ENV=test $(NPM) --prefix $(SERVER_DIR) test
	$(NPM) --prefix $(CLIENT_DIR) test
	$(NPM) --prefix $(CLIENT_DIR) run lint
	$(NPM) --prefix $(CLIENT_DIR) run build
	git diff --check
	@echo ""
	@echo "VERIFY=PASS"
	@echo "Protected final-test evaluations were not executed."


# ==============================================================================
# ==============================================================================
#
#               INTERNAL COMMANDS — DO NOT USE DIRECTLY
#
#   These targets exist only to support the main commands and compatibility.
#
# ==============================================================================
# ==============================================================================

.PHONY: \
	internal-config-check \
	internal-compile-check \
	internal-database-check \
	internal-clean-generated \
	internal-reset-database \
	internal-refresh-data \
	internal-data-quality \
	internal-sync-history \
	internal-features \
	internal-feature-quality \
	internal-training-data \
	internal-spike-definition \
	internal-spike-regime \
	internal-regression-models \
	internal-select-regression \
	internal-classification-models \
	internal-select-classification \
	internal-decision-window-analysis \
	internal-decision-regime-analysis \
	internal-decision-backtest \
	internal-decision-calibration \
	internal-decision-analysis \
	internal-live-datasets \
	internal-live-validations \
	internal-lifecycle-run \
	internal-validate-candidate \
	internal-promote-models \
	internal-sync-and-predict \
	internal-start \
	internal-stop \
	internal-app-check \
	sync-and-predict \
	worker-run \
	hourly-refresh \
	dev \
	app-check \
	database-check \
	db-clean \
	lifecycle-run \
	lifecycle-status \
	lifecycle-promote


internal-config-check:
	$(PYTHON) -c \
		"from electricity_predictor.config import load_configuration; print(load_configuration()['project']['name'])"


internal-compile-check:
	$(PYTHON) -m compileall -q src


internal-database-check:
	@test -x "$(DOTENV)" || \
		(echo "ERROR: dotenv executable not found: $(DOTENV)"; exit 1)
	$(DOTENV) \
		-e .env \
		-- sh -c \
		'psql "$$DATABASE_URL" -v ON_ERROR_STOP=1 -c \
		"SELECT current_database(), current_user, NOW() AS database_time;"'


internal-clean-generated:
	@if [ "$(CONFIRM)" != "YES" ]; then \
		echo "ERROR: confirmation required."; \
		exit 1; \
	fi
	@echo ""
	@echo "Deleting generated files..."
	@for directory in $(GENERATED_DIRECTORIES); do \
		mkdir -p "$$directory"; \
		find "$$directory" -mindepth 1 -maxdepth 1 -exec rm -rf {} +; \
	done
	@echo "GENERATED_FILES_CLEANED=PASS"


internal-reset-database:
	@if [ "$(CONFIRM)" != "YES" ]; then \
		echo "ERROR: confirmation required."; \
		exit 1; \
	fi
	@CONFIRM_DB_CLEANUP=YES \
		./scripts/cleanup_local_database.sh
	@echo "DATABASE_RESET=PASS"


internal-refresh-data:
	$(PYTHON) \
		src/electricity_predictor/data/pipeline.py


internal-data-quality:
	$(PYTHON) \
		src/electricity_predictor/data/data_quality.py


internal-sync-history:
	$(PYTHON) \
		-m electricity_predictor.worker.research_history_sync


internal-features:
	$(PYTHON) \
		src/electricity_predictor/features/feature_engineering.py


internal-feature-quality:
	$(PYTHON) \
		src/electricity_predictor/features/feature_quality.py


internal-training-data:
	$(PYTHON) \
		src/electricity_predictor/features/training_data.py


internal-spike-definition:
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/analyze_spike_definition.py


internal-spike-regime:
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/analyze_spike_regime.py


internal-regression-models:
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/run_regression_models.py


internal-select-regression:
	$(PYTHON) \
		src/electricity_predictor/modeling/regression/best_model_selection.py


internal-classification-models:
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/run_classification_models.py


internal-select-classification:
	$(PYTHON) \
		src/electricity_predictor/modeling/classification/best_model_selection.py


internal-decision-window-analysis:
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.analyze_decision_windows


internal-decision-regime-analysis:
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.analyze_decision_regimes


internal-decision-backtest:
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.backtest_decision_windows


internal-decision-calibration:
	$(PYTHON) \
		-m electricity_predictor.modeling.decision.calibrate_decision_policy


internal-decision-analysis:
	$(MAKE) internal-decision-window-analysis
	$(MAKE) internal-decision-regime-analysis
	$(MAKE) internal-decision-backtest
	$(MAKE) internal-decision-calibration


internal-live-datasets:
	$(PYTHON) \
		-m electricity_predictor.modeling.live_contract.live_model_datasets
	@test -f data/processed/live_modeling_dataset.csv
	@test -f data/processed/live_training_dataset.csv


internal-live-validations:
	@mkdir -p reports
	$(PYTHON) \
		-m electricity_predictor.modeling.live_contract.regression_validation \
		--output reports/live_regression_validation_results.csv
	$(PYTHON) \
		-m electricity_predictor.modeling.live_contract.classification_validation \
		--output reports/live_classification_validation_results.csv
	@test -f reports/live_regression_validation_results.csv
	@test -f reports/live_classification_validation_results.csv


internal-lifecycle-run:
	@force_flag=""; \
	if [ "$(FORCE)" = "1" ]; then \
		force_flag="--force"; \
	fi; \
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_retraining_scheduler \
		$$force_flag


internal-validate-candidate:
	$(PYTHON) -c '\
import json; \
from pathlib import Path; \
paths = sorted( \
    Path("models/candidates").glob("candidate-*/candidate_manifest.json"), \
    key=lambda path: path.stat().st_mtime \
); \
assert paths, "No lifecycle candidate exists. Run: make rebuild"; \
manifest = json.loads(paths[-1].read_text(encoding="utf-8")); \
comparison = manifest.get("comparison", {}); \
assert comparison.get("regression_gate_pass") is True, \
    "Regression gate did not pass"; \
assert comparison.get("classification_gate_pass") is True, \
    "Classification gate did not pass"; \
assert comparison.get("promotion_ready") is True, \
    "Candidate is not ready for activation"; \
print("candidate=" + str(manifest.get("model_version"))); \
print("candidate_validation=PASS")'


internal-promote-models:
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_promotion \
		--task regression \
		--task classification


internal-sync-and-predict:
	$(PYTHON) \
		-m electricity_predictor.worker.application_prediction_pipeline


internal-start:
	./scripts/dev-app.sh


internal-stop:
	@pkill -f "nodemon" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@echo "APPLICATION_STOPPED=PASS"


internal-app-check:
	@echo ""
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


# ------------------------------------------------------------------------------
# Compatibility aliases
# ------------------------------------------------------------------------------

sync-and-predict: sync

worker-run: sync

hourly-refresh: sync

dev: start

app-check: check

database-check: internal-database-check

db-clean:
	$(MAKE) internal-reset-database CONFIRM="$(CONFIRM)"

lifecycle-run:
	$(MAKE) internal-lifecycle-run FORCE="$(FORCE)"

lifecycle-status:
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_retraining_scheduler \
		--status

lifecycle-promote:
	@if [ "$(TASK)" != "regression" ] && \
		[ "$(TASK)" != "classification" ]; then \
		echo "ERROR: use TASK=regression or TASK=classification"; \
		exit 1; \
	fi
	$(PYTHON) \
		-m electricity_predictor.modeling.lifecycle.model_promotion \
		--task "$(TASK)"
