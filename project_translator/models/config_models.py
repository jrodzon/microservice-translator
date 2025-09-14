"""
Configuration models for Project Translator.

This module contains models for application configuration using dataclasses
as a fallback when Pydantic is not available.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    
    level: str = "INFO"
    file: str = "logs/project_translator.log"
    max_file_size: int = 10485760  # 10MB
    backup_count: int = 5
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.level.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of: {", ".join(allowed_levels)}')
        self.level = self.level.upper()
        
        if self.max_file_size <= 0:
            raise ValueError('Max file size must be positive')
        
        if self.backup_count < 0:
            raise ValueError('Backup count must be non-negative')


@dataclass
class LLMProviderConfig:
    """LLM provider configuration settings."""
    
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 60
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        allowed_providers = ['openai', 'anthropic', 'local']
        if self.provider.lower() not in allowed_providers:
            raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        self.provider = self.provider.lower()
        
        if self.max_tokens <= 0:
            raise ValueError('Max tokens must be positive')
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        
        if self.timeout <= 0:
            raise ValueError('Timeout must be positive')


@dataclass
class TranslationConfig:
    """Translation-specific configuration settings."""
    
    method: str = "mcp"  # "mcp" or "batch"
    max_iterations: int = 50
    save_conversation: bool = True
    conversation_file: str = "translation_conversation.json"
    conversation_dir: str = "conversations"
    auto_save_interval: int = 5  # Save every N iterations
    retry_on_error: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        allowed_methods = ['mcp', 'batch']
        if self.method.lower() not in allowed_methods:
            raise ValueError(f'Translation method must be one of: {", ".join(allowed_methods)}')
        self.method = self.method.lower()
        
        if self.max_iterations <= 0:
            raise ValueError('Max iterations must be positive')
        
        if self.auto_save_interval <= 0:
            raise ValueError('Auto save interval must be positive')
        
        if self.max_retries < 0:
            raise ValueError('Max retries must be non-negative')
        
        if self.retry_delay < 0:
            raise ValueError('Retry delay must be non-negative')


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    base_url: str = "http://localhost:8000"
    timeout: int = 60
    startup_timeout: int = 120
    shutdown_timeout: int = 30
    check_interval: int = 2
    output_file: str = "test_results.json"
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    llm_provider: LLMProviderConfig = field(default_factory=LLMProviderConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        self.base_url = self.base_url.rstrip('/')
        
        for attr_name in ['timeout', 'startup_timeout', 'shutdown_timeout', 'check_interval']:
            value = getattr(self, attr_name)
            if value <= 0:
                raise ValueError(f'{attr_name} must be positive')


@dataclass
class Config(AppConfig):
    """Main configuration class that extends AppConfig with file management."""
    
    config_file: Optional[str] = "config.json"
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'Config':
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
            
        Returns:
            Config instance loaded from file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file contains invalid data
        """
        import json
        
        config_file = Path(config_path) if config_path else Path("config.json")
        
        if not config_file.exists():
            # Create default config file
            default_config = cls()
            default_config.save(config_file)
            return default_config
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Parse logging configuration
            logging_data = config_data.get("logging", {})
            logging_config = LoggingConfig(**logging_data)
            
            # Parse LLM provider configuration
            llm_data = config_data.get("llm_provider", {})
            llm_config = LLMProviderConfig(**llm_data)
            
            # Parse translation configuration
            translation_data = config_data.get("translation", {})
            translation_config = TranslationConfig(**translation_data)
            
            # Create config instance
            config = cls(
                base_url=config_data.get("base_url", "http://localhost:8000"),
                timeout=config_data.get("timeout", 60),
                startup_timeout=config_data.get("startup_timeout", 120),
                shutdown_timeout=config_data.get("shutdown_timeout", 30),
                check_interval=config_data.get("check_interval", 2),
                output_file=config_data.get("output_file", "test_results.json"),
                logging=logging_config,
                llm_provider=llm_config,
                translation=translation_config,
                config_file=str(config_file)
            )
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config: {e}")
    
    def save(self, config_path: Optional[str] = None) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Path to save config file. If None, uses current config_file.
        """
        import json
        
        save_path = Path(config_path) if config_path else Path(self.config_file)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "startup_timeout": self.startup_timeout,
            "shutdown_timeout": self.shutdown_timeout,
            "check_interval": self.check_interval,
            "output_file": self.output_file,
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count
            },
            "llm_provider": {
                "provider": self.llm_provider.provider,
                "model": self.llm_provider.model,
                "api_key": self.llm_provider.api_key,
                "base_url": self.llm_provider.base_url,
                "max_tokens": self.llm_provider.max_tokens,
                "temperature": self.llm_provider.temperature,
                "timeout": self.llm_provider.timeout
            },
            "translation": {
                "method": self.translation.method,
                "max_iterations": self.translation.max_iterations,
                "save_conversation": self.translation.save_conversation,
                "conversation_file": self.translation.conversation_file,
                "conversation_dir": self.translation.conversation_dir,
                "auto_save_interval": self.translation.auto_save_interval,
                "retry_on_error": self.translation.retry_on_error,
                "max_retries": self.translation.max_retries,
                "retry_delay": self.translation.retry_delay
            }
        }
        
        with open(save_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "startup_timeout": self.startup_timeout,
            "shutdown_timeout": self.shutdown_timeout,
            "check_interval": self.check_interval,
            "output_file": self.output_file,
            "logging": {
                "level": self.logging.level,
                "file": self.logging.file,
                "max_file_size": self.logging.max_file_size,
                "backup_count": self.logging.backup_count
            },
            "llm_provider": {
                "provider": self.llm_provider.provider,
                "model": self.llm_provider.model,
                "api_key": self.llm_provider.api_key,
                "base_url": self.llm_provider.base_url,
                "max_tokens": self.llm_provider.max_tokens,
                "temperature": self.llm_provider.temperature,
                "timeout": self.llm_provider.timeout
            },
            "translation": {
                "method": self.translation.method,
                "max_iterations": self.translation.max_iterations,
                "save_conversation": self.translation.save_conversation,
                "conversation_file": self.translation.conversation_file,
                "conversation_dir": self.translation.conversation_dir,
                "auto_save_interval": self.translation.auto_save_interval,
                "retry_on_error": self.translation.retry_on_error,
                "max_retries": self.translation.max_retries,
                "retry_delay": self.translation.retry_delay
            }
        }