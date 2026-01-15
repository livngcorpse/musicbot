import asyncio
import logging
import signal
import sys
from pyrogram import Client, idle
from pyrogram.enums import ParseMode

from config import config
from utils.decorators import catch_errors
from database.mongo import db

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize clients
bot_app = Client(
    "musicbot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    parse_mode=ParseMode.HTML
)

user_app = Client(
    "musicuser",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.STRING_SESSION
) if config.STRING_SESSION else None

# Import handlers after client initialization to avoid circular imports
from handlers import register_handlers

async def setup_database():
    """Setup database connection"""
    try:
        connected = await db.connect()
        if connected:
            logger.info("Database connected successfully")
        else:
            logger.warning("Database connection failed. Running without database.")
    except Exception as e:
        logger.error(f"Database setup error: {e}")

async def setup_core_modules():
    """Initialize core modules"""
    try:
        from core.calls import init_call_manager
        from core.downloader import downloader
        from core.player import player
        from core.queue import queue_manager
        
        # Initialize call manager with user app
        if user_app:
            await init_call_manager(user_app)
            logger.info("Call manager initialized")
        else:
            logger.warning("No user session provided. Voice chat features will be limited.")
            
        logger.info("Core modules initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing core modules: {e}")
        raise

async def start_bot():
    """Start the bot"""
    try:
        logger.info("Starting Music Bot...")
        
        # Setup database
        await setup_database()
        
        # Start bot client
        await bot_app.start()
        logger.info("Bot client started")
        
        # Start user client if available
        if user_app:
            await user_app.start()
            logger.info("User client started")
        
        # Setup core modules
        await setup_core_modules()
        
        # Register handlers
        register_handlers(bot_app)
        logger.info("Handlers registered")
        
        # Get bot info
        me = await bot_app.get_me()
        logger.info(f"Bot started as @{me.username}")
        
        # Run forever
        await idle()
        
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await stop_bot()

async def stop_bot():
    """Gracefully stop the bot"""
    logger.info("Stopping bot...")
    
    try:
        # Stop core modules
        from core.calls import call_manager
        from core.player import player
        from core.queue import queue_manager
        
        if call_manager:
            await call_manager.cleanup()
            logger.info("Call manager cleaned up")
            
        # Stop clients
        if user_app and user_app.is_connected:
            await user_app.stop()
            logger.info("User client stopped")
            
        if bot_app.is_connected:
            await bot_app.stop()
            logger.info("Bot client stopped")
            
        # Close database
        await db.disconnect()
        logger.info("Database disconnected")
        
        logger.info("Bot stopped gracefully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info(f"Received signal {signum}")
    # The main loop will catch the KeyboardInterrupt
    raise KeyboardInterrupt()

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the bot
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()