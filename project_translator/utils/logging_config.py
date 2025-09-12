"""
Logging configuration module for Project Translator.

This module provides centralized logging configuration with file output
and structured logging for better debugging and monitoring.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console


class ProjectTranslatorLogger:
    """Centralized logging configuration for Project Translator."""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None, 
                 max_file_size: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        Initialize the logger configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file. If None, uses default location
            max_file_size: Maximum size of log file before rotation (bytes)
            backup_count: Number of backup files to keep
        """
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.log_file = log_file or self._get_default_log_file()
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.console = Console()
        
        self._setup_logging()
    
    def _get_default_log_file(self) -> str:
        """Get default log file path."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(log_dir / f"project_translator_{timestamp}.log")
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create logger
        self.logger = logging.getLogger("project_translator")
        self.logger.setLevel(self.log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # Console handler with Rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=True,
            markup=True
        )
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(simple_formatter)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(detailed_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance.
        
        Args:
            name: Logger name. If None, returns the main logger
            
        Returns:
            Logger instance
        """
        if name:
            return self.logger.getChild(name)
        return self.logger
    
    def set_level(self, level: str):
        """
        Set logging level.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(self.log_level)
        
        # Update console handler level
        for handler in self.logger.handlers:
            if isinstance(handler, RichHandler):
                handler.setLevel(self.log_level)
    
    def get_log_file_path(self) -> str:
        """Get the current log file path."""
        return self.log_file
    
    def log_test_start(self, test_project: str, test_cases: str):
        """Log test execution start."""
        self.logger.info("=" * 60)
        self.logger.info("Starting test execution")
        self.logger.info(f"Test Project: {test_project}")
        self.logger.info(f"Test Cases: {test_cases}")
        self.logger.info(f"Log File: {self.log_file}")
        self.logger.info("=" * 60)
    
    def log_test_end(self, success: bool, total_scenarios: int, passed_scenarios: int):
        """Log test execution end."""
        self.logger.info("=" * 60)
        self.logger.info("Test execution completed")
        self.logger.info(f"Overall Success: {success}")
        self.logger.info(f"Total Scenarios: {total_scenarios}")
        self.logger.info(f"Passed Scenarios: {passed_scenarios}")
        self.logger.info(f"Failed Scenarios: {total_scenarios - passed_scenarios}")
        self.logger.info("=" * 60)
    
    def log_scenario_start(self, scenario_name: str, scenario_description: str = ""):
        """Log scenario execution start."""
        self.logger.info(f"Starting scenario: {scenario_name}")
        if scenario_description:
            self.logger.info(f"Description: {scenario_description}")
    
    def log_scenario_end(self, scenario_name: str, success: bool, total_steps: int, passed_steps: int):
        """Log scenario execution end."""
        status = "PASSED" if success else "FAILED"
        self.logger.info(f"Scenario '{scenario_name}' {status} ({passed_steps}/{total_steps} steps)")
    
    def log_step_result(self, step_name: str, success: bool, error: Optional[str] = None, 
                       status_code: Optional[int] = None, expected_status: Optional[int] = None):
        """Log individual step result."""
        status = "PASSED" if success else "FAILED"
        self.logger.info(f"  Step '{step_name}': {status}")
        
        if not success:
            if error:
                self.logger.error(f"    Error: {error}")
            if status_code is not None and expected_status is not None:
                self.logger.error(f"    Status Code: {status_code} (expected: {expected_status})")
    
    def log_service_event(self, event: str, details: str = ""):
        """Log service-related events."""
        self.logger.info(f"Service Event: {event}")
        if details:
            self.logger.info(f"  Details: {details}")
    
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with full traceback."""
        if context:
            self.logger.error(f"Error in {context}: {str(error)}")
        else:
            self.logger.error(f"Error: {str(error)}")
        
        # Log full traceback at DEBUG level
        self.logger.debug("Full traceback:", exc_info=True)


# Global logger instance
_logger_instance: Optional[ProjectTranslatorLogger] = None


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> ProjectTranslatorLogger:
    """
    Set up global logging configuration.
    
    Args:
        log_level: Logging level
        log_file: Path to log file
        
    Returns:
        Logger instance
    """
    global _logger_instance
    _logger_instance = ProjectTranslatorLogger(log_level, log_file)
    return _logger_instance


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if _logger_instance is None:
        setup_logging()
    
    return _logger_instance.get_logger(name)


def get_log_file_path() -> str:
    """Get the current log file path."""
    if _logger_instance is None:
        setup_logging()
    
    return _logger_instance.get_log_file_path()
