"""
Configuration management module for Project Translator.

This module provides backward compatibility for the old config system.
New code should use the models from project_translator.models.config_models.
"""

from typing import Optional
from ..models.config_models import Config as PydanticConfig, LoggingConfig as PydanticLoggingConfig


# Backward compatibility aliases
Config = PydanticConfig
LoggingConfig = PydanticLoggingConfig