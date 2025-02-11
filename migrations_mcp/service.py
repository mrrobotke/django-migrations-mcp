"""
Django Migrations MCP Service.
This service provides endpoints for managing Django migrations through MCP.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

from django.core.management import call_command
from django.db import connection
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools.base import Tool
from pydantic import BaseModel
from asgiref.sync import sync_to_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MigrationStatus(BaseModel):
    """Model representing migration status."""
    app: str
    name: str
    applied: bool
    dependencies: List[str] = []

class MigrationResult(BaseModel):
    """Model representing migration operation result."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None

class DjangoMigrationsMCP(FastMCP):
    """MCP service for managing Django migrations."""

    async def show_migrations(self) -> List[str]:
        """Show all migrations."""
        try:
            @sync_to_async
            def _show_migrations():
                with connection.cursor() as cursor:
                    call_command('showmigrations', stdout=cursor)
                    return cursor.fetchall()
            return await _show_migrations()
        except Exception as e:
            return [f"Error showing migrations: {str(e)}"]

    show_migrations_tool = Tool.from_function(show_migrations)

    async def make_migrations(self, apps: Optional[List[str]] = None) -> MigrationResult:
        """Make migrations for specified apps or all apps."""
        try:
            @sync_to_async
            def _make_migrations():
                call_command('makemigrations', *apps if apps else [])
            await _make_migrations()
            return MigrationResult(
                success=True,
                message="Migrations created successfully"
            )
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Error creating migrations: {str(e)}"
            )

    make_migrations_tool = Tool.from_function(make_migrations)

    async def migrate(self, app: Optional[str] = None) -> MigrationResult:
        """Apply migrations for specified app or all apps."""
        try:
            @sync_to_async
            def _migrate():
                call_command('migrate', app if app else '')
            await _migrate()
            return MigrationResult(
                success=True,
                message="Migrations applied successfully"
            )
        except Exception as e:
            return MigrationResult(
                success=False,
                message=f"Error applying migrations: {str(e)}"
            )

    migrate_tool = Tool.from_function(migrate)

if __name__ == "__main__":
    service = DjangoMigrationsMCP()
    service.run() 