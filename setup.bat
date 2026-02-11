@echo off
echo ========================================
echo AI Compliance Engine - Setup Script
echo ========================================
echo.

REM Check Python version
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

echo.
echo Step 1: Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo.
echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Step 3: Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Step 4: Installing backend dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo Step 5: Installing frontend dependencies...
cd frontend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)
cd ..

echo.
echo Step 6: Creating .env file...
if not exist .env (
    copy .env.example .env
    echo Created .env file from .env.example
    echo IMPORTANT: Please edit .env and add your API keys!
) else (
    echo .env file already exists
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo IMPORTANT NEXT STEPS:
echo 1. Edit .env file and add your API keys (OPENAI_API_KEY or ANTHROPIC_API_KEY)
echo 2. Install Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki
echo 3. Update TESSERACT_PATH in .env with the installation path
echo 4. Start PostgreSQL and Redis (or use Docker)
echo 5. Run: docker-compose up -d (for Docker deployment)
echo    OR run services manually:
echo    - Backend: cd backend ^&^& uvicorn app.main:app --reload
echo    - Celery: cd backend ^&^& celery -A app.workers.celery_app worker --loglevel=info
echo    - Frontend: cd frontend ^&^& streamlit run app.py
echo.
pause
