# Project Translator

A comprehensive application for automated testing and translation of CRUD services using Large Language Models (LLMs). This tool provides both testing capabilities for validating translated services and automated project translation from one programming language to another.

## 🚀 Features

### Testing Capabilities
- **Automated Service Management**: Starts and stops test services automatically
- **Comprehensive Test Execution**: Runs all scenarios with detailed reporting
- **Rich Console Output**: Beautiful console output with progress indicators and colored results
- **Result Persistence**: Saves detailed test results to JSON files
- **Error Handling**: Robust error handling with graceful service cleanup

### Translation Capabilities
- **LLM-Powered Translation**: Automated project translation using OpenAI GPT models
- **Multi-Language Support**: Translate between Python, JavaScript, and other languages
- **Model Context Protocol (MCP)**: Structured communication with LLMs for complex translations
- **Automatic Conversation Saving**: All translation conversations saved for analysis and debugging
- **Configurable Translation Parameters**: Fine-tune translation behavior via configuration

### System Features
- **Modular Design**: Clean architecture following Python best practices
- **Centralized Configuration**: All settings managed through config.json
- **Rich Logging**: Comprehensive logging with file rotation and console output
- **Docker Integration**: Full Docker and Docker Compose support

## ⚡ Quick Start

### 1. Setup
```bash
# Clone and setup
git clone <repository-url>
cd whole-project-translation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure OpenAI API key
python -m project_translator translate configure --api-key "your-openai-api-key"
```

### 2. Translate a Project
```bash
# Translate Python to JavaScript
python -m project_translator translate translate-project \
  --source ./input/project \
  --output ./output/translated \
  --from-lang Python \
  --to-lang JavaScript
```

### 3. Test the Translation
```bash
# Test the translated service
python -m project_translator test run-tests \
  -p ./output/translated \
  -t ./input/test_cases.json
```

## 📦 Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd whole-project-translation
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure OpenAI API key** (for translation features):
```bash
python -m project_translator translate configure --api-key "your-openai-api-key"
```

## 🏗️ Architecture

The application follows a clean, modular architecture:

```
project_translator/
├── __init__.py              # Package initialization
├── __main__.py              # Module entry point
├── main.py                  # Main CLI interface
├── core/                    # Core functionality
│   ├── test_runner.py       # Test orchestration
│   ├── service_manager.py   # Service lifecycle management
│   ├── request_executor.py  # HTTP request handling
│   └── result_handler.py    # Result processing and reporting
├── translation/             # Translation functionality
│   ├── translator.py        # Main translation engine
│   ├── llm_providers/       # LLM provider implementations
│   │   ├── base.py          # Base LLM provider interface
│   │   └── openai.py        # OpenAI provider implementation
│   ├── protocols/           # Communication protocols
│   │   └── mcp.py           # Model Context Protocol
│   └── tools/               # Translation tools
│       ├── file_operations.py # File system operations
│       └── project_analysis.py # Project analysis tools
├── commands/                # CLI commands
│   ├── test_commands.py     # Test-related commands
│   └── translation_commands.py # Translation commands
├── models/                  # Data models
│   ├── config_models.py     # Configuration models
│   └── test_case_models.py  # Test case models
└── utils/                   # Utilities and helpers
    ├── config.py            # Configuration management
    └── validators.py        # Validation utilities
```

## 🎯 Usage

### Project Translation

#### Basic Translation
```bash
# Translate a Python project to JavaScript
python -m project_translator translate translate-project \
  --source ./input/project \
  --output ./output/translated \
  --from-lang Python \
  --to-lang JavaScript
```

#### Advanced Translation Options
```bash
# Override configuration settings
python -m project_translator translate translate-project \
  --source ./input/project \
  --output ./output/translated \
  --from-lang Python \
  --to-lang JavaScript \
  --max-iterations 20 \
  --conversation-file "custom_conversation.json"
```

