"""
Model Context Protocol (MCP) implementation for LLM communication.

This module implements the MCP protocol for structured communication
with LLM providers during project translation.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class MCPMessageType(str, Enum):
    """Types of MCP messages."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESPONSE = "function_response"


@dataclass
class MCPMessage:
    """Represents an MCP message."""
    role: MCPMessageType
    content: Any
    id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        result = {
            "role": self.role.value,
            "content": self.content,
            "id": self.id
        }
        
        return result


@dataclass
class FunctionCallContent:
    """Represents a function call content."""
    name: str
    arguments: Any
    call_id: str


class MCPProtocol:
    """Model Context Protocol implementation for project translation."""
    
    def __init__(self):
        """Initialize MCP protocol."""
        self.conversation_history: List[MCPMessage] = []
        self.available_tools = [
            {
                "type": "function",
                "name": "get_file",
                "description": "Get the content of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"],
                    "additionalProperties": False
                },
                "strict": True
            },
            {
                "type": "function",
                "name": "write_file", 
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path where to write the file"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"],
                    "additionalProperties": False
                },
                "strict": True
            },
            {
                "type": "function",
                "name": "list_directory",
                "description": "List contents of a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Path to the directory to list"
                        }
                    },
                    "required": ["directory_path"],
                    "additionalProperties": False
                },
                "strict": True
            },
            {
                "type": "function",
                "name": "ask_question",
                "description": "Ask a clarifying question",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to ask"
                        }
                    },
                    "required": ["question"],
                    "additionalProperties": False
                },
                "strict": True
            }
        ]
    
    def create_system_message(self, source_lang: str, target_lang: str, 
                            project_type: str = "Docker containerized REST API") -> MCPMessage:
        """Create the initial system message for translation."""
        system_prompt = f"""You are an expert project translator. Your task is to translate a {project_type} project from {source_lang} to {target_lang} while maintaining exact functionality.

IMPORTANT REQUIREMENTS:
1. The translated project must be a Docker containerized REST API
2. The API behavior must be EXACTLY the same as the original
3. The Dockerfile must use port 8000
4. All functionalities must be preserved
5. The project structure should be adapted to {target_lang} conventions

COMMUNICATION PROTOCOL:
You can use the following tools to interact with the project:
- get_file(file_path): Get the content of any file
- write_file(file_path, content): Write content to a file in the output directory
- list_directory(directory_path): List contents of a directory
- ask_question(question): Ask clarifying questions

TRANSLATION PROCESS:
1. First, request the directory structure with list_directory("/")
2. Analyze the project architecture and plan your translation strategy
3. Request source files as needed with get_file()
4. Translate files and write them with write_file()
5. Ensure all dependencies and configurations are properly translated
6. Verify the translation maintains the same API behavior

Start by requesting the directory structure of the source project."""

        return MCPMessage(
            role=MCPMessageType.SYSTEM,
            content=system_prompt,
            id="system"
        )
    
    def add_message(self, message: MCPMessage) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append(message)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history in dictionary format."""
        return [msg.to_dict() for msg in self.conversation_history]
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.available_tools
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
