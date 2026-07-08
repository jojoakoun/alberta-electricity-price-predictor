.PHONY: install test config-check pipeline data-quality features feature-quality training-data project-context baseline

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