#### Translation Configuration
```bash
# Configure translation settings
python -m project_translator translate configure \
  --max-iterations 30 \
  --auto-save-interval 5 \
  --save-conversation \
  --conversation-dir "translation_logs"

# Configure LLM provider
python -m project_translator translate configure \
  --api-key "your-openai-api-key" \
  --model "gpt-4" \
  --temperature 0.1 \
  --max-tokens 4000
```

#### Translation Analysis
```bash
# Analyze a project before translation
python -m project_translator translate analyze --source ./input/project

# List available LLM providers
python -m project_translator translate providers

# List available models for a provider
python -m project_translator translate list-models --provider openai
```

### Testing Translated Services

#### Basic Test Execution
```bash
# Run tests against translated project
python -m project_translator test run-tests -p ./output/translated -t ./input/test_cases.json
```

#### Advanced Testing Options
```bash
# Run with custom configuration
python -m project_translator test run-tests \
  -p ./output/translated \
  -t ./input/test_cases.json \
  -o custom_results.json \
  -u http://localhost:9000 \
  -v -d

# Validate test project without running tests
python -m project_translator test validate -p ./output/translated -t ./input/test_cases.json

# Generate test summary
python -m project_translator test summary -p ./output/translated -t ./input/test_cases.json

# Show current log file path
python -m project_translator test logs
```

### Command Options

#### Global Options
- `-c, --config`: Path to configuration file (default: config.json)
- `-v, --verbose`: Enable verbose output

#### Translation Commands
- `translate-project`: Translate a project from one language to another
  - `-s, --source`: Source project path (required)
  - `-o, --output`: Output project path (required)
  - `-f, --from-lang`: Source programming language (required)
  - `-t, --to-lang`: Target programming language (required)
  - `--max-iterations`: Maximum translation iterations (overrides config)
  - `--save-conversation`: Save conversation to file (overrides config)
  - `--conversation-file`: Conversation file name (overrides config)

- `configure`: Configure translation and LLM settings
  - `-p, --provider`: LLM provider (openai, anthropic, local)
  - `-k, --api-key`: API key for LLM provider
  - `-m, --model`: LLM model name
  - `--max-tokens`: Maximum tokens per request
  - `--temperature`: Generation temperature
  - `--max-iterations`: Maximum translation iterations
  - `--save-conversation/--no-save-conversation`: Enable/disable conversation saving
  - `--conversation-file`: Conversation file name
  - `--conversation-dir`: Conversation directory
  - `--auto-save-interval`: Auto-save interval (iterations)

- `analyze`: Analyze project structure and dependencies
  - `-s, --source`: Source project path (required)

- `providers`: List available LLM providers
- `list-models`: List available models for a provider
  - `-p, --provider`: LLM provider (required)
  - `-k, --api-key`: API key (optional)

#### Testing Commands
- `run-tests`: Run test scenarios
  - `-p, --test-project`: Path to test project directory (required)
  - `-t, --test-cases`: Path to test_cases.json file (required)
  - `-o, --output`: Output file for test results (default: from config)
  - `-d, --detailed`: Show detailed step-by-step results
  - `-u, --base-url`: Base URL for API requests (default: from config)

- `validate`: Validate test project structure
  - `-p, --test-project`: Path to test project directory (required)
  - `-t, --test-cases`: Path to test_cases.json file (required)
  - `-s, --scenario`: Specific scenario to validate (optional)

- `summary`: Generate test summary
  - `-p, --test-project`: Path to test project directory (required)
  - `-t, --test-cases`: Path to test_cases.json file (required)
  - `-o, --output`: Output file for summary (default: test_summary.json)

- `logs`: Show current log file path and information

#### Configuration Commands
- `config-info`: Display current configuration
- `config show`: Display current configuration
- `config set`: Set configuration values
- `config reset`: Reset to default configuration
- `config export`: Export configuration to file
- `config import`: Import configuration from file

