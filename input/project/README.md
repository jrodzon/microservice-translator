# Test CRUD Service

A simple CRUD REST API service designed for testing translation capabilities using LLMs.

## Features

- **REST API**: Complete CRUD operations for items
- **FastAPI**: Modern Python web framework with automatic API documentation
- **Docker**: Fully containerized application
- **Health Checks**: Built-in health monitoring
- **Test Cases**: Comprehensive JSON test suite with self-contained data creation
- **Clean State**: No hardcoded data - tests create all required data

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint with service info |
| GET | `/health` | Health check |
| GET | `/items` | Get all items |
| GET | `/items/{id}` | Get item by ID |
| POST | `/items` | Create new item |
| PUT | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Delete item |
| GET | `/items/category/{category}` | Get items by category |

## Quick Start

### Prerequisites
- Docker and docker-compose installed and running
- Bash shell (Linux/macOS) or Git Bash (Windows)

### Option 1: Using Scripts (Recommended)
```bash
# Start the service
./start.sh

# Stop the service
./shutdown.sh
```

### Option 2: Using docker-compose directly
```bash
# Start the service
docker-compose up -d --build

# Stop the service
docker-compose down

# View logs
docker-compose logs -f
```

The service will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Manual Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get all items
curl http://localhost:8000/items

# Create new item
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "A test item", "price": 29.99, "category": "Test"}'

# Get specific item
curl http://localhost:8000/items/1

# Update item
curl -X PUT http://localhost:8000/items/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Item", "price": 39.99}'

# Delete item
curl -X DELETE http://localhost:8000/items/1
```

## Test Cases

The `test_cases.json` file contains comprehensive test scenarios including:

- **Service Health**: Basic health and endpoint verification
- **Data Setup**: Self-contained data creation for testing
- **Basic CRUD Operations**: Create, Read, Update, Delete
- **Error Handling**: 404 errors, validation errors
- **Edge Cases**: Non-existent items, missing fields, special characters
- **Workflow Tests**: Complete CRUD workflows
- **Category Filtering**: Case-insensitive category-based queries
- **Bulk Operations**: Multiple item creation and management
- **Data Validation**: Edge cases with extreme values and unicode

## Development

### Local Development (without Docker)

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

### Project Structure

```
test-project/
├── app.py              # Main FastAPI application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker configuration
├── docker-compose.yml # Docker Compose configuration
├── start.sh           # Startup script (uses docker-compose)
├── shutdown.sh        # Shutdown script (uses docker-compose)
├── test_cases.json    # Test cases definition
└── README.md          # This file
```

## Translation Testing

This service is designed to be translated to different programming languages using LLMs. The structure includes:

- **Clear API contracts** with Pydantic models
- **Comprehensive test cases** for validation
- **Simple business logic** for easy translation
- **Standard REST patterns** for consistency

## API Documentation

When the service is running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.
