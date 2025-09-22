"""
Batch translation protocol for efficient project translation.

This module implements a batch translation protocol that sends the entire
project in one request to reduce token usage and improve efficiency.
"""

import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from project_translator.utils import get_logger

logger = get_logger("batch_protocol")


@dataclass
class ProjectFile:
    """Represents a project file with its content."""
    path: str
    content: str
    file_type: str  # e.g., 'python', 'javascript', 'dockerfile', 'config'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "path": self.path,
            "content": self.content,
            "file_type": self.file_type
        }


@dataclass
class TranslatedFile:
    """Represents a translated file."""
    path: str
    content: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "path": self.path,
            "content": self.content
        }


@dataclass
class BatchTranslationRequest:
    """Represents a batch translation request."""
    source_language: str
    target_language: str
    project_files: List[ProjectFile]
    translation_instructions: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "project_files": [f.to_dict() for f in self.project_files],
            "translation_instructions": self.translation_instructions
        }


@dataclass
class BatchTranslationResponse:
    """Represents a batch translation response."""
    translated_files: List[TranslatedFile]
    translation_summary: str
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "translated_files": [f.to_dict() for f in self.translated_files],
            "translation_summary": self.translation_summary,
            "warnings": self.warnings
        }


class BatchTranslationProtocol:
    """Batch translation protocol for efficient project translation."""
    
    def __init__(self):
        """Initialize batch translation protocol."""
        self.logger = get_logger("batch_protocol")
    
    def create_translation_request(self, source_path: str, source_lang: str, 
                                 target_lang: str) -> BatchTranslationRequest:
        """
        Create a batch translation request from project files.
        
        Args:
            source_path: Path to source project
            source_lang: Source programming language
            target_lang: Target programming language
            
        Returns:
            BatchTranslationRequest object
        """
        try:
            # Collect all project files
            project_files = self._collect_project_files(source_path)
            
            # Create translation instructions
            instructions = self._create_translation_instructions(source_lang, target_lang)
            
            request = BatchTranslationRequest(
                source_language=source_lang,
                target_language=target_lang,
                project_files=project_files,
                translation_instructions=instructions
            )
            
            self.logger.info(f"Created batch translation request with {len(project_files)} files")
            return request
            
        except Exception as e:
            self.logger.error(f"Error creating translation request: {str(e)}")
            raise
    
    def _collect_project_files(self, source_path: str) -> List[ProjectFile]:
        """
        Collect all relevant project files.
        
        Args:
            source_path: Path to source project
            
        Returns:
            List of ProjectFile objects
        """
        source_dir = Path(source_path)
        project_files = []
        
        # Directories to exclude
        exclude_dirs = {
            '__pycache__', '.git', 'node_modules', '.venv', 'venv',
            'target', 'build', 'dist', '.pytest_cache', '.coverage',
            'logs', 'tmp', 'temp'
        }
        
        for file_path in source_dir.rglob('*'):
            # Skip directories
            if file_path.is_dir():
                continue
            
            # Skip excluded directories
            if any(part in exclude_dirs for part in file_path.parts):
                continue
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Get relative path
                relative_path = str(file_path.relative_to(source_dir))
                
                project_file = ProjectFile(
                    path=relative_path,
                    content=content,
                    file_type=file_path.suffix
                )
                
                project_files.append(project_file)
                
            except Exception as e:
                self.logger.warning(f"Could not read file {file_path}: {str(e)}")
                continue
        
        self.logger.info(f"Collected {len(project_files)} project files")
        return project_files
    
    def _create_translation_instructions(self, source_lang: str, target_lang: str, 
                                       ) -> str:
        """
        Create detailed translation instructions.
        
        Args:
            source_lang: Source programming language
            target_lang: Target programming language
            
        Returns:
            Translation instructions string
        """
        instructions = f"""You are an expert project translator. Your task is to translate a project from {source_lang} to {target_lang} while maintaining exact functionality.

CRITICAL REQUIREMENTS:
1. The translated project must be a Docker containerized REST API
2. The API behavior must be EXACTLY the same as the original
3. The Dockerfile must use port 8000
4. All functionalities must be preserved
5. The project structure should be adapted to {target_lang} conventions
6. The project must be able to be built and run with Docker without any other tools

RESPONSE FORMAT:
You must respond with a JSON object containing:
{{
    "translated_files": [
        {{
            "path": "relative/path/to/file",
            "content": "file content here",
            "original_path": "original/path/to/file"
        }}
    ],
    "translation_summary": "Brief summary of what was translated",
    "warnings": ["any warnings or notes about the translation"]
}}

TRANSLATION GUIDELINES:
1. Translate all source code files to {target_lang}
2. Update dependency files (requirements.txt, package.json, etc.) for {target_lang}
3. Update Dockerfile to use appropriate {target_lang} base image
4. Maintain the same API endpoints and behavior
5. Preserve all configuration settings
6. Update documentation if present
7. Ensure the project can be built and run with Docker
8. If the target language needs to be compiled, consider using a multi-stage build Dockerfile

IMPORTANT: Respond ONLY with the JSON object. Do not include any other text or explanations."""
        
        return instructions
    
    def parse_translation_response(self, response_text: str) -> BatchTranslationResponse:
        """
        Parse the LLM response into a BatchTranslationResponse.
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            BatchTranslationResponse object
        """
        try:
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in response")
            
            json_text = response_text[json_start:json_end]
            response_data = self.parse_malformed_json(json_text)
            
            # Parse translated files
            translated_files = []
            for file_data in response_data.get('translated_files', []):
                translated_file = TranslatedFile(
                    path=file_data['path'],
                    content=file_data['content']
                )
                translated_files.append(translated_file)
            
            # Create response object
            response = BatchTranslationResponse(
                translated_files=translated_files,
                translation_summary=response_data.get('translation_summary', ''),
                warnings=response_data.get('warnings', [])
            )
            
            self.logger.info(f"Parsed translation response with {len(translated_files)} files")
            return response
            
        except Exception as e:
            self.logger.error(f"Error parsing translation response: {str(e)}")
            raise ValueError(f"Failed to parse translation response: {str(e)}")
    
    def parse_malformed_json(self, json_string: str) -> Dict[str, Any]:
        """
        Parse the malformed JSON by extracting fields manually.
        
        The JSON string contains backticks instead of proper JSON quotes for content fields.
        We need to find the exact boundaries: "content": `...content...`
        This approach correctly handles backticks within the content itself.
        """

        logger.debug(f"Parsing malformed JSON: {json_string}")
        result = {}
        
        # Extract translated_files array
        translated_files = []
        
        # Find all file objects by looking for the specific pattern:
        # "content": `...content...`
        # We'll use a more robust approach by finding the start and end markers
        
        # Find all "content": ` patterns
        content_start_pattern = r'"content":\s*(`|")'
        content_starts = [m.start() for m in re.finditer(content_start_pattern, json_string)]
        
        # Find all ` patterns  
        content_end_pattern = r'(`|")\s*,\s*"original_path"'
        content_ends = [m.start() for m in re.finditer(content_end_pattern, json_string)]
        
        # Find all path pairs
        path_pattern = r'"path":\s*"([^"]+)"'
        
        paths = re.findall(path_pattern, json_string)
        
        # Extract content between the markers
        matches = []
        for i, path in enumerate(paths):
            if i < len(content_starts) and i < len(content_ends):
                start_pos = content_starts[i] + len(re.search(content_start_pattern, json_string[content_starts[i]:]).group())
                end_pos = content_ends[i]
                content = json_string[start_pos:end_pos]
                matches.append((path, content))
        
        
        for match in matches:
            file_obj = {
                "path": match[0],
                "content": self.process_file_content(match[1])
            }
            translated_files.append(file_obj)
        
        result["translated_files"] = translated_files
        
        # Extract translation_summary
        summary_pattern = r'"translation_summary":\s*"([^"]+)"'
        summary_match = re.search(summary_pattern, json_string)
        if summary_match:
            result["translation_summary"] = summary_match.group(1)
        
        # Extract warnings array
        warnings_pattern = r'"warnings":\s*\["([^"]+)"\]'
        warnings_match = re.search(warnings_pattern, json_string)
        if warnings_match:
            result["warnings"] = [warnings_match.group(1)]
        
        return result
    
    def process_file_content(self, content: str) -> str:
        """Process the file content to remove the backticks and quotes."""
        return content.replace("\\n", "\n").replace("\\\"", "\"").replace("\\'", "'").replace("\\`", "`").replace("\\\\", "\\")
    
    def validate_response(self, response: BatchTranslationResponse) -> List[str]:
        """
        Validate the translation response.
        
        Args:
            response: BatchTranslationResponse to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not response.translated_files:
            errors.append("No translated files provided")
        
        for i, file in enumerate(response.translated_files):
            if not file.path:
                errors.append(f"File {i}: Missing file path")
            if not file.content:
                errors.append(f"File {i}: Missing file content")
        
        return errors
