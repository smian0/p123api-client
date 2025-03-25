# P123 API Client

[![codecov](https://img.shields.io/badge/coverage-55%25-yellow)](https://github.com/smian0/p123api-client/actions/workflows/tests.yml)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/smian0/p123api-client/tests.yml?branch=main&label=tests)](https://github.com/smian0/p123api-client/actions/workflows/tests.yml)

A Python client library for interacting with the Portfolio123 (P123) API.

## Features

- **Authentication:** Secure API authentication and session management
- **Data Retrieval:** Fetch market data and stock information
- **Screening:** Run stock screens with multiple criteria
- **Backtesting:** Test strategies against historical data
- **Ranking:** Use built-in or custom ranking systems
- **Pandas Integration:** Convert results to pandas DataFrames

## Quick Start

```bash
pip install p123api-client
```

Create a `.env` file with your API credentials:
```
P123_API_ID=your_id_here
P123_API_KEY=your_key_here
P123_CACHE_PATH=/path/to/cache.db  # Optional: Custom cache path
```

### Basic Usage

```python
import os
from p123api_client import ScreenRunAPI

# Initialize the API client
api = ScreenRunAPI(
    api_id=os.environ["P123_API_ID"],
    api_key=os.environ["P123_API_KEY"]
)

# Run a simple screen
df = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200"
)

# Display results
print(f"Found {len(df)} stocks:")
print(df.head())
```

### With Caching (Recommended)

```python
import os
from p123api_client import CachedScreenRunAPI

# Initialize the API client with caching
api = CachedScreenRunAPI(
    api_id=os.environ["P123_API_ID"],
    api_key=os.environ["P123_API_KEY"]
    # Caching is enabled by default with sensible settings
)

# First call will hit the API
df1 = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200"
)

# Second call with the same parameters will use the cache
df2 = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200"
)

# Force a fresh API call by bypassing the cache
df3 = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200",
    bypass_cache=True
)
```

#### Environment Variables

The API client automatically reads credentials from environment variables:

```
P123_API_ID=your_api_id
P123_API_KEY=your_api_key
```

You can set these in your environment or use a `.env` file with the `python-dotenv` package.

For more examples, see the `examples/` directory.

## Caching Support

The library provides cached versions of API clients that automatically handle caching with sensible defaults:

- `CachedScreenRunAPI`: Cached version of the screen run API
- `CachedRankPerformanceAPI`: Cached version of the rank performance API

These classes require no additional configuration and will automatically cache API responses to improve performance:

```python
from p123api_client import CachedScreenRunAPI, CachedRankPerformanceAPI

# Initialize API clients with caching enabled
screen_api = CachedScreenRunAPI()
rank_api = CachedRankPerformanceAPI()

# All API calls are automatically cached
```

Caching is implemented using SQLite for persistence and automatically handles:

- Cache invalidation when P123 updates its data (default: 3 AM Eastern)
- Cache size management
- Statistics tracking
- Timezone handling
```

### Environment Variables

You can configure the API client through environment variables:

```
P123_API_ID=your_api_id              # Your Portfolio123 API ID
P123_API_KEY=your_api_key            # Your Portfolio123 API key
P123_CACHE_PATH=/path/to/cache.db    # Custom cache database path (default: ~/.p123cache/cache.db)
```

No additional configuration is needed for most use cases.

## Usage

### Screen Run API

```python
from p123api_client import CachedScreenRunAPI

# Initialize the API client
api = CachedScreenRunAPI()

# Run a simple screen
df = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200"
)

print(f"Found {len(df)} stocks:")
print(df.head())
```

### Rank Performance API

```python
from datetime import date
from p123api_client import CachedRankPerformanceAPI
from p123api_client.models.enums import RankType, Scope
from p123api_client.rank_performance.schemas import Factor, RankingDefinition, RankPerformanceAPIRequest

# Initialize the API client
api = CachedRankPerformanceAPI()

# Create a test factor
factor = Factor(
    rank_type=RankType.HIGHER,
    formula="Close(0)",
    description="Yesterday's Close Price"
)

# Create a ranking definition
ranking_def = RankingDefinition(
    factors=[factor],
    scope=Scope.UNIVERSE,
    description="Test ranking system"
)

# Create a rank performance request
request = RankPerformanceAPIRequest(
    ranking_definition=ranking_def,
    start_dt=date(2022, 1, 1),
    end_dt=date(2022, 12, 31),
    universe="SP500"
)

# Run rank performance analysis
df = api.run_rank_performance([request])

# Display results
print(df.head())
```

## Documentation

### API Classes

The library provides the following API classes:

#### Base API Classes
- `ScreenRunAPI`: Base class for running stock screens
- `RankPerformanceAPI`: Base class for rank performance analysis

#### Cached API Classes (Recommended)
- `CachedScreenRunAPI`: Screen run API with automatic caching
- `CachedRankPerformanceAPI`: Rank performance API with automatic caching

### Caching System

The caching system has been simplified to use SQLite for storage with the following components:

1. **SQLite Storage** (`cache/storage.py`): Efficient SQLite-based storage with performance optimizations
2. **Cache Manager** (`cache/manager.py`): Handles cache operations and statistics
3. **Decorator-based Caching** (`cache/decorators.py`): Adds caching to API methods

For more detailed documentation, see:
- [Project Guide](./docs/project_guide.md)
- [Product Overview](./docs/product_overview.md)
- [Architecture](./docs/architecture.md)
- [API Reference](./docs/api/README.md)
- [Contributing Guide](./CONTRIBUTING.md)

## Development

See the [Contributing Guide](./CONTRIBUTING.md) for development setup and guidelines.

## Testing

The project includes both unit tests and integration tests. Tests have been consolidated into comprehensive test suites for better coverage and reduced duplication.

### Running Tests

To run all tests:
```bash
python -m pytest
```

### Coverage Reports

For a basic test coverage report:
```bash
python -m pytest --cov=p123api_client
```

For a more detailed HTML coverage report:
```bash
python -m pytest --cov=p123api_client --cov-report=html
```
This creates a directory `htmlcov` with an interactive HTML report. Open `htmlcov/index.html` in your browser to explore the coverage results.

For XML coverage report (used by CI tools):
```bash
python -m pytest --cov=p123api_client --cov-report=xml
```

To run a specific test module:
```bash
python -m pytest tests/screen_run/test_screen_run_consolidated.py
```

### VCR Testing

The project uses VCR.py for testing API calls without making real network requests. VCR records API interactions and replays them for future test runs, which:

- Makes tests faster and more reliable
- Allows testing without API credentials
- Prevents unnecessary API calls during testing 
- Enables testing against fixed responses

For detailed instructions on working with VCR, see the [VCR Workflow Guide](./docs/vcr_workflow.md).

#### Environment-Controlled VCR

You can control VCR behavior globally using environment variables:

```bash
# Disable VCR (use real API calls)
export VCR_ENABLED=false

# Or set specific recording mode
export VCR_RECORD_MODE=once   # Record once then replay (default)
export VCR_RECORD_MODE=none   # Never record, only replay
export VCR_RECORD_MODE=all    # Always record
export VCR_RECORD_MODE=new_episodes  # Record new interactions, replay existing
```

This is especially useful for CI environments where you might want to:
- Use existing cassettes only (`VCR_RECORD_MODE=none`) 
- Use real API calls to test against current data (`VCR_ENABLED=false`)

#### Using Auto-VCR

The project provides an `auto_vcr` fixture that automatically configures VCR based on environment variables:

```python
def test_my_api_call(auto_vcr):
    # Test code here - VCR will be configured based on environment variables
    api = ScreenRunAPI()
    result = api.run_screen(...)
    assert result is not None
```

#### Manual VCR Decorator

For more control, you can still use the manual VCR decorator:

```python
import pytest

@pytest.mark.vcr()
def test_my_api_call():
    # Test with VCR recording/playback
    pass
```

### Key Test Suites

- **Screen Run Tests**: `tests/screen_run/test_screen_run_consolidated.py`
  - Tests basic API functionality, parameter validation, and caching
  - Includes visual verification of cache database contents

- **Rank Performance Tests**: `tests/rank_performance/test_rank_performance_api.py`
  - Tests rank performance API with single and multiple factors
  - Tests loading ranking definitions from XML files

- **Cached Rank Performance Tests**: `tests/rank_performance/test_cached_rank_performance_api.py`
  - Tests caching functionality for rank performance API
  - Verifies cache persistence across API instances

## Cache System

The caching system has been simplified to use SQLite for storage with sensible defaults. The system includes:

1. **SQLite Storage** (`cache/storage.py`): Optimized SQLite-based storage with performance enhancements including:
   - WAL mode for better concurrency
   - Optimized indexes for faster lookups
   - Efficient datetime handling for expiration checks
   - Improved statistics tracking

2. **Cache Manager** (`cache/manager.py`): Manages cache operations with streamlined methods for:
   - Getting and putting cache entries
   - Handling cache statistics
   - Managing cache size

3. **Decorator-based Caching** (`cache/decorators.py`): Adds caching to API methods via decorators

The cache system supports:
- Thread-safe database connections
- JSON serialization for all data types
- Automatic expiration handling based on P123 data refresh times
- DataFrame storage and retrieval
- Endpoint-based cache invalidation
- Automatic cache size management

### Using Caching (Recommended)

The simplest way to use caching is to use the cached API classes:

```python
# Instead of this (no caching):
from p123api_client import ScreenRunAPI
api = ScreenRunAPI()

# Do this (with caching):
from p123api_client import CachedScreenRunAPI
api = CachedScreenRunAPI()
```

That's it! Now all your API calls will be automatically cached, providing significant performance improvements for repeated calls. The API credentials will be read from the environment variables `P123_API_ID` and `P123_API_KEY`.

#### Using the API

```python
# Initialize the API with caching (credentials from environment variables)
from p123api_client import CachedScreenRunAPI
api = CachedScreenRunAPI()

# Use the API as normal - caching is handled automatically
result = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200"
)

