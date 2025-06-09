import eventlet
eventlet.monkey_patch()

import os
import sys
from flask import Flask, session
from flask_socketio import join_room, leave_room # Added join_room, leave_room
from datetime import timedelta

# Check if we're running on Windows
IS_WINDOWS = sys.platform.startswith('win')

# Only import Flask-Session and Redis if we're not in development mode on Windows
# This avoids compatibility issues with eventlet and Windows
if not (IS_WINDOWS and os.environ.get('FLASK_ENV') == 'development'):
    import redis
    from flask_session import Session # Added for Flask-Session

# Import models and db from models.py
from .models import db, User, ShoppingList, ListItem, ListShare

# Import extensions from extensions.py
from .extensions import login_manager, socketio
from flask_migrate import Migrate

migrate = Migrate()

def create_app(config_overrides=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # Configuration settings
    # Load SECRET_KEY from environment variable, with a default for development
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_very_secret_key_for_dev')
    # Load DATABASE_URL from environment variable, with a default SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shopping_list.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Session configuration
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365) # 1 year duration
    app.config['SESSION_PERMANENT'] = True # Make sessions permanent by default
    
    # Only use Flask-Session if not in development mode on Windows
    if not (IS_WINDOWS and os.environ.get('FLASK_ENV') == 'development'):
        app.config['SESSION_TYPE'] = os.environ.get('SESSION_TYPE', 'filesystem') # Use 'redis' in production, 'filesystem' in development
        app.config['SESSION_USE_SIGNER'] = True # Encrypt session cookie
        
        # Only configure Redis if SESSION_TYPE is redis
        if app.config['SESSION_TYPE'] == 'redis':
            app.config['SESSION_REDIS'] = redis.StrictRedis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    else:
        # For Windows development, use Flask's default session handling
        # which uses the SECRET_KEY to sign the session cookie
        app.config['SESSION_TYPE'] = 'null'
    
    # REMEMBER_COOKIE settings for Flask-Login's "remember me" functionality
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=365) # 1 year
    app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True

    if config_overrides:
        app.config.update(config_overrides)

    # Specific test configurations
    if app.config.get('TESTING'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('TEST_DATABASE_URL', 'sqlite:///:memory:')
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['LOGIN_DISABLED'] = False
        app.config['SECRET_KEY'] = 'test_secret_key' # Consistent key for tests

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Only initialize Flask-Session if not in development mode on Windows AND not testing
    if not (IS_WINDOWS and os.environ.get('FLASK_ENV') == 'development') and not app.config.get('TESTING', False):
        Session(app) # Initialize Flask-Session

    socketio.init_app(app, async_mode='eventlet', message_queue=os.environ.get('SOCKETIO_MESSAGE_QUEUE'))
    migrate.init_app(app, db)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import and register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # For development/testing only, create database tables if they don't exist
    # This is only executed when running the app directly with 'flask run' or 'python -m shopping_list_app'
    # For production, use migrations (flask db upgrade) in your deployment pipeline
    if os.environ.get('FLASK_ENV') == 'development' and os.environ.get('FLASK_RUN_FROM_CLI', 'false').lower() == 'true':
        with app.app_context():
            try:
                db.create_all()
                print("Database tables created for development.")
            except Exception as e:
                print(f"Development database initialization error: {e}")

    return app

# Only create the app instance if running directly (not on import)
if __name__ == '__main__':
    app = create_app()
    # Use socketio.run for development to enable WebSocket support
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) # Pass debug to socketio.run

@socketio.on('join_list_room')
def handle_join_list_room(data):
    list_id = data.get('list_id')
    if list_id:
        room_name = f'list_{list_id}'
        join_room(room_name)
        print(f'Client joined room: {room_name}') # Server-side log for debugging
        # You could also emit a confirmation back to the client if needed

@socketio.on('leave_list_room') # Optional: if you want explicit leave handling
def handle_leave_list_room(data):
    list_id = data.get('list_id')
    if list_id:
        room_name = f'list_{list_id}'
        leave_room(room_name)
        print(f'Client left room: {room_name}') # Server-side log for debugging
