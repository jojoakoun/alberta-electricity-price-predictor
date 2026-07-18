.PHONY: install test app-dev app-stop compile-check config-check pipeline data-quality features feature-quality training-data baseline linear-regression ridge-regression lasso-regression lasso-tuning elastic-net-regression elastic-net-tuning regression-models select-best-regression-model final-regression-evaluation save-selected-regression-models spike-definition-analysis spike-regime-analysis classification-baseline logistic-regression logistic-tuning random-forest random-forest-tuning gradient-boosting gradient-boosting-tuning classification-models select-best-classification-model final-classification-evaluation save-selected-classification-models inference-check ml-pipeline application-pipeline pipelines project-context project-zip project-export production-pipeline decision-window-analysis decision-regime-analysis decision-policy-backtest decision-policy-calibration predicted-decision-stress-test decision-analysis

install:
	# Install dependencies and register the local package.
	pip install -r requirements.txt
	pip install -e .

test:
	# Run the project test suite.
	pytest

compile-check:
	# Compile project source files to detect syntax and import problems.
	python -m compileall -q src

config-check:
	# Check that the configuration can be loaded.
	python -c "from electricity_predictor.config import load_configuration; print(load_configuration()['project']['name'])"

pipeline:
	# Build the current historical dataset from CSV and AESO API data.
	python src/electricity_predictor/data/pipeline.py

data-quality:
	# Inspect the current historical dataset before feature engineering.
	python src/electricity_predictor/data/data_quality.py

features:
	# Build the first modeling dataset for machine learning.
	python src/electricity_predictor/features/feature_engineering.py

feature-quality:
	# Inspect missing values created by feature engineering.
	python src/electricity_predictor/features/feature_quality.py


training-data:
	# Build the model-ready training dataset.
	python src/electricity_predictor/features/training_data.py


baseline:
	# Run the naive regression baseline.
	python src/electricity_predictor/modeling/regression/baseline/naive_baseline.py

linear-regression:
	# Train and evaluate the Linear Regression model on the validation split.
	python src/electricity_predictor/modeling/regression/linear/linear_regression.py

ridge-regression:
	# Train and evaluate the Ridge Regression model on the validation split.
	python src/electricity_predictor/modeling/regression/ridge/ridge_regression.py


lasso-regression:
	# Train and evaluate the Lasso Regression model on the validation split.
	python src/electricity_predictor/modeling/regression/lasso/lasso_regression.py

lasso-tuning:
	# Tune Lasso Regression with TimeSeriesSplit on the chronological train split.
	python src/electricity_predictor/modeling/regression/lasso/lasso_tuning.py

elastic-net-regression:
	# Train and evaluate the Elastic Net Regression model on the validation split.
	python src/electricity_predictor/modeling/regression/elastic_net/elastic_net_regression.py

elastic-net-tuning:
	# Tune Elastic Net Regression with TimeSeriesSplit on the chronological train split.
	python src/electricity_predictor/modeling/regression/elastic_net/elastic_net_tuning.py

regression-models:
	# Train and evaluate all current regression models.
	python src/electricity_predictor/modeling/regression/run_regression_models.py

select-best-regression-model:
	# Select the best validation regression model from the model results summary.
	python src/electricity_predictor/modeling/regression/best_model_selection.py

final-regression-evaluation:
	# Evaluate selected regression models on the protected test split.
	python src/electricity_predictor/modeling/regression/final_test_evaluation.py

save-selected-regression-models:
	# Train and save the selected regression models as local joblib artifacts.
	python src/electricity_predictor/modeling/regression/save_selected_models.py


spike-definition-analysis:
	# Compare train-derived spike definitions across fixed chronological splits.
	python src/electricity_predictor/modeling/classification/analyze_spike_definition.py

spike-regime-analysis:
	# Analyze yearly spike rates and price regimes using the frozen train threshold.
	python src/electricity_predictor/modeling/classification/analyze_spike_regime.py

classification-baseline:
	# Evaluate the naive spike baseline on the chronological validation split.
	python src/electricity_predictor/modeling/classification/baseline/naive_spike_baseline.py

