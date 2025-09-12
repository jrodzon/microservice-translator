"""
Base LLM provider class for project translation.

This module defines the base interface for LLM providers used in
project translation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from project_translator.utils import get_logger

logger = get_logger("llm_provider")


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, model: str, api_key: Optional[str] = None, **kwargs):
        """
        Initialize LLM provider.
        
        Args:
            model: Model name to use
            api_key: API key for the provider
            **kwargs: Additional provider-specific parameters
        """
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs
        logger.info(f"Initialized {self.__class__.__name__} with model: {model}")
    
    @abstractmethod
    def send_message(self, messages: List[Dict[str, Any]], 
                    tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """
        Send messages to the LLM and get response.
        
        Args:
            messages: List of messages in the conversation
            tools: List of available tools for the LLM
            
        Returns:
            LLMResponse with the model's response
        """
        pass
    
    @abstractmethod
    def send_tool_response(self, messages: List[Dict[str, Any]], 
                          tool_response: Dict[str, Any]) -> LLMResponse:
        """
        Send tool response back to the LLM.
        
        Args:
            messages: Current conversation messages
            tool_response: Response from tool execution
            
        Returns:
            LLMResponse with the model's next response
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider.
        
        Returns:
            List of model names
        """
        pass
    
    def validate_configuration(self) -> bool:
        """
        Validate provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not self.api_key:
            logger.error("API key is required")
            return False
        return True
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about the provider.
        
        Returns:
            Dictionary with provider information
        """
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
            "has_api_key": bool(self.api_key),
            "available_models": self.get_available_models()
        }
