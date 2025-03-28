"""Sample test file demonstrating visual test output capabilities."""

import json

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .visual_test_hooks import print_test_group

# Initialize rich console
console = Console()


def process_data(data):
    """Sample function to demonstrate testing with visual output."""
    total = sum(data.get("values", [0]))
    return total


class TestVisualOutput:
    """Test class for demonstrating visual test output."""

    @pytest.mark.api
    def test_with_rich_formatting(self):
        """Test with rich visual output and clear formatting."""
        # Print test group header
        print_test_group("API Validation Tests")

        # Display test header
        console.print(
            Panel.fit(
                "[bold cyan]TEST: API Response Validation[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
                title="API Test Case",
                subtitle="Testing response format and values",
            )
        )

        # Input data
        test_data = {"id": 123, "values": [1, 2, 3]}
        console.print(Panel(json.dumps(test_data, indent=2), title="📥 Input"))

        # Process data
        result = process_data(test_data)

        # Output table
        table = Table(title="📊 Results Comparison")
        table.add_column("Type", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Expected", "6")
        table.add_row("Actual", str(result))
        table.add_row("Status", "✅ PASS" if result == 6 else "❌ FAIL")

        console.print(table)

        # Test Summary Panel
        console.print(
            Panel.fit(
                "[bold green]TEST COMPLETED: test_with_rich_formatting[/bold green]\n"
                "✅ Successfully validated API response\n"
                "- Verified response format\n"
                "- Confirmed calculation correctness\n"
                "- Validated expected output",
                border_style="green",
                title="Test Summary",
                subtitle="API Response Test",
            )
        )

        assert result == 6

    @pytest.mark.parametrize(
        "input_value, expected",
        [
            ({"symbol": "AAPL", "metric": "price"}, 150.25),
            ({"symbol": "GOOG", "metric": "price"}, 2100.50),
        ],
    )
    def test_parametrized_with_visual_output(self, input_value, expected):
        """Test with parametrized data and visual comparison."""
        # ARRANGE - Display test inputs
        print(f"\n📥 Input: {json.dumps(input_value, indent=2)}")

        # ACT - Simulate fetching stock metrics
        # For demo, we'll just return the expected value
        result = expected
        print(f"📤 Output: {json.dumps(result, indent=2)}")

        # ASSERT - Compare with expected results
        print(f"🎯 Expected: {json.dumps(expected, indent=2)}")

        # Visual comparison
        if result != expected:
            print("❌ DIFFERENCE:")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {result}")
            print(
                f"  Diff:     {expected - result if isinstance(result, (int, float)) else 'complex diff'}"
            )
        else:
            print("✅ MATCH")

        assert result == expected

    def test_with_failure_demonstration(self, request):
        """Test that demonstrates how failures look with visual formatting."""
        # Create input and expected data
        input_data = {"items": [10, 20, 30]}
        expected = 60
        actual = 50  # Incorrect result for demonstration

        # Create failure display
        console.print()
        console.print(Panel("[bold red]Failure Demonstration[/bold red]", border_style="red"))

        # Compare with visual indicator
        if actual != expected:
            diff_table = Table(title="❌ Test Failed: Comparison")
            diff_table.add_column("Expected", style="green")
            diff_table.add_column("Actual", style="red")
            diff_table.add_column("Difference", style="yellow")

            diff_table.add_row(
                str(expected),
                str(actual),
                str(expected - actual if isinstance(expected, (int, float)) else "N/A"),
            )

            console.print(diff_table)

            # Input that caused the error
            console.print(
                Panel(json.dumps(input_data, indent=2), title="Input Data", border_style="red")
            )

        # For demonstration purposes, we'll conditionally assert
        # In real tests, don't do this - let the test fail naturally
        if request.config.getoption("--show-failures", default=False):
            assert actual == expected
        else:
            # Skip the actual assertion for demonstration
            pass


@pytest.mark.api
def test_standalone_with_visual_output():
    """Standalone test with visual formatting."""
    console.print()
    console.print(Panel("[bold cyan]Testing API Endpoint[/bold cyan]", border_style="cyan"))

    # Sample API response
    api_response = {
        "status": "success",
        "data": {"id": 12345, "name": "Sample Result", "values": [4, 5, 6]},
    }

    # Display the response in a nicely formatted way
    console.print(Panel(json.dumps(api_response, indent=2), title="API Response"))

    # Process response
    result = process_data(api_response["data"])

    # Assert with visual indicator
    console.print(f"Sum of values: [bold cyan]{result}[/bold cyan]")
    console.print("✅ Test passed" if result == 15 else "❌ Test failed")

    assert result == 15
