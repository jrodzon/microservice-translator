"""
Main translation engine for project translation.

This module implements the core translation engine that routes
translation requests to the appropriate translator based on the method.
"""

from typing import Dict, Any
from rich.console import Console

from .llm_providers.base import BaseLLMProvider
from .mcp_translator import MCPProjectTranslator
from .batch_translator import BatchProjectTranslator
from project_translator.utils import get_logger

console = Console()
logger = get_logger("translator")


class ProjectTranslator:
    """Main translation engine that routes to appropriate translator."""
    
    def __init__(self, llm_provider: BaseLLMProvider, source_lang: str, target_lang: str, 
                 translation_method: str = "mcp"):
        """
        Initialize project translator.
        
        Args:
            llm_provider: LLM provider instance
            source_lang: Source programming language
            target_lang: Target programming language
            translation_method: Translation method to use ("mcp" or "batch")
        """
        self.llm_provider = llm_provider
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translation_method = translation_method.lower()
        
        # Initialize appropriate translator
        if self.translation_method == "batch":
            self.translator = BatchProjectTranslator(llm_provider, source_lang, target_lang)
        else:
            self.translator = MCPProjectTranslator(llm_provider, source_lang, target_lang)
        
        logger.info(f"ProjectTranslator initialized: {source_lang} -> {target_lang} (method: {translation_method})")
    
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
        Translate a project from source to target language.
        
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
        # Route to appropriate translator
        return self.translator.translate_project(
            source_path, output_path, max_iterations, save_conversation,
            conversation_file, conversation_dir, auto_save_interval,
            retry_on_error, max_retries, retry_delay
        )
    
    def get_translation_summary(self) -> Dict[str, Any]:
        """Get summary of translation process."""
        return self.translator.get_translation_summary()
    
    def save_conversation(self, file_path: str) -> bool:
        """Save conversation history to file."""
        # Delegate to the appropriate translator
        if hasattr(self.translator, 'save_conversation'):
            return self.translator.save_conversation(file_path)
        return False
