.PHONY: help install update lint format clean dev-setup test test-ci test-specific test-api test-cache run-app quality

# Python settings
PYTHON_VERSION := 3.10
VENV := .venv
PYTHON_PATH := $(shell pwd)/src
SCRIPTS_DIR := scripts
FORMAT_TEST_OUTPUT := $(SCRIPTS_DIR)/format_test_output.py

# Default test flags for visual output
TEST_FLAGS := --visual-output -p no:sugar --capture=no --no-header

# Test patterns
ALL_TESTS_PATTERN := tests/
API_TEST_PATTERN := tests/screen_run/ tests/rank_performance/ tests/strategy/ tests/screen_backtest/ tests/rank_update/ tests/rank_ranks/ tests/strategy_ranks/ 
CACHE_TEST_PATTERN := tests/cache_tests.py tests/test_cache_manager.py tests/screen_run/test_screen_run_consolidated.py::TestScreenRunCache

help: ## Show this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Setup and Build Targets ---

install: clean ## Install project dependencies using uv
	uv venv $(VENV)
	. $(VENV)/bin/activate && uv pip install -e ".[test]"

update: ## Update all dependencies to their latest compatible versions
	. $(VENV)/bin/activate && uv pip install --upgrade -e ".[test]"

dev-setup: clean install lint test ## Setup development environment

# --- Code Quality Targets ---

format: ## Format code using ruff
	. $(VENV)/bin/activate && ruff format src tests
	. $(VENV)/bin/activate && ruff check --fix src tests

lint: ## Run all linting checks
	. $(VENV)/bin/activate && ruff check src tests
	# Temporarily disabled: . $(VENV)/bin/activate && mypy src tests

quality: format lint ## Run all code quality checks (format and lint)

# --- Test Targets ---

test: ## Run all tests with visual detailed output
	@echo "🧪 Running tests with detailed visual output..."
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest $(TEST_FLAGS) $(ALL_TESTS_PATTERN)

test-simple: ## Run tests without visual formatting
	@echo "🧪 Running tests with simple output..."
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest -v $(ALL_TESTS_PATTERN)

test-ci: ## Run tests in CI mode (using cassettes only, no real API calls)
	@echo "🧪 Running tests in CI mode..."
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && VCR_ENABLED=true VCR_RECORD_MODE=none pytest $(TEST_FLAGS) $(ALL_TESTS_PATTERN)

test-specific: ## Run specific test module (usage: make test-specific TEST=path/to/test.py)
	@echo "🧪 Running specific test with visual output..."
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest $(TEST_FLAGS) $(TEST)

test-api: ## Run all API-related tests with visual output
	@echo "🧪 Running API tests with visual output..."
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest $(TEST_FLAGS) $(API_TEST_PATTERN)
	@$(PYTHON) $(FORMAT_TEST_OUTPUT) tests/screen_run/test_screen_run_consolidated.py "ScreenRun" run_screen get_universes

test-cache: ## Run all cache-related tests with visual output
	@echo "🧪 Running cache tests with visual output..."
	PYTHONPATH=$(PYTHON_PATH) . $(VENV)/bin/activate && pytest $(TEST_FLAGS) $(CACHE_TEST_PATTERN)
	@$(PYTHON) $(FORMAT_TEST_OUTPUT) tests/cache_tests.py "Cache" store_and_retrieve expiration delete_and_clear

# --- Application Targets ---

run-app: ## Run the Streamlit app
	. $(VENV)/bin/activate && streamlit run src/p123_streamlit/app.py

# --- Maintenance Targets ---

clean: ## Clean up environment and cache files
	rm -rf $(VENV)
	rm -f requirements.lock
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
