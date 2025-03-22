# P123 API Client

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
P123_API_KEY=your_key_here
P123_API_SECRET=your_secret_here
```

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
    formula="close > 200"
)

# Display results
print(f"Found {len(df)} stocks:")
print(df.head())
```

For more examples, see the `examples/` directory.

## Usage

```python
from p123api_client import MarketClient

client = MarketClient()
data = client.get_market_data()
```

## Documentation

- [Project Guide](./docs/project_guide.md) - Detailed technical documentation
- [Product Overview](./docs/product_overview.md)
- [Architecture](./docs/architecture.md)
- [API Reference](./docs/api/README.md)
- [Contributing Guide](./CONTRIBUTING.md)

## Development

See the [Contributing Guide](./CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT License](./LICENSE)
