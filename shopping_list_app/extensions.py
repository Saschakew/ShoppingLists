"""
Flask extensions and shared resources.
This module initializes Flask extensions that are used across the application.
"""
from flask_socketio import SocketIO
from flask_login import LoginManager
import os

# Initialize extensions without app
login_manager = LoginManager()

# Configure SocketIO with appropriate CORS settings for the subdomain
cors_origins = ["*"]
if os.environ.get('SERVER_NAME'):
    # Add specific origins for production with subdomain
    cors_origins = [
        f"http://{os.environ.get('SERVER_NAME')}", 
        f"https://{os.environ.get('SERVER_NAME')}"
    ]

socketio = SocketIO(cors_allowed_origins=cors_origins, async_mode='eventlet')
