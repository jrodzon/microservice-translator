"""
Base LLM provider class for project translation.

This module defines the base interface for LLM providers used in
project translation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from project_translator.translation.protocols.mcp import MCPMessage
from project_translator.utils import get_logger

logger = get_logger("llm_provider")


@dataclass
class UsageData:
    """Represents usage data."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """Represents an LLM response."""
    messages: List[MCPMessage]
    usage: UsageData
    is_complete: bool



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
    def send_message(self, messages: List[MCPMessage], 
                    tools: Optional[List[Dict[str, Any]]] = None) -> LLMResponse:
        """
        Send messages to the LLM and get response.
        
        Args:
            messages: List of messages in the conversation
            tools: List of available tools for the LLM
            
        Returns:
            LLMResponse object with the model's response
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
    
    @abstractmethod
    def get_model_description(self, model_name: str) -> str:
        """
        Get description for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Description of the model
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
