# VCR Testing Workflow

This document explains how VCR (Virtual Cassette Recorder) is used for testing in the P123 API Client project and outlines the workflow for developers.

## What is VCR?

VCR.py records HTTP interactions during tests and replays them during future test runs. This provides several benefits:

- **Faster tests**: No actual API calls are made during test replay
- **Consistent results**: Tests run against the same data each time
- **No API credentials needed**: After recording, tests can run without real credentials
- **No API consumption**: Avoid using up API quota during testing

## Environment Variables

The VCR configuration can be controlled with these environment variables:

- `VCR_ENABLED`: Set to "false" to disable VCR completely (default: "true")
- `VCR_RECORD_MODE`: Set to control recording mode (default: "once")
  - `once`: Record once, then replay
  - `none`: Never record, replay only
  - `new_episodes`: Record new interactions, replay existing ones
  - `all`: Always record

## Workflow for Developers

### Running Tests Locally

1. **First-time setup**: Run tests with recording enabled to create cassettes:
   ```bash
   VCR_RECORD_MODE=all pytest tests/
   ```

2. **Normal development**: Run tests with cassettes (no API calls):
   ```bash
   pytest tests/
   ```

3. **Updating cassettes**: When API responses change or you add new tests:
   ```bash
   VCR_RECORD_MODE=all pytest tests/
   ```

4. **Force real API calls**: To test against current real data:
   ```bash
   VCR_ENABLED=false pytest tests/
   ```

### Adding New Tests

1. Create your test and run it with recording mode:
   ```bash
   VCR_RECORD_MODE=all pytest tests/your_new_test.py
   ```

2. Verify the cassette was created in `tests/your_module/cassettes/`

3. Commit both your test and the cassette files

### CI Workflow

In CI environments:
- Tests **always** run with `VCR_RECORD_MODE=none`
- No real API calls are ever made
- If tests fail because cassettes are missing or outdated, you'll need to update them locally and commit

## Using auto_vcr Fixture

Instead of manually adding VCR decorators to each test, you can use the `auto_vcr` fixture:

```python
def test_something(auto_vcr):
    # This test will automatically use VCR with environment-based configuration
    api = ScreenRunAPI()
    result = api.some_method()
    assert result is not None
```

## Sensitive Data

All cassettes automatically have sensitive data masked:
- API keys
- Authentication tokens
- Passwords or secrets

Cassettes are safe to commit to the repository.

## Troubleshooting

- **Test fails in CI but passes locally**: Update cassettes with `VCR_RECORD_MODE=all`
- **Need to match on different request properties**: Edit `vcr_config` fixture in `conftest.py`
- **Sensitive data appearing in cassettes**: Add patterns to `SENSITIVE_PATTERNS` in `conftest.py` 