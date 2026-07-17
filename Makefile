.PHONY: install test compile-check config-check pipeline data-quality features feature-quality training-data audit baseline linear-regression ridge-regression lasso-regression lasso-tuning elastic-net-regression elastic-net-tuning regression-models select-best-regression-model final-regression-evaluation save-selected-regression-models spike-definition-analysis spike-regime-analysis classification-baseline logistic-regression logistic-tuning random-forest random-forest-tuning gradient-boosting gradient-boosting-tuning classification-models select-best-classification-model final-classification-evaluation save-selected-classification-models inference-check ml-pipeline application-pipeline pipelines

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
	$(MAKE) compile-check
	$(MAKE) inference-check
	$(MAKE) test

application-pipeline:
	# Synchronize PostgreSQL, generate predictions, and save results.
	python -m electricity_predictor.application_pipeline

pipelines:
	# Run the ML pipeline, then the application pipeline.
	$(MAKE) ml-pipeline
	$(MAKE) application-pipeline

audit:
	# Export complete source code, reports, artifacts, Git state, and verification evidence.
	mkdir -p context_exports
	{ \
		echo "===== AUDIT EXPORT GENERATED AT ====="; \
		date; \
		echo ""; \
		echo "===== GIT BRANCH ====="; \
		git branch --show-current; \
		echo ""; \
		echo "===== GIT LOG ====="; \
		git log --oneline -15; \
		echo ""; \
		echo "===== GIT STATUS ====="; \
		git status --short; \
		echo ""; \
		echo "===== BRANCH RELATIONSHIP WITH MAIN ====="; \
		echo "Main HEAD:"; \
		git log main --oneline -1 2>/dev/null || echo "main branch unavailable"; \
		echo ""; \
		echo "Commits on current branch not in main:"; \
		git log --oneline main..HEAD 2>/dev/null || true; \
		echo ""; \
		echo "Commits on main not in current branch:"; \
		git log --oneline HEAD..main 2>/dev/null || true; \
		echo ""; \
		echo "Merge base:"; \
		git merge-base HEAD main 2>/dev/null || echo "merge base unavailable"; \
		echo ""; \
		echo "===== PROJECT FILE INVENTORY ====="; \
		find . \
			-path "./.git" -prune -o \
			-path "./.venv" -prune -o \
			-path "./data" -prune -o \
			-path "./models" -prune -o \
			-path "./context_exports" -prune -o \
			-path "*/__pycache__" -prune -o \
			-path "./.pytest_cache" -prune -o \
			-path "./.ipynb_checkpoints" -prune -o \
			-name "*.pyc" -prune -o \
			-type f \( \
				-name "*.py" -o \
				-name "*.md" -o \
				-name "*.yaml" -o \
				-name "*.yml" -o \
				-name "*.toml" -o \
				-name "Makefile" -o \
				-name "requirements.txt" -o \
				-name ".gitignore" \
			\) -print | sort; \
		echo ""; \
		echo "===== COMPLETE SOURCE CODE, TESTS, DOCS, AND CONFIG ====="; \
		find . \
			-path "./.git" -prune -o \
			-path "./.venv" -prune -o \
			-path "./data" -prune -o \
			-path "./models" -prune -o \
			-path "./context_exports" -prune -o \
			-path "*/__pycache__" -prune -o \
			-path "./.pytest_cache" -prune -o \
			-path "./.ipynb_checkpoints" -prune -o \
			-name "*.pyc" -prune -o \
			-type f \( \
				-name "*.py" -o \
				-name "*.md" -o \
				-name "*.yaml" -o \
				-name "*.yml" -o \
				-name "*.toml" -o \
				-name "Makefile" -o \
				-name "requirements.txt" -o \
				-name ".gitignore" \
			\) -print | sort | while read file; do \
				echo ""; \
				echo "===== $$file ====="; \
				cat "$$file"; \
				echo ""; \
			done; \
		echo ""; \
		echo "===== REPORT INVENTORY ====="; \
		if [ -d reports ]; then \
			find reports -maxdepth 1 -type f -print | sort; \
		else \
			echo "Missing reports directory"; \
		fi; \
		echo ""; \
		echo "===== reports/model_results.csv ====="; \
		if [ -f reports/model_results.csv ]; then cat reports/model_results.csv; else echo "Missing reports/model_results.csv"; fi; \
		echo ""; \
		echo "===== reports/best_regression_model.csv ====="; \
		if [ -f reports/best_regression_model.csv ]; then cat reports/best_regression_model.csv; else echo "Missing reports/best_regression_model.csv"; fi; \
		echo ""; \
		echo "===== reports/final_regression_test_results.csv ====="; \
		if [ -f reports/final_regression_test_results.csv ]; then cat reports/final_regression_test_results.csv; else echo "Missing reports/final_regression_test_results.csv"; fi; \
		echo ""; \
		echo "===== reports/spike_definition_analysis.csv ====="; \
		if [ -f reports/spike_definition_analysis.csv ]; then cat reports/spike_definition_analysis.csv; else echo "Missing reports/spike_definition_analysis.csv"; fi; \
		echo ""; \
		echo "===== reports/spike_regime_analysis.csv ====="; \
		if [ -f reports/spike_regime_analysis.csv ]; then cat reports/spike_regime_analysis.csv; else echo "Missing reports/spike_regime_analysis.csv"; fi; \
		echo ""; \
		echo "===== reports/best_classification_model.csv ====="; \
		if [ -f reports/best_classification_model.csv ]; then cat reports/best_classification_model.csv; else echo "Missing reports/best_classification_model.csv"; fi; \
		echo ""; \
		echo "===== reports/final_classification_test_results.csv ====="; \
		if [ -f reports/final_classification_test_results.csv ]; then cat reports/final_classification_test_results.csv; else echo "Missing reports/final_classification_test_results.csv"; fi; \
		echo ""; \
		echo "===== reports/final_classification_confusion_matrices.csv ====="; \
		if [ -f reports/final_classification_confusion_matrices.csv ]; then cat reports/final_classification_confusion_matrices.csv; else echo "Missing reports/final_classification_confusion_matrices.csv"; fi; \
		echo ""; \
		echo "===== reports/final_classification_confidence_intervals.csv ====="; \
		if [ -f reports/final_classification_confidence_intervals.csv ]; then cat reports/final_classification_confidence_intervals.csv; else echo "Missing reports/final_classification_confidence_intervals.csv"; fi; \
		echo ""; \
		echo "===== REGRESSION MODEL METADATA ====="; \
		if [ -f models/regression/selected_regression_model_metadata.csv ]; then \
			cat models/regression/selected_regression_model_metadata.csv; \
		else \
			echo "Missing regression model metadata"; \
		fi; \
		echo ""; \
		echo "===== CLASSIFICATION MODEL METADATA ====="; \
		if [ -f models/classification/selected_classification_model_metadata.csv ]; then \
			cat models/classification/selected_classification_model_metadata.csv; \
		else \
			echo "Missing classification model metadata"; \
		fi; \
		echo ""; \
		echo "===== REGRESSION ARTIFACT INVENTORY ====="; \
		if [ -d models/regression ]; then \
			find models/regression -maxdepth 1 -type f -print | sort; \
		else \
			echo "Missing models/regression directory"; \
		fi; \
		echo ""; \
		echo "===== CLASSIFICATION ARTIFACT INVENTORY ====="; \
		if [ -d models/classification ]; then \
			find models/classification -maxdepth 1 -type f -print | sort; \
		else \
			echo "Missing models/classification directory"; \
		fi; \
		echo ""; \
		echo "===== PYTHON COMPILATION ====="; \
		if python -m compileall -q src; then \
			echo "Compilation passed"; \
		else \
			echo "Compilation failed"; \
		fi; \
		echo ""; \
		echo "===== COMPLETE TEST SUITE ====="; \
		pytest -q; \
	} > context_exports/project_context_full_audit.txt 2>&1
	@echo "Full audit context exported to context_exports/project_context_full_audit.txt"
