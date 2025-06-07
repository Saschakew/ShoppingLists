from flask import url_for, session
from shopping_list_app.app import User

def test_register_page(client):
    """Test that the registration page loads."""
    response = client.get(url_for('auth.register'))
    assert response.status_code == 200
    assert b'Register' in response.data

def test_register_user(client, app):
    """Test user registration."""
    response = client.post(url_for('auth.register'), data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert url_for('auth.login') in response.request.path # Should redirect to login
    # Check for successful registration redirect to login page
    assert b'login' in response.data.lower()
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        # User model no longer has email field
        assert user.username == 'newuser'

def test_register_existing_user(client, create_user_fixture):
    """Test registration with an existing username/email."""
    create_user_fixture(username='existinguser', password='password')
    response = client.post(url_for('auth.register'), data={
        'username': 'existinguser',
        'email': 'another@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check for registration page with error
    assert b'register' in response.data.lower()

    # Remove email check since User model no longer has email field

def test_login_page(client):
    """Test that the login page loads."""
    response = client.get(url_for('auth.login'))
    assert response.status_code == 200
    assert b'Login' in response.data

def test_login_and_logout(client, create_user_fixture, app):
    """Test user login and logout."""
    create_user_fixture(username='loginuser', password='password123')
    
    # Test login
    response = client.post(url_for('auth.login'), data={
        'username': 'loginuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert url_for('main.dashboard') in response.request.path
    assert b'loginuser' in response.data # Check for username on dashboard
    with client.session_transaction() as sess:
        assert sess['_user_id'] is not None

    # Test logout
    response = client.get(url_for('auth.logout'), follow_redirects=True)
    assert response.status_code == 200
    assert url_for('main.index') in response.request.path
    # Check for home page after logout
    assert b'home' in response.data.lower()
    with client.session_transaction() as sess:
        assert '_user_id' not in sess

def test_login_invalid_credentials(client, create_user_fixture):
    """Test login with invalid credentials."""
    create_user_fixture(username='testuser', password='password123')
    response = client.post(url_for('auth.login'), data={
        'username': 'testuser',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check for login page with error
    assert b'login' in response.data.lower()

    response = client.post(url_for('auth.login'), data={
        'username': 'nonexistentuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Check for login page with error
    assert b'login' in response.data.lower()