### General Commands

```bash
# Display application information
python -m project_translator info

# Show current configuration (includes translation settings)
python -m project_translator config-info

# Set configuration values
python -m project_translator config set --base-url http://localhost:9000 --timeout 120

# Reset to default configuration
python -m project_translator config reset

# Export configuration
python -m project_translator config export --output my_config.json

# Import configuration
python -m project_translator config import --input my_config.json
```

## ⚙️ Configuration

### Configuration File

The application uses a comprehensive JSON configuration file (`config.json`) for all settings:

```json
{
  "base_url": "http://localhost:8000",
  "timeout": 60,
  "startup_timeout": 120,
  "shutdown_timeout": 30,
  "check_interval": 2,
  "output_file": "test_results.json",
  "logging": {
    "level": "INFO",
    "file": "logs/project_translator.log",
    "max_file_size": 10485760,
    "backup_count": 5
  },
  "llm_provider": {
    "provider": "openai",
    "model": "gpt-4",
    "api_key": "your-openai-api-key",
    "base_url": null,
    "max_tokens": 4000,
    "temperature": 0.1,
    "timeout": 60
  },
  "translation": {
    "max_iterations": 50,
    "save_conversation": true,
    "conversation_file": "translation_conversation.json",
    "conversation_dir": "conversations",
    "auto_save_interval": 5,
    "retry_on_error": true,
    "max_retries": 3,
    "retry_delay": 1.0
  }
}
```

### Configuration Options

#### Application Settings
- `base_url`: Default base URL for API requests
- `timeout`: Default timeout for operations (seconds)
- `startup_timeout`: Timeout for service startup (seconds)
- `shutdown_timeout`: Timeout for service shutdown (seconds)
- `check_interval`: Interval between health checks (seconds)
- `output_file`: Default output file for results

#### Logging Configuration
- `logging`: Logging configuration
  - `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `file`: Log file path
  - `max_file_size`: Maximum log file size before rotation (bytes)
  - `backup_count`: Number of backup log files to keep

#### LLM Provider Configuration
- `llm_provider`: LLM provider settings
  - `provider`: LLM provider (openai, anthropic, local)
  - `model`: Model name (gpt-4, gpt-3.5-turbo, etc.)
  - `api_key`: API key for the provider
  - `base_url`: Custom base URL (optional)
  - `max_tokens`: Maximum tokens per request
  - `temperature`: Generation temperature (0.0-2.0)
  - `timeout`: Request timeout (seconds)

#### Translation Configuration
- `translation`: Translation-specific settings
  - `max_iterations`: Maximum translation iterations
  - `save_conversation`: Whether to save conversations (default: true)
  - `conversation_file`: Conversation file name
  - `conversation_dir`: Directory for conversation files
  - `auto_save_interval`: Auto-save every N iterations
  - `retry_on_error`: Whether to retry on errors
  - `max_retries`: Maximum retry attempts
  - `retry_delay`: Delay between retries (seconds)

### Custom Configuration

You can specify a custom configuration file:

```bash
# Use custom config for testing
python -m project_translator --config my_config.json test run-tests -p ./output/translated -t ./input/test_cases.json

# Use custom config for translation
python -m project_translator --config my_config.json translate translate-project \
  --source ./input/project --output ./output/translated \
  --from-lang Python --to-lang JavaScript
```

If the configuration file doesn't exist, the application will create a default one automatically.

### Configuration Management

```bash
# View current configuration
python -m project_translator config-info

# Update specific settings
python -m project_translator translate configure --api-key "new-key" --model "gpt-4"

# Export configuration for backup
python -m project_translator config export --output backup_config.json

