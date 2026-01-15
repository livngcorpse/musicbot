@echo off
title Telegram Music Bot

echo 🎵 Starting Telegram Music Bot...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check for .env file
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo Please copy .env.example to .env and configure your settings.
    pause
    exit /b 1
)

REM Check for required executables
echo Checking system dependencies...

ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg not found. Please install FFmpeg.
    pause
    exit /b 1
)

echo ✅ All system dependencies found

REM Start the bot
echo 🚀 Starting bot...
python bot.py

pause