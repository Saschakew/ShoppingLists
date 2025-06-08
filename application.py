# This file is the entry point for AWS Elastic Beanstalk.
# It imports the Flask app instance from your application package.

from shopping_list_app.app import app as application

# If you also need to expose socketio directly for some reason, you can import it too,
# but gunicorn will typically interact with the 'application' callable.
# from shopping_list_app.app import socketio

if __name__ == '__main__':
    # This part is not strictly necessary for Elastic Beanstalk as it uses the Procfile,
    # but can be useful for local testing with a production-like setup.
    # Note: Gunicorn should be used for production, not this direct run.
    application.run()
