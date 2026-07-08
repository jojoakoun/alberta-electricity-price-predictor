.PHONY: install test config-check pipeline data-quality features feature-quality training-data project-context baseline linear-regression ridge-regression lasso-regression lasso-tuning elastic-net-regression elastic-net-tuning regression-models full-pipeline

install:
	# Install dependencies and register the local package.
	pip install -r requirements.txt
	pip install -e .

test:
	# Run the project test suite.
	pytest

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


project-context:
	# Export important project files into one text file for context sharing.
	mkdir -p context_exports
	find . \
		-path "./.git" -prune -o \
		-path "./.venv" -prune -o \
		-path "./data" -prune -o \
		-path "./context_exports" -prune -o \
		-path "./__pycache__" -prune -o \
		-path "./.pytest_cache" -prune -o \
		-path "./.ipynb_checkpoints" -prune -o \
		-name "*.csv" -prune -o \
		-name "*.pkl" -prune -o \
		-name "*.joblib" -prune -o \
		-name "*.pyc" -prune -o \
		-type f \( \
			-name "*.py" -o \
			-name "*.md" -o \
			-name "*.yaml" -o \
			-name "*.yml" -o \
			-name "*.toml" -o \
			-name "Makefile" -o \
			-name "requirements.txt" \
		\) -print | sort | while read file; do \
			echo "===== $$file ====="; \
			sed -n '1,260p' "$$file"; \
			echo ""; \
		done > context_exports/project_context.txt
	@echo "Project context exported to context_exports/project_context.txt"

baseline:
	# Run the naive regression baseline.
	python src/electricity_predictor/modeling/regression/baseline.py

linear-regression:
	# Train and evaluate the Linear Regression model on the validation split.
	python src/electricity_predictor/modeling/regression/linear_regression.py

ridge-regression:
	# Train and evaluate the Ridge Regression model on the validation split.
	python src/electricity_predictor/modeling/regression/ridge_regression.py


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

full-pipeline:
	# Run the complete current workflow from data refresh to model results and tests.
	$(MAKE) pipeline
	$(MAKE) data-quality
	$(MAKE) features
	$(MAKE) feature-quality
	$(MAKE) training-data
	$(MAKE) regression-models
	$(MAKE) test

