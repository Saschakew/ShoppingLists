import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_socketio import join_room, leave_room # Added join_room, leave_room

# Import models and db from models.py
from .models import db, User, ShoppingList, ListItem, ListShare

# Import extensions from extensions.py
from .extensions import login_manager, socketio


def create_app(config_overrides=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_very_secret_key_here' # Change in production!
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopping_list.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Mobile-optimized settings
    app.config['PERMANENT_SESSION_LIFETIME'] = 31536000  # 1 year in seconds
    app.config['SESSION_PERMANENT'] = True
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['REMEMBER_COOKIE_DURATION'] = 31536000  # 1 year in seconds
    app.config['REMEMBER_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    # app.config['DEBUG'] = debug # Debug will be set by FLASK_DEBUG or app.run() argument

    if config_overrides:
        app.config.update(config_overrides)

    if app.config.get('TESTING'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for simpler form testing
        app.config['LOGIN_DISABLED'] = False # Ensure login is not disabled unless explicitly set in tests

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Simple Socket.IO configuration for better mobile compatibility
    socketio.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login' # Corrected to blueprint name 'auth'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import and register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth') # Add a prefix for auth routes

    # Import and register the main blueprint
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Create database tables if they don't exist
    # This is a simple way for development; for production, use migrations (e.g., Flask-Migrate)
    with app.app_context():
        db.create_all()

    return app

# Create the app instance outside of __name__ == '__main__' check
# This ensures it's available for module imports
app = create_app()

if __name__ == '__main__':
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
