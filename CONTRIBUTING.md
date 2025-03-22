# Contributing to P123 API Client

Thank you for your interest in contributing to the P123 API Client! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/p123api-client.git
cd p123api-client
```

2. **Set up a virtual environment**

We recommend using `uv` for Python environment management:

```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
uv pip install -e ".[test]"
```

## Development Workflow

1. **Create a new branch for your feature**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

3. **Run tests**

```bash
pytest
```

Or use the Makefile:

```bash
make test
```

4. **Check code style**

```bash
make lint
```

5. **Submit a Pull Request**

Push your branch to your fork and submit a pull request against the main repository.

## Code Style

This project follows:

- [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python style
- [mypy](https://mypy.readthedocs.io/) for type checking
- [ruff](https://github.com/charliermarsh/ruff) for linting and formatting

Our automated tests include linting checks to ensure code quality.

## Commit Messages

Please use clear and descriptive commit messages with the following format:

```
<type>: <subject>

<body>
```

Types:
- feat: A new feature
- fix: A bug fix
- docs: Documentation changes
- style: Code style changes (formatting, etc.)
- refactor: Code refactoring without behavior changes
- test: Adding or updating tests
- chore: Routine tasks, maintenance, dependency updates

Example:
```
feat: Add support for screen backtest API

Implements the screen backtest API client with parameter validation
and response parsing. Includes tests and documentation.
```

## Pull Request Process

1. Update the README.md if your changes add new functionality
2. Add tests for new features
3. Ensure all tests pass
4. Update documentation as needed
5. Your PR will be reviewed and merged once approved

## License

By contributing to P123 API Client, you agree that your contributions will be licensed under the project's MIT License. 