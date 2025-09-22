"""
Batch translator for efficient project translation.

This module implements a batch translator that translates entire projects
in one request to reduce token usage and improve efficiency.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .llm_providers.base import BaseLLMProvider
from .protocols.batch import BatchTranslationProtocol, BatchTranslationRequest, BatchTranslationResponse
from .protocols.mcp import MCPMessage, MCPMessageType
from .tools.file_operations import FileOperationsTool
from .retry_mechanism import RetryMechanism
from project_translator.utils import get_logger, error_with_stacktrace

console = Console()
logger = get_logger("batch_translator")


class BatchProjectTranslator:
    """Batch translator for efficient project translation."""
    
    def __init__(self, llm_provider: BaseLLMProvider, source_lang: str, target_lang: str):
        """
        Initialize batch project translator.
        
        Args:
            llm_provider: LLM provider instance
            source_lang: Source programming language
            target_lang: Target programming language
        """
        self.llm_provider = llm_provider
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.batch_protocol = BatchTranslationProtocol()
        self.translation_stats = {
            "files_read": 0,
            "files_written": 0,
            "start_time": None,
            "end_time": None,
            "total_tokens": 0,
            "cost_estimate": 0.0,
            "translation_method": "batch"
        }
        
        logger.info(f"BatchProjectTranslator initialized: {source_lang} -> {target_lang}")
    
    def _send_batch_request(self, batch_request: BatchTranslationRequest) -> str:
        """
        Send batch translation request to LLM provider.
        
        Args:
            batch_request: BatchTranslationRequest object
            
        Returns:
            Response text from LLM
        """
        try:
            # Format the request as a single message
            request_text = self._format_batch_request(batch_request)
            
            messages = [
                MCPMessage(
                    role=MCPMessageType.SYSTEM,
                    content=batch_request.translation_instructions,
                    id="batch_system"
                ),
                MCPMessage(
                    role=MCPMessageType.USER,
                    content=request_text,
                    id="batch_request"
                )
            ]
            
            response = self.llm_provider.send_message(messages)
            
            # Extract response text
            response_text = ""
            for message in response.messages:
                if message.role == MCPMessageType.ASSISTANT:
                    response_text += str(message.content)
            
            return response_text
                
        except Exception as e:
            error_msg = f"Error sending batch request: {str(e)}"
            error_with_stacktrace(error_msg, e)
            raise
    
    def _format_batch_request(self, batch_request: BatchTranslationRequest) -> str:
        """
        Format batch request for LLM.
        
        Args:
            batch_request: BatchTranslationRequest object
            
        Returns:
            Formatted request text
        """
        import json
        
        formatted = f"Please translate this project from {batch_request.source_language} to {batch_request.target_language}:\n\n"
        formatted += f"PROJECT FILES ({len(batch_request.project_files)} files):\n\n"
        
        for i, file_data in enumerate(batch_request.project_files, 1):
            formatted += f"--- FILE {i}: {file_data.path} ({file_data.file_type}) ---\n"
            formatted += file_data.content
            formatted += "\n\n"
        
        return formatted
    
    def translate_project(self, source_path: str, output_path: str, 
                         max_iterations: int = 50,
                         save_conversation: bool = True,
                         conversation_file: str = "batch_translation_conversation.json",
                         conversation_dir: str = "conversations",
                         auto_save_interval: int = 5,
                         retry_on_error: bool = True,
                         max_retries: int = 3,
                         retry_delay: float = 1.0,
                         test_cases_path: Optional[str] = None,
                         enable_auto_testing: bool = True) -> Dict[str, Any]:
        """
        Translate a project using batch translation with optional automatic testing and retry.
        
        Args:
            source_path: Path to source project
            output_path: Path to output project
            max_iterations: Maximum number of translation iterations (not used in batch mode)
            save_conversation: Whether to save conversation to file
            conversation_file: Name of conversation file
            conversation_dir: Directory to save conversations
            auto_save_interval: Auto-save interval (not used in batch mode)
            retry_on_error: Whether to retry on errors
            max_retries: Maximum number of retries
            retry_delay: Delay between retries (not used in batch mode)
            test_cases_path: Path to test cases file for automatic testing
            enable_auto_testing: Whether to enable automatic testing and retry
            
        Returns:
            Dictionary with translation results
        """
        self.translation_stats["start_time"] = time.time()
        
        try:
            console.print(f"[blue]🚀 Starting batch project translation: {self.source_lang} -> {self.target_lang}[/blue]")
            console.print(f"[blue]📁 Source: {source_path}[/blue]")
            console.print(f"[blue]📁 Output: {output_path}[/blue]")
            
            # Validate LLM provider
            if not self.llm_provider.validate_configuration():
                raise ValueError("LLM provider configuration is invalid")
            
            # Check if we should use retry mechanism with testing
            if enable_auto_testing and retry_on_error and test_cases_path:
                console.print(f"[blue]🔄 Using retry mechanism with automatic testing[/blue]")
                console.print(f"[blue]🧪 Test cases: {test_cases_path}[/blue]")
                console.print(f"[blue]🔄 Max retries: {max_retries}[/blue]")
                
                # Use retry mechanism
                retry_mechanism = RetryMechanism(
                    self.llm_provider, 
                    self.source_lang, 
                    self.target_lang,
                    max_retries=max_retries,
                    test_cases_path=test_cases_path
                )
                
                result = retry_mechanism.translate_with_retry(
                    source_path, 
                    output_path,
                    save_conversation=save_conversation,
                    conversation_file=conversation_file,
                    conversation_dir=conversation_dir
                )
                
                # Update stats
                self.translation_stats["end_time"] = time.time()
                if "stats" not in result:
                    result["stats"] = self.translation_stats
                
                return result
            
            else:
                # Use original batch translation without retry mechanism
                console.print(f"[blue]📝 Using standard batch translation[/blue]")
                
                # Initialize tools
                file_ops = FileOperationsTool(source_path, output_path)
                
                # Perform batch translation
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    TimeElapsedColumn(),
                    console=console
                ) as progress:
                    task = progress.add_task("Translating project...", total=None)
                    
                    # Create batch translation request
                    batch_request = self.batch_protocol.create_translation_request(
                        source_path, self.source_lang, self.target_lang
                    )
                    
                    self.translation_stats["files_read"] = len(batch_request.project_files)
                    
                    # Send single request to LLM
                    response_text = self._send_batch_request(batch_request)
                    
                    # Parse response
                    batch_response = self.batch_protocol.parse_translation_response(response_text)
                
                # Write translated files
                console.print(f"[blue]📝 Writing {len(batch_response.translated_files)} translated files...[/blue]")
                
                written_files = 0
                for translated_file in batch_response.translated_files:
                    try:
                        # Use the path from translation
                        output_file_path = Path(output_path) / translated_file.path
                        
                        # Ensure parent directory exists
                        output_file_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write file
                        with open(output_file_path, 'w', encoding='utf-8') as f:
                            f.write(translated_file.content)
                        
                        written_files += 1
                        console.print(f"[green]✅ Written: {output_file_path.relative_to(Path(output_path))}[/green]")
                        
                    except Exception as e:
                        error_msg = f"Error writing file {translated_file.path}: {str(e)}"
                        error_with_stacktrace(error_msg, e)
                        console.print(f"[red]❌ {error_msg}[/red]")
                
                self.translation_stats["files_written"] = written_files
                self.translation_stats["end_time"] = time.time()
                
                # Create result
                result = {
                    "success": True,
                    "message": "Batch translation completed successfully",
                    "translation_summary": batch_response.translation_summary,
                    "warnings": batch_response.warnings,
                    "files_translated": len(batch_response.translated_files),
                    "files_written": written_files,
                    "stats": self.translation_stats
                }
                
                # Save conversation if enabled
                if save_conversation:
                    conversation_path = self._setup_conversation_saving(
                        conversation_dir, conversation_file, source_path, output_path
                    )
                    self.save_conversation(conversation_path, batch_response, result)
                    console.print(f"[green]💾 Conversation saved to: {conversation_path}[/green]")
                
                console.print(f"[green]✅ Batch translation completed successfully![/green]")
                console.print(f"[green]📊 Files processed: {self.translation_stats['files_read']} read, {written_files} written[/green]")
                console.print(f"[green]📝 Summary: {batch_response.translation_summary}[/green]")
                
                if batch_response.warnings:
                    console.print(f"[yellow]⚠️  Warnings: {len(batch_response.warnings)} warnings generated[/yellow]")
                    for warning in batch_response.warnings:
                        console.print(f"[yellow]   - {warning}[/yellow]")
                
                return result
            
        except Exception as e:
            error_msg = f"Batch translation failed: {str(e)}"
            error_with_stacktrace(error_msg, e)
            console.print(f"[red]❌ {error_msg}[/red]")
            
            self.translation_stats["end_time"] = time.time()
            return {
                "success": False,
                "error": error_msg,
                "stats": self.translation_stats
            }
    
    def get_translation_summary(self) -> Dict[str, Any]:
        """Get summary of translation process."""
        duration = None
        if self.translation_stats["start_time"] and self.translation_stats["end_time"]:
            duration = self.translation_stats["end_time"] - self.translation_stats["start_time"]
        
        return {
            "source_language": self.source_lang,
            "target_language": self.target_lang,
            "duration_seconds": duration,
            "files_processed": self.translation_stats["files_read"],
            "files_created": self.translation_stats["files_written"],
            "total_tokens": self.translation_stats["total_tokens"],
            "cost_estimate": self.translation_stats["cost_estimate"]
        }
    
    def _setup_conversation_saving(self, conversation_dir: str, conversation_file: str, 
                                  source_path: str, output_path: str) -> str:
        """
        Setup conversation saving directory and file.
        
        Args:
            conversation_dir: Directory to save conversations
            conversation_file: Name of conversation file
            source_path: Source project path
            output_path: Output project path
            
        Returns:
            Path to conversation file
        """
        from datetime import datetime
        
        # Create conversation directory
        conv_dir = Path(conversation_dir)
        conv_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate conversation filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_path).name
        target_name = Path(output_path).name
        
        if conversation_file == "batch_translation_conversation.json":
            # Use default naming with timestamp
            filename = f"batch_translation_{source_name}_to_{target_name}_{timestamp}.json"
        else:
            # Use provided filename
            filename = conversation_file
            
        conversation_path = conv_dir / filename
        
        # Save initial conversation metadata
        initial_data = {
            "metadata": {
                "translation_type": "batch",
                "source_language": self.source_lang,
                "target_language": self.target_lang,
                "source_path": str(source_path),
                "output_path": str(output_path),
                "start_time": datetime.now().isoformat(),
                "batch_provider": self.llm_provider.get_provider_info(),
                "translation_stats": self.translation_stats
            },
            "conversation": []
        }
        
        with open(conversation_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Conversation saving setup: {conversation_path}")
        return str(conversation_path)
    
    def save_conversation(self, file_path: str, batch_response: BatchTranslationResponse = None, 
                         result: Dict[str, Any] = None) -> bool:
        """Save conversation history to file."""
        try:
            conversation_data = {
                "translation_summary": self.get_translation_summary(),
                "llm_provider": self.llm_provider.get_provider_info()
            }
            
            if batch_response:
                conversation_data["batch_response"] = batch_response.to_dict()
            
            if result:
                conversation_data["translation_result"] = result
            
            if hasattr(self.llm_provider, 'raw_responses'):
                conversation_data["raw_responses"] = self.llm_provider.raw_responses
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversation saved to: {file_path}")
            return True
            
        except Exception as e:
            error_with_stacktrace("Error saving conversation", e)
            return False