# To bypass the cache for a specific call
fresh_result = api.run_simple_screen(
    universe="SP500",
    formula="PRICE > 200",
    bypass_cache=True  # Force a fresh API call
)
```

#### Rank Performance API Example

```python
from datetime import date
from p123api_client import CachedRankPerformanceAPI
from p123api_client.models.enums import RankType, Scope, PitMethod
from p123api_client.rank_performance.schemas import Factor, RankingDefinition, RankPerformanceAPIRequest

# Initialize the API with caching
api = CachedRankPerformanceAPI()

# Create a ranking definition with multiple factors
factors = [
    Factor(rank_type=RankType.HIGHER, formula="ROE", description="Return on Equity"),
    Factor(rank_type=RankType.LOWER, formula="PE", description="Price to Earnings")
]

ranking_def = RankingDefinition(
    factors=factors,
    scope=Scope.UNIVERSE,
    description="Value Ranking System"
)

# Create a request with additional parameters
request = RankPerformanceAPIRequest(
    ranking_definition=ranking_def,
    start_dt=date(2022, 1, 1),
    end_dt=date(2022, 12, 31),
    universe="SP500",
    pit_method=PitMethod.PRELIM,
    num_buckets=5
)

# Run rank performance analysis
df = api.run_rank_performance([request])

