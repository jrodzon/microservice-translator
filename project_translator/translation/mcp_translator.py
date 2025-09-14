"""
MCP translator for iterative project translation.

This module implements an MCP-based translator that uses the Model Context Protocol
for iterative communication with LLM providers during project translation.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .protocols.mcp import MCPProtocol, MCPMessage, MCPMessageType
from .llm_providers.base import BaseLLMProvider, LLMResponse
from .tools.file_operations import FileOperationsTool
from project_translator.utils import get_logger, error_with_stacktrace

console = Console()
logger = get_logger("mcp_translator")


class MCPProjectTranslator:
    """MCP-based translator for iterative project translation."""
    
    def __init__(self, llm_provider: BaseLLMProvider, source_lang: str, target_lang: str):
        """
        Initialize MCP project translator.
        
        Args:
            llm_provider: LLM provider instance
            source_lang: Source programming language
            target_lang: Target programming language
        """
        self.llm_provider = llm_provider
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.mcp_protocol = MCPProtocol()
        self.translation_stats = {
            "files_read": 0,
            "files_written": 0,
            "tool_calls": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None,
            "translation_method": "mcp"
        }
        
        logger.info(f"MCPProjectTranslator initialized: {source_lang} -> {target_lang}")
    
    def translate_project(self, source_path: str, output_path: str, 
                         max_iterations: int = 50,
                         save_conversation: bool = True,
                         conversation_file: str = "translation_conversation.json",
                         conversation_dir: str = "conversations",
                         auto_save_interval: int = 5,
                         retry_on_error: bool = True,
                         max_retries: int = 3,
                         retry_delay: float = 1.0) -> Dict[str, Any]:
        """
        Translate a project using MCP method.
        
        Args:
            source_path: Path to source project
            output_path: Path to output project
            max_iterations: Maximum number of translation iterations
            save_conversation: Whether to save conversation to file
            conversation_file: Name of conversation file
            conversation_dir: Directory to save conversations
            auto_save_interval: Save conversation every N iterations
            retry_on_error: Whether to retry on errors
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Returns:
            Dictionary with translation results
        """
        self.translation_stats["start_time"] = time.time()
        
        try:
            console.print(f"[blue]🚀 Starting MCP project translation: {self.source_lang} -> {self.target_lang}[/blue]")
            console.print(f"[blue]📁 Source: {source_path}[/blue]")
            console.print(f"[blue]📁 Output: {output_path}[/blue]")
            
            # Initialize tools
            file_ops = FileOperationsTool(source_path, output_path)
            
            # Validate LLM provider
            if not self.llm_provider.validate_configuration():
                raise ValueError("LLM provider configuration is invalid")
            
            # Initialize conversation
            self._initialize_conversation()
            
            # Setup conversation saving
            conversation_path = None
            if save_conversation:
                conversation_path = self._setup_conversation_saving(
                    conversation_dir, conversation_file, source_path, output_path
                )
            
            # Start translation process
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Translating project...", total=None)
                
                result = self._run_translation_loop(
                    file_ops, max_iterations, progress, task,
                    save_conversation, conversation_path, auto_save_interval
                )
            
            self.translation_stats["end_time"] = time.time()
            result["stats"] = self.translation_stats
            
            # Save final conversation if enabled
            if save_conversation and conversation_path:
                self.save_conversation(conversation_path)
                console.print(f"[green]💾 Conversation saved to: {conversation_path}[/green]")
            
            console.print(f"[green]✅ Translation completed successfully![/green]")
            console.print(f"[green]📊 Files processed: {self.translation_stats['files_read']} read, {self.translation_stats['files_written']} written[/green]")
            
            return result
            
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            error_with_stacktrace(error_msg, e)
            console.print(f"[red]❌ {error_msg}[/red]")
            
            self.translation_stats["end_time"] = time.time()
            return {
                "success": False,
                "error": error_msg,
                "stats": self.translation_stats
            }
    
    def _initialize_conversation(self) -> None:
        """Initialize the conversation with the LLM."""
        # Create system message
        system_message = self.mcp_protocol.create_system_message(
            self.source_lang, self.target_lang
        )
        
        # Add to conversation history
        self.mcp_protocol.add_message(system_message)
        
        logger.info("Conversation initialized with LLM")
    
    def _run_translation_loop(self, file_ops: FileOperationsTool, 
                            max_iterations: int, progress, task,
                            save_conversation: bool = True, 
                            conversation_path: Optional[str] = None,
                            auto_save_interval: int = 5) -> Dict[str, Any]:
        """Run the main translation loop."""
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            progress.update(task, description=f"Translation iteration {iteration}/{max_iterations}")
            
            try:
                # Send conversation to LLM
                response = self.llm_provider.send_message(
                    self.mcp_protocol.get_conversation_history(),
                    tools=self.mcp_protocol.get_available_tools()
                )
                
                # Add LLM response to conversation
                self._add_llm_response(response)
                
                tool_calls = self._process_tool_calls(
                    response.messages, file_ops
                )

                for tool_call in tool_calls:
                    self.mcp_protocol.add_message(tool_call)
                
                # Auto-save conversation if enabled
                if save_conversation and conversation_path and iteration % auto_save_interval == 0:
                    self.save_conversation(conversation_path)
                    logger.info(f"Auto-saved conversation at iteration {iteration}")

                if self._is_translation_complete(tool_calls):
                    return {
                        "success": True,
                        "message": "Translation completed successfully",
                        "iterations": iteration,
                        "conversation_length": len(self.mcp_protocol.get_conversation_history())
                    }
                
                # Small delay to prevent rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                error_with_stacktrace(error_msg, e)
                self.translation_stats["errors"] += 1
                
                # Add error to conversation
                error_message = MCPMessage(
                    id=f"error_{iteration}",
                    role=MCPMessageType.USER,
                    content=f"Error occurred: {error_msg}. Please continue with the translation."
                )
                self.mcp_protocol.add_message(error_message)
        
        return {
            "success": False,
            "error": f"Translation did not complete within {max_iterations} iterations",
            "iterations": iteration,
            "conversation_length": len(self.mcp_protocol.get_conversation_history())
        }
    
    def _add_llm_response(self, response: LLMResponse) -> None:
        """Add LLM response to conversation history."""
        for item in response.messages:
            self.mcp_protocol.add_message(item)
        
        logger.info(f"Added LLM response: {len(response.messages)} messages")
    
    def _process_tool_calls(self, tool_calls: List[MCPMessage], 
                          file_ops: FileOperationsTool) -> List[MCPMessage]:
        """Process tool calls from LLM."""
        results = []
        
        for tool_call in filter(lambda x: x.role == MCPMessageType.FUNCTION_CALL, tool_calls):
            try:
                self.translation_stats["tool_calls"] += 1
                
                tool_name = tool_call.content.name
                arguments = json.loads(tool_call.content.arguments)
                
                logger.info(f"Processing tool call: {tool_name} with args: {arguments}")
                
                # Route tool calls to appropriate handlers
                if tool_name == "get_file":
                    result = file_ops.get_file(arguments["file_path"])
                    self.translation_stats["files_read"] += 1
                    
                elif tool_name == "write_file":
                    result = file_ops.write_file(
                        arguments["file_path"], 
                        arguments["content"]
                    )
                    self.translation_stats["files_written"] += 1
                    
                elif tool_name == "list_directory":
                    result = file_ops.list_directory(arguments["directory_path"])
                    
                elif tool_name == "ask_question":
                    result = self._handle_question(arguments["question"])

                elif tool_name == "translation_complete":
                    result = self._handle_translation_complete(arguments["translation_summary"])
                    
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown tool: {tool_name}"
                    }
                
                # Format result for LLM
                tool_call_result = MCPMessage(
                    role=MCPMessageType.FUNCTION_RESPONSE,
                    content=str(result),
                    id=tool_call.id
                )
                results.append(tool_call_result)
                
            except Exception as e:
                error_msg = f"Error processing tool call {tool_call.id}: {str(e)}"
                error_with_stacktrace(error_msg, e)
                self.translation_stats["errors"] += 1
                
                tool_call_result = MCPMessage(
                    role=MCPMessageType.FUNCTION_RESPONSE,
                    content={
                        "success": False,
                        "error": error_msg
                    },
                    id=tool_call.id
                )
                results.append(tool_call_result)
        
        return results
    
    def _handle_question(self, question: str) -> Dict[str, Any]:
        """Handle questions from the LLM."""
        console.print(f"[yellow]🤔 LLM Question: {question}[/yellow]")
        
        # For now, provide a generic response
        # In a real implementation, you might want to handle specific questions
        return {
            "success": True,
            "answer": "Please continue with the translation. If you need specific information, use the available tools to explore the project structure.",
            "question": question
        }
    
    def _handle_translation_complete(self, translation_summary: str) -> Dict[str, Any]:
        """Handle translation complete from the LLM."""
        console.print(f"[green]🎉 Translation complete: {translation_summary}[/green]")
        return {
            "success": True,
            "translation_summary": translation_summary
        }
    
    def _is_translation_complete(self, tool_calls: List[MCPMessage]) -> bool:
        """Check if translation is complete."""
        return any(tool_call.role == MCPMessageType.FUNCTION_CALL and tool_call.content.name == "translation_complete" for tool_call in tool_calls)
    
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
            "tool_calls": self.translation_stats["tool_calls"],
            "errors": self.translation_stats["errors"],
            "conversation_length": len(self.mcp_protocol.get_conversation_history())
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
        
        if conversation_file == "translation_conversation.json":
            # Use default naming with timestamp
            filename = f"translation_{source_name}_to_{target_name}_{timestamp}.json"
        else:
            # Use provided filename
            filename = conversation_file
            
        conversation_path = conv_dir / filename
        
        # Save initial conversation metadata
        initial_data = {
            "metadata": {
                "translation_type": "mcp",
                "source_language": self.source_lang,
                "target_language": self.target_lang,
                "source_path": str(source_path),
                "output_path": str(output_path),
                "start_time": datetime.now().isoformat(),
                "llm_provider": self.llm_provider.get_provider_info(),
                "translation_stats": self.translation_stats
            },
            "conversation": []
        }
        
        with open(conversation_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Conversation saving setup: {conversation_path}")
        return str(conversation_path)
    
    def save_conversation(self, file_path: str) -> bool:
        """Save conversation history to file."""
        try:
            conversation_data = {
                "translation_summary": self.get_translation_summary(),
                "conversation_history": list(map(lambda x: x.to_dict(), self.mcp_protocol.get_conversation_history())),
                "raw_responses": self.llm_provider.get_raw_responses(),
                "mcp_protocol": {
                    "available_tools": self.mcp_protocol.get_available_tools()
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversation saved to: {file_path}")
            return True
            
        except Exception as e:
            error_with_stacktrace("Error saving conversation", e)
            return False
