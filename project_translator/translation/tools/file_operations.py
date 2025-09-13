"""
File operations tool for project translation.

This module provides tools for reading and writing files during
the translation process.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from rich.console import Console

from project_translator.utils import get_logger, error_with_stacktrace

console = Console()
logger = get_logger("file_operations")


class FileOperationsTool:
    """Tool for handling file operations during translation."""
    
    def __init__(self, source_path: str, output_path: str):
        """
        Initialize file operations tool.
        
        Args:
            source_path: Path to the source project directory
            output_path: Path to the output project directory
        """
        self.source_path = Path(source_path).resolve()
        self.output_path = Path(output_path).resolve()
        
        # Ensure output directory exists
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileOperationsTool initialized - Source: {self.source_path}, Output: {self.output_path}")
    
    def get_file(self, file_path: str) -> Dict[str, Any]:
        """
        Get the content of a file from the source project.
        
        Args:
            file_path: Path to the file relative to source project root
            
        Returns:
            Dictionary with file content and metadata
        """
        try:
            # Resolve the full path
            full_path = self.source_path / file_path.lstrip('/')
            
            # Security check - ensure path is within source directory
            if not str(full_path.resolve()).startswith(str(self.source_path.resolve())):
                return {
                    "success": False,
                    "error": f"Access denied: Path {file_path} is outside source directory"
                }
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            if not full_path.is_file():
                return {
                    "success": False,
                    "error": f"Path is not a file: {file_path}"
                }
            
            # Read file content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file metadata
            stat = full_path.stat()
            
            result = {
                "success": True,
                "content": content,
                "file_path": file_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": full_path.suffix,
                "is_binary": self._is_binary(content)
            }
            
            logger.info(f"Successfully read file: {file_path} ({stat.st_size} bytes)")
            return result
            
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            error_with_stacktrace(error_msg, e)
            return {
                "success": False,
                "error": error_msg
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file in the output project.
        
        Args:
            file_path: Path to the file relative to output project root
            content: Content to write to the file
            
        Returns:
            Dictionary with operation result
        """
        try:
            # Resolve the full path
            full_path = self.output_path / file_path.lstrip('/')
            
            # Security check - ensure path is within output directory
            if not str(full_path.resolve()).startswith(str(self.output_path.resolve())):
                return {
                    "success": False,
                    "error": f"Access denied: Path {file_path} is outside output directory"
                }
            
            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Get file metadata
            stat = full_path.stat()
            
            result = {
                "success": True,
                "file_path": file_path,
                "size": stat.st_size,
                "message": f"File written successfully: {file_path}"
            }
            
            logger.info(f"Successfully wrote file: {file_path} ({stat.st_size} bytes)")
            return result
            
        except Exception as e:
            error_msg = f"Error writing file {file_path}: {str(e)}"
            error_with_stacktrace(error_msg, e)
            return {
                "success": False,
                "error": error_msg
            }
    
    def list_directory(self, directory_path: str = "/") -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            directory_path: Path to the directory relative to source project root
            
        Returns:
            Dictionary with directory contents
        """
        try:
            # Handle root directory
            if directory_path == "/":
                full_path = self.source_path
            else:
                full_path = self.source_path / directory_path.lstrip('/')
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.source_path.resolve())):
                return {
                    "success": False,
                    "error": f"Access denied: Path {directory_path} is outside source directory"
                }
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory_path}"
                }
            
            if not full_path.is_dir():
                return {
                    "success": False,
                    "error": f"Path is not a directory: {directory_path}"
                }
            
            # List directory contents
            items = []
            for item in sorted(full_path.iterdir()):
                relative_path = item.relative_to(self.source_path)
                items.append({
                    "name": item.name,
                    "path": str(relative_path),
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            result = {
                "success": True,
                "directory_path": directory_path,
                "items": items,
                "count": len(items)
            }
            
            logger.info(f"Successfully listed directory: {directory_path} ({len(items)} items)")
            return result
            
        except Exception as e:
            error_msg = f"Error listing directory {directory_path}: {str(e)}"
            error_with_stacktrace(error_msg, e)
            return {
                "success": False,
                "error": error_msg
            }
    
    def get_project_structure(self) -> Dict[str, Any]:
        """
        Get the complete project structure as a tree.
        
        Returns:
            Dictionary with project structure
        """
        try:
            structure = self._build_tree(self.source_path, self.source_path)
            
            result = {
                "success": True,
                "project_structure": structure,
                "root_path": str(self.source_path)
            }
            
            logger.info("Successfully built project structure")
            return result
            
        except Exception as e:
            error_msg = f"Error building project structure: {str(e)}"
            error_with_stacktrace(error_msg, e)
            return {
                "success": False,
                "error": error_msg
            }
    
    def _build_tree(self, path: Path, root_path: Path) -> Dict[str, Any]:
        """Recursively build directory tree."""
        try:
            if path.is_file():
                return {
                    "name": path.name,
                    "type": "file",
                    "size": path.stat().st_size,
                    "extension": path.suffix
                }
            elif path.is_dir():
                children = []
                for child in sorted(path.iterdir()):
                    if child.name.startswith('.'):
                        continue  # Skip hidden files
                    children.append(self._build_tree(child, root_path))
                
                return {
                    "name": path.name,
                    "type": "directory",
                    "children": children,
                    "count": len(children)
                }
        except Exception as e:
            error_with_stacktrace(f"Error processing {path}", e)
            return {
                "name": path.name,
                "type": "error",
                "error": str(e)
            }
    
    def _is_binary(self, content: str) -> bool:
        """Check if content appears to be binary."""
        try:
            # Try to encode as UTF-8, if it fails it might be binary
            content.encode('utf-8')
            return False
        except UnicodeEncodeError:
            return True
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a file without reading its content.
        
        Args:
            file_path: Path to the file relative to source project root
            
        Returns:
            Dictionary with file information
        """
        try:
            full_path = self.source_path / file_path.lstrip('/')
            
            if not full_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }
            
            stat = full_path.stat()
            
            return {
                "success": True,
                "file_path": file_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": full_path.suffix,
                "is_file": full_path.is_file(),
                "is_directory": full_path.is_dir()
            }
            
        except Exception as e:
            error_msg = f"Error getting file info for {file_path}: {str(e)}"
            error_with_stacktrace(error_msg, e)
            return {
                "success": False,
                "error": error_msg
            }