logistic-regression:
	# Train and evaluate base Logistic Regression for all forecast horizons.
	python src/electricity_predictor/modeling/classification/logistic/logistic_regression.py

logistic-tuning:
	# Tune Logistic Regression with TimeSeriesSplit for all forecast horizons.
	python src/electricity_predictor/modeling/classification/logistic/logistic_tuning.py


random-forest:
	# Train and evaluate Random Forest for all forecast horizons.
	python src/electricity_predictor/modeling/classification/random_forest/random_forest_classifier.py

random-forest-tuning:
	# Tune Random Forest with TimeSeriesSplit for all forecast horizons.
	python src/electricity_predictor/modeling/classification/random_forest/random_forest_tuning.py


gradient-boosting:
	# Train and evaluate Gradient Boosting for all forecast horizons.
	python src/electricity_predictor/modeling/classification/gradient_boosting/gradient_boosting_classifier.py

gradient-boosting-tuning:
	# Tune Gradient Boosting with TimeSeriesSplit for all forecast horizons.
	python src/electricity_predictor/modeling/classification/gradient_boosting/gradient_boosting_tuning.py

classification-models:
	# Run the current multi-horizon classification comparison workflow.
	python src/electricity_predictor/modeling/classification/run_classification_models.py

select-best-classification-model:
	# Select the strongest validation classifier for each horizon.
	python src/electricity_predictor/modeling/classification/best_model_selection.py

final-classification-evaluation:
	# Evaluate selected classifiers on the protected chronological test split.
	python src/electricity_predictor/modeling/classification/final_test_evaluation.py

save-selected-classification-models:
	# Train and save selected classification models as joblib artifacts.
	python src/electricity_predictor/modeling/classification/save_selected_models.py

inference-check:
	# Run serving and inference tests.
	pytest -q tests/serving

ml-pipeline:
	# Rebuild ML data, reports, selected artifacts, and run verification.
	$(MAKE) config-check
	$(MAKE) pipeline
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
	$(MAKE) test

decision-window-analysis:
	# Compare 72h, 168h, 336h, and 720h rolling windows and write detailed and summary stability reports.
	python -m electricity_predictor.modeling.decision.analyze_decision_windows

decision-regime-analysis:
	# Compare decision-window stability across the 2020-2023 and 2024-2026 market regimes.
	python -m electricity_predictor.modeling.decision.analyze_decision_regimes

decision-policy-backtest:
	# Backtest the 336h and 720h decision windows and summarize recommendation-label stability.
	python -m electricity_predictor.modeling.decision.backtest_decision_windows

decision-policy-calibration:
	# Evaluate candidate recommendation quantiles and avoid-threshold multipliers on calibration and holdout periods.
	python -m electricity_predictor.modeling.decision.calibrate_decision_policy

predicted-decision-stress-test:
	# Compare predicted recommendations with labels derived from actual future prices across all forecast horizons.
	python -m electricity_predictor.modeling.decision.stress_test_predicted_decisions

decision-analysis:
	# Regenerate all reproducible decision-policy reports in dependency order.
	$(MAKE) decision-window-analysis
	$(MAKE) decision-regime-analysis
	$(MAKE) decision-policy-backtest
	$(MAKE) decision-policy-calibration
	$(MAKE) predicted-decision-stress-test

application-pipeline:
	# Synchronize PostgreSQL, generate predictions, and save results.
	python -m electricity_predictor.application_pipeline


production-pipeline:
	# Refresh AESO data, synchronize PostgreSQL, and generate predictions.
	$(MAKE) pipeline
	$(MAKE) application-pipeline

pipelines:
	# Run the ML pipeline, then the application pipeline.
	$(MAKE) ml-pipeline
	$(MAKE) application-pipeline

project-context:
	# Export all tracked and non-ignored text files without running pipelines.
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
	# Archive all tracked and non-ignored files without running pipelines.
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
	# Generate the text context and ZIP archive without running pipelines.
	$(MAKE) project-context
	$(MAKE) project-zip

app-dev:
	./scripts/dev-app.sh

app-stop:
	pkill -f nodemon || true
	pkill -f vite || true
