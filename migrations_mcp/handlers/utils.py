"""Utility functions for migration validation and checks."""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from django.apps import apps
from django.db.migrations.loader import MigrationLoader


def get_migration_files(app_label: str) -> List[str]:
    """Get all migration files for an app."""
    app_config = apps.get_app_config(app_label)
    migrations_dir = Path(app_config.path) / 'migrations'
    
    if not migrations_dir.exists():
        return []
    
    return [
        f.name for f in migrations_dir.iterdir()
        if f.is_file() and f.name.endswith('.py')
        and not f.name.startswith('__')
    ]

def parse_migration_number(filename: str) -> Optional[int]:
    """Extract migration number from filename."""
    match = re.match(r'^(\d{4})_.*\.py$', filename)
    return int(match.group(1)) if match else None

def check_sequential_order(app_label: str) -> Tuple[bool, List[str]]:
    """Check if migrations are in sequential order."""
    files = get_migration_files(app_label)
    numbers = [parse_migration_number(f) for f in files]
    numbers = [n for n in numbers if n is not None]
    
    if not numbers:
        return True, []
    
    expected = list(range(min(numbers), max(numbers) + 1))
    missing = set(expected) - set(numbers)
    
    if missing:
        return False, [
            f"Missing migration number(s): {', '.join(map(str, missing))}"
        ]
    return True, []

def detect_conflicts(app_label: str) -> List[str]:
    """Detect migration conflicts."""
    loader = MigrationLoader(None)
    conflicts = []
    
    # Check for conflicts in the migration graph
    if loader.graph.conflicts:
        for app, nodes in loader.graph.conflicts.items():
            if app == app_label:
                conflicts.extend([
                    f"Conflict in {app}: migrations {', '.join(nodes)}"
                ])
    
    return conflicts

def validate_dependencies(app_label: str) -> List[str]:
    """Validate migration dependencies."""
    loader = MigrationLoader(None)
    errors = []
    
    for migration in loader.disk_migrations.values():
        if migration.app_label == app_label:
            for dep_app, dep_name in migration.dependencies:
                # Check if dependency exists
                if (dep_app, dep_name) not in loader.disk_migrations:
                    errors.append(
                        f"Missing dependency: {dep_app}.{dep_name} "
                        f"required by {app_label}.{migration.name}"
                    )
    
    return errors

def get_migration_plan(app_label: Optional[str] = None) -> List[Tuple[str, bool]]:
    """Get the migration plan showing what needs to be applied."""
    from django.db import connections
    from django.db.migrations.executor import MigrationExecutor
    
    executor = MigrationExecutor(connections['default'])
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    
    if app_label:
        plan = [
            (migration, backwards)
            for migration, backwards in plan
            if migration.app_label == app_label
        ]
    
    return plan

def check_migration_safety(
    app_label: str,
    migration_name: str
) -> Tuple[bool, List[str]]:
    """Check if a migration is safe to apply."""
    warnings = []
    is_safe = True
    
    # Load the migration
    loader = MigrationLoader(None)
    try:
        migration = loader.get_migration_by_prefix(app_label, migration_name)
    except KeyError:
        return False, ["Migration not found"]
    
    # Check for dangerous operations
    for operation in migration.operations:
        op_name = operation.__class__.__name__
        
        if op_name == 'DeleteModel':
            warnings.append(f"Warning: Migration deletes model {operation.name}")
            is_safe = False
        
        elif op_name == 'RemoveField':
            warnings.append(
                f"Warning: Migration removes field {operation.model_name}."
                f"{operation.name}"
            )
            is_safe = False
        
        elif op_name == 'AlterField':
            warnings.append(
                f"Warning: Migration alters field {operation.model_name}."
                f"{operation.name}"
            )
    
    return is_safe, warnings 