# Import configuration from file
python -m project_translator config import --input backup_config.json
```

## 💾 Conversation Saving

The translation system automatically saves all conversations with the LLM for analysis, debugging, and reproducibility.

### Automatic Conversation Saving

- **Default Behavior**: Conversations are saved by default (`save_conversation: true`)
- **Auto-Save**: Conversations are automatically saved every N iterations (configurable via `auto_save_interval`)
- **Smart Naming**: Files are named with timestamp and project names for easy identification
- **Organized Storage**: Conversations are saved in a dedicated `conversations/` directory

### Conversation File Structure

```json
{
  "metadata": {
    "source_language": "Python",
    "target_language": "JavaScript",
    "source_path": "/path/to/source",
    "output_path": "/path/to/output",
    "start_time": "2025-09-12T23:56:47",
    "llm_provider": {
      "provider": "OpenAIProvider",
      "model": "gpt-4",
      "has_api_key": true
    },
    "translation_stats": {
      "files_read": 3,
      "files_written": 2,
      "tool_calls": 15,
      "errors": 0
    }
  },
  "conversation": [
    {
      "role": "system",
      "content": "You are an expert project translator..."
    },
    {
      "role": "assistant",
      "content": "I'll help you translate this project...",
      "tool_calls": [...]
    }
  ]
}
```

### Conversation Management

```bash
# Configure conversation saving
python -m project_translator translate configure \
  --save-conversation \
  --conversation-dir "translation_logs" \
  --auto-save-interval 5

# Disable conversation saving
python -m project_translator translate configure --no-save-conversation

# View conversation files
ls -la conversations/
```

## 📝 Logging

The application provides comprehensive logging with both console and file output:

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about test execution
- **WARNING**: Warning messages for non-critical issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause application failure

### Log Output
- **Console**: Rich formatted output with colors and progress indicators
- **File**: Detailed logs saved to `logs/project_translator.log` with rotation

### Log File Management
- **Automatic Rotation**: Log files are rotated when they reach the maximum size
- **Backup Files**: Old log files are kept as backups (configurable count)
- **Consistent Logging**: All application logs are written to a single, consistent log file

### Logging Configuration
```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/project_translator.log",
    "max_file_size": 10485760,
    "backup_count": 5
  }
}
```

### Verbose Mode
Use the `-v` or `--verbose` flag to enable DEBUG level logging:
```bash
python -m project_translator -v test run-tests -p ./test-project -t ./test-project/test_cases.json
```

## 🧪 Project Structure

### Input Project Structure

The source project for translation should have the following structure:

```
input/
├── project/            # Source project directory
│   ├── app.py         # Main application file
│   ├── requirements.txt # Dependencies
│   ├── Dockerfile     # Docker configuration
│   └── README.md      # Project documentation
├── test_cases.json    # Test cases for validation
├── start.sh           # Service startup script
├── shutdown.sh        # Service shutdown script
└── docker-compose.yml # Docker Compose configuration
```

### Output Project Structure

After translation, the output will have the following structure:

```
output/
├── translated/        # Translated project directory
│   ├── app.js        # Translated application file
│   ├── package.json  # Node.js dependencies
│   ├── Dockerfile    # Translated Docker configuration
│   └── README.md     # Translated documentation
└── conversations/     # Translation conversation logs
    └── translation_project_to_translated_20250912_235647.json
