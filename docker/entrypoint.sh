#!/bin/bash
set -e

# Validate environment variables
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    echo "Error: DJANGO_SETTINGS_MODULE environment variable is required"
    exit 1
fi

# Wait for database if needed (uncomment and modify as needed)
# until nc -z $DB_HOST $DB_PORT; do
#     echo "Waiting for database..."
#     sleep 1
# done

# Start the MCP service
exec python -m migrations_mcp.service 