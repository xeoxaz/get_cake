@echo off
setlocal
cd /d "%~dp0"

if not exist .venv (
	echo Creating virtual environment...
	py -3 -m venv .venv || (
		echo Failed to create venv. Ensure Python is installed and on PATH.
		pause
		exit /b 1
	)
)

call .venv\Scripts\activate.bat || (
	echo Failed to activate venv.
	pause
	exit /b 1
)

python -c "import pynput, pyautogui" 1>nul 2>nul
if errorlevel 1 (
	echo Installing dependencies...
	python -m pip install --upgrade pip >nul
	pip install -r requirements.txt || (
		echo Failed to install dependencies.
		pause
		exit /b 1
	)
)

echo Starting app... Hotkeys: [r]=record, [s]=stop, [p]=play, [c]=clear, [l]=loop.
python app.py

endlocal