"""
Test case models for Project Translator.

This module contains models for test case structures using dataclasses
as a fallback when Pydantic is not available.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class HttpMethod(str, Enum):
    """HTTP methods enum."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ResponseType(str, Enum):
    """Response type enum."""
    ARRAY = "array"
    OBJECT = "object"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


@dataclass
class TestStep:
    """Model for a single test step."""
    
    name: str
    method: HttpMethod
    endpoint: str
    
    # Optional fields
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    
    # Response validation fields
    expected_response: Optional[Dict[str, Any]] = None
    expected_response_contains: Optional[List[str]] = None
    expected_response_type: Optional[ResponseType] = None
    expected_items: Optional[int] = None
    expected_min_items: Optional[int] = None
    
    # Data saving
    save_response_field: Optional[str] = None
    
    def __post_init__(self):
        """Validate step configuration after initialization."""
        # Validate HTTP status code
        if not (100 <= self.expected_status <= 599):
            raise ValueError('Status code must be between 100 and 599')
        
        # Validate endpoint
        if not self.endpoint.startswith('/'):
            raise ValueError('Endpoint must start with /')
        
        # Validate item counts
        for attr_name in ['expected_items', 'expected_min_items']:
            value = getattr(self, attr_name)
            if value is not None and value < 0:
                raise ValueError(f'{attr_name} must be non-negative')
        
        # Validate that at least one response validation method is specified
        validation_fields = [
            'expected_response',
            'expected_response_contains', 
            'expected_response_type',
            'expected_items',
            'expected_min_items'
        ]
        
        has_validation = any(getattr(self, field) is not None for field in validation_fields)
        
        if not has_validation and self.method != HttpMethod.GET:
            # For GET requests, it's common to not have explicit validation
            pass  # This is a warning, not an error


@dataclass
class TestScenario:
    """Model for a test scenario containing multiple steps."""
    
    name: str
    steps: List[TestStep]
    description: str = ""
    
    def __post_init__(self):
        """Validate scenario configuration after initialization."""
        if not self.steps:
            raise ValueError('Scenario must have at least one step')
        
        if not self.name.strip():
            raise ValueError('Scenario name cannot be empty')
        self.name = self.name.strip()


@dataclass
class TestSuite:
    """Model for a complete test suite containing multiple scenarios."""
    
    test_suite: str
    scenarios: List[TestScenario]
    description: str = ""
    base_url: str = "http://localhost:8000"
    
    def __post_init__(self):
        """Validate test suite configuration after initialization."""
        if not self.scenarios:
            raise ValueError('Test suite must have at least one scenario')
        
        if not self.test_suite.strip():
            raise ValueError('Test suite name cannot be empty')
        self.test_suite = self.test_suite.strip()
        
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        self.base_url = self.base_url.rstrip('/')
    
    @classmethod
    def load(cls, file_path: str) -> 'TestSuite':
        """
        Load test suite from JSON file.
        
        Args:
            file_path: Path to test cases JSON file
            
        Returns:
            TestSuite instance loaded from file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file contains invalid data
        """
        import json
        from pathlib import Path
        
        test_file = Path(file_path)
        if not test_file.exists():
            raise FileNotFoundError(f"Test cases file not found: {file_path}")
        
        try:
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            # Parse scenarios
            scenarios = []
            for scenario_data in data.get('scenarios', []):
                steps = []
                for step_data in scenario_data.get('steps', []):
                    # Convert method string to enum
                    method = HttpMethod(step_data.get('method', 'GET'))
                    
                    # Convert response type string to enum if present
                    response_type = None
                    if 'expected_response_type' in step_data:
                        response_type = ResponseType(step_data['expected_response_type'])
                    
                    step = TestStep(
                        name=step_data['name'],
                        method=method,
                        endpoint=step_data['endpoint'],
                        headers=step_data.get('headers'),
                        body=step_data.get('body'),
                        expected_status=step_data.get('expected_status', 200),
                        expected_response=step_data.get('expected_response'),
                        expected_response_contains=step_data.get('expected_response_contains'),
                        expected_response_type=response_type,
                        expected_items=step_data.get('expected_items'),
                        expected_min_items=step_data.get('expected_min_items'),
                        save_response_field=step_data.get('save_response_field')
                    )
                    steps.append(step)
                
                scenario = TestScenario(
                    name=scenario_data['name'],
                    description=scenario_data.get('description', ''),
                    steps=steps
                )
                scenarios.append(scenario)
            
            return cls(
                test_suite=data.get('test_suite', 'Unknown Test Suite'),
                description=data.get('description', ''),
                base_url=data.get('base_url', 'http://localhost:8000'),
                scenarios=scenarios
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in test cases file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading test cases: {e}")
    
    def save(self, file_path: str) -> None:
        """
        Save test suite to JSON file.
        
        Args:
            file_path: Path to save test cases file
        """
        import json
        from pathlib import Path
        
        save_path = Path(file_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dictionary format
        data = {
            "test_suite": self.test_suite,
            "description": self.description,
            "base_url": self.base_url,
            "scenarios": []
        }
        
        for scenario in self.scenarios:
            scenario_data = {
                "name": scenario.name,
                "description": scenario.description,
                "steps": []
            }
            
            for step in scenario.steps:
                step_data = {
                    "name": step.name,
                    "method": step.method.value,
                    "endpoint": step.endpoint,
                    "expected_status": step.expected_status
                }
                
                # Add optional fields if they exist
                if step.headers is not None:
                    step_data["headers"] = step.headers
                if step.body is not None:
                    step_data["body"] = step.body
                if step.expected_response is not None:
                    step_data["expected_response"] = step.expected_response
                if step.expected_response_contains is not None:
                    step_data["expected_response_contains"] = step.expected_response_contains
                if step.expected_response_type is not None:
                    step_data["expected_response_type"] = step.expected_response_type.value
                if step.expected_items is not None:
                    step_data["expected_items"] = step.expected_items
                if step.expected_min_items is not None:
                    step_data["expected_min_items"] = step.expected_min_items
                if step.save_response_field is not None:
                    step_data["save_response_field"] = step.save_response_field
                
                scenario_data["steps"].append(step_data)
            
            data["scenarios"].append(scenario_data)
        
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def to_dict(self) -> dict:
        """Convert test suite to dictionary format."""
        return {
            "test_suite": self.test_suite,
            "description": self.description,
            "base_url": self.base_url,
            "scenarios": [
                {
                    "name": scenario.name,
                    "description": scenario.description,
                    "steps": [
                        {
                            "name": step.name,
                            "method": step.method.value,
                            "endpoint": step.endpoint,
                            "expected_status": step.expected_status,
                            **({k: v for k, v in {
                                "headers": step.headers,
                                "body": step.body,
                                "expected_response": step.expected_response,
                                "expected_response_contains": step.expected_response_contains,
                                "expected_response_type": step.expected_response_type.value if step.expected_response_type else None,
                                "expected_items": step.expected_items,
                                "expected_min_items": step.expected_min_items,
                                "save_response_field": step.save_response_field
                            }.items() if v is not None})
                        }
                        for step in scenario.steps
                    ]
                }
                for scenario in self.scenarios
            ]
        }