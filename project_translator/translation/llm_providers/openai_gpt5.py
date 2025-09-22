"""
OpenAI provider implementation for project translation.

This module implements the OpenAI API provider for LLM communication
during project translation using the Responses API.
"""

from typing import List, Dict, Any, Optional
from openai.types.responses.response_input_item import Message, ResponseInputItem
from openai.types.responses.response_input_text import ResponseInputText
from openai.types.responses.response_input_item import FunctionCallOutput
from openai.types.responses.response_output_item import ResponseOutputItem
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall
from openai.types.responses.response_output_text import ResponseOutputText
from rich.console import Console

from project_translator.translation.protocols.mcp import MCPMessage, MCPMessageType
from project_translator.translation.protocols.mcp import FunctionCallContent
from project_translator.translation.llm_providers.base import BaseLLMProvider, LLMResponse, UsageData
from project_translator.utils import get_logger, error_with_stacktrace

console = Console()
logger = get_logger("openai_provider")


class OpenAIGPT5Provider(BaseLLMProvider):
    """OpenAI API provider implementation."""
    
    def __init__(self, model: str = "gpt-5", api_key: Optional[str] = None, **kwargs):
        """
        Initialize OpenAI provider.
        
        Args:
            model: OpenAI model name (default: gpt-5)
            api_key: OpenAI API key
            **kwargs: Additional OpenAI parameters
        """
        super().__init__(model, api_key, **kwargs)
        self.base_url = kwargs.get("base_url", "https://api.openai.com/v1")
        
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
                input_parts.append(Message(role="system", content=[ResponseInputText(text=content, type="input_text")]))
            elif role == MCPMessageType.USER:
                input_parts.append(Message(role="user", content=[ResponseInputText(text=content, type="input_text")]))
            elif role == MCPMessageType.ASSISTANT:
                input_parts.append(ResponseOutputMessage(content=[ResponseOutputText(text=content, type="output_text", annotations=[])], id=message.id, role="assistant", status="completed", type="message"))
            elif role == MCPMessageType.FUNCTION_CALL:
                input_parts.append(ResponseFunctionToolCall(name=content.name, arguments=content.arguments, call_id=message.id, status="completed", type="function_call"))
            elif role == MCPMessageType.FUNCTION_RESPONSE:
                input_parts.append(FunctionCallOutput(call_id=message.id, output=content, status="completed", type="function_call_output"))
        
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
                "reasoning": {"effort": "high" }
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

            self.raw_responses.append(response.to_dict())
            
            logger.info(f"Received response from OpenAI: {len(response.model_dump_json(indent=2))} chars")
            logger.debug(f"Response: {response.model_dump_json(indent=2)}")
            
            # Extract response data from Responses API format
            response_messages = []
            
            # Handle different response types from Responses API
            if hasattr(response, 'output') and isinstance(response.output, list) and response.output:
                for output_item in response.output:
                    if output_item.type == "reasoning":
                        continue
                    if isinstance(output_item, ResponseOutputMessage):
                        response_messages.append(self._convert_openai_output_message_to_mcp_message(output_item))
                    elif isinstance(output_item, ResponseFunctionToolCall):
                        response_messages.append(self._convert_openai_output_function_call_to_mcp_message(output_item))
                    else:
                        response_messages.append(self._convert_openai_output_to_mcp_message(output_item))
            
            # Extract usage information
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = UsageData(
                    input_tokens= response.usage.input_tokens,
                    output_tokens= response.usage.output_tokens,
                    total_tokens= response.usage.total_tokens
                )
            
            return LLMResponse(messages=response_messages, usage=usage)
            
        except Exception as e:
            error_msg = f"Error sending message to OpenAI: {str(e)}"
            error_with_stacktrace(error_msg, e)
            console.print(f"[red]OpenAI API Error: {error_msg}[/red]")
            raise

    def get_available_models(self) -> List[str]:
        """
        Get list of available OpenAI models.
        
        Returns:
            List of available model names
        """
        return [
            "gpt-5",
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
            "gpt-5": "Most capable GPT-5 model",
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
            error_with_stacktrace("OpenAI configuration validation failed", e)
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary with model information
        """
        model_info = {
            "gpt-5": {
                "context_window": 1280000,
                "description": "Most capable GPT-5 model"
            }
        }
        
        return model_info.get(self.model, {
            "context_window": self.context_window,
            "description": f"Custom model: {self.model}"
        })

    
    def _convert_openai_output_message_to_mcp_message(self, output_item: ResponseOutputMessage) -> MCPMessage:
        """
        Convert OpenAI output message to MCP message.
        """
        content = "\n".join([x.text for x in output_item.content])
        return MCPMessage(role=MCPMessageType.ASSISTANT, content=content, id=output_item.id)
        
    def _convert_openai_output_function_call_to_mcp_message(self, output_item: ResponseFunctionToolCall) -> MCPMessage:
        """
        Convert OpenAI output function call to MCP message.
        """
        return MCPMessage(role=MCPMessageType.FUNCTION_CALL, content=FunctionCallContent(name=output_item.name, arguments=output_item.arguments, call_id=output_item.call_id), id=output_item.id)
    
    def _convert_openai_output_to_mcp_message(self, output_item: ResponseOutputItem) -> MCPMessage:
        """
        Convert OpenAI output to MCP message.
        """
        return MCPMessage(role=MCPMessageType.ASSISTANT, content=str(output_item.output), id=output_item.id)
