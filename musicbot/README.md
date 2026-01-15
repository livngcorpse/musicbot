# Telegram Music Bot

A powerful, feature-rich Telegram music bot built with Python, inspired by popular bots like YukkiMusic and VCPlayer.

## 🎵 Features

### Core Playback
- **Play from YouTube**: Search and play songs directly from YouTube
- **Audio File Support**: Upload and play MP3, WAV, and other audio formats
- **Queue Management**: Add multiple songs to a queue for continuous playback
- **Voice Chat Control**: Full control over Telegram voice chats

### Queue System
- **FIFO Queue**: First-in, first-out song queuing
- **Queue Manipulation**: Clear, shuffle, and remove specific items
- **Auto-play**: Automatically plays next song when current one ends
- **Queue Display**: View current queue with detailed information

### Voice Chat Features
- **Join/Leave VC**: Automatic voice chat joining and leaving
- **Pause/Resume**: Control playback state
- **Skip/Stop**: Skip tracks or stop playback entirely
- **Auto-leave**: Automatically leaves VC when inactive

### Administration
- **Permission System**: Owner, sudo users, and chat admin controls
- **Rate Limiting**: Built-in flood protection
- **Command Logging**: Track command usage (with database)
- **Maintenance Mode**: Temporarily disable bot (configurable)

### Advanced Features
- **Database Integration**: MongoDB support for persistent data
- **Caching**: Optional Redis caching for better performance
- **Statistics**: User play counts and bot usage stats
- **Playlist Support**: Save and manage user playlists

## 🚀 Installation

### Prerequisites

1. **Python 3.10+**
2. **FFmpeg** (essential for audio processing)
3. **MongoDB** (recommended for persistence)
4. **Redis** (optional, for caching)

### System Dependencies

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg python3-pip python3-venv mongodb redis-server

# Or install FFmpeg manually
sudo apt install ffmpeg
```

### Setup Steps

1. **Clone and setup virtual environment:**
```bash
git clone <repository-url>
cd musicbot
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Get Telegram credentials:**
   - Create a bot with [@BotFather](https://t.me/BotFather)
   - Get API ID and Hash from [Telegram](https://my.telegram.org)
   - Generate user session string (see below)

5. **Generate User Session:**
```python
# Run this script to generate STRING_SESSION
from pyrogram import Client

api_id = YOUR_API_ID
api_hash = "YOUR_API_HASH"

with Client(":memory:", api_id=api_id, api_hash=api_hash) as app:
    print("Session string:", app.export_session_string())
```

## ⚙️ Configuration

Edit `.env` file with your settings:

```env
# Telegram API Credentials (Required)
BOT_TOKEN=your_bot_token_here
API_ID=your_api_id_here
API_HASH=your_api_hash_here
STRING_SESSION=your_user_session_string_here

# Database Configuration (Recommended)
MONGO_DB_URI=mongodb://localhost:27017/musicbot
DB_NAME=musicbot

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379
USE_REDIS=True

# Owner and Permissions
OWNER_ID=your_telegram_user_id
SUDO_USERS=user_id1,user_id2
```

## ▶️ Usage

### Starting the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python bot.py
```

### Basic Commands

**In Groups with Voice Chats:**
```
/play <song name or URL> - Search and play a song
/pause - Pause current playback
/resume - Resume paused playback
/skip - Skip current song (admin)
/stop - Stop playback and leave VC (admin)
/current - Show currently playing song
/queue - Display current queue
/clear - Clear the entire queue (admin)
/shuffle - Shuffle the queue (admin)
/remove <position> - Remove specific item (admin)
```

**Admin Commands:**
```
/ping - Check bot responsiveness
/help - Show available commands
/stats - Show bot statistics (owner)
/restart - Restart bot (owner)
```

## 🏗️ Architecture

### Core Components

1. **Bot Layer** (`bot.py`)
   - Main entry point
   - Client initialization
   - Handler registration

2. **Core Modules** (`core/`)
   - `calls.py` - PyTgCalls voice chat management
   - `downloader.py` - YouTube audio downloading
   - `player.py` - Audio streaming and playback
   - `queue.py` - Song queue management

3. **Handlers** (`handlers/`)
   - Command implementations
   - Message filtering
   - User interaction

4. **Utilities** (`utils/`)
   - Decorators for common patterns
   - Filters for permissions
   - Time formatting utilities

5. **Database** (`database/`)
   - MongoDB integration
   - User data management
   - Statistics tracking

### Data Flow

```
User Command → Handler → Core Module → Voice Chat
     ↓              ↓           ↓           ↓
   Filter      Validation   Processing   Playback
```

## 🔧 Customization

### Adding New Commands

1. Create handler in `handlers/`
2. Register in `handlers/__init__.py`
3. Add appropriate decorators

### Modifying Audio Quality

Adjust in `config.py`:
```python
AUDIO_QUALITY = "high"  # high, medium, low
MAX_AUDIO_DURATION = 3600  # seconds
```

### Changing Queue Behavior

Modify in `core/queue.py`:
```python
MAX_QUEUE_SIZE = 100
AUTO_LEAVE_VC = True
AUTO_LEAVE_DELAY = 300  # seconds
```

## 🛠️ Troubleshooting

### Common Issues

1. **"No module named 'pytgcalls'"**
   ```bash
   pip install pytgcalls
   ```

2. **FFmpeg not found**
   ```bash
   sudo apt install ffmpeg
   ```

3. **Database connection failed**
   - Ensure MongoDB is running
   - Check connection URI in `.env`

4. **Voice chat not working**
   - Verify user session is valid
   - Check user account has VC permissions
   - Ensure bot is admin in the group

### Logs

Check `musicbot.log` for detailed error information:
```bash
tail -f musicbot.log
```

## 🔒 Security

### Important Notes

- **Never share** your `STRING_SESSION` or API credentials
- **Disable** `/eval` and `/exec` commands in production
- **Restrict** owner commands to trusted users only
- **Regularly update** dependencies for security patches

### Production Recommendations

1. Use environment variables for all secrets
2. Implement proper logging and monitoring
3. Set up automatic backups for database
4. Use a process manager like PM2 or systemd
5. Enable SSL/TLS for database connections

## 📊 Performance Tips

1. **Use Redis caching** for frequently accessed data
2. **Optimize MongoDB indexes** for user queries
3. **Limit queue size** to prevent memory issues
4. **Clean temporary files** regularly
5. **Monitor system resources** during peak usage

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Inspired by YukkiMusic, Zaid, and VCPlayer
- Built with Pyrogram and PyTgCalls
- Uses yt-dlp for audio extraction
- Powered by FFmpeg for audio processing

## 🆘 Support

For issues and questions:
- Check existing GitHub issues
- Review the documentation
- Contact the development team

---

*Made with ❤️ for the Telegram community*