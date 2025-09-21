"""
Anthropic provider implementation for project translation.

This module implements the Anthropic API provider for LLM communication
during project translation using Claude models.
"""

from typing import List, Dict, Any, Optional
from rich.console import Console
import json

from project_translator.translation.protocols.mcp import MCPMessage, MCPMessageType
from project_translator.translation.protocols.mcp import FunctionCallContent
from project_translator.translation.llm_providers.base import BaseLLMProvider, LLMResponse, UsageData
from project_translator.utils import get_logger, error_with_stacktrace

console = Console()
logger = get_logger("anthropic_provider")


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider implementation."""
    
    def __init__(self, model: str = "claude-opus-4-20250514", api_key: Optional[str] = None, **kwargs):
        """
        Initialize Anthropic provider.
        
        Args:
            model: Anthropic model name (default: claude-opus-4-20250514)
            api_key: Anthropic API key
            **kwargs: Additional Anthropic parameters
        """
        super().__init__(model, api_key, **kwargs)
        self.max_tokens = kwargs.get("max_tokens", 32000)
        self.temperature = kwargs.get("temperature", 0.1)
        
        # Try to import anthropic
        try:
            import anthropic
            self.anthropic = anthropic
        except ImportError:
            logger.error("Anthropic library not installed. Install with: pip install anthropic")
            raise ImportError("Anthropic library is required for AnthropicProvider")
        
        # Initialize Anthropic client with API key
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def _convert_messages_to_anthropic_format(self, messages: List[MCPMessage]) -> List[Dict[str, Any]]:
        """
        Convert MCP messages to Anthropic API format.
        
        Args:
            messages: List of MCP messages
            
        Returns:
            List of messages in Anthropic format
        """
        anthropic_messages = []
        system_message = None
        
        for message in messages:
            role = message.role
            content = message.content
            
            if role == MCPMessageType.SYSTEM:
                system_message = content
            elif role == MCPMessageType.USER:
                anthropic_messages.append({
                    "role": "user",
                    "content": content
                })
            elif role == MCPMessageType.ASSISTANT:
                anthropic_messages.append({
                    "role": "assistant", 
                    "content": content
                })
            elif role == MCPMessageType.FUNCTION_CALL:
                # Convert function call to tool use format
                if isinstance(content, FunctionCallContent):
                    anthropic_messages.append({
                        "role": "assistant",
                        "content": [{
                            "type": "tool_use",
                            "id": content.call_id,
                            "name": content.name,
                            "input": self._parse_arguments(content.arguments)
                        }]
                    })
            elif role == MCPMessageType.FUNCTION_RESPONSE:
                # Convert function response to tool result format
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": message.id,
                        "content": str(content)
                    }]
                })
        
        return anthropic_messages, system_message
    
    def _parse_arguments(self, arguments: str) -> Dict[str, Any]:
        """
        Parse function call arguments from string to dictionary.
        
        Args:
            arguments: JSON string of arguments
            
        Returns:
            Dictionary of parsed arguments
        """
        try:
            import json
            return json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Failed to parse arguments: {arguments}")
            return {}
    
    def _convert_anthropic_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tools to Anthropic format.
        
        Args:
            tools: List of tools in OpenAI format
            
        Returns:
            List of tools in Anthropic format
        """
        anthropic_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                anthropic_tool = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["parameters"]
                }
                anthropic_tools.append(anthropic_tool)
        
        return anthropic_tools
    
    def send_message(self, messages: List[MCPMessage], 
                    tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """
        Send messages to Anthropic API using streaming.
        
        Args:
            messages: List of messages in the conversation
            tools: List of available tools for the LLM
            
        Returns:
            LLMResponse object with the model's response
        """
        try:
            if not self.validate_configuration():
                raise ValueError("Invalid Anthropic configuration")
            
            # Convert messages to Anthropic format
            anthropic_messages, system_message = self._convert_messages_to_anthropic_format(messages)
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": anthropic_messages
            }
            
            # Add system message if present
            if system_message:
                request_params["system"] = system_message
            
            # Add tools if provided
            if tools:
                anthropic_tools = self._convert_anthropic_tools(tools)
                request_params["tools"] = anthropic_tools
            
            logger.info(f"Sending streaming request to Anthropic {self.model} with {len(messages)} messages")
            logger.debug(f"Request parameters: {request_params}")
            
            # Make streaming API call
            if not self.client:
                raise ValueError("Anthropic client not initialized. API key may be missing.")
            
            # Initialize variables to accumulate streaming response
            accumulated_content = []
            accumulated_usage = None
            response_id = None
            
            # Process streaming response
            with self.client.messages.stream(**request_params) as stream:
                for chunk in stream:
                    # Store raw chunk for debugging
                    self.raw_responses.append(chunk.model_dump())
                    
                    # Handle different chunk types
                    if chunk.type == "message_start":
                        response_id = chunk.message.id
                        logger.debug(f"Started streaming message: {response_id}")
                        
                    elif chunk.type == "content_block_start":
                        logger.debug(f"Started content block: {chunk.content_block.type}")
                        
                    elif chunk.type == "content_block_delta":
                        # Accumulate text content
                        if hasattr(chunk.delta, 'text') and chunk.delta.text:
                            accumulated_content.append({
                                "type": "text",
                                "text": chunk.delta.text
                            })
                            logger.debug(f"Received text delta: {len(chunk.delta.text)} chars")
                            
                    elif chunk.type == "content_block_stop":
                        logger.debug("Content block completed")
                        
                    elif chunk.type == "message_delta":
                        # Handle usage information
                        if hasattr(chunk.delta, 'usage') and chunk.delta.usage:
                            accumulated_usage = chunk.delta.usage
                            logger.debug(f"Received usage delta: {chunk.delta.usage}")
                            
                    elif chunk.type == "message_stop":
                        logger.debug("Message streaming completed")
                        break
                        
                    elif chunk.type == "error":
                        error_msg = f"Streaming error: {chunk.error}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
            
            # Create a mock response object with accumulated data
            class MockResponse:
                def __init__(self, content, usage, response_id):
                    self.content = content
                    self.usage = usage
                    self.id = response_id
                    
                def model_dump(self):
                    # Convert content blocks to serializable format
                    serializable_content = []
                    for block in self.content:
                        if hasattr(block, 'type') and hasattr(block, 'text'):
                            serializable_content.append({
                                "type": block.type,
                                "text": block.text
                            })
                        else:
                            serializable_content.append(str(block))
                    
                    return {
                        "id": self.id,
                        "content": serializable_content,
                        "usage": self.usage
                    }
                    
                def model_dump_json(self, indent=None):
                    import json
                    return json.dumps(self.model_dump(), indent=indent)
            
            # Create mock response with accumulated content
            mock_content = []
            for content_item in accumulated_content:
                if content_item["type"] == "text":
                    # Group consecutive text deltas into a single text block
                    if mock_content and mock_content[-1].type == "text":
                        mock_content[-1].text += content_item["text"]
                    else:
                        class MockTextBlock:
                            def __init__(self, text):
                                self.type = "text"
                                self.text = text
                        mock_content.append(MockTextBlock(content_item["text"]))
            
            response = MockResponse(mock_content, accumulated_usage, response_id)
            
            logger.info(f"Received complete streaming response from Anthropic: {len(response.model_dump_json())} chars")
            logger.debug(f"Response: {response.model_dump_json()}")
            
            # Convert response to MCP messages
            response_messages = []
            
            for content_block in response.content:
                if content_block.type == "text":
                    response_messages.append(MCPMessage(
                        role=MCPMessageType.ASSISTANT,
                        content=content_block.text,
                        id=response.id
                    ))
                elif content_block.type == "tool_use":
                    response_messages.append(MCPMessage(
                        role=MCPMessageType.FUNCTION_CALL,
                        content=FunctionCallContent(
                            name=content_block.name,
                            arguments=str(content_block.input),
                            call_id=content_block.id
                        ),
                        id=content_block.id
                    ))
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = UsageData(
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
                )
            
            return LLMResponse(messages=response_messages, usage=usage)
            
        except Exception as e:
            error_msg = f"Error sending message to Anthropic: {str(e)}"
            error_with_stacktrace(error_msg, e)
            console.print(f"[red]Anthropic API Error: {error_msg}[/red]")
            raise

    def get_available_models(self) -> List[str]:
        """
        Get list of available Anthropic models.
        
        Returns:
            List of available model names
        """
        return [
            "claude-opus-4-20250514"
        ]
    
    def get_model_description(self, model_name: str) -> str:
        """
        Get description for a specific Anthropic model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Description of the model
        """
        model_descriptions = {
            "claude-opus-4-20250514": "Claude Opus 4.0 - Most capable model with advanced reasoning"
        }
        
        return model_descriptions.get(model_name, f"Anthropic {model_name} model")
    
    def validate_configuration(self) -> bool:
        """
        Validate Anthropic configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not super().validate_configuration():
            return False
        
        # Test API key and client initialization
        try:
            if not self.api_key or len(self.api_key) < 20:
                logger.error("Invalid Anthropic API key format")
                return False
            
            # Check if client is properly initialized
            if not self.client:
                logger.error("Anthropic client not initialized")
                return False
                
            return True
        except Exception as e:
            error_with_stacktrace("Anthropic configuration validation failed", e)
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        model_info = {
            "claude-opus-4-20250514": {
                "max_tokens": 200000,
                "context_window": 200000,
                "description": "Claude Opus 4.0 - Most capable model with advanced reasoning"
            }
        }
        
        return model_info.get(self.model, {
            "max_tokens": self.max_tokens,
            "context_window": "Unknown",
            "description": f"Custom model: {self.model}"
        })
