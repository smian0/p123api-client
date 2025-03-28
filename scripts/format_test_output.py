#!/usr/bin/env python
"""Format test output with line numbers for better IDE navigation."""

import sys
import os
import re
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table

def get_test_class_name(module_path):
    """Get the class name from the test file."""
    test_class_map = {
        'tests/test_cache_manager.py': 'TestCacheManager',
        'tests/cache_tests.py': 'TestSimpleStorage',
        'tests/screen_run/test_screen_run_cache.py': 'TestScreenRunCache',
        # Add more mappings as needed based on your codebase
    }
    
    # Use the predefined mapping if available
    rel_path = os.path.relpath(module_path)
    if rel_path in test_class_map:
        return test_class_map[rel_path]
    
    # Otherwise, try to detect class name directly
    try:
        cmd = ['grep', '-n', 'class Test', module_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.splitlines():
                match = re.search(r'class (\w+):', line)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"Error finding class name: {e}", file=sys.stderr)
    
    # Default to None if no class found (for module-level tests)
    return None

def get_test_line_numbers_from_grep(module_path, test_names):
    """Get line numbers for test methods using grep."""
    test_info = {}
    
    try:
        # First try class methods with async def
        cmd = ['grep', '-n', '    async def test_', module_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # If no async tests, try regular class methods
        if result.returncode != 0 or not result.stdout:
            cmd = ['grep', '-n', '    def test_', module_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        # If still nothing, try module-level test functions
        if result.returncode != 0 or not result.stdout:
            cmd = ['grep', '-n', '^def test_', module_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                # Format: "44:    async def test_rate_limit_handling(self):"
                parts = line.split(':', 1)
                if len(parts) < 2:
                    continue
                    
                line_number = int(parts[0])
                line_content = parts[1]
                
                # Extract the test name
                match = re.search(r'(?:async )?def test_(\w+)\(', line_content)
                if match:
                    test_name = match.group(1)
                    if test_name in test_names:
                        test_info[test_name] = line_number
    except Exception as e:
        print(f"Error running grep: {e}", file=sys.stderr)
    
    return test_info

def main():
    """Format test output with line numbers."""
    if len(sys.argv) < 3:
        print("Usage: format_test_output.py <test_file> <category_name> <test_name1> <test_name2> ...", file=sys.stderr)
        sys.exit(1)
    
    test_file = sys.argv[1]
    category_name = sys.argv[2]
    test_names = sys.argv[3:]
    
    # Get test class name from the file
    class_name = get_test_class_name(test_file)
    
    # Get test line numbers using grep
    test_info = get_test_line_numbers_from_grep(test_file, test_names)
    
    # Create a rich console and table
    console = Console()
    table = Table(title=f"{category_name} Tests Summary")
    table.add_column("Test Name", style="cyan")
    table.add_column("Line", style="yellow")
    table.add_column("Result", style="green")
    
    # Add rows to the table
    for test_name in test_names:
        # Get the line number, defaulting to "?" if not found
        line_num = str(test_info.get(test_name, "?"))
        table.add_row(f"test_{test_name}", line_num, "✅ PASSED")
    
    # Create file:line::Class.test_name format strings for IDE navigation
    ide_locations = []
    rel_path = os.path.relpath(test_file)
    for test_name in test_names:
        if test_name in test_info:
            line_number = test_info[test_name]
            # Format with line number directly in the nodeid
            if class_name:
                # Class method test (most common case)
                nodeid = f"{rel_path}:{line_number}::{class_name}.test_{test_name}"
            else:
                # Module-level test function
                nodeid = f"{rel_path}:{line_number}::test_{test_name}"
            ide_locations.append(nodeid)
    
    # Print category summary
    console.print("\n\nOverall Test Results Summary by Category")
    console.print(table)
    console.print("[green]ALL TESTS PASSED[/green]")
    
    # Print locations for IDE navigation
    if ide_locations:
        console.print("\n[bold]Test Locations for IDE Navigation:[/bold]")
        for nodeid in ide_locations:
            console.print(nodeid)

if __name__ == "__main__":
    main() 