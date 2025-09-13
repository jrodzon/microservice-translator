"""
CLI commands for project translation functionality.

This module provides CLI commands for translating projects using
various LLM providers.
"""

import os
import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..translation import ProjectTranslator
from ..translation.llm_providers import OpenAIProvider
from ..utils import get_logger, Config

console = Console()
logger = get_logger("translation_commands")


@click.group()
def translate():
    """Project translation commands."""
    pass


@translate.command()
@click.option('--source', '-s', required=True, help='Source project path')
@click.option('--output', '-o', required=True, help='Output project path')
@click.option('--from-lang', '-f', required=True, help='Source programming language')
@click.option('--to-lang', '-t', required=True, help='Target programming language')
@click.option('--max-iterations', type=int, help='Maximum translation iterations (overrides config)')
@click.option('--save-conversation', type=bool, help='Save conversation to file (overrides config)')
@click.option('--conversation-file', help='Conversation file name (overrides config)')
@click.option('--config', help='Configuration file path')
@click.pass_context
def translate_project(ctx, source: str, output: str, from_lang: str, to_lang: str,
                     max_iterations: Optional[int], save_conversation: Optional[bool],
                     conversation_file: Optional[str], config: Optional[str]):
    """Translate a project from one programming language to another."""
    
    try:
        # Get configuration from context or load from file
        if config:
            app_config = Config.load(config)
        else:
            app_config = ctx.obj.get('config') or Config.load()
        
        # Get LLM provider and translation configuration
        llm_config = app_config.llm_provider
        translation_config = app_config.translation
        
        # Override config with command-line options if provided
        if max_iterations is not None:
            translation_config.max_iterations = max_iterations
        if save_conversation is not None:
            translation_config.save_conversation = save_conversation
        if conversation_file is not None:
            translation_config.conversation_file = conversation_file
        
        # Validate API key
        if not llm_config.api_key:
            console.print("[red]❌ API key is required. Please configure it in config.json or use --config option.[/red]")
            console.print("[yellow]💡 You can set the API key using: python -m project_translator translate configure[/yellow]")
            return
        
        # Validate paths
        source_path = Path(source).resolve()
        if not source_path.exists():
            console.print(f"[red]❌ Source path does not exist: {source_path}[/red]")
            return
        
        output_path = Path(output).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize LLM provider based on configuration
        if llm_config.provider.lower() == 'openai':
            llm_provider = OpenAIProvider(
                model=llm_config.model,
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                max_tokens=llm_config.max_tokens,
                temperature=llm_config.temperature
            )
        else:
            console.print(f"[red]❌ Unsupported provider: {llm_config.provider}[/red]")
            return
        
        # Create translator
        translator = ProjectTranslator(llm_provider, from_lang, to_lang)
        
        # Display configuration
        config_panel = Panel(
            f"[bold]Source Language:[/bold] {from_lang}\n"
            f"[bold]Target Language:[/bold] {to_lang}\n"
            f"[bold]Provider:[/bold] {llm_config.provider}\n"
            f"[bold]Model:[/bold] {llm_config.model}\n"
            f"[bold]Max Tokens:[/bold] {llm_config.max_tokens}\n"
            f"[bold]Temperature:[/bold] {llm_config.temperature}\n"
            f"[bold]Max Iterations:[/bold] {translation_config.max_iterations}\n"
            f"[bold]Save Conversation:[/bold] {translation_config.save_conversation}\n"
            f"[bold]Conversation File:[/bold] {translation_config.conversation_file}\n"
            f"[bold]Source Path:[/bold] {source_path}\n"
            f"[bold]Output Path:[/bold] {output_path}",
            title="Translation Configuration",
            border_style="blue"
        )
        console.print(config_panel)
        
        # Start translation
        result = translator.translate_project(
            str(source_path), 
            str(output_path), 
            max_iterations=translation_config.max_iterations,
            save_conversation=translation_config.save_conversation,
            conversation_file=translation_config.conversation_file,
            conversation_dir=translation_config.conversation_dir,
            auto_save_interval=translation_config.auto_save_interval,
            retry_on_error=translation_config.retry_on_error,
            max_retries=translation_config.max_retries,
            retry_delay=translation_config.retry_delay
        )
        
        # Display results
        if result["success"]:
            console.print("[green]✅ Translation completed successfully![/green]")
            
            # Display statistics
            stats = result.get("stats", {})
            stats_table = Table(title="Translation Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green")
            
            stats_table.add_row("Files Read", str(stats.get("files_read", 0)))
            stats_table.add_row("Files Written", str(stats.get("files_written", 0)))
            stats_table.add_row("Tool Calls", str(stats.get("tool_calls", 0)))
            stats_table.add_row("Errors", str(stats.get("errors", 0)))
            
            if stats.get("start_time") and stats.get("end_time"):
                duration = stats["end_time"] - stats["start_time"]
                stats_table.add_row("Duration", f"{duration:.2f} seconds")
            
            console.print(stats_table)
            
        else:
            console.print(f"[red]❌ Translation failed: {result.get('error', 'Unknown error')}[/red]")
        
        # Save conversation if requested
        if save_conversation:
            if translator.save_conversation(save_conversation):
                console.print(f"[green]💾 Conversation saved to: {save_conversation}[/green]")
            else:
                console.print(f"[red]❌ Failed to save conversation to: {save_conversation}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Error during translation: {str(e)}[/red]")
        logger.error(f"Translation error: {e}")


