# 8. Testing Strategy

This guide outlines the testing strategy for the ShoppingLists application, how to run existing tests, and how to write new ones using Pytest and `pytest-flask`.

## 1. Overview

Automated tests are crucial for ensuring the application's stability, correctness, and maintainability. They help catch regressions early and provide confidence when refactoring or adding new features.

This project uses:
*   **Pytest:** A powerful and flexible Python testing framework.
*   **pytest-flask:** A Pytest plugin that provides useful fixtures and utilities for testing Flask applications.

Tests are primarily focused on backend logic, including routes, authentication, database interactions, and core application functionality.

## 2. Directory Structure

*   All tests are located in the `tests/` directory at the root of the project.
*   **`tests/conftest.py`**: This file contains shared Pytest fixtures (helper functions and objects) that are available to all test files. It's central to setting up the testing environment.
*   Test files are typically named `test_*.py` (e.g., `test_auth.py`, `test_main.py`) and group related tests for specific modules or features.

## 3. Running Tests

1.  **Activate Virtual Environment:** Ensure your Python virtual environment is activated:
    ```bash
    # On Windows (Git Bash or similar)
    source venv/Scripts/activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

2.  **Navigate to Project Root:** Open your terminal in the project's root directory (`ShoppingLists`).

3.  **Run All Tests:**
    ```bash
    pytest
    ```
    Or, explicitly using the Python module:
    ```bash
    python -m pytest
    ```

4.  **Running Specific Tests:**
    *   **Run a specific file:**
        ```bash
        pytest tests/test_auth.py
        ```
    *   **Run a specific test function within a file:**
        ```bash
        pytest tests/test_auth.py::test_login_page
        ```
    *   **Run tests matching a keyword expression (`-k`):**
        ```bash
        pytest -k "login and not register"
        ```

5.  **Common Pytest Options:**
    *   `-v` or `--verbose`: Increase verbosity, showing each test function name.
    *   `-s`: Show any `print()` statements from your tests (useful for debugging).
    *   `--lf` or `--last-failed`: Run only the tests that failed during the last run.
    *   `--pdb`: Enter the Python debugger on test failure.

## 4. Writing Tests

### Basic Test Structure

Test functions should:
*   Be defined within a `test_*.py` file.
*   Have names starting with `test_` (e.g., `def test_my_feature():`).
*   Use Pytest fixtures for setup and dependencies.
*   Include assertions to check expected outcomes.

```python
# Example: tests/test_example.py
from flask import url_for

def test_example_route(client): # 'client' is a fixture from conftest.py
    response = client.get(url_for('main.index'))
    assert response.status_code == 200
    assert b"Welcome" in response.data
```

### Key Fixtures (from `tests/conftest.py`)

*   **`app` (session-scoped):** Provides the Flask application instance, configured for testing (e.g., in-memory SQLite database, `TESTING=True`). Database tables are created at the start of the session and dropped at the end.
*   **`db` (function-scoped):** Provides a SQLAlchemy database session. It ensures the session is cleaned up after each test.
*   **`client`:** Provides a Flask test client instance. Use this to make requests to your application (e.g., `client.get('/login')`, `client.post('/submit-form', data={...})`).
*   **`runner`:** Provides a test runner for Flask CLI commands.
*   **`auth_client_fixture` (factory fixture):** Returns a test client that is pre-authenticated. You call it like a function to get an authenticated client:
    ```python
    def test_protected_route(auth_client_fixture):
        authenticated_client = auth_client_fixture(username='testuser', password='password')
        response = authenticated_client.get(url_for('main.dashboard'))
        assert response.status_code == 200
    ```
*   **`create_user_fixture` (factory fixture):** Creates a user directly in the database and returns the user object. Call it like a function:
    ```python
    def test_user_exists(create_user_fixture, app):
        user = create_user_fixture(username='testuser', password='password123')
        with app.app_context():
            assert User.query.filter_by(username='testuser').first() is not None
    ```

### Making Requests and Assertions

*   Use `client.get()`, `client.post()`, `client.put()`, `client.delete()` to simulate HTTP requests.
*   Pass `data={...}` for form data in POST requests.
*   Pass `json={...}` for JSON payloads.
*   Set `follow_redirects=True` if you expect a redirect and want to test the final response.
*   Use `url_for('blueprint_name.route_function_name')` to generate URLs dynamically.
*   **Assertions:**
    *   `assert response.status_code == 200`
    *   `assert b'Expected Text' in response.data` (for HTML content)
    *   `assert response.json == {'key': 'value'}` (for JSON responses)
    *   `assert 'redirect_url_part' in response.request.path` (after a redirect)

### Testing Database Interactions

*   Use the `db` fixture and the `app` fixture's application context.
    ```python
    from shopping_list_app.models import User # Or your specific model

    def test_user_creation_in_db(app, db, create_user_fixture):
        create_user_fixture(username='dbuser', password='password')
        with app.app_context():
            user = User.query.filter_by(username='dbuser').first()
            assert user is not None
            assert user.username == 'dbuser'
    ```

### Testing Authentication

*   Use `auth_client_fixture` for routes requiring login.
*   Test login/logout flows explicitly (see `tests/test_auth.py` for examples).
*   Check session content using `with client.session_transaction() as sess:`.

## 5. `conftest.py` Details

The `tests/conftest.py` file is crucial. It sets up:
*   The application factory (`create_app`) is called with test-specific configurations:
    *   `TESTING = True`
    *   `SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'` (fast, isolated database for each test session)
    *   `WTF_CSRF_ENABLED = False` (simplifies form testing)
    *   `SESSION_TYPE = 'null'` (disables Flask-Session to avoid issues with eventlet/filesystem in tests)
*   Database creation (`_db.create_all()`) and teardown (`_db.drop_all()`).
*   The various fixtures (`app`, `db`, `client`, `runner`, `auth_client_fixture`, `create_user_fixture`) described above.

## 6. Test Coverage (Recommended)

While not currently configured, using a tool like `pytest-cov` is highly recommended to measure test coverage.

To add coverage:
1.  Install: `pip install pytest-cov`
2.  Run tests with coverage: `pytest --cov=shopping_list_app --cov-report=html`
    (This will generate an HTML report in an `htmlcov/` directory.)

This helps identify parts of your codebase that are not covered by tests.

## 7. Note on JavaScript Tests

The file `tests/test_offline_manager.js` appears to be a JavaScript test file. This guide primarily focuses on backend Python testing with Pytest. If client-side JavaScript testing is a requirement, a separate JavaScript testing framework (e.g., Jest, Mocha) and runner would typically be used for those tests.
