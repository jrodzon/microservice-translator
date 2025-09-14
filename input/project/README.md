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

Build and run the docker image:

```bash
docker run -p 8000:8000 --rm -it $(docker build -q .)
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

## API Documentation

When the service is running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.
