"""Test Django migrations with MCP service."""
import os
import pytest
from migrations_mcp.service import DjangoMigrationsMCP

# Configure Django settings for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'testproject.settings')

@pytest.fixture
def service():
    """Create a DjangoMigrationsMCP service instance."""
    return DjangoMigrationsMCP()

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_show_migrations(service):
    """Test show_migrations command."""
    result = await service.show_migrations()
    assert isinstance(result, list)
    # At least one migration should exist (initial migration)
    assert len(result) > 0

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_make_migrations(service):
    """Test make_migrations command."""
    result = await service.make_migrations(['testapp'])
    assert result.success
    assert "Migrations created successfully" in result.message

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_migrate(service):
    """Test migrate command."""
    result = await service.migrate('testapp')
    assert result.success
    assert "Migrations applied successfully" in result.message 