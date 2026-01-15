#!/bin/bash

# Music Bot Startup Script

echo "🎵 Starting Telegram Music Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Please copy .env.example to .env and configure your settings."
    exit 1
fi

# Check for required executables
echo "Checking system dependencies..."

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg not found. Please install FFmpeg:"
    echo "   Ubuntu/Debian: sudo apt install ffmpeg"
    exit 1
fi

echo "✅ All system dependencies found"

# Start the bot
echo "🚀 Starting bot..."
python bot.py