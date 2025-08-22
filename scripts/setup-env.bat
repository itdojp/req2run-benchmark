@echo off
REM Req2Run Benchmark Environment Setup Script
REM For Windows Command Prompt (CMD)

setlocal enabledelayedexpansion

REM Header
echo ==================================
echo Req2Run Benchmark Environment Setup
echo ==================================
echo.

REM Check Python version
echo [*] Checking Python version...
python --version 2>nul
if %errorlevel% neq 0 (
    echo [X] Python not found. Please install Python 3.9 or higher
    echo     Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Parse Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found

REM Check if virtual environment already exists
if exist venv (
    echo [!] Virtual environment 'venv' already exists
    set /p RECREATE="Do you want to recreate it? (y/n): "
    
    if /i "!RECREATE!"=="y" (
        echo [*] Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo [*] Using existing virtual environment
    )
)

REM Create virtual environment
if not exist venv (
    echo [*] Creating virtual environment...
    python -m venv venv
    
    if !errorlevel! equ 0 (
        echo [OK] Virtual environment created successfully
    ) else (
        echo [X] Failed to create virtual environment
        echo [!] Trying alternative method with virtualenv...
        
        pip install --user virtualenv
        virtualenv venv
        
        if !errorlevel! neq 0 (
            echo [X] Failed to create virtual environment with virtualenv
            pause
            exit /b 1
        )
    )
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [*] Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements if file exists
if exist requirements.txt (
    echo [*] Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    
    if !errorlevel! equ 0 (
        echo [OK] Dependencies installed successfully
    ) else (
        echo [!] Some dependencies failed to install
        echo [!] You may need to install them manually
    )
) else (
    echo [!] requirements.txt not found in current directory
)

REM Install commonly needed packages for benchmarks
echo [*] Installing common benchmark packages...
pip install click pandas numpy tqdm pytest 2>nul

REM Create .env file if it doesn't exist
if not exist .env (
    echo [*] Creating .env file...
    (
        echo # Req2Run Environment Configuration
        echo PYTHONPATH=.
        echo REQ2RUN_ENV=development
    ) > .env
)

REM Final instructions
echo.
echo ==================================
echo Setup Complete!
echo ==================================
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To deactivate the virtual environment, run:
echo   deactivate
echo.
echo To install problem-specific dependencies:
echo   cd baselines\[PROBLEM-ID]
echo   pip install -r requirements.txt
echo.
echo [OK] Environment setup completed successfully!
echo.
pause