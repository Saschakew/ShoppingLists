"""
Flask extensions and shared resources.
This module initializes Flask extensions that are used across the application.
"""
from flask_socketio import SocketIO
from flask_login import LoginManager

# Initialize extensions
# These will be configured later in the create_app function
login_manager = LoginManager()
# Initialize Socket.IO with simple defaults
socketio = SocketIO(cors_allowed_origins="*", async_mode='eventlet')
