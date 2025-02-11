# Django Migrations MCP Service

A Model Context Protocol (MCP) service for managing Django migrations in distributed environments. This service wraps Django's migration commands and exposes them as MCP endpoints, making it easy to manage migrations across multiple services and integrate with CI/CD pipelines.

## Features

- Asynchronous migration management
- Distributed migration coordination
- Migration status checks (`showmigrations`)
- Migration creation with validation (`makemigrations`)
- Migration application with safety checks (`migrate`)
- In-memory SQLite support for testing
- Docker support for production deployment

## Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/mrrobotke/django-migrations-mcp.git
cd django-migrations-mcp
```

[Rest of the README content...]