# Display results
print(df)
```

#### Advanced: Using the Decorator Directly

For advanced use cases, you can also use the `cached_api_call` decorator directly on your own API methods:

```python
from p123api_client.cache import CacheManager, CacheConfig, cached_api_call
from p123api_client import ScreenRunAPI

class MyCustomAPI(ScreenRunAPI):
    def __init__(self, api_id=None, api_key=None):
        super().__init__(api_id=api_id, api_key=api_key)
        # Create a cache manager for this instance
        self.cache_manager = CacheManager(CacheConfig())
    
    # Apply the decorator to your method
    @cached_api_call(endpoint="my_custom_endpoint")
    def my_custom_method(self, param1, param2, bypass_cache=False):
        # Your API method implementation
        # The decorator will handle caching automatically
        return self.make_request("some_endpoint", {"param1": param1, "param2": param2})
```

### APIs with Caching Support

The following APIs support caching:

| API | Base Class | Cached Class | Description |
|-----|------------|--------------|-------------|
| Screen Run | `ScreenRunAPI` | `CachedScreenRunAPI` | Run stock screens with optional ranking |
| Rank Performance | `RankPerformanceAPI` | `CachedRankPerformanceAPI` | Analyze performance of ranking systems |
```

**Note:** This approach is only recommended for advanced users who need to create custom API methods with caching. For most use cases, simply using the `CachedScreenRunAPI` and `CachedRankPerformanceAPI` classes is sufficient.

### Cache Configuration

The caching system uses sensible defaults that work out of the box:

- Cache is stored at `~/.p123cache/cache.db` in the user's home directory
- Maximum cache size is 100MB with automatic cleanup
- Cache statistics are enabled
- Data refresh time is set to 3 AM Eastern (when P123 updates its data)

For most users, **no configuration is needed** - just use the cached API versions (e.g., `CachedScreenRunAPI`) and everything works automatically.

If you need to customize the cache location, you can use the `P123_CACHE_PATH` environment variable:

```bash
# Set a custom cache location
export P123_CACHE_PATH=/path/to/custom/cache.db
```

### APIs with Caching Support

The following APIs support caching by default when using the Cached version:

| Regular API | Cached API with Caching |
|-------------|------------------------|
| `ScreenRunAPI` | `CachedScreenRunAPI` |
| `RankPerformanceAPI` | `CachedRankPerformanceAPI` |

### Disabling Caching for Specific Calls

All API methods support caching by default. If you need to bypass the cache for a specific call, use the `bypass_cache` parameter:

```python
# Normal call (uses cache)
result = api.run_simple_screen("SP500", "PRICE > 200")

# Bypass cache for this specific call
fresh_result = api.run_simple_screen("SP500", "PRICE > 200", bypass_cache=True)
```

The cache system includes automatic size management, which will remove the oldest entries when the cache exceeds the configured size limit (default: 100MB).

## License

[MIT License](./LICENSE)

#### CI Configuration

In CI environments, you can control VCR behavior globally using environment variables:

```bash
# Example GitHub Actions workflow configuration
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      # Run tests with real API calls against current data
      - name: Run integration tests with real API
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        env:
          P123_API_ID: ${{ secrets.P123_API_ID }}
          P123_API_KEY: ${{ secrets.P123_API_KEY }}
          VCR_ENABLED: false  # Disable VCR to use real API calls
        run: pytest tests/

      # Run tests using only existing cassettes (no recording)
      - name: Run tests with existing cassettes
        if: github.event_name == 'pull_request'
        env:
          VCR_RECORD_MODE: none  # Only use existing cassettes
        run: pytest tests/
```

This approach allows you to:
- Use real API calls to test against current data (on main branch)
- Use existing cassettes for pull requests (to avoid API calls and API credentials)