```

### Test Project Structure

For testing translated services, the structure should be:

```
test-project/
├── app.py              # Main FastAPI application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── start.sh           # Startup script (executable)
├── shutdown.sh        # Shutdown script (executable)
├── test_cases.json    # Test cases definition
└── README.md          # Project documentation
```

## 📊 Test Cases Format

Test cases are defined in JSON format with scenarios containing steps:

```json
{
  "test_suite": "CRUD API Test Scenarios",
  "description": "Comprehensive test scenarios for the CRUD REST API service",
  "base_url": "http://localhost:8000",
  "scenarios": [
    {
      "name": "service_health_verification",
      "description": "Verify service is running and healthy",
      "steps": [
        {
          "name": "check_health_endpoint",
          "method": "GET",
          "endpoint": "/health",
          "expected_status": 200,
          "expected_response": {
            "status": "healthy",
            "service": "crud-api"
          }
        }
      ]
    }
  ]
}
```

## 📈 Output Formats

### Console Output
- Real-time progress indicators
- Colored success/failure indicators
- Detailed summary tables
- Step-by-step execution details

### JSON Results
```json
{
  "success": true,
  "test_suite": "CRUD API Test Scenarios",
  "total_scenarios": 9,
  "passed_scenarios": 9,
  "scenario_results": [
    {
      "scenario_name": "service_health_verification",
      "success": true,
      "total_steps": 2,
      "passed_steps": 2,
      "step_results": [...]
    }
  ],
  "timestamp": "2024-01-15T10:30:00"
}
```

## 🔧 Development

### Local Development

1. **Set up development environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Run the application**:
```bash
python -m project_translator test run-tests -p ./test-project -t ./test-project/test_cases.json
```

### Adding New Commands

1. **Create command module** in `commands/`:
```python
import click

@click.command()
def new_command():
    """New command implementation."""
    pass
```

2. **Register command** in `commands/__init__.py`:
```python
from .new_commands import new_command
```

3. **Add to main CLI** in `main.py`:
```python
cli.add_command(new_command)
```

## 🐛 Troubleshooting

### Common Issues

1. **Service won't start**: Check that Docker is running and start.sh is executable
2. **Tests timeout**: Increase timeout values or check service startup logs
3. **Permission errors**: Ensure scripts are executable (`chmod +x start.sh shutdown.sh`)

### Debug Mode

Use verbose mode for detailed output:
```bash
python -m project_translator test run-tests -p ./test-project -t ./test-project/test_cases.json -v
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Use Cases

### Project Translation
- **Language Migration**: Translate projects from Python to JavaScript, Java to Python, etc.
- **Framework Migration**: Convert between different frameworks (FastAPI to Express.js, etc.)
- **Legacy Modernization**: Update legacy codebases to modern languages and frameworks
- **Cross-Platform Development**: Create equivalent services for different platforms

### Translation Testing
- **Functional Validation**: Ensure translated services maintain exact API behavior
- **Regression Testing**: Comprehensive testing to catch translation errors
- **Performance Comparison**: Compare performance between original and translated services
- **Integration Testing**: Validate translated services work with existing systems

### Service Validation
- **API Testing**: Automated testing of REST APIs
- **Service Health Monitoring**: Continuous health checks and monitoring
- **Performance Testing**: Response time and throughput measurement
- **Reliability Testing**: Error handling and edge case validation

### Development Workflow
- **Continuous Integration**: Automated testing in CI/CD pipelines
- **Pre-deployment Validation**: Ensure services work before deployment
- **Service Integration**: Test service interactions and dependencies
- **Quality Assurance**: Automated quality checks for translated code

## 🔮 Future Enhancements

### Translation Features
- **Multi-Provider Support**: Support for Anthropic Claude, Google Gemini, and local models
- **Batch Translation**: Translate multiple projects simultaneously
- **Translation Templates**: Pre-defined translation patterns for common scenarios
- **Code Quality Analysis**: Automated code quality assessment for translated code
- **Translation Validation**: Built-in validation of translated code syntax and structure

### Testing Features
- **Parallel Test Execution**: Run multiple scenarios concurrently
- **Test Report Generation**: HTML/PDF report generation with visual comparisons
- **Service Discovery**: Automatic service detection and testing
- **Performance Metrics**: Response time and throughput measurement
- **Custom Validators**: Pluggable validation mechanisms
- **Database Integration**: Support for database-backed services

### System Features
- **Web Interface**: Browser-based UI for translation and testing
- **API Endpoints**: REST API for programmatic access
- **Plugin System**: Extensible architecture for custom providers and tools
- **Cloud Integration**: Support for cloud-based LLM providers and deployment
- **Translation History**: Track and compare translation results over time