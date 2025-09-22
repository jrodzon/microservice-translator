"""
Retry mechanism for batch translation with automatic testing and error feedback.

This module implements the retry mechanism that automatically tests translated
projects and retries translation with error feedback when issues are detected.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from .error_analyzer import ErrorAnalyzer, ErrorInfo, ErrorType
from .test_executor import TestExecutor, TestExecutionResult
from .llm_providers.base import BaseLLMProvider
from .protocols.batch import BatchTranslationProtocol, BatchTranslationRequest, BatchTranslationResponse
from .protocols.mcp import MCPMessage, MCPMessageType
from ..utils import get_logger

console = Console()
logger = get_logger("retry_mechanism")


@dataclass
class RetryAttempt:
    """Information about a retry attempt."""
    attempt_number: int
    success: bool
    errors: List[ErrorInfo]
    test_result: Optional[TestExecutionResult] = None
    translation_result: Optional[Dict[str, Any]] = None


class RetryMechanism:
    """Handles retry logic for batch translation with testing."""
    
    def __init__(self, llm_provider: BaseLLMProvider, source_lang: str, target_lang: str,
                 max_retries: int = 3, test_cases_path: Optional[str] = None):
        """
        Initialize the retry mechanism.
        
        Args:
            llm_provider: LLM provider instance
            source_lang: Source programming language
            target_lang: Target programming language
            max_retries: Maximum number of retry attempts
            test_cases_path: Path to test cases file (optional)
        """
        self.llm_provider = llm_provider
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.max_retries = max_retries
        self.test_cases_path = test_cases_path
        
        self.batch_protocol = BatchTranslationProtocol()
        self.error_analyzer = ErrorAnalyzer()
        
        self.retry_attempts: List[RetryAttempt] = []
        
        logger.info(f"RetryMechanism initialized: {source_lang} -> {target_lang}, max_retries={max_retries}")
    
    def translate_with_retry(self, source_path: str, output_path: str,
                           save_conversation: bool = True,
                           conversation_file: str = "retry_translation_conversation.json",
                           conversation_dir: str = "conversations") -> Dict[str, Any]:
        """
        Translate a project with automatic testing and retry mechanism.
        
        Args:
            source_path: Path to source project
            output_path: Path to output project
            save_conversation: Whether to save conversation
            conversation_file: Name of conversation file
            conversation_dir: Directory to save conversations
            
        Returns:
            Dictionary with translation results including retry information
        """
        console.print(f"[blue]🚀 Starting translation with retry mechanism: {self.source_lang} -> {self.target_lang}[/blue]")
        console.print(f"[blue]📁 Source: {source_path}[/blue]")
        console.print(f"[blue]📁 Output: {output_path}[/blue]")
        console.print(f"[blue]🔄 Max retries: {self.max_retries}[/blue]")
        
        # Setup conversation saving
        conversation_path = None
        if save_conversation:
            conversation_path = self._setup_conversation_saving(
                conversation_dir, conversation_file, source_path, output_path
            )
        
        # Initial translation attempt
        attempt = 0
        overall_success = False
        final_result = None
        
        while attempt <= self.max_retries:
            attempt += 1
            console.print(f"\n[cyan]🔄 Attempt {attempt}/{self.max_retries + 1}[/cyan]")
            
            # Perform translation
            translation_result = self._perform_translation(source_path, output_path, attempt)
            
            if not translation_result.get("success", False):
                # Translation itself failed
                errors = [ErrorInfo(
                    error_type=ErrorType.UNKNOWN_ERROR,
                    message="Translation failed",
                    context=translation_result.get("error", "Unknown error")
                )]
                
                retry_attempt = RetryAttempt(
                    attempt_number=attempt,
                    success=False,
                    errors=errors,
                    translation_result=translation_result
                )
                self.retry_attempts.append(retry_attempt)
                
                if attempt > self.max_retries:
                    break
                continue
            
            # Test the translated project
            test_result = self._test_translated_project(output_path)
            
            # Analyze errors
            errors = self._analyze_test_result(test_result, output_path)
            
            retry_attempt = RetryAttempt(
                attempt_number=attempt,
                success=test_result.success,
                errors=errors,
                test_result=test_result,
                translation_result=translation_result
            )
            self.retry_attempts.append(retry_attempt)
            
            if test_result.success:
                console.print(f"[green]✅ Translation and testing successful on attempt {attempt}![/green]")
                overall_success = True
                final_result = translation_result
                break
            else:
                console.print(f"[yellow]⚠️  Attempt {attempt} failed with {len(errors)} errors[/yellow]")
                
                if attempt > self.max_retries:
                    console.print(f"[red]❌ All {self.max_retries + 1} attempts failed[/red]")
                    break
                
                # Prepare for retry with error feedback
                console.print(f"[blue]🔄 Preparing retry with error feedback...[/blue]")
                self._prepare_retry_with_feedback(errors, source_path)
        
        # Create final result
        final_result = self._create_final_result(
            overall_success, final_result, source_path, output_path
        )
        
        # Save conversation if enabled
        if save_conversation and conversation_path:
            self._save_retry_conversation(conversation_path, final_result)
            console.print(f"[green]💾 Conversation saved to: {conversation_path}[/green]")
        
        return final_result
    
    def _perform_translation(self, source_path: str, output_path: str, 
                           attempt: int) -> Dict[str, Any]:
        """
        Perform a single translation attempt.
        
        Args:
            source_path: Path to source project
            output_path: Path to output project
            attempt: Attempt number
            
        Returns:
            Translation result dictionary
        """
        console.print(f"[blue]📝 Performing translation (attempt {attempt})...[/blue]")
        
        try:
            # Create batch translation request
            batch_request = self.batch_protocol.create_translation_request(
                source_path, self.source_lang, self.target_lang
            )
            
            # Add retry context if this is a retry
            if attempt > 1:
                batch_request = self._add_retry_context(batch_request, attempt)
            
            # Send request to LLM
            response_text = self._send_batch_request(batch_request)
            
            # Parse response
            batch_response = self.batch_protocol.parse_translation_response(response_text)
            
            # Write translated files
            written_files = self._write_translated_files(batch_response, output_path)
            
            return {
                "success": True,
                "message": f"Translation completed on attempt {attempt}",
                "translation_summary": batch_response.translation_summary,
                "warnings": batch_response.warnings,
                "files_translated": len(batch_response.translated_files),
                "files_written": written_files,
                "attempt": attempt
            }
            
        except Exception as e:
            error_msg = f"Translation failed on attempt {attempt}: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "attempt": attempt
            }
    
    def _add_retry_context(self, batch_request: BatchTranslationRequest, 
                          attempt: int) -> BatchTranslationRequest:
        """
        Add retry context to the batch request.
        
        Args:
            batch_request: Original batch request
            attempt: Attempt number
            
        Returns:
            Modified batch request with retry context
        """
        # Get error feedback from previous attempts
        error_feedback = self._generate_error_feedback()
        
        # Modify translation instructions to include error feedback
        retry_instructions = f"""
{batch_request.translation_instructions}

