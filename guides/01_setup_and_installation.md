# 1. Setup and Installation Guide

This guide provides instructions for setting up the development environment and running the ShoppingLists application locally.

## Prerequisites

*   **Python:** Ensure you have Python 3 installed (Python 3.8+ recommended). You can download it from [python.org](https://www.python.org/).
*   **Git:** Required for cloning the repository. Download from [git-scm.com](https://git-scm.com/).
*   **(Optional) Redis:** If you plan to test with Redis for session management (as per production setup), you'll need a Redis server running. For local development, the default filesystem session backend is used by `run_dev.bat`.

## Setup Steps

1.  **Clone the Repository:**
    Open your terminal or command prompt and navigate to the directory where you want to store the project. Then, clone the repository:
    ```bash
    git clone <YOUR_REPOSITORY_URL>
    cd ShoppingLists
    ```
    Replace `<YOUR_REPOSITORY_URL>` with the actual URL of your Git repository.

2.  **Set up Virtual Environment and Install Dependencies (Windows):**
    The project includes a `run_dev.bat` script that automates this process on Windows. Simply double-click it or run it from your command prompt:
    ```bash
    run_dev.bat
    ```
    This script will:
    *   Check for and kill any process using port 5000 (or try 5001 if 5000 is busy).
    *   Create a Python virtual environment named `venv` if it doesn't exist.
    *   Activate the virtual environment.
    *   Install or update all required dependencies from `requirements.txt` (including `flask-migrate`).
    *   Set necessary environment variables for development (`FLASK_APP`, `FLASK_ENV`, `FLASK_DEBUG`, `SESSION_TYPE=filesystem`).
    *   Start the Flask development server with SocketIO support.

3.  **Manual Setup (Linux/macOS or if `run_dev.bat` is not used):**

    *   **Create and Activate Virtual Environment:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate  # On Linux/macOS
        # venv\Scripts\activate   # On Windows (if not using run_dev.bat)
        ```

    *   **Install Dependencies:**
        ```bash
        pip install -r requirements.txt
        pip install flask-migrate # Ensure flask-migrate is installed
        ```

    *   **Set Environment Variables:**
        Before running the application, you need to set the following environment variables:
        ```bash
        export FLASK_APP=shopping_list_app.app
        export FLASK_ENV=development
        export FLASK_DEBUG=1
        export SESSION_TYPE=filesystem # For local development
        # For production, you might use 'redis' and configure REDIS_URL
        # export SECRET_KEY='your_very_secret_key_here' # Important for sessions
        ```
        *Note: A `SECRET_KEY` is crucial for session security. While Flask can run with a default debug key, it's good practice to set one, especially if you are testing features that rely heavily on sessions.*
        *For managing environment variables more robustly, consider using a `.env` file with `python-dotenv` (which is in `requirements.txt`). Create a `.env` file in the project root with your variables, e.g.:*
        ```
        FLASK_APP=shopping_list_app.app
        FLASK_ENV=development
        FLASK_DEBUG=1
        SESSION_TYPE=filesystem
        SECRET_KEY=your_actual_secret_key
        ```

    *   **Initialize/Upgrade Database (if applicable):**
        If this is the first time setting up or if there are new database migrations:
        ```bash
        flask db init  # Only if the migrations folder doesn't exist
        flask db migrate -m "Initial migration" # Or a descriptive message for new changes
        flask db upgrade
        ```
        *(The `application.py` seems to handle `db.create_all()`, but for a production-like setup with migrations, these are the commands.)*

4.  **Run the Development Server (Manual):**
    If you performed the manual setup, run the application using:
    ```bash
    python -c "from shopping_list_app.app import create_app, socketio; app = create_app(); socketio.run(app, debug=True, port=5000)"
    ```
    Or, if not using SocketIO directly for a simple run (though `run_dev.bat` uses SocketIO):
    ```bash
    flask run
    ```

## Accessing the Application

Once the server is running, you can access the application by opening your web browser and navigating to:
`http://127.0.0.1:5000` (or `http://127.0.0.1:5001` if port 5000 was busy and `run_dev.bat` switched to 5001).

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Next Steps

With the application running locally, you can proceed to explore its features or start development. Refer to other guides in this series for more detailed information on specific aspects of the project.
