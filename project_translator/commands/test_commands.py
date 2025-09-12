"""
Test-related commands for Project Translator.

This module contains commands for running tests and managing test scenarios.
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core import TestRunner
from ..utils import Config, get_log_file_path

console = Console()


@click.group()
def test_group():
    """Test-related commands."""
    pass


@test_group.command()
@click.option('--test-project', '-p', required=True, help='Path to test project directory')
@click.option('--test-cases', '-t', required=True, help='Path to test_cases.json file')
@click.option('--output', '-o', default=None, help='Output file for test results')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed step-by-step results')
@click.option('--base-url', '-u', default=None, help='Base URL for API requests')
def run_tests(test_project: str, test_cases: str, output: str, verbose: bool, 
              detailed: bool, base_url: str):
    """Run test scenarios against a test project."""
    
    # Load configuration
    config = Config.load()
    
    # Set defaults
    if output is None:
        output = config.output_file
    if base_url is None:
        base_url = config.base_url
    
    # Display configuration
    console.print(Panel.fit(
        "[bold blue]CRUD Service Test Runner[/bold blue]\n"
        f"Test Project: {test_project}\n"
        f"Test Cases: {test_cases}\n"
        f"Output: {output}\n"
        f"Base URL: {base_url}",
        title="Configuration"
    ))
    
    # Initialize test runner
    runner = TestRunner(test_project, test_cases, base_url)
    
    # Run tests with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running tests...", total=None)
        
        results = runner.run_tests()
        
        progress.update(task, description="Tests completed")
    
    # Print results
    if detailed:
        runner.print_detailed_results(results)
    else:
        runner.print_summary(results)
    
    # Show log file path for failed tests
    if not results.get("success", True):
        log_file = get_log_file_path()
        console.print(f"\n[yellow]Detailed logs available at: {log_file}[/yellow]")
    
    # Save results
    if results.get("success") is not None:
        runner.save_results(results, output)
    
    # Exit with appropriate code
    sys.exit(0 if results.get("success", False) else 1)


@test_group.command()
@click.option('--test-project', '-p', required=True, help='Path to test project directory')
@click.option('--test-cases', '-t', required=True, help='Path to test_cases.json file')
@click.option('--scenario', '-s', help='Specific scenario to validate')
def validate(test_project: str, test_cases: str, scenario: str):
    """Validate test project and test cases without running tests."""
    
    console.print("[blue]Validating test project and test cases...[/blue]")
    
    # Initialize test runner for validation
    runner = TestRunner(test_project, test_cases)
    
    # Validate paths
    if not runner.validate_paths():
        console.print("[red]Path validation failed[/red]")
        sys.exit(1)
    
    # Load and validate test cases
    test_cases_data = runner.load_test_cases()
    if not test_cases_data:
        console.print("[red]Failed to load test cases[/red]")
        sys.exit(1)
    
    scenarios = test_cases_data.get("scenarios", [])
    if not scenarios:
        console.print("[red]No scenarios found in test cases[/red]")
        sys.exit(1)
    
    console.print(f"[green]Found {len(scenarios)} test scenarios[/green]")
    
    # Validate specific scenario if requested
    if scenario:
        scenario_found = False
        for s in scenarios:
            if s.get("name") == scenario:
                scenario_found = True
                steps = s.get("steps", [])
                console.print(f"[green]Scenario '{scenario}' found with {len(steps)} steps[/green]")
                break
        
        if not scenario_found:
            console.print(f"[red]Scenario '{scenario}' not found[/red]")
            sys.exit(1)
    
    console.print("[green]Validation completed successfully[/green]")


@test_group.command()
@click.option('--test-project', '-p', required=True, help='Path to test project directory')
@click.option('--test-cases', '-t', required=True, help='Path to test_cases.json file')
@click.option('--output', '-o', default='test_summary.json', help='Output file for summary')
def summary(test_project: str, test_cases: str, output: str):
    """Generate a summary of test scenarios without running them."""
    
    console.print("[blue]Generating test summary...[/blue]")
    
    # Initialize test runner
    runner = TestRunner(test_project, test_cases)
    
    # Load test cases
    test_cases_data = runner.load_test_cases()
    if not test_cases_data:
        console.print("[red]Failed to load test cases[/red]")
        sys.exit(1)
    
    scenarios = test_cases_data.get("scenarios", [])
    
    # Generate summary
    summary_data = {
        "test_suite": test_cases_data.get("test_suite", "Unknown"),
        "description": test_cases_data.get("description", ""),
        "base_url": test_cases_data.get("base_url", "http://localhost:8000"),
        "total_scenarios": len(scenarios),
        "scenarios": [
            {
                "name": s.get("name", "Unknown"),
                "description": s.get("description", ""),
                "total_steps": len(s.get("steps", []))
            }
            for s in scenarios
        ]
    }
    
    # Save summary
    runner.save_results(summary_data, output)
    
    # Display summary
    console.print(f"[green]Test suite: {summary_data['test_suite']}[/green]")
    console.print(f"[green]Total scenarios: {summary_data['total_scenarios']}[/green]")
    console.print(f"[green]Summary saved to: {output}[/green]")


@test_group.command()
def logs():
    """Show current log file path."""
    try:
        log_file = get_log_file_path()
        console.print(f"[green]Current log file: {log_file}[/green]")
        
        # Check if log file exists and show some stats
        from pathlib import Path
        log_path = Path(log_file)
        if log_path.exists():
            size = log_path.stat().st_size
            console.print(f"[green]Log file size: {size:,} bytes[/green]")
        else:
            console.print("[yellow]Log file does not exist yet (no tests have been run)[/yellow]")
    except Exception as e:
        console.print(f"[red]Error getting log file path: {e}[/red]")
