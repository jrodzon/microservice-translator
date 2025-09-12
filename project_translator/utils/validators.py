"""
Validation utilities module.

This module provides validation functions for paths, responses,
and other data structures used in the CLI application.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

console = Console()


class PathValidator:
    """Validates file and directory paths."""
    
    @staticmethod
    def validate_directory(path: str) -> bool:
        """
        Validate that a path is an existing directory.
        
        Args:
            path: Path to validate
            
        Returns:
            True if valid directory, False otherwise
        """
        try:
            path_obj = Path(path).resolve()
            if not path_obj.exists():
                console.print(f"[red]Path does not exist: {path}[/red]")
                return False
            if not path_obj.is_dir():
                console.print(f"[red]Path is not a directory: {path}[/red]")
                return False
            return True
        except Exception as e:
            console.print(f"[red]Error validating directory path: {e}[/red]")
            return False
    
    @staticmethod
    def validate_file(path: str) -> bool:
        """
        Validate that a path is an existing file.
        
        Args:
            path: Path to validate
            
        Returns:
            True if valid file, False otherwise
        """
        try:
            path_obj = Path(path).resolve()
            if not path_obj.exists():
                console.print(f"[red]File does not exist: {path}[/red]")
                return False
            if not path_obj.is_file():
                console.print(f"[red]Path is not a file: {path}[/red]")
                return False
            return True
        except Exception as e:
            console.print(f"[red]Error validating file path: {e}[/red]")
            return False
    
    @staticmethod
    def validate_executable(path: str) -> bool:
        """
        Validate that a path is an executable file.
        
        Args:
            path: Path to validate
            
        Returns:
            True if valid executable, False otherwise
        """
        try:
            path_obj = Path(path).resolve()
            if not PathValidator.validate_file(str(path_obj)):
                return False
            
            if not path_obj.stat().st_mode & 0o111:
                console.print(f"[red]File is not executable: {path}[/red]")
                return False
            
            return True
        except Exception as e:
            console.print(f"[red]Error validating executable path: {e}[/red]")
            return False


class ResponseValidator:
    """Validates HTTP responses and test results."""
    
    @staticmethod
    def validate_status_code(response_code: int, expected_code: int) -> bool:
        """
        Validate HTTP status code.
        
        Args:
            response_code: Actual status code
            expected_code: Expected status code
            
        Returns:
            True if codes match, False otherwise
        """
        return response_code == expected_code
    
    @staticmethod
    def validate_response_structure(response_data: Any, expected_structure: Dict[str, Any]) -> bool:
        """
        Validate response data structure.
        
        Args:
            response_data: Response data to validate
            expected_structure: Expected structure
            
        Returns:
            True if structure matches, False otherwise
        """
        if not isinstance(response_data, dict):
            return False
        
        for key, expected_value in expected_structure.items():
            if key not in response_data:
                return False
            if response_data[key] != expected_value:
                return False
        
        return True
    
    @staticmethod
    def validate_response_contains(response_data: Any, required_keys: List[str]) -> bool:
        """
        Validate that response contains required keys.
        
        Args:
            response_data: Response data to validate
            required_keys: List of required keys
            
        Returns:
            True if all keys present, False otherwise
        """
        if isinstance(response_data, dict):
            return all(key in response_data for key in required_keys)
        elif isinstance(response_data, str):
            return all(key in response_data for key in required_keys)
        return False
    
    @staticmethod
    def validate_response_type(response_data: Any, expected_type: str) -> bool:
        """
        Validate response data type.
        
        Args:
            response_data: Response data to validate
            expected_type: Expected type ("array", "object", etc.)
            
        Returns:
            True if type matches, False otherwise
        """
        if expected_type == "array":
            return isinstance(response_data, list)
        elif expected_type == "object":
            return isinstance(response_data, dict)
        return False
    
    @staticmethod
    def validate_item_count(response_data: Any, expected_count: int, min_count: Optional[int] = None) -> bool:
        """
        Validate item count in response.
        
        Args:
            response_data: Response data to validate
            expected_count: Expected exact count (if min_count is None)
            min_count: Minimum count (if provided, overrides expected_count)
            
        Returns:
            True if count matches expectations, False otherwise
        """
        if not isinstance(response_data, list):
            return False
        
        actual_count = len(response_data)
        
        if min_count is not None:
            return actual_count >= min_count
        else:
            return actual_count == expected_count
