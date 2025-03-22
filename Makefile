.PHONY: help install test lint format clean dev-setup run-app

# Python settings
PYTHON_VERSION := 3.10
VENV := .venv
PYTHON_PATH := $(shell pwd)/src

help: ## Show this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z0-9_-]+:.*?## .*$$/ {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: clean ## Install project dependencies using uv
	uv venv $(VENV)
	. $(VENV)/bin/activate && uv pip install -e ".[test]"

update: ## Update all dependencies to their latest compatible versions
	. $(VENV)/bin/activate && uv pip install --upgrade -e ".[test]"

lint: ## Run all linting checks
	. $(VENV)/bin/activate && ruff check src tests
	. $(VENV)/bin/activate && mypy src tests

format: ## Format code using ruff
	. $(VENV)/bin/activate && ruff format src tests
	. $(VENV)/bin/activate && ruff check --fix src tests

test: ## Run all tests with proper Python path
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v

test-cov: ## Run tests with coverage report
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest --cov=p123api_client --cov-report=term-missing

test-specific: ## Run specific test module (usage: make test-specific TEST=path/to/test.py)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v $(TEST)

run-app: ## Run the Streamlit app
	. $(VENV)/bin/activate && streamlit run src/p123_streamlit/app.py

generate-diagrams: ## Generate model diagrams
	@echo "Generating model diagrams..."
	. $(VENV)/bin/activate && python docs/generate_model_diagrams.py
	@echo "Converting PlantUML files to PNG..."
	find docs/model_diagrams -name "*.puml" -exec plantuml {} \;
	@echo "Model diagrams have been generated in docs/model_diagrams/"

dev-setup: clean install lint test ## Setup development environment

clean: ## Clean up environment and cache files
	rm -rf $(VENV)
	rm -f requirements.lock
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
