"""
Model Context Protocol (MCP) implementation for LLM communication.

This module implements the MCP protocol for structured communication
with LLM providers during project translation.
"""

import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from enum import Enum


class MCPMessageType(str, Enum):
    """Types of MCP messages."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"


@dataclass
class MCPMessage:
    """Represents an MCP message."""
    role: MCPMessageType
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary format."""
        result = {
            "role": self.role.value,
            "content": self.content
        }
        
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
            
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
            
        return result


@dataclass
class MCPToolCall:
    """Represents a tool call in MCP protocol."""
    id: str
    type: str
    function: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool call to dictionary format."""
        return {
            "id": self.id,
            "type": self.type,
            "function": self.function
        }


class MCPProtocol:
    """Model Context Protocol implementation for project translation."""
    
    def __init__(self):
        """Initialize MCP protocol."""
        self.conversation_history: List[MCPMessage] = []
        self.available_tools = [
            {
                "type": "function",
                "function": {
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
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
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
                        "required": ["file_path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
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
                        "required": ["directory_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
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
                        "required": ["question"]
                    }
                }
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
            content=system_prompt
        )
    
    def add_message(self, message: MCPMessage) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append(message)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history in dictionary format."""
        return [msg.to_dict() for msg in self.conversation_history]
    
    def parse_tool_calls(self, response: str) -> List[MCPToolCall]:
        """Parse tool calls from LLM response."""
        tool_calls = []
        
        # Look for tool call patterns in the response
        # Format: TOOL_CALL: {"name": "tool_name", "arguments": {...}}
        tool_call_pattern = r'TOOL_CALL:\s*(\{.*?\})'
        matches = re.findall(tool_call_pattern, response, re.DOTALL)
        
        for i, match in enumerate(matches):
            try:
                tool_data = json.loads(match)
                tool_call = MCPToolCall(
                    id=f"call_{i}",
                    type="function",
                    function=tool_data
                )
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
                
        return tool_calls
    
    def format_tool_response(self, tool_call_id: str, result: Any, 
                           success: bool = True, error: Optional[str] = None) -> MCPMessage:
        """Format a tool response message."""
        if success:
            content = f"Tool call {tool_call_id} completed successfully. Result: {result}"
        else:
            content = f"Tool call {tool_call_id} failed. Error: {error}"
            
        return MCPMessage(
            role=MCPMessageType.TOOL_RESPONSE,
            content=content,
            tool_call_id=tool_call_id
        )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return self.available_tools
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
