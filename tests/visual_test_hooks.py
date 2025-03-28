"""Visual test hooks for improved test output formatting and grouping."""

import time
from collections import defaultdict

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Initialize rich console
console = Console()

# Dictionary to store test results by category
test_results = defaultdict(list)

# Mapping of test file names to categories
file_to_category = {
    "test_cache_manager.py": "Cache",
    "cache_tests.py": "Cache",
    "screen_run_cache.py": "ScreenRun",
    "test_screen_run.py": "ScreenRun",
    "test_rank_update.py": "RankUpdate",
    "test_strategy.py": "Strategy",
    # Add more mappings as needed
}

# Track the current category
current_category = None
current_category_start_time = None
current_category_tests = []

# Store item to category mapping
item_to_category = {}


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    """Add markers for test categories."""
    config.addinivalue_line("markers", "cache: Cache related tests")
    config.addinivalue_line("markers", "api: API related tests")
    config.addinivalue_line("markers", "screen: Screen run related tests")
    config.addinivalue_line("markers", "rank: Rank system related tests")
    config.addinivalue_line("markers", "strategy: Strategy related tests")
    # Add more category markers as needed


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Set up test run and print test group headers."""
    global current_category, current_category_start_time, current_category_tests

    # Get test file name
    file_name = item.fspath.basename
    category = file_to_category.get(file_name, "Other")

    # Store the category with the item for later use
    item_to_category[item.nodeid] = category

    # Check if we need to print a category header
    if current_category != category:
        # If there was a previous category, print its summary
        if current_category is not None:
            print_category_summary(current_category, current_category_tests)
            current_category_tests = []

        console.print()
        console.print(
            Panel(
                f"[bold blue]Starting {category} Tests[/bold blue]",
                border_style="blue",
                expand=False,
            )
        )
        current_category = category
        current_category_start_time = time.time()

    # Add the current test to the category tests
    current_category_tests.append(item.nodeid)


@pytest.hookimpl(trylast=True)
def pytest_runtest_logreport(report):
    """Process test results and categorize them."""
    if report.when == "call":
        # Get the test category from stored mapping
        category = item_to_category.get(report.nodeid, "Other")
        test_name = report.nodeid.split("::")[-1]

        # Store result
        test_results[category].append((test_name, report.passed))


@pytest.hookimpl(trylast=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print summary of test results by category."""
    global current_category, current_category_tests

    # Print summary for the last category if it exists
    if current_category is not None and current_category_tests:
        print_category_summary(current_category, current_category_tests)

    console.print("\n[bold]Overall Test Results Summary by Category[/bold]")

    all_passed = True

    for category, results in test_results.items():
        table = Table(title=f"{category} Tests Summary", show_header=True, header_style="bold")
        table.add_column("Test Name")
        table.add_column("Result")

        category_passed = True

        for test_name, passed in results:
            result_text = "✅ PASSED" if passed else "❌ FAILED"
            result_style = "green" if passed else "red"
            table.add_row(test_name, f"[{result_style}]{result_text}[/{result_style}]")

            if not passed:
                category_passed = False
                all_passed = False

        # Add category summary row
        summary_style = "green" if category_passed else "red"
        summary_text = "ALL PASSED" if category_passed else "SOME FAILED"
        table.add_row(
            "[bold]Category Summary[/bold]",
            f"[bold {summary_style}]{summary_text}[/bold {summary_style}]",
        )

        console.print(table)
        console.print()

    # Print overall summary
    overall_style = "green" if all_passed else "red"
    overall_text = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    console.print(
        Panel(
            f"[bold {overall_style}]{overall_text}[/bold {overall_style}]",
            border_style=overall_style,
            expand=False,
        )
    )


def print_category_summary(category, test_nodeid_list):
    """Print a summary for the just-completed category."""
    end_time = time.time()
    duration = end_time - current_category_start_time

    # Get results just for this category
    category_results = test_results.get(category, [])
    test_count = len(category_results)
    passed_count = sum(1 for _, passed in category_results if passed)
    failed_count = test_count - passed_count

    # Only print summary if we have results
    if test_count > 0:
        console.print()
        console.print(
            Panel(
                f"[bold blue]Completed {category} Tests[/bold blue]\n"
                f"Tests: {test_count} | Passed: [green]{passed_count}[/green] | "
                f"Failed: [red]{failed_count}[/red] | "
                f"Duration: {duration:.2f}s",
                border_style="blue",
                expand=False,
            )
        )
        console.print()


def print_test_group(group_name):
    """Print a visually distinct group header for related tests."""
    console.print()
    console.print(Panel(f"[bold blue]{group_name}[/bold blue]", border_style="blue", expand=False))
