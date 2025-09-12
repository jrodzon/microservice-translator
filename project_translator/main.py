"""
Main entry point for the Project Translator application.

This module provides the main CLI interface and command routing.
"""

import click
from rich.console import Console
from rich.panel import Panel

from .commands import test_group, config_group
from .commands.translation_commands import translate
from .utils import Config, setup_logging, get_logger

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="Project Translator")
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """
    Project Translator - Automated testing for CRUD service translation.
    
    A modular application that provides automated testing capabilities
    for CRUD services with comprehensive reporting and service management.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Store configuration in context
    ctx.obj['config'] = Config.load(config)
    ctx.obj['verbose'] = verbose
    
    # Set up logging
    log_level = "DEBUG" if verbose else ctx.obj['config'].logging.level
    setup_logging(log_level, ctx.obj['config'].logging.file)
    
    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


# Add command groups
cli.add_command(test_group, name='test')
cli.add_command(config_group, name='config')
cli.add_command(translate, name='translate')


@cli.command()
def info():
    """Display application information."""
    console.print(Panel.fit(
        "[bold blue]Project Translator[/bold blue]\n"
        "Version: 1.0.0\n"
        "Description: Automated testing for CRUD service translation\n"
        "Author: Project Translator Team\n\n"
        "[bold]Features:[/bold]\n"
        "• Automated service management\n"
        "• Comprehensive test execution\n"
        "• Rich console output\n"
        "• Result persistence\n"
        "• Error handling\n"
        "• Modular design",
        title="Application Information"
    ))


@cli.command()
@click.pass_context
def config_info(ctx):
    """Display current configuration."""
    config = ctx.obj['config']
    
    console.print(Panel.fit(
        f"[bold]Application Configuration:[/bold]\n"
        f"Config File: {config.config_file}\n"
        f"Base URL: {config.base_url}\n"
        f"Timeout: {config.timeout}s\n"
        f"Startup Timeout: {config.startup_timeout}s\n"
        f"Shutdown Timeout: {config.shutdown_timeout}s\n"
        f"Check Interval: {config.check_interval}s\n"
        f"Output File: {config.output_file}\n\n"
        f"[bold]LLM Provider Configuration:[/bold]\n"
        f"Provider: {config.llm_provider.provider}\n"
        f"Model: {config.llm_provider.model}\n"
        f"API Key: {'*' * 10 if config.llm_provider.api_key else 'Not set'}\n"
        f"Max Tokens: {config.llm_provider.max_tokens}\n"
        f"Temperature: {config.llm_provider.temperature}\n"
        f"Timeout: {config.llm_provider.timeout}s\n\n"
        f"[bold]Translation Configuration:[/bold]\n"
        f"Max Iterations: {config.translation.max_iterations}\n"
        f"Save Conversation: {config.translation.save_conversation}\n"
        f"Conversation File: {config.translation.conversation_file}\n"
        f"Conversation Dir: {config.translation.conversation_dir}\n"
        f"Auto Save Interval: {config.translation.auto_save_interval}\n"
        f"Retry on Error: {config.translation.retry_on_error}\n"
        f"Max Retries: {config.translation.max_retries}\n"
        f"Retry Delay: {config.translation.retry_delay}s",
        title="Current Configuration"
    ))


if __name__ == "__main__":
    cli()
