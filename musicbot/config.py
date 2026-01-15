import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")  # Your bot token from @BotFather
    STRING_SESSION = os.getenv("STRING_SESSION")  # User account session string
    API_ID = int(os.getenv("API_ID"))  # From https://my.telegram.org
    API_HASH = os.getenv("API_HASH")  # From https://my.telegram.org
    
    # Assistant Bot Configuration
    ASSISTANT_BOT_TOKEN = os.getenv("ASSISTANT_BOT_TOKEN")  # Optional: separate bot for assistant
    ASSISTANT_SESSION = os.getenv("ASSISTANT_SESSION")  # Assistant user session
    
    # Database Configuration
    MONGO_DB_URI = os.getenv("MONGO_DB_URI", "mongodb://localhost:27017/musicbot")
    DB_NAME = os.getenv("DB_NAME", "musicbot")
    
    # Redis Configuration (Optional)
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    USE_REDIS = os.getenv("USE_REDIS", "False").lower() == "true"
    
    # Audio Settings
    AUDIO_QUALITY = os.getenv("AUDIO_QUALITY", "high")  # high, medium, low
    MAX_AUDIO_DURATION = int(os.getenv("MAX_AUDIO_DURATION", "3600"))  # 1 hour in seconds
    DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./temp")
    
    # Queue Settings
    MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "100"))
    AUTO_LEAVE_VC = os.getenv("AUTO_LEAVE_VC", "True").lower() == "true"
    AUTO_LEAVE_DELAY = int(os.getenv("AUTO_LEAVE_DELAY", "300"))  # 5 minutes
    
    # Bot Settings
    OWNER_ID = int(os.getenv("OWNER_ID", "0"))  # Your Telegram user ID
    SUDO_USERS = list(map(int, os.getenv("SUDO_USERS", "").split())) or []
    LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "0"))  # For logging (optional)
    
    # Feature Toggles
    ENABLE_PLAYLISTS = os.getenv("ENABLE_PLAYLISTS", "True").lower() == "true"
    ENABLE_GLOBAL_BAN = os.getenv("ENABLE_GLOBAL_BAN", "False").lower() == "true"
    ENABLE_STATS = os.getenv("ENABLE_STATS", "True").lower() == "true"
    
    # Cache Settings
    CACHE_DIR = os.getenv("CACHE_DIR", "./cache")
    CLEAN_CACHE_INTERVAL = int(os.getenv("CLEAN_CACHE_INTERVAL", "3600"))  # 1 hour
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "musicbot.log")

# Global config instance
config = Config()