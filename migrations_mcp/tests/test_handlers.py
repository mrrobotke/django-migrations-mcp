"""Tests for the Django Migrations MCP service."""
import os
import pytest
from pathlib import Path
from typing import List, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

from django.apps import apps
from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader

from migrations_mcp.service import DjangoMigrationsMCP
from migrations_mcp.handlers.utils import (
    check_sequential_order,
    detect_conflicts,
    validate_dependencies,
    check_migration_safety
)

@pytest.fixture
def service():
    """Create a DjangoMigrationsMCP service instance."""
    return DjangoMigrationsMCP()

@pytest.fixture
def mock_app_config():
    """Mock Django app configuration."""
    mock = MagicMock()
    mock.path = str(Path(__file__).parent / 'test_migrations')
    return mock

@pytest.fixture
def mock_migration_loader():
    """Mock Django migration loader."""
    mock = MagicMock()
    mock.disk_migrations = {}
    mock.graph.conflicts = {}
    return mock

@pytest.mark.asyncio
async def test_show_migrations(service):
    """Test show_migrations handler."""
    with patch('django.core.management.call_command') as mock_call:
        mock_call.return_value = None
        result = await service.show_migrations()
        assert isinstance(result, list)
        mock_call.assert_called_once_with(
            'showmigrations',
            list=True,
            _callback=pytest.ANY
        )

@pytest.mark.asyncio
async def test_make_migrations(service):
    """Test make_migrations handler."""
    with patch('django.core.management.call_command') as mock_call:
        mock_call.return_value = "Created migration"
        result = await service.make_migrations(
            app_labels=['testapp'],
            dry_run=True
        )
        assert result.success
        assert "successfully" in result.message
        mock_call.assert_called_once_with(
            'makemigrations',
            'testapp',
            dry_run=True,
            verbosity=2
        )

@pytest.mark.asyncio
async def test_migrate(service):
    """Test migrate handler."""
    with patch('django.core.management.call_command') as mock_call:
        mock_call.return_value = "Applied migration"
        result = await service.migrate(
            app_label='testapp',
            migration_name='0001',
            fake=True
        )
        assert result.success
        assert "successfully" in result.message
        mock_call.assert_called_once_with(
            'migrate',
            'testapp',
            '0001',
            fake=True,
            plan=False,
            verbosity=2
        )

def test_check_sequential_order(mock_app_config):
    """Test migration sequential order checking."""
    with patch('django.apps.apps.get_app_config', return_value=mock_app_config):
        # Create test migration files
        migrations_dir = Path(mock_app_config.path)
        migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test migration files
        migrations = ['0001_initial.py', '0002_update.py', '0004_change.py']
        for migration in migrations:
            (migrations_dir / migration).touch()
        
        is_sequential, errors = check_sequential_order('testapp')
        assert not is_sequential
        assert any('Missing migration number(s): 3' in error for error in errors)
        
        # Cleanup
        for migration in migrations:
            (migrations_dir / migration).unlink()
        migrations_dir.rmdir()

def test_detect_conflicts(mock_migration_loader):
    """Test migration conflict detection."""
    with patch('migrations_mcp.handlers.utils.MigrationLoader',
              return_value=mock_migration_loader):
        mock_migration_loader.graph.conflicts = {
            'testapp': ['0001_initial', '0001_other']
        }
        
        conflicts = detect_conflicts('testapp')
        assert len(conflicts) == 1
        assert 'Conflict in testapp' in conflicts[0]

def test_validate_dependencies(mock_migration_loader):
    """Test migration dependency validation."""
    with patch('migrations_mcp.handlers.utils.MigrationLoader',
              return_value=mock_migration_loader):
        # Mock a migration with missing dependency
        migration = MagicMock()
        migration.app_label = 'testapp'
        migration.name = '0001_initial'
        migration.dependencies = [('other_app', '0001_initial')]
        
        mock_migration_loader.disk_migrations = {
            ('testapp', '0001_initial'): migration
        }
        
        errors = validate_dependencies('testapp')
        assert len(errors) == 1
        assert 'Missing dependency' in errors[0]

def test_check_migration_safety():
    """Test migration safety checking."""
    with patch('migrations_mcp.handlers.utils.MigrationLoader') as mock_loader:
        # Mock a migration with unsafe operations
        migration = MagicMock()
        delete_op = MagicMock()
        delete_op.__class__.__name__ = 'DeleteModel'
        delete_op.name = 'TestModel'
        migration.operations = [delete_op]
        
        mock_loader_instance = MagicMock()
        mock_loader_instance.get_migration_by_prefix.return_value = migration
        mock_loader.return_value = mock_loader_instance
        
        is_safe, warnings = check_migration_safety('testapp', '0001')
        assert not is_safe
        assert len(warnings) == 1
        assert 'deletes model' in warnings[0]

if __name__ == '__main__':
    pytest.main([__file__]) 