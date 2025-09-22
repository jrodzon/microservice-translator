# Automatic Testing and Retry Mechanism

This document describes the automatic testing and retry mechanism implemented for the batch translator. This feature automatically tests translated projects and retries translation with error feedback when issues are detected.

## Overview

The retry mechanism provides:

1. **Automatic Testing**: After translation, the system automatically builds and tests the translated project
2. **Error Analysis**: Comprehensive analysis of different types of errors (build, compile, runtime, test failures)
3. **Intelligent Retry**: Retries translation with detailed error feedback to the LLM
4. **Progress Tracking**: Detailed logging and reporting of retry attempts

## Components

### 1. Error Analyzer (`error_analyzer.py`)

Analyzes different types of errors and provides suggestions for fixes:

- **Build Errors**: Docker build failures, missing files, permission issues
- **Compile Errors**: Syntax errors, missing dependencies, compilation failures
- **Runtime Errors**: Service startup failures, connection issues, null pointer exceptions
- **Test Failures**: API test failures, validation errors, timeout issues

### 2. Test Executor (`test_executor.py`)

Executes the full test cycle against translated projects:

- **Build Phase**: Runs the project's start script to build the service
- **Service Startup**: Starts the service and waits for it to be ready
- **Test Execution**: Runs test cases against the service
- **Cleanup**: Shuts down the service after testing

### 3. Retry Mechanism (`retry_mechanism.py`)

Orchestrates the retry process:

- **Translation**: Performs initial translation
- **Testing**: Automatically tests the translated project
- **Error Analysis**: Analyzes failures and generates feedback
- **Retry Logic**: Retries translation with error feedback
- **Result Tracking**: Tracks all attempts and results

## Usage

### Command Line Interface

```bash
# Use automatic testing and retry (enabled by default in config.json)
python -m project_translator translate \
    --source input/project \
    --output output/project \
    --from-lang python \
    --to-lang java \
    --method batch \
    --test-cases input/test_cases.json

# Override test cases path from command line
python -m project_translator translate \
    --source input/project \
    --output output/project \
    --from-lang python \
    --to-lang java \
    --method batch \
    --test-cases /path/to/custom/test_cases.json

# To disable auto-testing, set enable_auto_testing: false in config.json
# or modify the config file:
# {
#   "translation": {
#     "enable_auto_testing": false
#   }
# }
```

### Programmatic Usage

```python
from project_translator.translation.batch_translator import BatchProjectTranslator
from project_translator.translation.llm_providers.openai import OpenAIProvider

# Initialize translator
llm_provider = OpenAIProvider(api_key="your-key", model="gpt-4")
translator = BatchProjectTranslator(llm_provider, "python", "java")

# Translate with retry mechanism (auto-testing enabled by default in config.json)
result = translator.translate_project(
    source_path="input/project",
    output_path="output/project",
    test_cases_path="input/test_cases.json",
    enable_auto_testing=True,  # Can be overridden, but defaults to config.json value
    max_retries=3,
    retry_on_error=True
)
```

## Configuration

### Config.json Settings

The automatic testing and retry mechanism is controlled by settings in `config.json`:

```json
{
  "translation": {
    "enable_auto_testing": true,
    "test_cases_path": null,
    "retry_on_error": true,
    "max_retries": 3
  }
}
```

- **`enable_auto_testing`**: Enable/disable automatic testing and retry mechanism (default: `true`)
- **`test_cases_path`**: Path to test cases file (can be overridden with `--test-cases` CLI option)
- **`retry_on_error`**: Whether to retry on errors (default: `true`)
- **`max_retries`**: Maximum number of retry attempts (default: `3`)

### Required Files

1. **Test Cases File**: JSON file containing test scenarios (see existing `test_cases.json` format)
2. **Start Script**: `start.sh` script in the project directory for building/starting the service
3. **Shutdown Script**: `shutdown.sh` script for cleaning up after testing

### Project Structure

```
project/
├── app.py              # Main application file
├── requirements.txt    # Dependencies
├── Dockerfile         # Docker configuration
├── start.sh           # Build/start script (executable)
├── shutdown.sh        # Shutdown script (executable)
└── test_cases.json    # Test cases (optional, can be separate)
```

## Error Types and Handling

### Build Errors
- **Docker build failures**: Invalid Dockerfile, missing files
- **Permission issues**: File permissions, ownership problems
- **Missing dependencies**: Required packages not available

### Compile Errors
- **Syntax errors**: Language-specific syntax issues
- **Import errors**: Missing modules, incorrect imports
- **Type errors**: Type mismatches, incorrect declarations

### Runtime Errors
- **Service startup failures**: Port conflicts, configuration issues
- **Connection errors**: Network connectivity, service availability
- **Memory issues**: Out of memory, resource constraints

### Test Failures
- **API endpoint failures**: Incorrect endpoints, missing functionality
- **Validation errors**: Response format, data validation
- **Timeout issues**: Service responsiveness, performance problems

## Retry Process

1. **Initial Translation**: Translate the project using batch method
2. **File Writing**: Write translated files to output directory
3. **Build Testing**: Run start script to build the project
4. **Service Testing**: Start service and verify it's running
5. **Test Execution**: Run test cases against the service
6. **Error Analysis**: Analyze any failures and categorize errors
7. **Retry Decision**: If errors found and retries remaining, retry with feedback
8. **Feedback Generation**: Generate detailed error feedback for the LLM
9. **Retry Translation**: Retry translation with error context
10. **Repeat**: Continue until success or max retries reached

## Output and Logging

### Console Output
- Real-time progress indicators
- Error summaries for each attempt
- Final success/failure status
- Detailed error information

### Conversation Files
- Complete retry history
- Error analysis details
- LLM feedback provided
- Test results for each attempt

### Example Output
```
🚀 Starting translation with retry mechanism: python -> java
📁 Source: input/project
📁 Output: output/project
🔄 Max retries: 3

🔄 Attempt 1/4
📝 Performing translation (attempt 1)...
✅ Written: app.java
✅ Written: pom.xml
✅ Written: Dockerfile
🧪 Testing translated project...
❌ Build failed: Docker build error
📊 Analyzing 1 errors for retry feedback...
  Error 1: build_error - Docker build failed
    - Check Dockerfile syntax and base image
    - Ensure all required files are copied correctly

🔄 Attempt 2/4
📝 Performing translation (attempt 2)...
...
✅ Translation and testing successful on attempt 2!
```

## Benefits

1. **Improved Success Rate**: Automatic retry with error feedback increases translation success
2. **Quality Assurance**: Automatic testing ensures translated projects work correctly
3. **Error Learning**: LLM learns from errors and improves subsequent attempts
4. **Comprehensive Feedback**: Detailed error analysis helps identify and fix issues
5. **Progress Tracking**: Full visibility into retry process and error patterns

## Limitations

1. **Test Dependency**: Requires test cases and proper project structure
2. **Time Overhead**: Testing adds time to the translation process
3. **Resource Usage**: Each retry consumes additional LLM tokens
4. **Service Requirements**: Projects must be containerizable and testable

## Future Enhancements

1. **Parallel Testing**: Test multiple retry attempts in parallel
2. **Error Pattern Learning**: Learn from common error patterns across projects
3. **Incremental Fixes**: Apply targeted fixes instead of full retranslation
4. **Performance Optimization**: Optimize test execution and error analysis
5. **Custom Error Handlers**: Allow custom error analysis for specific project types
