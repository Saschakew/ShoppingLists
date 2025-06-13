# This file is the entry point for AWS Elastic Beanstalk.
# It imports the Flask app instance from your application package.

from shopping_list_app.app import create_app

application = create_app()

# If you also need to expose socketio directly for some reason, you can import it too,
# but gunicorn will typically interact with the 'application' callable.
# from shopping_list_app.app import socketio

if __name__ == '__main__':
    # This block allows running the app directly with `python application.py` for local testing.
    # It's not used by Gunicorn in production but can be helpful.
    # For SocketIO support, Flask-SocketIO's run method is needed.
    from shopping_list_app.extensions import socketio # Ensure socketio is initialized in extensions.py and imported here
    
    # Consider making host, port, and debug configurable via environment variables for flexibility.
    # For true development, use run_dev.bat. For production-like local test, debug=False.
    socketio.run(application, host='0.0.0.0', port=5000, debug=False, use_reloader=False)

