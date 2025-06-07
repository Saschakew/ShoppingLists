import sys
import os

# Add the project root directory to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest
from shopping_list_app.app import create_app, db as _db # Renamed to avoid conflict with fixture
from shopping_list_app.app import User # Import User for creating test users

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    app_instance = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False, # Disable CSRF for tests
        'LOGIN_DISABLED': False, # Ensure login is active for testing auth
        'SERVER_NAME': 'localhost.test' # Required for url_for to work without active request context in some cases
    })

    # Establish an application context before creating the tables.
    with app_instance.app_context():
        _db.create_all()

    yield app_instance

    # Teardown: clear out the database
    with app_instance.app_context():
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """Provide the transactional fixtures with access to the database."""
    with app.app_context():
        yield _db
        # Clean up the database session to ensure no pending transactions interfere with subsequent tests.
        # For an in-memory SQLite database, this might be less critical than with a persistent DB,
        # but it's good practice.
        _db.session.remove()
        # If you want to clear all data from tables between tests (within the same session-scoped app context):
        # for table in reversed(_db.metadata.sorted_tables):
        #     _db.session.execute(table.delete())
        # _db.session.commit()

@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture()
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client_fixture(db, app): # Removed client dependency
    """A test client that is pre-authenticated with a test user."""
    def _auth_client(username='testuser', password='password'):
        # Create a new test client for each authenticated user
        test_client = app.test_client()
        
        with app.app_context(): # Ensure operations are within app context
            # Register user
            test_client.post('/auth/register', data={'username': username, 'password': password, 'confirm_password': password})
            
            # Login user
            response = test_client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)
            assert response.status_code == 200 # Should redirect to dashboard
        return test_client
    return _auth_client

@pytest.fixture
def create_user_fixture(db, app):
    """Fixture to create a user directly in the database."""
    def _create_user(username, password):
        with app.app_context(): # Ensure operations are within app context
            user = User(username=username)
            user.set_password(password)
            _db.session.add(user)
            _db.session.commit()
            return user
    return _create_user
