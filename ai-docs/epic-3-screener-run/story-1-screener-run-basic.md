# Epic-3-screener-run: Implement P123 Screener Run API Integration
# Story-1: Implement Basic Screener Run Functionality

## Story

**As a** quantitative researcher
**I want** to execute P123 screeners programmatically
**so that** I can incorporate screening results into my analysis workflow

## Status

Completed

## Context

Part of Epic-3-screener-run which implements the P123 Screener Run API integration. This initial story focuses on establishing the core functionality to execute a screener run with basic parameters and handle the response. The P123 Screener Run API allows users to execute predefined screeners or create custom screening criteria to filter securities.

The API endpoint follows the standard P123 API pattern and requires proper authentication. Subsequent stories will build upon this foundation to add more advanced features and better integration with the Python ecosystem.

## Estimation

**Story Points**: 3

**Implementation Time Estimates**:
- **Human Development**: 3 days
- **AI-Assisted Development**: 0.05 days (~30 minutes)

## Tasks

1. - [x] Create Screener Run Tests
   1. - [x] Write test for basic screener run functionality
   2. - [x] Write test for error handling
   3. - [x] Write test for parameter validation
   4. - [x] Write test for response parsing

2. - [x] Implement Screener Run Client Methods
   1. - [x] Define screener run parameter types
   2. - [x] Implement basic run_screener method
   3. - [x] Add parameter validation
   4. - [x] Create response parsing logic

3. - [x] Implement Error Handling
   1. - [x] Add specific error types for screener run failures
   2. - [x] Implement validation error handling
   3. - [x] Add response error detection

4. - [x] Add Basic Documentation
   1. - [x] Document the run_screener method
   2. - [x] Create simple usage example
   3. - [x] Document parameter requirements

## API Signature

Based on the P123 API documentation, the screener run endpoint requires:

```python
def run_screener(
    self,
    screen: Union[int, str, Dict],  # Screen ID, name, or definition
    as_of_date: Optional[str] = None,  # Format: 'YYYY-MM-DD'
    end_date: Optional[str] = None,  # Format: 'YYYY-MM-DD'
    vendor: Optional[str] = None,
    pit_method: Optional[str] = None,
    precision: Optional[int] = None
) -> Dict:
    """
    Execute a P123 screener and return the results.
    
    Args:
        screen: Screen ID, name, or definition dict
        as_of_date: The as-of date for the screener run (default: today)
        end_date: Optional end date for historical screener runs
        vendor: Optional data vendor specification
        pit_method: Optional point-in-time method
        precision: Optional result precision
        
    Returns:
        Dict containing the screener results
    """
    pass
```

## Implementation Notes

- The screener run API has been implemented in the `ScreenRunAPI` class
- Both basic and advanced interfaces are available:
  - `run_simple_screen` for simple formula-based screens
  - `run_screen` for more complex screening with rules and ranking
- Results are converted to pandas DataFrames by default
- Comprehensive integration tests with VCR cassette recording
- Proper error handling for API-specific error formats
- Test output is saved in CSV format for easier inspection

## Challenges Overcome

- Handling API-specific format for formula and rule syntax
- Ensuring proper authentication and API parameter structure
- Managing API response with appropriate error handling
- Setting up VCR cassette recording with masked sensitive information

## Next Steps

Further stories in this epic will build on this foundation to add more advanced features such as:
- Custom universe definitions
- Complex multi-factor ranking
- Historical screening across date ranges
- Additional output format options

## Chat Command Log

- User: @ai-docs In the AI docs, add a new epic to implement the screen run API call here. Review the docs folder for the signature for the p123 screener run API call. follow @rules for document creation and formatting
- AI: Creating the epic and first story documents for the screener run API implementation 
- User: @test Let's implement the tests for this API endpoint
- AI: Implemented integration tests in tests/integration/test_screen_run_integration.py
- User: @vcr Let's use VCR.py for the tests to avoid making API calls during testing
- AI: Added VCR.py integration and masked sensitive data in cassettes
- User: @cassettes Let's organize the cassettes properly in the test directory structure
- AI: Moved the integration tests to tests/screen_run/test_screen_run_integration.py with cassettes in tests/screen_run/cassettes
- User: @test_output Let's save the test output to CSV files
- AI: Added CSV output saving to tests/screen_run/test_output directory 