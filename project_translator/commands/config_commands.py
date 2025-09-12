"""
Configuration management commands for Project Translator.

This module contains commands for managing configuration files.
"""

import click
import json
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..utils import Config

console = Console()


@click.group()
def config_group():
    """Configuration management commands."""
    pass


@config_group.command()
@click.option('--config', '-c', help='Configuration file path')
def show(config: str):
    """Display current configuration."""
    config_obj = Config.load(config)
    
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Config File", config_obj.config_file)
    table.add_row("Base URL", config_obj.base_url)
    table.add_row("Timeout", f"{config_obj.timeout}s")
    table.add_row("Startup Timeout", f"{config_obj.startup_timeout}s")
    table.add_row("Shutdown Timeout", f"{config_obj.shutdown_timeout}s")
    table.add_row("Check Interval", f"{config_obj.check_interval}s")
    table.add_row("Output File", config_obj.output_file)
    
    console.print(table)


@config_group.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--base-url', help='Set base URL')
@click.option('--timeout', type=int, help='Set timeout in seconds')
@click.option('--startup-timeout', type=int, help='Set startup timeout in seconds')
@click.option('--shutdown-timeout', type=int, help='Set shutdown timeout in seconds')
@click.option('--check-interval', type=int, help='Set check interval in seconds')
@click.option('--output-file', help='Set output file path')
def set(config: str, base_url: str, timeout: int, startup_timeout: int, 
        shutdown_timeout: int, check_interval: int, output_file: str):
    """Set configuration values."""
    config_obj = Config.load(config)
    
    # Update configuration with provided values
    updates = {}
    if base_url is not None:
        updates['base_url'] = base_url
    if timeout is not None:
        updates['timeout'] = timeout
    if startup_timeout is not None:
        updates['startup_timeout'] = startup_timeout
    if shutdown_timeout is not None:
        updates['shutdown_timeout'] = shutdown_timeout
    if check_interval is not None:
        updates['check_interval'] = check_interval
    if output_file is not None:
        updates['output_file'] = output_file
    
    if not updates:
        console.print("[yellow]No configuration values provided to update[/yellow]")
        return
    
    # Create updated configuration
    updated_config = config_obj.update(**updates)
    
    # Save updated configuration
    if updated_config.save(config):
        console.print("[green]Configuration updated successfully[/green]")
        
        # Show updated values
        for key, value in updates.items():
            console.print(f"[green]✓[/green] {key}: {value}")
    else:
        console.print("[red]Failed to save configuration[/red]")


@config_group.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--force', '-f', is_flag=True, help='Force reset without confirmation')
def reset(config: str, force: bool):
    """Reset configuration to default values."""
    if not force:
        if not click.confirm("Are you sure you want to reset the configuration to default values?"):
            console.print("[yellow]Configuration reset cancelled[/yellow]")
            return
    
    # Create default configuration
    default_config = Config()
    default_config.config_file = config or "config.json"
    
    # Save default configuration
    if default_config.save(config):
        console.print("[green]Configuration reset to default values[/green]")
    else:
        console.print("[red]Failed to reset configuration[/red]")


@config_group.command()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--output', '-o', help='Output file path')
def export(config: str, output: str):
    """Export configuration to a file."""
    config_obj = Config.load(config)
    
    if output is None:
        output = f"config_export_{config_obj.config_file}"
    
    try:
        with open(output, 'w') as f:
            json.dump(config_obj.to_dict(), f, indent=2)
        
        console.print(f"[green]Configuration exported to: {output}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to export configuration: {e}[/red]")


@config_group.command()
@click.option('--input', '-i', required=True, help='Input configuration file path')
@click.option('--config', '-c', help='Target configuration file path')
@click.option('--force', '-f', is_flag=True, help='Force import without confirmation')
def import_config(input: str, config: str, force: bool):
    """Import configuration from a file."""
    input_path = Path(input)
    
    if not input_path.exists():
        console.print(f"[red]Input file does not exist: {input}[/red]")
        return
    
    if not force:
        if not click.confirm(f"Are you sure you want to import configuration from {input}?"):
            console.print("[yellow]Configuration import cancelled[/yellow]")
            return
    
    try:
        with open(input_path, 'r') as f:
            config_data = json.load(f)
        
        # Create configuration from imported data
        imported_config = Config(
            base_url=config_data.get("base_url", Config().base_url),
            timeout=config_data.get("timeout", Config().timeout),
            startup_timeout=config_data.get("startup_timeout", Config().startup_timeout),
            shutdown_timeout=config_data.get("shutdown_timeout", Config().shutdown_timeout),
            check_interval=config_data.get("check_interval", Config().check_interval),
            output_file=config_data.get("output_file", Config().output_file),
            config_file=config or "config.json"
        )
        
        # Save imported configuration
        if imported_config.save(config):
            console.print("[green]Configuration imported successfully[/green]")
        else:
            console.print("[red]Failed to save imported configuration[/red]")
            
    except Exception as e:
        console.print(f"[red]Failed to import configuration: {e}[/red]")
