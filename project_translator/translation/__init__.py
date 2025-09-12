"""
Translation module for automatic project translation using LLM providers.

This module provides functionality to translate entire projects from one
programming language to another while maintaining exact functionality.
"""

from .translator import ProjectTranslator
from .protocols.mcp import MCPProtocol
from .tools.file_operations import FileOperationsTool

__all__ = [
    "ProjectTranslator",
    "MCPProtocol", 
    "FileOperationsTool"
]
