"""
Test executor module for running tests against translated projects.

This module provides functionality to execute tests against translated projects
and collect results for the retry mechanism.
"""

import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..core.test_runner import TestRunner
from ..core.service_manager import ServiceManager
from ..utils import get_logger

logger = get_logger("test_executor")


@dataclass
class TestExecutionResult:
    """Result of test execution."""
    success: bool
    build_success: bool
    service_startup_success: bool
    test_success: bool
    build_errors: List[str]
    service_errors: List[str]
    test_errors: List[str]
    test_results: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0


class TestExecutor:
    """Executes tests against translated projects."""
    
    def __init__(self, project_path: str, test_cases_path: str, 
                 base_url: str = "http://localhost:8000"):
        """
        Initialize the test executor.
        
        Args:
            project_path: Path to the translated project
            test_cases_path: Path to test cases JSON file
            base_url: Base URL for the service
        """
        self.project_path = Path(project_path).resolve()
        self.test_cases_path = Path(test_cases_path).resolve()
        self.base_url = base_url
        self.logger = get_logger("test_executor")
        
        # Find start.sh and shutdown.sh scripts
        self.start_script = self._find_script("start.sh")
        self.shutdown_script = self._find_script("shutdown.sh")
    
    def _find_script(self, script_name: str) -> Optional[Path]:
        """
        Find a script in the project directory.
        
        Args:
            script_name: Name of the script to find
            
        Returns:
            Path to the script or None if not found
        """
        # Look in project root first
        script_path = self.project_path / script_name
        if script_path.exists():
            return script_path
        
        # Look in parent directory (common pattern)
        parent_script = self.project_path.parent / script_name
        if parent_script.exists():
            return parent_script
        
        return None
    
    def validate_setup(self) -> Tuple[bool, List[str]]:
        """
        Validate that the test setup is correct.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self.project_path.exists():
            errors.append(f"Project path does not exist: {self.project_path}")
        
        if not self.test_cases_path.exists():
            errors.append(f"Test cases file does not exist: {self.test_cases_path}")
        
        if not self.start_script:
            errors.append("start.sh script not found in project or parent directory")
        
        if not self.shutdown_script:
            errors.append("shutdown.sh script not found in project or parent directory")
        
        return len(errors) == 0, errors
    
    def build_project(self) -> Tuple[bool, List[str]]:
        """
        Build the project using the start script.
        
        Returns:
            Tuple of (success, error_messages)
        """
        if not self.start_script:
            return False, ["No start script found"]
        
        self.logger.info(f"Building project using: {self.start_script}")
        
        try:
            # Run the start script
            result = subprocess.run(
                ["./start.sh"],
                cwd=self.start_script.parent,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                self.logger.info("Project build successful")
                return True, []
            else:
                error_msg = f"Build failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr}"
                self.logger.error(error_msg)
                return False, [error_msg]
                
        except subprocess.TimeoutExpired:
            error_msg = "Build timed out after 5 minutes"
            self.logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Build failed with exception: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg]
    
    def start_service(self) -> Tuple[bool, List[str]]:
        """
        Start the service and wait for it to be ready.
        
        Returns:
            Tuple of (success, error_messages)
        """
        if not self.start_script:
            return False, ["No start script found"]
        
        self.logger.info("Starting service...")
        
        try:
            # Start the service
            result = subprocess.run(
                ["./start.sh"],
                cwd=self.start_script.parent,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for startup
            )
            
            if result.returncode != 0:
                error_msg = f"Service startup failed with return code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr}"
                return False, [error_msg]
            
            # Wait for service to be ready
            if not self._wait_for_service():
                return False, ["Service failed to become ready within timeout"]
            
            self.logger.info("Service started successfully")
            return True, []
            
        except subprocess.TimeoutExpired:
            return False, ["Service startup timed out"]
        except Exception as e:
            return False, [f"Service startup failed: {str(e)}"]
    
    def _wait_for_service(self, timeout: int = 60) -> bool:
        """
        Wait for the service to become ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if service becomes ready, False otherwise
        """
        import requests
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        return False
    
    def run_tests(self) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
        """
        Run tests against the service.
        
        Returns:
            Tuple of (success, error_messages, test_results)
        """
        self.logger.info("Running tests...")
        
        try:
            # Create test runner
            test_runner = TestRunner(
                str(self.project_path),
                str(self.test_cases_path),
                self.base_url
            )
            
            # Run tests
            results = test_runner.run_tests()
            
            if results.get("success", False):
                self.logger.info("All tests passed")
                return True, [], results
            else:
                error_msg = "Some tests failed"
                if "error" in results:
                    error_msg += f": {results['error']}"
                self.logger.error(error_msg)
                return False, [error_msg], results
                
        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            self.logger.error(error_msg)
            return False, [error_msg], None
    
    def shutdown_service(self) -> bool:
        """
        Shutdown the service.
        
        Returns:
            True if shutdown successful or no shutdown script, False on error
        """
        if not self.shutdown_script:
            self.logger.warning("No shutdown script found")
            return True
        
        self.logger.info("Shutting down service...")
        
        try:
            result = subprocess.run(
                ["./shutdown.sh"],
                cwd=self.shutdown_script.parent,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info("Service shutdown successful")
                return True
            else:
                self.logger.warning(f"Service shutdown warning: {result.stderr}")
                return True  # Don't fail for shutdown issues
                
        except Exception as e:
            self.logger.warning(f"Service shutdown error: {str(e)}")
            return True  # Don't fail for shutdown issues
    
    def execute_full_test(self) -> TestExecutionResult:
        """
        Execute the full test cycle: build, start service, run tests, shutdown.
        
        Returns:
            TestExecutionResult with complete results
        """
        start_time = time.time()
        
        # Validate setup
        is_valid, setup_errors = self.validate_setup()
        if not is_valid:
            return TestExecutionResult(
                success=False,
                build_success=False,
                service_startup_success=False,
                test_success=False,
                build_errors=setup_errors,
                service_errors=[],
                test_errors=[]
            )
        
        # Build project
        build_success, build_errors = self.build_project()
        
        # Start service
        service_success, service_errors = self.start_service()
        
        # Run tests (only if service started successfully)
        test_success = False
        test_errors = []
        test_results = None
        
        if service_success:
            test_success, test_errors, test_results = self.run_tests()
        else:
            test_errors = ["Cannot run tests - service failed to start"]
        
        # Always try to shutdown
        self.shutdown_service()
        
        execution_time = time.time() - start_time
        
        overall_success = build_success and service_success and test_success
        
        return TestExecutionResult(
            success=overall_success,
            build_success=build_success,
            service_startup_success=service_success,
            test_success=test_success,
            build_errors=build_errors,
            service_errors=service_errors,
            test_errors=test_errors,
            test_results=test_results,
            execution_time=execution_time
        )
