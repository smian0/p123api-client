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
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

# --- Test Targets ---

test: ## Run all tests with proper Python path
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v

test-vcr: ## Run all tests with VCR enabled (once mode - uses existing cassettes)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=once pytest -v

test-vcr-new: ## Run all tests with VCR in record mode (records new cassettes)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=new_episodes pytest -v

test-vcr-all: ## Run all tests with VCR in all mode (records all interactions)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=all pytest -v

test-ci: ## Run tests in CI mode (using existing cassettes only, no real API calls)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=none pytest -v

test-cov: ## Run tests with coverage report
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest --cov=p123api_client --cov-report=term-missing

test-specific: ## Run specific test module (usage: make test-specific TEST=path/to/test.py)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v $(TEST)

test-specific-vcr: ## Run specific test with VCR enabled (usage: make test-specific-vcr TEST=path/to/test.py)
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=once pytest -v $(TEST)

# --- Cache Test Targets ---

test-cache: ## Run all cache-related tests
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v tests/cache_tests.py tests/test_cache_manager.py tests/screen_run/test_screen_run_cache.py

test-cache-storage: ## Run tests for cache storage implementations only
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v tests/cache_tests.py

test-cache-manager: ## Run CacheManager tests only
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v tests/test_cache_manager.py

test-cache-integration: ## Run cache integration tests only
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v tests/screen_run/test_screen_run_cache.py

# --- API Test Targets ---

test-api: ## Run all API-related tests
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v tests/screen_run/ tests/rank_performance/ tests/strategy/ tests/screen_backtest/ tests/rank_update/ tests/rank_ranks/ tests/strategy_ranks/

test-api-vcr: ## Run all API-related tests with VCR enabled
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=once pytest -v tests/screen_run/ tests/rank_performance/ tests/strategy/ tests/screen_backtest/ tests/rank_update/ tests/rank_ranks/ tests/strategy_ranks/

# --- Application Targets ---

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