IMPORTANT: This is retry attempt {attempt}. The previous translation had issues:

{error_feedback}

Please carefully address these issues in your translation. Focus on:
1. Fixing the specific errors mentioned above
2. Ensuring the project builds and runs correctly
3. Maintaining exact API functionality
4. Proper dependency management
5. Correct configuration settings

Make sure to test your understanding of the errors before providing the translation.
"""
        
        # Create new request with updated instructions
        return BatchTranslationRequest(
            source_language=batch_request.source_language,
            target_language=batch_request.target_language,
            project_files=batch_request.project_files,
            translation_instructions=retry_instructions
        )
    
    def _send_batch_request(self, batch_request: BatchTranslationRequest) -> str:
        """
        Send batch translation request to LLM provider.
        
        Args:
            batch_request: BatchTranslationRequest object
            
        Returns:
            Response text from LLM
        """
        try:
            # Format the request as a single message
            request_text = self._format_batch_request(batch_request)
            
            messages = [
                MCPMessage(
                    role=MCPMessageType.SYSTEM,
                    content=batch_request.translation_instructions,
                    id="batch_system"
                ),
                MCPMessage(
                    role=MCPMessageType.USER,
                    content=request_text,
                    id="batch_request"
                )
            ]
            
            response = self.llm_provider.send_message(messages)
            
            # Extract response text
            response_text = ""
            for message in response.messages:
                if message.role == MCPMessageType.ASSISTANT:
                    response_text += str(message.content)
            
            return response_text
                
        except Exception as e:
            error_msg = f"Error sending batch request: {str(e)}"
            logger.error(error_msg)
            raise
    
    def _format_batch_request(self, batch_request: BatchTranslationRequest) -> str:
        """
        Format batch request for LLM.
        
        Args:
            batch_request: BatchTranslationRequest object
            
        Returns:
            Formatted request text
        """
        formatted = f"Please translate this project from {batch_request.source_language} to {batch_request.target_language}:\n\n"
        formatted += f"PROJECT FILES ({len(batch_request.project_files)} files):\n\n"
        
        for i, file_data in enumerate(batch_request.project_files, 1):
            formatted += f"--- FILE {i}: {file_data.path} ({file_data.file_type}) ---\n"
            formatted += file_data.content
            formatted += "\n\n"
        
        return formatted
    
    def _write_translated_files(self, batch_response: BatchTranslationResponse, 
                               output_path: str) -> int:
        """
        Write translated files to output directory.
        
        Args:
            batch_response: Batch translation response
            output_path: Output directory path
            
        Returns:
            Number of files written successfully
        """
        written_files = 0
        
        for translated_file in batch_response.translated_files:
            try:
                output_file_path = Path(output_path) / translated_file.path
                output_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    f.write(translated_file.content)
                
                written_files += 1
                console.print(f"[green]✅ Written: {output_file_path.relative_to(Path(output_path))}[/green]")
                
            except Exception as e:
                error_msg = f"Error writing file {translated_file.path}: {str(e)}"
                logger.error(error_msg)
                console.print(f"[red]❌ {error_msg}[/red]")
        
        return written_files
    
    def _test_translated_project(self, output_path: str) -> TestExecutionResult:
        """
        Test the translated project.
        
        Args:
            output_path: Path to the translated project
            
        Returns:
            TestExecutionResult object
        """
        console.print(f"[blue]🧪 Testing translated project...[/blue]")
        
        if not self.test_cases_path:
            console.print(f"[yellow]⚠️  No test cases provided, skipping testing[/yellow]")
            return TestExecutionResult(
                success=True,
                build_success=True,
                service_startup_success=True,
                test_success=True,
                build_errors=[],
                service_errors=[],
                test_errors=[]
            )
        
        try:
            test_executor = TestExecutor(output_path, self.test_cases_path)
            return test_executor.execute_full_test()
            
        except Exception as e:
            error_msg = f"Test execution failed: {str(e)}"
            logger.error(error_msg)
            return TestExecutionResult(
                success=False,
                build_success=False,
                service_startup_success=False,
                test_success=False,
                build_errors=[error_msg],
                service_errors=[],
                test_errors=[]
            )
    
    def _analyze_test_result(self, test_result: TestExecutionResult, 
                           project_path: str) -> List[ErrorInfo]:
        """
        Analyze test result and extract errors.
        
        Args:
            test_result: Test execution result
            project_path: Path to the project
            
        Returns:
            List of ErrorInfo objects
        """
        errors = []
        
        # Analyze build errors
        for build_error in test_result.build_errors:
            error_info = self.error_analyzer.analyze_error(
                build_error, project_path, ErrorType.BUILD_ERROR
            )
            errors.append(error_info)
        
        # Analyze service errors
        for service_error in test_result.service_errors:
            error_info = self.error_analyzer.analyze_error(
                service_error, project_path, ErrorType.SERVICE_STARTUP_ERROR
            )
            errors.append(error_info)
        
        # Analyze test errors
        for test_error in test_result.test_errors:
            error_info = self.error_analyzer.analyze_error(
                test_error, project_path, ErrorType.TEST_FAILURE
            )
            errors.append(error_info)
        
        # Analyze test results if available
        if test_result.test_results:
            test_errors = self.error_analyzer.analyze_test_failure(test_result.test_results)
            errors.extend(test_errors)
        
        return errors
    
    def _generate_error_feedback(self) -> str:
        """
        Generate error feedback from all previous attempts.
        
        Returns:
            Formatted error feedback string
        """
        if not self.retry_attempts:
            return "No previous attempts to analyze."
        
        all_errors = []
        for attempt in self.retry_attempts:
            all_errors.extend(attempt.errors)
        
        return self.error_analyzer.generate_error_feedback(all_errors, "")
    
    def _prepare_retry_with_feedback(self, errors: List[ErrorInfo], source_path: str):
        """
        Prepare for retry by analyzing errors and generating feedback.
        
        Args:
            errors: List of errors from current attempt
            source_path: Path to source project
        """
        console.print(f"[blue]📊 Analyzing {len(errors)} errors for retry feedback...[/blue]")
        
        for i, error in enumerate(errors, 1):
            console.print(f"[yellow]  Error {i}: {error.error_type.value} - {error.message}[/yellow]")
            if error.suggestions:
                for suggestion in error.suggestions[:2]:  # Show first 2 suggestions
                    console.print(f"[dim]    - {suggestion}[/dim]")
    
    def _create_final_result(self, success: bool, final_result: Optional[Dict[str, Any]],
                           source_path: str, output_path: str) -> Dict[str, Any]:
        """
        Create the final result dictionary.
        
        Args:
            success: Whether the overall process was successful
            final_result: Final translation result
            source_path: Source project path
            output_path: Output project path
            
        Returns:
            Final result dictionary
        """
        if success and final_result:
            return {
                "success": True,
                "message": f"Translation completed successfully after {len(self.retry_attempts)} attempts",
                "attempts": len(self.retry_attempts),
                "retry_attempts": [
                    {
                        "attempt": attempt.attempt_number,
                        "success": attempt.success,
                        "error_count": len(attempt.errors),
                        "errors": [
                            {
                                "type": error.error_type.value,
                                "message": error.message,
                                "suggestions": error.suggestions
                            }
                            for error in attempt.errors
                        ]
                    }
                    for attempt in self.retry_attempts
                ],
                **final_result
            }
        else:
            return {
                "success": False,
                "message": f"Translation failed after {len(self.retry_attempts)} attempts",
                "attempts": len(self.retry_attempts),
                "retry_attempts": [
                    {
                        "attempt": attempt.attempt_number,
                        "success": attempt.success,
                        "error_count": len(attempt.errors),
                        "errors": [
                            {
                                "type": error.error_type.value,
                                "message": error.message,
                                "suggestions": error.suggestions
                            }
                            for error in attempt.errors
                        ]
                    }
                    for attempt in self.retry_attempts
                ],
                "error": "All retry attempts failed"
            }
    
    def _setup_conversation_saving(self, conversation_dir: str, conversation_file: str,
                                 source_path: str, output_path: str) -> str:
        """
        Setup conversation saving directory and file.
        
        Args:
            conversation_dir: Directory to save conversations
            conversation_file: Name of conversation file
            source_path: Source project path
            output_path: Output project path
            
        Returns:
            Path to conversation file
        """
        from datetime import datetime
        
        # Create conversation directory
        conv_dir = Path(conversation_dir)
        conv_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate conversation filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(source_path).name
        target_name = Path(output_path).name
        
        if conversation_file == "retry_translation_conversation.json":
            filename = f"retry_translation_{source_name}_to_{target_name}_{timestamp}.json"
        else:
            filename = conversation_file
            
        conversation_path = conv_dir / filename
        
        # Save initial conversation metadata
        initial_data = {
            "metadata": {
                "translation_type": "retry_batch",
                "source_language": self.source_lang,
                "target_language": self.target_lang,
                "source_path": str(source_path),
                "output_path": str(output_path),
                "start_time": datetime.now().isoformat(),
                "max_retries": self.max_retries,
                "test_cases_path": self.test_cases_path
            },
            "retry_attempts": []
        }
        
        with open(conversation_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Conversation saving setup: {conversation_path}")
        return str(conversation_path)
    
    def _save_retry_conversation(self, file_path: str, final_result: Dict[str, Any]):
        """
        Save retry conversation to file.
        
        Args:
            file_path: Path to conversation file
            final_result: Final result dictionary
        """
        try:
            conversation_data = {
                "metadata": {
                    "translation_type": "retry_batch",
                    "source_language": self.source_lang,
                    "target_language": self.target_lang,
                    "max_retries": self.max_retries,
                    "test_cases_path": self.test_cases_path,
                    "llm_provider": self.llm_provider.get_provider_info()
                },
                "final_result": final_result,
                "retry_attempts": [
                    {
                        "attempt": attempt.attempt_number,
                        "success": attempt.success,
                        "errors": [
                            {
                                "type": error.error_type.value,
                                "message": error.message,
                                "file_path": error.file_path,
                                "line_number": error.line_number,
                                "context": error.context,
                                "suggestions": error.suggestions
                            }
                            for error in attempt.errors
                        ],
                        "test_result": {
                            "success": attempt.test_result.success if attempt.test_result else None,
                            "build_success": attempt.test_result.build_success if attempt.test_result else None,
                            "service_startup_success": attempt.test_result.service_startup_success if attempt.test_result else None,
                            "test_success": attempt.test_result.test_success if attempt.test_result else None,
                            "execution_time": attempt.test_result.execution_time if attempt.test_result else None
                        } if attempt.test_result else None
                    }
                    for attempt in self.retry_attempts
                ]
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Retry conversation saved to: {file_path}")
            
        except Exception as e:
            logger.error(f"Error saving retry conversation: {str(e)}")
