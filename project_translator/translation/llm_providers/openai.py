"""
OpenAI provider implementation for project translation.

This module implements the OpenAI API provider for LLM communication
during project translation using the Responses API.
"""

from typing import List, Dict, Any, Optional
from openai.types.responses.response_input_item import Message, ResponseInputItem
from openai.types.responses.response_input_item import FunctionCallOutput
from openai.types.responses.response_output_item import ResponseOutputItem
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall
from rich.console import Console

from project_translator.translation.protocols.mcp import MCPMessage, MCPMessageType
from project_translator.translation.protocols.mcp import FunctionCallContent
from project_translator.translation.llm_providers.base import BaseLLMProvider, LLMResponse
from project_translator.utils import get_logger

console = Console()
logger = get_logger("openai_provider")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model name (default: gpt-4)
            api_key: OpenAI API key
            **kwargs: Additional OpenAI parameters
        """
        super().__init__(model, api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.temperature = kwargs.get("temperature", 0.1)
        
        # Try to import openai
        try:
            import openai
            self.openai = openai
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
            raise ImportError("OpenAI library is required for OpenAIProvider")
        
        # Initialize OpenAI client with API key
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        else:
            self.client = None
    
    def _convert_messages_to_input(self, messages: List[MCPMessage]) -> List[ResponseInputItem]:
        """
        Convert messages list to input string for Responses API.
        
        Args:
            messages: List of messages in the conversation
            
        Returns:
            List of OpenAI input items
        """
        input_parts : List[ResponseInputItem] = []
        for message in messages:
            role = message.role
            content = message.content
            if role == MCPMessageType.SYSTEM:
                input_parts.append(Message(role="system", content=content))
            elif role == MCPMessageType.USER:
                input_parts.append(Message(role="user", content=content))
            elif role == MCPMessageType.ASSISTANT:
                input_parts.append(ResponseOutputMessage(content=content, id=message.id))
            elif role == MCPMessageType.FUNCTION_CALL:
                input_parts.append(ResponseFunctionToolCall(name=content.name, arguments=content.arguments, call_id=message.id))
            elif role == MCPMessageType.FUNCTION_RESPONSE:
                input_parts.append(FunctionCallOutput(call_id=message.id, output=content))
        
        return input_parts
    
    def send_message(self, messages: List[MCPMessage], 
                    tools: Optional[List[Dict[str, Any]]] = None) -> List[MCPMessage]:
        """
        Send messages to OpenAI API using the Responses API.
        
        Args:
            messages: List of messages in the conversation
            tools: List of available tools for the LLM
            
        Returns:
            List of messages with the model's response
        """
        try:
            if not self.validate_configuration():
                raise ValueError("Invalid OpenAI configuration")
            
            # Convert messages to input format for Responses API
            input_text = self._convert_messages_to_input(messages)
            
            # Prepare request parameters for Responses API
            request_params = {
                "model": self.model,
                "input": input_text,
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            logger.info(f"Sending request to OpenAI {self.model} with {len(messages)} messages")
            logger.debug(f"Request parameters: {request_params}")
            
            # Make API call using Responses API
            if not self.client:
                raise ValueError("OpenAI client not initialized. API key may be missing.")
            
            response = self.client.responses.create(**request_params)

            logger.info(f"Received response from OpenAI: {len(response.content)} chars")
            logger.debug(f"Response: {response.model_dump_json(indent=2)}")
            
            # Extract response data from Responses API format
            response_messages = []
            
            # Handle different response types from Responses API
            if hasattr(response, 'output') and isinstance(response.output, list) and response.output:
                for output_item in response.output:
                    if isinstance(output_item, ResponseOutputMessage):
                        response_messages.append(self._convert_openai_output_message_to_mcp_message(output_item))
                    elif isinstance(output_item, ResponseFunctionToolCall):
                        response_messages.append(self._convert_openai_output_function_call_to_mcp_message(output_item))
                    else:
                        response_messages.append(self._convert_openai_output_to_mcp_message(output_item))
            
            # Extract usage information
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(messages=response_messages, usage=usage, is_complete=response.status == "completed")
            
        except Exception as e:
            error_msg = f"Error sending message to OpenAI: {str(e)}"
            logger.error(error_msg)
            console.print(f"[red]OpenAI API Error: {error_msg}[/red]")
            raise

    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models.
        
        Returns:
            List of available model names
        """
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k"
        ]
    
    def get_model_description(self, model_name: str) -> str:
        """
        Get description for a specific OpenAI model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Description of the model
        """
        model_info = self.get_model_info()
        if model_name == self.model:
            return model_info.get("description", f"OpenAI {model_name} model")
        
        # Get description for other models
        model_descriptions = {
            "gpt-4": "Most capable GPT-4 model",
            "gpt-4-turbo": "Faster GPT-4 model with vision support",
            "gpt-4-32k": "GPT-4 with 32k context window",
            "gpt-4o": "Latest GPT-4 model with improved capabilities",
            "gpt-4o-mini": "Efficient GPT-4 model",
            "gpt-3.5-turbo": "Fast and efficient GPT-3.5 model",
            "gpt-3.5-turbo-16k": "GPT-3.5 with 16k context window"
        }
        
        return model_descriptions.get(model_name, f"OpenAI {model_name} model")
    
    def validate_configuration(self) -> bool:
        """
        Validate OpenAI configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not super().validate_configuration():
            return False
        
        # Test API key and client initialization
        try:
            if not self.api_key or len(self.api_key) < 20:
                logger.error("Invalid OpenAI API key format")
                return False
            
            # Check if client is properly initialized
            if not self.client:
                logger.error("OpenAI client not initialized")
                return False
                
            return True
        except Exception as e:
            logger.error(f"OpenAI configuration validation failed: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        model_info = {
            "gpt-4": {
                "max_tokens": 8192,
                "context_window": 128000,
                "description": "Most capable GPT-4 model"
            },
            "gpt-4-turbo": {
                "max_tokens": 4096,
                "context_window": 128000,
                "description": "Faster GPT-4 model"
            },
            "gpt-4-32k": {
                "max_tokens": 32768,
                "context_window": 32768,
                "description": "GPT-4 with 32k context window"
            },
            "gpt-3.5-turbo": {
                "max_tokens": 4096,
                "context_window": 16384,
                "description": "Fast and efficient GPT-3.5 model"
            },
            "gpt-3.5-turbo-16k": {
                "max_tokens": 16384,
                "context_window": 16384,
                "description": "GPT-3.5 with 16k context window"
            }
        }
        
        return model_info.get(self.model, {
            "max_tokens": self.max_tokens,
            "context_window": "Unknown",
            "description": f"Custom model: {self.model}"
        })
    
    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> Dict[str, float]:
        """
        Estimate cost for API usage.
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Dictionary with cost estimates
        """
        # OpenAI pricing (as of 2024, in USD per 1K tokens)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4-32k": {"input": 0.06, "output": 0.12},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004}
        }
        
        model_pricing = pricing.get(self.model, {"input": 0.01, "output": 0.02})
        
        input_cost = (prompt_tokens / 1000) * model_pricing["input"]
        output_cost = (completion_tokens / 1000) * model_pricing["output"]
        total_cost = input_cost + output_cost
        
        return {
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "currency": "USD"
        }
    
    def _convert_openai_output_message_to_mcp_message(self, output_item: ResponseOutputMessage) -> MCPMessage:
        """
        Convert OpenAI output message to MCP message.
        """
        return MCPMessage(role=MCPMessageType.ASSISTANT, content=output_item.content, id=output_item.id)
        
    def _convert_openai_output_function_call_to_mcp_message(self, output_item: ResponseFunctionToolCall) -> MCPMessage:
        """
        Convert OpenAI output function call to MCP message.
        """
        return MCPMessage(role=MCPMessageType.FUNCTION_CALL, content=FunctionCallContent(name=output_item.name, arguments=output_item.arguments, call_id=output_item.call_id), id=output_item.id)
    
    def _convert_openai_output_to_mcp_message(self, output_item: ResponseOutputItem) -> MCPMessage:
        """
        Convert OpenAI output to MCP message.
        """
        return MCPMessage(role=MCPMessageType.ASSISTANT, content=output_item.output, id=output_item.id)
