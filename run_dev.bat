@echo off
REM Kill any process using port 5000
echo Checking for processes using port 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5000" ^| find "LISTENING"') do (
    echo Killing process on port 5000 with PID %%a
    taskkill /F /PID %%a
)
echo Starting ShoppingLists development server...

REM Check if virtual environment exists, if not create it
if not exist venv\ (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install or update dependencies
echo Installing/updating dependencies...
pip install -r requirements.txt
pip install flask-migrate

REM Set environment variables
set FLASK_APP=shopping_list_app.app
set FLASK_ENV=development
set FLASK_DEBUG=1
set SESSION_TYPE=filesystem
set FLASK_RUN_FROM_CLI=true

REM Run Flask development server with SocketIO support
echo Starting Flask development server with SocketIO...
python -c "from shopping_list_app.app import socketio, app; socketio.run(app, debug=True, port=5000)"

REM Keep window open if there's an error
pause
