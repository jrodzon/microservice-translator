"""
Error analysis module for translation retry mechanism.

This module provides functionality to analyze different types of errors
that can occur during translation, testing, and execution.
"""

import re
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils import get_logger

logger = get_logger("error_analyzer")


class ErrorType(Enum):
    """Types of errors that can occur during translation and testing."""
    BUILD_ERROR = "build_error"
    COMPILE_ERROR = "compile_error"
    RUNTIME_ERROR = "runtime_error"
    TEST_FAILURE = "test_failure"
    SERVICE_STARTUP_ERROR = "service_startup_error"
    DEPENDENCY_ERROR = "dependency_error"
    SYNTAX_ERROR = "syntax_error"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorInfo:
    """Information about a specific error."""
    error_type: ErrorType
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    context: Optional[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class ErrorAnalyzer:
    """Analyzes errors and provides suggestions for fixes."""
    
    def __init__(self):
        """Initialize the error analyzer."""
        self.logger = get_logger("error_analyzer")
        
        # Error pattern mappings
        self.error_patterns = {
            ErrorType.BUILD_ERROR: [
                r"build failed",
                r"docker build.*failed",
                r"dockerfile.*error",
                r"build.*error",
                r"failed to build"
            ],
            ErrorType.COMPILE_ERROR: [
                r"compilation.*error",
                r"syntax.*error",
                r"parse.*error",
                r"compiler.*error",
                r"javac.*error",
                r"gcc.*error",
                r"g\+\+.*error"
            ],
            ErrorType.RUNTIME_ERROR: [
                r"runtime.*error",
                r"exception.*thrown",
                r"segmentation.*fault",
                r"null.*pointer",
                r"index.*out.*of.*bounds",
                r"connection.*refused",
                r"port.*already.*in.*use"
            ],
            ErrorType.DEPENDENCY_ERROR: [
                r"package.*not.*found",
                r"module.*not.*found",
                r"import.*error",
                r"dependency.*missing",
                r"npm.*error",
                r"pip.*error",
                r"maven.*error"
            ],
            ErrorType.SYNTAX_ERROR: [
                r"syntax.*error",
                r"unexpected.*token",
                r"missing.*semicolon",
                r"unclosed.*bracket",
                r"invalid.*syntax"
            ],
            ErrorType.CONFIGURATION_ERROR: [
                r"config.*error",
                r"configuration.*invalid",
                r"missing.*config",
                r"invalid.*setting"
            ]
        }
    
    def analyze_build_error(self, error_output: str, project_path: str) -> ErrorInfo:
        """
        Analyze build errors from Docker or build scripts.
        
        Args:
            error_output: Error output from build process
            project_path: Path to the project
            
        Returns:
            ErrorInfo object with analysis
        """
        suggestions = []
        
        # Check for common Docker build issues
        if "dockerfile" in error_output.lower():
            suggestions.extend([
                "Check Dockerfile syntax and base image",
                "Ensure all required files are copied correctly",
                "Verify build context includes all necessary files"
            ])
        
        if "permission" in error_output.lower():
            suggestions.append("Check file permissions and ownership")
        
        if "no such file" in error_output.lower():
            suggestions.append("Verify all referenced files exist in the build context")
        
        if "port" in error_output.lower():
            suggestions.append("Check port configuration and availability")
        
        return ErrorInfo(
            error_type=ErrorType.BUILD_ERROR,
            message="Build process failed",
            context=error_output,
            suggestions=suggestions
        )
    
    def analyze_compile_error(self, error_output: str, project_path: str) -> ErrorInfo:
        """
        Analyze compilation errors.
        
        Args:
            error_output: Error output from compilation
            project_path: Path to the project
            
        Returns:
            ErrorInfo object with analysis
        """
        suggestions = []
        
        # Extract file and line information
        file_path = None
        line_number = None
        
        # Common patterns for file:line errors
        file_line_patterns = [
            r"([^:\s]+):(\d+):",
            r"([^:\s]+)\((\d+)\):",
            r"at\s+([^:\s]+):(\d+)"
        ]
        
        for pattern in file_line_patterns:
            match = re.search(pattern, error_output)
            if match:
                file_path = match.group(1)
                line_number = int(match.group(2))
                break
        
        # Language-specific suggestions
        if "java" in error_output.lower() or "javac" in error_output.lower():
            suggestions.extend([
                "Check Java syntax and imports",
                "Verify classpath and dependencies",
                "Ensure proper package declarations"
            ])
        elif "javascript" in error_output.lower() or "node" in error_output.lower():
            suggestions.extend([
                "Check JavaScript syntax",
                "Verify module imports and exports",
                "Check for missing semicolons or brackets"
            ])
        elif "python" in error_output.lower():
            suggestions.extend([
                "Check Python syntax and indentation",
                "Verify import statements",
                "Check for missing colons or parentheses"
            ])
        
        return ErrorInfo(
            error_type=ErrorType.COMPILE_ERROR,
            message="Compilation failed",
            file_path=file_path,
            line_number=line_number,
            context=error_output,
            suggestions=suggestions
        )
    
    def analyze_runtime_error(self, error_output: str, project_path: str) -> ErrorInfo:
        """
        Analyze runtime errors.
        
        Args:
            error_output: Error output from runtime
            project_path: Path to the project
            
        Returns:
            ErrorInfo object with analysis
        """
        suggestions = []
        
        if "connection refused" in error_output.lower():
            suggestions.extend([
                "Check if the service is running on the correct port",
                "Verify network configuration",
                "Check firewall settings"
            ])
        elif "port already in use" in error_output.lower():
            suggestions.extend([
                "Change the port number in configuration",
                "Stop other services using the same port",
                "Check for zombie processes"
            ])
        elif "null pointer" in error_output.lower():
            suggestions.extend([
                "Check for null value handling",
                "Add null checks before object access",
                "Verify object initialization"
            ])
        elif "out of memory" in error_output.lower():
            suggestions.extend([
                "Increase memory allocation",
                "Check for memory leaks",
                "Optimize memory usage"
            ])
        
        return ErrorInfo(
            error_type=ErrorType.RUNTIME_ERROR,
            message="Runtime error occurred",
            context=error_output,
            suggestions=suggestions
        )
    
    def analyze_test_failure(self, test_results: Dict[str, Any]) -> List[ErrorInfo]:
        """
        Analyze test failures.
        
        Args:
            test_results: Test execution results
            
        Returns:
            List of ErrorInfo objects for each failure
        """
        errors = []
        
        if not test_results.get("success", True):
            scenario_results = test_results.get("scenario_results", [])
            
            for scenario in scenario_results:
                if not scenario.get("success", True):
                    step_results = scenario.get("step_results", [])
                    
                    for step in step_results:
                        if not step.get("success", True):
                            error_type = ErrorType.TEST_FAILURE
                            message = f"Test step '{step.get('step_name', 'Unknown')}' failed"
                            
                            suggestions = []
                            if "error" in step:
                                error_msg = step["error"]
                                if "status" in error_msg.lower():
                                    suggestions.append("Check HTTP status code handling")
                                if "timeout" in error_msg.lower():
                                    suggestions.append("Increase timeout or check service responsiveness")
                                if "connection" in error_msg.lower():
                                    suggestions.append("Verify service connectivity and configuration")
                            
                            errors.append(ErrorInfo(
                                error_type=error_type,
                                message=message,
                                context=json.dumps(step, indent=2),
                                suggestions=suggestions
                            ))
        
        return errors
    
    def analyze_error(self, error_output: str, project_path: str, 
                     error_type_hint: Optional[ErrorType] = None) -> ErrorInfo:
        """
        Analyze an error and determine its type and suggestions.
        
        Args:
            error_output: Error output to analyze
            project_path: Path to the project
            error_type_hint: Optional hint about the error type
            
        Returns:
            ErrorInfo object with analysis
        """
        error_output_lower = error_output.lower()
        
        # If we have a hint, use the appropriate analyzer
        if error_type_hint == ErrorType.BUILD_ERROR:
            return self.analyze_build_error(error_output, project_path)
        elif error_type_hint == ErrorType.COMPILE_ERROR:
            return self.analyze_compile_error(error_output, project_path)
        elif error_type_hint == ErrorType.RUNTIME_ERROR:
            return self.analyze_runtime_error(error_output, project_path)
        
        # Otherwise, try to determine the error type
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_output_lower):
                    if error_type == ErrorType.BUILD_ERROR:
                        return self.analyze_build_error(error_output, project_path)
                    elif error_type == ErrorType.COMPILE_ERROR:
                        return self.analyze_compile_error(error_output, project_path)
                    elif error_type == ErrorType.RUNTIME_ERROR:
                        return self.analyze_runtime_error(error_output, project_path)
                    else:
                        return ErrorInfo(
                            error_type=error_type,
                            message=f"Error detected: {error_type.value}",
                            context=error_output,
                            suggestions=[f"Investigate {error_type.value.replace('_', ' ')}"]
                        )
        
        # Default to unknown error
        return ErrorInfo(
            error_type=ErrorType.UNKNOWN_ERROR,
            message="Unknown error occurred",
            context=error_output,
            suggestions=["Review error output for specific issues"]
        )
    
    def generate_error_feedback(self, errors: List[ErrorInfo], 
                               project_path: str) -> str:
        """
        Generate feedback text for the LLM based on errors.
        
        Args:
            errors: List of ErrorInfo objects
            project_path: Path to the project
            
        Returns:
            Formatted feedback text for the LLM
        """
        if not errors:
            return "No errors detected."
        
        feedback = "TRANSLATION ERRORS DETECTED:\n\n"
        
        for i, error in enumerate(errors, 1):
            feedback += f"ERROR {i}: {error.error_type.value.upper()}\n"
            feedback += f"Message: {error.message}\n"
            
            if error.file_path:
                feedback += f"File: {error.file_path}\n"
            if error.line_number:
                feedback += f"Line: {error.line_number}\n"
            
            if error.context:
                # Truncate context if too long
                context = error.context
                if len(context) > 500:
                    context = context[:500] + "..."
                feedback += f"Context: {context}\n"
            
            if error.suggestions:
                feedback += "Suggestions:\n"
                for suggestion in error.suggestions:
                    feedback += f"  - {suggestion}\n"
            
            feedback += "\n"
        
        feedback += "\nPlease fix these errors and provide an updated translation.\n"
        feedback += "Focus on the specific issues mentioned above.\n"
        
        return feedback
