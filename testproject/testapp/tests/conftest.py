"""Test configuration for pytest."""
import pytest
from django.conf import settings

@pytest.fixture(scope="function")
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass

@pytest.fixture(scope="session")
def django_db_setup():
    """Configure Django database for tests."""
    settings.DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    } 