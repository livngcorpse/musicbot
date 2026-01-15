# Quick Setup Guide

## 1. Install Python Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install required packages
pip install -r requirements.txt
```

## 2. Configure Environment Variables

```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Required configuration:
- `BOT_TOKEN` - From @BotFather
- `API_ID` and `API_HASH` - From https://my.telegram.org
- `STRING_SESSION` - Generated using the session generator script

## 3. Generate User Session String

Create a file `generate_session.py`:

```python
from pyrogram import Client

API_ID = int(input("Enter API ID: "))
API_HASH = input("Enter API Hash: ")

with Client(":memory:", api_id=API_ID, api_hash=API_HASH) as app:
    print("\nYour STRING_SESSION:")
    print(app.export_session_string())
```

Run it:
```bash
python generate_session.py
```

## 4. Run Verification

```bash
python verify_installation.py
```

## 5. Start the Bot

```bash
# Linux/Mac
./start.sh

# Windows  
start.bat

# Or manually
python bot.py
```

## Troubleshooting

If you see import errors, make sure you're in the virtual environment and have installed all packages.

For database errors, the bot will work without MongoDB but some features will be limited.

For voice chat issues, verify your user session is valid and the user account can join voice chats.