"""
Service management module for handling test service lifecycle.

This module provides functionality to start, monitor, and stop test services
using their startup and shutdown scripts.
"""

import subprocess
import time
import requests
from pathlib import Path
from typing import Optional
from rich.console import Console

from ..utils import get_logger

console = Console()
logger = get_logger("service_manager")


class ServiceManager:
    """Manages the lifecycle of test services."""
    
    def __init__(self, test_project_path: str, scripts_dir: str, base_url: str = "http://localhost:8000"):
        """
        Initialize the service manager.
        
        Args:
            test_project_path: Path to the test project directory
            scripts_dir: Path to the directory containing start.sh and shutdown.sh scripts
            base_url: Base URL for the service health checks
        """
        self.test_project_path = Path(test_project_path).resolve()
        self.scripts_dir = Path(scripts_dir).resolve()
        self.base_url = base_url
        self.start_script = self.scripts_dir / "start.sh"
        self.shutdown_script = self.scripts_dir / "shutdown.sh"
    
    def validate_scripts(self) -> bool:
        """
        Validate that required scripts exist and are executable.
        
        Returns:
            True if scripts are valid, False otherwise
        """
        if not self.start_script.exists():
            console.print(f"[red]Error: start.sh not found: {self.start_script}[/red]")
            return False
            
        if not self.shutdown_script.exists():
            console.print(f"[red]Error: shutdown.sh not found: {self.shutdown_script}[/red]")
            return False
            
        if not self.start_script.stat().st_mode & 0o111:
            console.print(f"[red]Error: start.sh is not executable: {self.start_script}[/red]")
            return False
            
        if not self.shutdown_script.stat().st_mode & 0o111:
            console.print(f"[red]Error: shutdown.sh is not executable: {self.shutdown_script}[/red]")
            return False
            
        return True
    
    def start_service(self, timeout: int = 120) -> bool:
        """
        Start the test service using start.sh.
        
        Args:
            timeout: Maximum time to wait for startup script to complete
            
        Returns:
            True if service started successfully, False otherwise
        """
        console.print("[blue]Starting test service...[/blue]")
        
        try:
            result = subprocess.run(
                ["./start.sh"],
                cwd=self.scripts_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                console.print(f"[red]Failed to start service: {result.stderr}[/red]")
                return False
                
            console.print("[green]Service startup script completed[/green]")
            return True
            
        except subprocess.TimeoutExpired:
            console.print("[red]Service startup timed out[/red]")
            return False
        except Exception as e:
            console.print(f"[red]Error starting service: {e}[/red]")
            return False
    
    def wait_for_service(self, timeout: int = 60, check_interval: int = 2) -> bool:
        """
        Wait for service to become ready by checking health endpoint.
        
        Args:
            timeout: Maximum time to wait for service to be ready
            check_interval: Time between health checks
            
        Returns:
            True if service becomes ready, False if timeout
        """
        console.print("[blue]Waiting for service to be ready...[/blue]")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    console.print("[green]Service is ready![/green]")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(check_interval)
        
        console.print("[red]Service failed to become ready within timeout[/red]")
        return False
    
    def shutdown_service(self, timeout: int = 30) -> bool:
        """
        Shutdown the test service using shutdown.sh.
        
        Args:
            timeout: Maximum time to wait for shutdown script to complete
            
        Returns:
            True if shutdown completed (or was already stopped), False on critical error
        """
        console.print("[blue]Shutting down test service...[/blue]")
        
        try:
            result = subprocess.run(
                ["./shutdown.sh"],
                cwd=self.scripts_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                console.print("[green]Service shutdown completed[/green]")
                return True
            else:
                console.print(f"[yellow]Service shutdown warning: {result.stderr}[/yellow]")
                return True  # Still consider it successful
                
        except Exception as e:
            console.print(f"[yellow]Error during shutdown: {e}[/yellow]")
            return True  # Don't fail the test run for shutdown issues
    
    def is_service_healthy(self) -> bool:
        """
        Check if the service is currently healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
