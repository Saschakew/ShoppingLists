@echo off
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

REM Run Flask development server directly
echo Starting Flask development server...
python -m shopping_list_app.app

REM Keep window open if there's an error
pause
