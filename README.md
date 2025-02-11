# Django Migrations MCP Service

A Model Context Protocol (MCP) service for managing Django migrations in distributed environments. This service wraps Django's migration commands and exposes them as MCP endpoints, making it easy to manage migrations across multiple services and integrate with CI/CD pipelines.

## Features

- Check migration status (equivalent to `showmigrations`)
- Create new migrations with validation (equivalent to `makemigrations`)
- Apply migrations with safety checks (equivalent to `migrate`)
- Additional validation and safety checks:
  - Sequential migration order verification
  - Conflict detection
  - Dependency validation
  - Safety analysis of migration operations

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/mrrobotke/django-migrations-mcp.git
cd django-migrations-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables:

```bash
export DJANGO_SETTINGS_MODULE="your_project.settings"
export MCP_SERVICE_PORT=8000  # Optional, defaults to 8000
```

## Usage

### Running the Service

1. Directly with Python:
```bash
python -m migrations_mcp.service
```

2. Using Docker:
```bash
docker build -t django-migrations-mcp .
docker run -e DJANGO_SETTINGS_MODULE=your_project.settings \
          -v /path/to/your/django/project:/app/project \
          -p 8000:8000 \
          django-migrations-mcp
```

### MCP Endpoints

1. Show Migrations:
```python
from mcp import MCPClient

client = MCPClient()
migrations = await client.call("show_migrations")
```

2. Make Migrations:
```python
result = await client.call("make_migrations", {
    "app_labels": ["myapp"],  # Optional
    "dry_run": True  # Optional
})
```

3. Apply Migrations:
```python
result = await client.call("migrate", {
    "app_label": "myapp",  # Optional
    "migration_name": "0001",  # Optional
    "fake": False,  # Optional
    "plan": True  # Optional
})
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Django Migrations Check

on:
  pull_request:
    paths:
      - '*/migrations/*.py'
      - '*/models.py'

jobs:
  check-migrations:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Start MCP service
      run: |
        python -m migrations_mcp.service &
    
    - name: Check migrations
      run: |
        python ci/check_migrations.py
```

Example check_migrations.py script:

```python
import asyncio
from mcp import MCPClient

async def check_migrations():
    client = MCPClient()
    
    # Check current status
    migrations = await client.call("show_migrations")
    
    # Try making migrations
    result = await client.call("make_migrations", {"dry_run": True})
    if not result.success:
        print(f"Error: {result.message}")
        exit(1)
    
    print("Migration check passed!")

if __name__ == "__main__":
    asyncio.run(check_migrations())
```

## Development

### Running Tests

```bash
pytest migrations_mcp/tests/
```

### Code Style

The project follows PEP 8 guidelines. Format your code using:

```bash
black migrations_mcp/
isort migrations_mcp/
```

## License

MIT License. See LICENSE file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Docker Usage

The project includes a `docker-commands.json` file that provides structured commands for different deployment scenarios. You can use these commands directly or parse them in your scripts.

### Available Docker Configurations

1. **Redis MCP Server**
```bash
# Run Redis MCP server
docker run -i --rm mcp/redis redis://host.docker.internal:6379
```

2. **Django Migrations MCP Server**
```bash
# Basic setup
docker run -d \
  --name django-migrations-mcp \
  -e DJANGO_SETTINGS_MODULE=your_project.settings \
  -e MCP_SERVICE_PORT=8000 \
  -v /path/to/your/django/project:/app/project \
  -p 8000:8000 \
  django-migrations-mcp

# With Redis integration
docker run -d \
  --name django-migrations-mcp \
  -e DJANGO_SETTINGS_MODULE=your_project.settings \
  -e MCP_SERVICE_PORT=8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  -v /path/to/your/django/project:/app/project \
  -p 8000:8000 \
  --network host \
  django-migrations-mcp
```

3. **Development Environment**
```bash
# Using docker-compose
docker-compose up -d --build
```

4. **Testing Environment**
```bash
# Run tests in container
docker run --rm \
  -e DJANGO_SETTINGS_MODULE=your_project.settings \
  -e PYTHONPATH=/app \
  -v ${PWD}:/app \
  django-migrations-mcp \
  pytest
```

5. **Production Environment**
```bash
# Production setup with health check
docker run -d \
  --name django-migrations-mcp \
  -e DJANGO_SETTINGS_MODULE=your_project.settings \
  -e MCP_SERVICE_PORT=8000 \
  -e REDIS_URL=redis://your-redis-host:6379 \
  -v /path/to/your/django/project:/app/project \
  -p 8000:8000 \
  --restart unless-stopped \
  --network your-network \
  django-migrations-mcp
```

### Using the Commands Programmatically

You can parse and use the commands programmatically:

```python
import json
import subprocess

# Load commands
with open('docker-commands.json') as f:
    commands = json.load(f)

# Run Redis MCP server
redis_config = commands['mcpServers']['redis']
subprocess.run([redis_config['command']] + redis_config['args'])

# Run Django Migrations MCP server
django_config = commands['mcpServers']['djangoMigrations']
subprocess.run([django_config['command']] + django_config['args'])
```

### Network Setup

1. **Development Network**
```bash
docker network create mcp-dev-network
```

2. **Production Network**
```bash
docker network create --driver overlay --attachable mcp-prod-network
```

### Using MCP Tools

The service exposes several endpoints that can be accessed via curl or any HTTP client:

1. **Show Migrations**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "show_migrations"}'
```

2. **Make Migrations**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "make_migrations", "params": {"apps": ["your_app"]}}'
```

3. **Apply Migrations**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "migrate", "params": {"app": "your_app"}}'
``` 