@translate.command()
@click.option('--provider', '-p', default='openai', help='LLM provider to list models for')
def list_models(provider: str):
    """List available models for a provider."""
    
    try:
        if provider.lower() == 'openai':
            provider_instance = OpenAIProvider()
            models = provider_instance.get_available_models()
            
            models_table = Table(title=f"Available {provider.title()} Models")
            models_table.add_column("Model Name", style="cyan")
            models_table.add_column("Description", style="green")
            
            for model in models:
                description = provider_instance.get_model_description(model)
                models_table.add_row(model, description)
            
            console.print(models_table)
            
        else:
            console.print(f"[red]❌ Unsupported provider: {provider}[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Error listing models: {str(e)}[/red]")


@translate.command()
@click.option('--provider', '-p', help='LLM provider to configure')
@click.option('--api-key', '-k', help='API key')
@click.option('--model', '-m', help='Default model')
@click.option('--max-tokens', help='Maximum tokens per request')
@click.option('--temperature', help='Temperature for generation')
@click.option('--max-iterations', help='Maximum translation iterations')
@click.option('--save-conversation/--no-save-conversation', help='Save conversation to file')
@click.option('--conversation-file', help='Conversation file name')
@click.option('--conversation-dir', help='Conversation directory')
@click.option('--auto-save-interval', help='Auto-save interval (iterations)')
@click.option('--config', '-c', default='config.json', help='Configuration file path')
@click.pass_context
def configure(ctx, provider: Optional[str], api_key: Optional[str], model: Optional[str], 
              max_tokens: Optional[str], temperature: Optional[str], max_iterations: Optional[str],
              save_conversation: Optional[bool], conversation_file: Optional[str], 
              conversation_dir: Optional[str], auto_save_interval: Optional[str], config: str):
    """Configure LLM provider settings in config.json."""
    
    try:
        # Load existing configuration
        app_config = Config.load(config)
        
        # Update LLM provider configuration if provided
        if provider:
            app_config.llm_provider.provider = provider
        if api_key is not None:  # Allow empty string to clear the key
            app_config.llm_provider.api_key = api_key if api_key else None
        if model:
            app_config.llm_provider.model = model
        if max_tokens:
            app_config.llm_provider.max_tokens = int(max_tokens)
        if temperature:
            app_config.llm_provider.temperature = float(temperature)
        
        # Update translation configuration if provided
        if max_iterations:
            app_config.translation.max_iterations = int(max_iterations)
        if save_conversation is not None:
            app_config.translation.save_conversation = save_conversation
        if conversation_file:
            app_config.translation.conversation_file = conversation_file
        if conversation_dir:
            app_config.translation.conversation_dir = conversation_dir
        if auto_save_interval:
            app_config.translation.auto_save_interval = int(auto_save_interval)
        
        # Save updated configuration
        app_config.save(config)
        
        console.print(f"[green]✅ Configuration saved to: {config}[/green]")
        
        # Display configuration
        llm_config = app_config.llm_provider
        translation_config = app_config.translation
        
        config_panel = Panel(
            f"[bold]LLM Provider Configuration:[/bold]\n"
            f"Provider: {llm_config.provider}\n"
            f"Model: {llm_config.model}\n"
            f"API Key: {'*' * 10 if llm_config.api_key else 'Not set'}\n"
            f"Max Tokens: {llm_config.max_tokens}\n"
            f"Temperature: {llm_config.temperature}\n"
            f"Timeout: {llm_config.timeout}s\n\n"
            f"[bold]Translation Configuration:[/bold]\n"
            f"Max Iterations: {translation_config.max_iterations}\n"
            f"Save Conversation: {translation_config.save_conversation}\n"
            f"Conversation File: {translation_config.conversation_file}\n"
            f"Conversation Dir: {translation_config.conversation_dir}\n"
            f"Auto Save Interval: {translation_config.auto_save_interval}\n"
            f"Retry on Error: {translation_config.retry_on_error}\n"
            f"Max Retries: {translation_config.max_retries}\n"
            f"Retry Delay: {translation_config.retry_delay}s",
            title="Configuration",
            border_style="green"
        )
        console.print(config_panel)
        
    except Exception as e:
        console.print(f"[red]❌ Error configuring provider: {str(e)}[/red]")


