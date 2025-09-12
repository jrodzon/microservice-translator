"""
Result handling module for test results processing and reporting.

This module provides functionality to process test results, generate reports,
and save results to files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


class ResultHandler:
    """Handles test result processing, reporting, and persistence."""
    
    def __init__(self):
        """Initialize the result handler."""
        pass
    
    def save_results(self, results: Dict[str, Any], output_file: str) -> bool:
        """
        Save test results to a JSON file.
        
        Args:
            results: Test results dictionary
            output_file: Path to output file
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            
            console.print(f"[green]Results saved to: {output_file}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to save results: {e}[/red]")
            return False
    
    def print_summary(self, results: Dict[str, Any]):
        """
        Print a formatted summary of test results.
        
        Args:
            results: Test results dictionary
        """
        # Check if there's a critical error (like service startup failure)
        if not results.get("success") and results.get("error"):
            console.print(f"[red]Test run failed: {results.get('error')}[/red]")
            return
        
        # Create summary table
        table = Table(title="Test Results Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Test Suite", results.get("test_suite", "Unknown"))
        table.add_row("Total Scenarios", str(results.get("total_scenarios", 0)))
        table.add_row("Passed Scenarios", str(results.get("passed_scenarios", 0)))
        table.add_row("Failed Scenarios", str(results.get("total_scenarios", 0) - results.get("passed_scenarios", 0)))
        
        total_scenarios = max(results.get("total_scenarios", 1), 1)
        passed_scenarios = results.get("passed_scenarios", 0)
        success_rate = (passed_scenarios / total_scenarios) * 100
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        
        console.print(table)
        
        # Show scenario details
        self._print_scenario_details(results.get("scenario_results", []))
        
        # Show failed scenario details if any
        failed_scenarios = [s for s in results.get("scenario_results", []) if not s.get("success", True)]
        if failed_scenarios:
            console.print("\n[red]Failed Scenarios Details:[/red]")
            for scenario in failed_scenarios:
                self._print_failed_scenario_details(scenario)
    
    def _print_scenario_details(self, scenario_results: List[Dict[str, Any]]):
        """
        Print detailed scenario results.
        
        Args:
            scenario_results: List of scenario result dictionaries
        """
        console.print("\n[cyan]Scenario Details:[/cyan]")
        for scenario in scenario_results:
            status = "✓" if scenario["success"] else "✗"
            color = "green" if scenario["success"] else "red"
            console.print(f"  [{color}]{status} {scenario['scenario_name']}[/{color}] ({scenario['passed_steps']}/{scenario['total_steps']} steps)")
    
    def _print_failed_scenario_details(self, scenario: Dict[str, Any]):
        """
        Print detailed information for a failed scenario.
        
        Args:
            scenario: Failed scenario result dictionary
        """
        console.print(f"\n[red]✗ {scenario['scenario_name']}[/red]")
        if scenario.get("scenario_description"):
            console.print(f"[dim]{scenario['scenario_description']}[/dim]")
        
        # Print failed steps
        failed_steps = [step for step in scenario.get("step_results", []) if not step.get("success", True)]
        if failed_steps:
            console.print("[red]Failed Steps:[/red]")
            for step in failed_steps:
                console.print(f"  [red]✗ {step['step_name']}[/red]")
                
                if "error" in step:
                    console.print(f"    [red]Error: {step['error']}[/red]")
                
                if "validation_errors" in step and step["validation_errors"]:
                    for error in step["validation_errors"]:
                        console.print(f"    [red]{error}[/red]")
                
                if step.get("status_code") is not None and step.get("expected_status") is not None:
                    if step["status_code"] != step["expected_status"]:
                        console.print(f"    [red]Status Code: {step['status_code']} (expected: {step['expected_status']})[/red]")
                
                if step.get("exception"):
                    console.print(f"    [red]Exception occurred during step execution[/red]")
    
    def print_detailed_results(self, results: Dict[str, Any]):
        """
        Print detailed test results with step-by-step information.
        
        Args:
            results: Test results dictionary
        """
        if not results.get("success"):
            console.print(f"[red]Test run failed: {results.get('error', 'Unknown error')}[/red]")
            return
        
        for scenario in results.get("scenario_results", []):
            self._print_scenario_detailed(scenario)
    
    def _print_scenario_detailed(self, scenario: Dict[str, Any]):
        """
        Print detailed information for a single scenario.
        
        Args:
            scenario: Scenario result dictionary
        """
        status = "✓" if scenario["success"] else "✗"
        color = "green" if scenario["success"] else "red"
        
        console.print(f"\n[{color}]{status} {scenario['scenario_name']}[/{color}]")
        if scenario.get("scenario_description"):
            console.print(f"[dim]{scenario['scenario_description']}[/dim]")
        
        # Print step results
        for step in scenario.get("step_results", []):
            step_status = "✓" if step["success"] else "✗"
            step_color = "green" if step["success"] else "red"
            console.print(f"  [{step_color}]{step_status} {step['step_name']}[/{step_color}]")
            
            if not step["success"]:
                if "error" in step:
                    console.print(f"    [red]Error: {step['error']}[/red]")
                if "validation_errors" in step and step["validation_errors"]:
                    for error in step["validation_errors"]:
                        console.print(f"    [red]{error}[/red]")
    
    def create_results_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of test results for reporting.
        
        Args:
            results: Full test results dictionary
            
        Returns:
            Summary dictionary
        """
        scenario_results = results.get("scenario_results", [])
        total_scenarios = len(scenario_results)
        passed_scenarios = sum(1 for r in scenario_results if r["success"])
        
        total_steps = sum(r.get("total_steps", 0) for r in scenario_results)
        passed_steps = sum(r.get("passed_steps", 0) for r in scenario_results)
        
        return {
            "test_suite": results.get("test_suite", "Unknown"),
            "timestamp": results.get("timestamp", datetime.now().isoformat()),
            "overall_success": results.get("success", False),
            "total_scenarios": total_scenarios,
            "passed_scenarios": passed_scenarios,
            "failed_scenarios": total_scenarios - passed_scenarios,
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": total_steps - passed_steps,
            "success_rate": (passed_scenarios / max(total_scenarios, 1)) * 100
        }
    
    def export_results_csv(self, results: Dict[str, Any], output_file: str) -> bool:
        """
        Export test results to CSV format.
        
        Args:
            results: Test results dictionary
            output_file: Path to output CSV file
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            import csv
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    "Scenario", "Status", "Total Steps", "Passed Steps", 
                    "Failed Steps", "Description"
                ])
                
                # Write scenario data
                for scenario in results.get("scenario_results", []):
                    writer.writerow([
                        scenario.get("scenario_name", ""),
                        "PASS" if scenario.get("success", False) else "FAIL",
                        scenario.get("total_steps", 0),
                        scenario.get("passed_steps", 0),
                        scenario.get("total_steps", 0) - scenario.get("passed_steps", 0),
                        scenario.get("scenario_description", "")
                    ])
            
            console.print(f"[green]CSV results exported to: {output_file}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to export CSV: {e}[/red]")
            return False
