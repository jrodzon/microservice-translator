"""
OpenAI provider implementation for project translation.

This module implements the OpenAI API provider for LLM communication
during project translation.
"""

import json
from typing import List, Dict, Any, Optional
from rich.console import Console

from .base import BaseLLMProvider, LLMResponse
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
    
    def send_message(self, messages: List[Dict[str, Any]], 
                    tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """
        Send messages to OpenAI API.
        
        Args:
            messages: List of messages in the conversation
            tools: List of available tools for the LLM
            
        Returns:
            LLMResponse with the model's response
        """
        try:
            if not self.validate_configuration():
                raise ValueError("Invalid OpenAI configuration")
            
            # Prepare request parameters
            request_params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "stream": False
            }
            
            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = "auto"
            
            logger.info(f"Sending request to OpenAI {self.model} with {len(messages)} messages")
            
            # Make API call
            if not self.client:
                raise ValueError("OpenAI client not initialized. API key may be missing.")
            
            response = self.client.chat.completions.create(**request_params)
            
            # Extract response
            choice = response.choices[0]
            message = choice.message
            
            # Parse tool calls if present
            tool_calls = None
            if message.tool_calls:
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            result = LLMResponse(
                content=message.content or "",
                tool_calls=tool_calls,
                usage=usage,
                model=self.model,
                finish_reason=choice.finish_reason
            )
            
            logger.info(f"Received response from OpenAI: {len(result.content)} chars, {len(tool_calls or [])} tool calls")
            return result
            
        except Exception as e:
            error_msg = f"Error sending message to OpenAI: {str(e)}"
            logger.error(error_msg)
            console.print(f"[red]OpenAI API Error: {error_msg}[/red]")
            raise
    
    def send_tool_response(self, messages: List[Dict[str, Any]], 
                          tool_response: Dict[str, Any]) -> LLMResponse:
        """
        Send tool response back to OpenAI.
        
        Args:
            messages: Current conversation messages
            tool_response: Response from tool execution
            
        Returns:
            LLMResponse with the model's next response
        """
        try:
            # Add tool response to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_response.get("tool_call_id"),
                "content": json.dumps(tool_response.get("result", {}))
            })
            
            # Send updated conversation
            return self.send_message(messages)
            
        except Exception as e:
            error_msg = f"Error sending tool response to OpenAI: {str(e)}"
            logger.error(error_msg)
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