@translate.command()
@click.option('--source', '-s', required=True, help='Source project path')
def analyze(source: str):
    """Analyze a project for translation."""
    
    try:
        from ..translation.tools.project_analysis import ProjectAnalysisTool
        
        source_path = Path(source).resolve()
        if not source_path.exists():
            console.print(f"[red]❌ Source path does not exist: {source_path}[/red]")
            return
        
        analyzer = ProjectAnalysisTool(str(source_path))
        result = analyzer.analyze_project()
        
        if result["success"]:
            analysis = result["analysis"]
            
            # Display project analysis
            console.print("[green]✅ Project analysis completed![/green]")
            
            # Project type
            console.print(f"[bold]Project Type:[/bold] {analysis['project_type']}")
            
            # Main files
            if analysis["main_files"]:
                console.print("\n[bold]Main Files:[/bold]")
                for file_info in analysis["main_files"]:
                    console.print(f"  • {file_info['name']}")
            
            # Dependencies
            if analysis["dependencies"]:
                console.print("\n[bold]Dependencies:[/bold]")
                for lang, deps in analysis["dependencies"].items():
                    console.print(f"  {lang.title()}: {', '.join(deps[:5])}{'...' if len(deps) > 5 else ''}")
            
            # Docker configuration
            docker_config = analysis["docker_config"]
            console.print(f"\n[bold]Docker Configuration:[/bold]")
            console.print(f"  • Has Dockerfile: {docker_config['has_dockerfile']}")
            console.print(f"  • Has Docker Compose: {docker_config['has_docker_compose']}")
            if docker_config["port"]:
                console.print(f"  • Port: {docker_config['port']}")
            if docker_config["base_image"]:
                console.print(f"  • Base Image: {docker_config['base_image']}")
            
            # API endpoints
            if analysis["api_endpoints"]:
                console.print(f"\n[bold]API Endpoints:[/bold]")
                for endpoint in analysis["api_endpoints"]:
                    console.print(f"  • {endpoint['file']} ({endpoint['framework']})")
            
        else:
            console.print(f"[red]❌ Analysis failed: {result.get('error', 'Unknown error')}[/red]")
    
    except Exception as e:
        console.print(f"[red]❌ Error analyzing project: {str(e)}[/red]")


@translate.command()
def providers():
    """List available LLM providers."""
    
    providers_table = Table(title="Available LLM Providers")
    providers_table.add_column("Provider", style="cyan")
    providers_table.add_column("Status", style="green")
    providers_table.add_column("Description", style="white")
    
    # OpenAI
    try:
        import openai
        providers_table.add_row("OpenAI", "✅ Available", "GPT-4, GPT-3.5 models")
    except ImportError:
        providers_table.add_row("OpenAI", "❌ Not Installed", "Install with: pip install openai")
    
    # Anthropic (placeholder)
    providers_table.add_row("Anthropic", "🚧 Coming Soon", "Claude models")
    
    # Local (placeholder)
    providers_table.add_row("Local", "🚧 Coming Soon", "Ollama, local models")
    
    console.print(providers_table)
