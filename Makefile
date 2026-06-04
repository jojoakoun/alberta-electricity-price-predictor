.PHONY: install test config-check

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