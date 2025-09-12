"""
Test runner module for orchestrating test execution.

This module provides the main TestRunner class that coordinates
service management, test execution, and result handling.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from rich.console import Console

from .service_manager import ServiceManager
from .request_executor import RequestExecutor
from .result_handler import ResultHandler
from ..utils import get_logger
from ..models import TestSuite, TestScenario, TestStep

console = Console()
logger = get_logger("test_runner")


class TestRunner:
    """Orchestrates test execution against CRUD services."""
    
    def __init__(self, test_project_path: str, test_cases_path: str, base_url: str = "http://localhost:8000"):
        """
        Initialize the test runner.
        
        Args:
            test_project_path: Path to test project directory
            test_cases_path: Path to test cases JSON file
            base_url: Base URL for API requests
        """
        self.test_project_path = Path(test_project_path).resolve()
        self.test_cases_path = Path(test_cases_path).resolve()
        self.base_url = base_url
        
        # Initialize components
        scripts_dir = self.test_project_path.parent
        self.service_manager = ServiceManager(test_project_path, str(scripts_dir), base_url)
        self.request_executor = RequestExecutor(base_url)
        self.result_handler = ResultHandler()
        
        self.results = []
    
    def validate_paths(self) -> bool:
        """
        Validate that required paths exist.
        
        Returns:
            True if paths are valid, False otherwise
        """
        logger.debug(f"Validating paths: project={self.test_project_path}, cases={self.test_cases_path}")
        
        if not self.test_project_path.exists():
            error_msg = f"Test project path does not exist: {self.test_project_path}"
            logger.error(error_msg)
            console.print(f"[red]Error: {error_msg}[/red]")
            return False
            
        if not self.test_cases_path.exists():
            error_msg = f"Test cases file does not exist: {self.test_cases_path}"
            logger.error(error_msg)
            console.print(f"[red]Error: {error_msg}[/red]")
            return False
        
        return self.service_manager.validate_scripts()
    
    def load_test_cases(self) -> Optional[TestSuite]:
        """
        Load test cases from JSON file using Pydantic models.
        
        Returns:
            TestSuite instance or None if error
        """
        try:
            logger.debug(f"Loading test cases from: {self.test_cases_path}")
            test_suite = TestSuite.load(str(self.test_cases_path))
            logger.info(f"Successfully loaded test cases: {len(test_suite.scenarios)} scenarios")
            return test_suite
        except Exception as e:
            error_msg = f"Error loading test cases: {e}"
            logger.error(error_msg, exc_info=True)
            console.print(f"[red]{error_msg}[/red]")
            return None
    
    def run_scenario(self, scenario: TestScenario, global_saved_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run a single test scenario.
        
        Args:
            scenario: TestScenario instance
            global_saved_data: Global saved data dictionary to maintain across scenarios
            
        Returns:
            Scenario execution results
        """
        scenario_name = scenario.name
        scenario_desc = scenario.description
        steps = scenario.steps
        
        logger.info(f"Starting scenario: {scenario_name}")
        if scenario_desc:
            logger.info(f"Description: {scenario_desc}")
        
        console.print(f"\n[cyan]Running scenario: {scenario_name}[/cyan]")
        if scenario_desc:
            console.print(f"[dim]{scenario_desc}[/dim]")
        
        # Use global saved data if provided, otherwise start fresh
        saved_data = global_saved_data if global_saved_data is not None else {}
        step_results = []
        scenario_success = True
        
        for i, step in enumerate(steps, 1):
            step_name = step.name
            logger.debug(f"Executing step {i}: {step_name}")
            console.print(f"  [blue]Step {i}: {step_name}[/blue]")
            
            try:
                result = self.request_executor.execute_request(step, saved_data)
                step_results.append({
                    "step_name": step_name,
                    "step_number": i,
                    **result
                })
                
                if result["success"]:
                    logger.info(f"Step '{step_name}': PASSED")
                    console.print(f"    [green]✓ Passed[/green]")
                else:
                    logger.error(f"Step '{step_name}': FAILED")
                    console.print(f"    [red]✗ Failed[/red]")
                    
                    if "error" in result:
                        logger.error(f"  Error: {result['error']}")
                        console.print(f"    [red]Error: {result['error']}[/red]")
                    elif not result.get("content_match", True):
                        logger.error(f"  Content validation failed")
                        console.print(f"    [red]Content validation failed[/red]")
                    
                    scenario_success = False
                    
            except Exception as e:
                logger.error(f"Step '{step_name}': EXCEPTION - {str(e)}", exc_info=True)
                step_results.append({
                    "step_name": step_name,
                    "step_number": i,
                    "success": False,
                    "error": str(e),
                    "exception": True
                })
                console.print(f"    [red]✗ Exception: {str(e)}[/red]")
                scenario_success = False
        
        passed_steps = sum(1 for r in step_results if r["success"])
        logger.info(f"Scenario '{scenario_name}' completed: {'PASSED' if scenario_success else 'FAILED'} ({passed_steps}/{len(steps)} steps)")
        
        return {
            "scenario_name": scenario_name,
            "scenario_description": scenario_desc,
            "success": scenario_success,
            "step_results": step_results,
            "total_steps": len(steps),
            "passed_steps": passed_steps
        }
    
    def run_tests(self) -> Dict[str, Any]:
        """
        Run all test scenarios.
        
        Returns:
            Complete test execution results
        """
        logger.info("Starting test execution")
        
        if not self.validate_paths():
            error_msg = "Path validation failed"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        test_suite = self.load_test_cases()
        if not test_suite:
            error_msg = "Failed to load test cases"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        scenarios = test_suite.scenarios
        if not scenarios:
            error_msg = "No scenarios found in test cases"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        logger.info(f"Found {len(scenarios)} test scenarios")
        console.print(f"[green]Found {len(scenarios)} test scenarios[/green]")
        
        # Start service
        logger.info("Starting test service")
        if not self.service_manager.start_service():
            error_msg = "Failed to start service"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Wait for service to be ready
        logger.info("Waiting for service to be ready")
        if not self.service_manager.wait_for_service():
            error_msg = "Service failed to become ready"
            logger.error(error_msg)
            self.service_manager.shutdown_service()
            return {"success": False, "error": error_msg}
        
        logger.info("Service is ready, starting test scenarios")
        
        # Run scenarios
        scenario_results = []
        overall_success = True
        global_saved_data = {}  # Maintain saved data across scenarios
        
        try:
            for i, scenario in enumerate(scenarios, 1):
                logger.info(f"Running scenario {i}/{len(scenarios)}: {scenario.name}")
                result = self.run_scenario(scenario, global_saved_data)
                scenario_results.append(result)
                if not result["success"]:
                    overall_success = False
                    logger.error(f"Scenario {i} FAILED: {scenario.name}")
                    
                    # Log details about failed steps
                    failed_steps = [step for step in result.get("step_results", []) if not step.get("success", True)]
                    for step in failed_steps:
                        logger.error(f"  Failed step: {step.get('step_name', 'Unknown')}")
                        if "error" in step:
                            logger.error(f"    Error: {step['error']}")
                        if "validation_errors" in step and step["validation_errors"]:
                            for error in step["validation_errors"]:
                                logger.error(f"    Validation Error: {error}")
                        if step.get("status_code") is not None and step.get("expected_status") is not None:
                            if step["status_code"] != step["expected_status"]:
                                logger.error(f"    Status Code: {step['status_code']} (expected: {step['expected_status']})")
                        if step.get("exception"):
                            logger.error(f"    Exception occurred during step execution")
        except Exception as e:
            logger.error(f"Unexpected error during test execution: {str(e)}", exc_info=True)
            overall_success = False
        finally:
            # Always shutdown service
            logger.info("Shutting down test service")
            self.service_manager.shutdown_service()
        
        passed_scenarios = sum(1 for r in scenario_results if r["success"])
        logger.info(f"Test execution completed: {passed_scenarios}/{len(scenarios)} scenarios passed")
        
        return {
            "success": overall_success,
            "test_suite": test_suite.test_suite,
            "total_scenarios": len(scenarios),
            "passed_scenarios": passed_scenarios,
            "scenario_results": scenario_results,
            "timestamp": self._get_timestamp()
        }
    
    def save_results(self, results: Dict[str, Any], output_file: str) -> bool:
        """
        Save test results to file.
        
        Args:
            results: Test results dictionary
            output_file: Path to output file
            
        Returns:
            True if saved successfully, False otherwise
        """
        return self.result_handler.save_results(results, output_file)
    
    def print_summary(self, results: Dict[str, Any]):
        """
        Print test results summary.
        
        Args:
            results: Test results dictionary
        """
        self.result_handler.print_summary(results)
    
    def print_detailed_results(self, results: Dict[str, Any]):
        """
        Print detailed test results.
        
        Args:
            results: Test results dictionary
        """
        self.result_handler.print_detailed_results(results)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
