"""
Request execution module for handling HTTP requests and response validation.

This module provides functionality to execute HTTP requests and validate
responses according to test case specifications.
"""

import requests
from typing import Dict, List, Any, Optional
from rich.console import Console
from ..models import TestStep

console = Console()


class RequestExecutor:
    """Handles HTTP request execution and response validation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the request executor.
        
        Args:
            base_url: Base URL for API requests
        """
        self.base_url = base_url
    
    def execute_request(self, step: TestStep, saved_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single test step HTTP request.
        
        Args:
            step: TestStep instance
            saved_data: Data saved from previous steps
            
        Returns:
            Dictionary containing execution results and validation status
        """
        method = step.method.value
        endpoint = step.endpoint
        headers = step.headers or {}
        body = step.body
        expected_status = step.expected_status
        
        # Replace placeholders in endpoint and body
        endpoint = self._replace_placeholders(endpoint, saved_data)
        if body:
            body = self._replace_placeholders_dict(body, saved_data)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            # Execute HTTP request
            response = self._make_request(method, url, headers, body)
            
            if response is None:
                return {
                    "success": False,
                    "error": f"Failed to execute {method} request",
                    "status_code": None
                }
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Validate response
            validation_result = self._validate_response(
                response, response_data, step, expected_status
            )
            
            # Save response data if requested
            saved_field = step.save_response_field
            if saved_field and validation_result["success"] and isinstance(response_data, dict):
                saved_data[saved_field] = response_data.get("id")
            
            return {
                "success": validation_result["success"],
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_data": response_data,
                "content_match": validation_result["content_match"],
                "saved_field": saved_field,
                "validation_errors": validation_result.get("errors", [])
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None
            }
    
    def _make_request(self, method: str, url: str, headers: Dict[str, str], body: Any) -> Optional[requests.Response]:
        """
        Make HTTP request based on method.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            body: Request body
            
        Returns:
            Response object or None if error
        """
        try:
            if method.upper() == "GET":
                return requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                return requests.post(url, json=body, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                return requests.put(url, json=body, headers=headers, timeout=10)
            elif method.upper() == "DELETE":
                return requests.delete(url, headers=headers, timeout=10)
            else:
                console.print(f"[red]Unsupported HTTP method: {method}[/red]")
                return None
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request failed: {e}[/red]")
            return None
    
    def _validate_response(self, response: requests.Response, response_data: Any, 
                          step: TestStep, expected_status: int) -> Dict[str, Any]:
        """
        Validate response against test step expectations.
        
        Args:
            response: HTTP response object
            response_data: Parsed response data
            step: TestStep instance
            expected_status: Expected HTTP status code
            
        Returns:
            Validation result dictionary
        """
        errors = []
        
        # Check status code
        status_match = response.status_code == expected_status
        if not status_match:
            errors.append(f"Status code mismatch: expected {expected_status}, got {response.status_code}")
        
        # Check response content
        content_match = True
        if step.expected_response is not None:
            content_match = self._check_response_content(response_data, step.expected_response)
            if not content_match:
                errors.append("Response content does not match expected values")
        elif step.expected_response_contains is not None:
            content_match = self._check_response_contains(response_data, step.expected_response_contains)
            if not content_match:
                errors.append("Response does not contain expected keys")
        elif step.expected_response_type is not None:
            content_match = self._check_response_type(response_data, step.expected_response_type.value)
            if not content_match:
                errors.append(f"Response type mismatch: expected {step.expected_response_type.value}")
        elif step.expected_min_items is not None:
            content_match = self._check_min_items(response_data, step.expected_min_items)
            if not content_match:
                errors.append(f"Response has fewer items than expected minimum: {step.expected_min_items}")
        elif step.expected_items is not None:
            content_match = self._check_exact_items(response_data, step.expected_items)
            if not content_match:
                errors.append(f"Response item count mismatch: expected {step.expected_items}")
        
        return {
            "success": status_match and content_match,
            "content_match": content_match,
            "errors": errors
        }
    
    def _replace_placeholders(self, text: str, saved_data: Dict[str, Any]) -> str:
        """Replace placeholders in text with saved data."""
        for key, value in saved_data.items():
            placeholder = f"{{saved_{key}}}"
            text = text.replace(placeholder, str(value))
        return text
    
    def _replace_placeholders_dict(self, data: Dict[str, Any], saved_data: Dict[str, Any]) -> Dict[str, Any]:
        """Replace placeholders in dictionary values."""
        if isinstance(data, dict):
            return {k: self._replace_placeholders_dict(v, saved_data) for k, v in data.items()}
        elif isinstance(data, str):
            return self._replace_placeholders(data, saved_data)
        else:
            return data
    
    def _check_response_content(self, response_data: Any, expected: Dict[str, Any]) -> bool:
        """Check if response matches expected content."""
        if not isinstance(response_data, dict):
            return False
        
        for key, expected_value in expected.items():
            if key not in response_data:
                return False
            if response_data[key] != expected_value:
                return False
        
        return True
    
    def _check_response_contains(self, response_data: Any, expected_keys: List[str]) -> bool:
        """Check if response contains expected keys."""
        if isinstance(response_data, dict):
            return all(key in response_data for key in expected_keys)
        elif isinstance(response_data, str):
            return all(key in response_data for key in expected_keys)
        return False
    
    def _check_response_type(self, response_data: Any, expected_type: str) -> bool:
        """Check if response is of expected type."""
        if expected_type == "array":
            return isinstance(response_data, list)
        elif expected_type == "object":
            return isinstance(response_data, dict)
        return False
    
    def _check_min_items(self, response_data: Any, min_count: int) -> bool:
        """Check if response has minimum number of items."""
        if isinstance(response_data, list):
            return len(response_data) >= min_count
        return False
    
    def _check_exact_items(self, response_data: Any, exact_count: int) -> bool:
        """Check if response has exact number of items."""
        if isinstance(response_data, list):
            return len(response_data) == exact_count
        return False
