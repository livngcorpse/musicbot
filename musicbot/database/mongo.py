import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    logging.warning("MongoDB dependencies not installed. Database features disabled.")

from config import config

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        
        if not MONGO_AVAILABLE:
            logger.warning("MongoDB not available. Running without database.")
            return
            
        try:
            self.client = AsyncIOMotorClient(config.MONGO_DB_URI)
            self.db = self.client[config.DB_NAME]
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            
    async def connect(self):
        """Connect to MongoDB"""
        if not MONGO_AVAILABLE or not self.client:
            return False
            
        try:
            # Test connection
            await self.client.admin.command('ping')
            self.connected = True
            logger.info("Connected to MongoDB successfully")
            return True
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self.connected = False
            return False
            
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("Disconnected from MongoDB")
            
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data"""
        if not self.connected:
            return None
            
        try:
            collection = self.db.users
            user = await collection.find_one({"user_id": user_id})
            return user
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
            
    async def create_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """Create new user record"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.users
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "play_count": 0,
                "play_time": 0,
                "commands_used": 0,
                "is_banned": False,
                "ban_reason": None
            }
            
            result = await collection.insert_one(user_data)
            logger.info(f"Created user record for {user_id}")
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            return False
            
    async def update_user_activity(self, user_id: int) -> bool:
        """Update user's last active timestamp"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.users
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": {"last_active": datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user activity for {user_id}: {e}")
            return False
            
    async def increment_play_count(self, user_id: int) -> bool:
        """Increment user's play count"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.users
            result = await collection.update_one(
                {"user_id": user_id},
                {"$inc": {"play_count": 1, "commands_used": 1}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error incrementing play count for {user_id}: {e}")
            return False
            
    async def ban_user(self, user_id: int, reason: str = None, banned_by: int = None) -> bool:
        """Ban a user"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.users
            result = await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_banned": True,
                        "ban_reason": reason,
                        "banned_by": banned_by,
                        "banned_at": datetime.now()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            return False
            
    async def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.users
            result = await collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {"is_banned": False},
                    "$unset": {"ban_reason": "", "banned_by": "", "banned_at": ""}
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            return False
            
    async def get_banned_users(self) -> List[int]:
        """Get list of banned user IDs"""
        if not self.connected:
            return []
            
        try:
            collection = self.db.users
            cursor = collection.find({"is_banned": True}, {"user_id": 1})
            banned_users = [doc["user_id"] async for doc in cursor]
            return banned_users
        except Exception as e:
            logger.error(f"Error getting banned users: {e}")
            return []
            
    async def log_command(self, user_id: int, chat_id: int, command: str, timestamp: datetime = None) -> bool:
        """Log command usage"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.command_logs
            log_entry = {
                "user_id": user_id,
                "chat_id": chat_id,
                "command": command,
                "timestamp": timestamp or datetime.now()
            }
            
            result = await collection.insert_one(log_entry)
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error logging command {command}: {e}")
            return False
            
    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics"""
        if not self.connected:
            return None
            
        try:
            collection = self.db.users
            user = await collection.find_one({"user_id": user_id})
            
            if not user:
                return None
                
            # Get recent command usage
            command_logs = self.db.command_logs
            recent_commands = await command_logs.count_documents({
                "user_id": user_id,
                "timestamp": {"$gte": datetime.now() - timedelta(days=30)}
            })
            
            return {
                "play_count": user.get("play_count", 0),
                "play_time": user.get("play_time", 0),
                "commands_used": user.get("commands_used", 0),
                "recent_commands": recent_commands,
                "created_at": user.get("created_at"),
                "last_active": user.get("last_active")
            }
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return None
            
    async def save_playlist(self, user_id: int, name: str, songs: List[Dict]) -> bool:
        """Save user playlist"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.playlists
            playlist = {
                "user_id": user_id,
                "name": name,
                "songs": songs,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # Check if playlist already exists
            existing = await collection.find_one({"user_id": user_id, "name": name})
            if existing:
                result = await collection.update_one(
                    {"user_id": user_id, "name": name},
                    {"$set": {"songs": songs, "updated_at": datetime.now()}}
                )
            else:
                result = await collection.insert_one(playlist)
                
            return result.acknowledged
        except Exception as e:
            logger.error(f"Error saving playlist for user {user_id}: {e}")
            return False
            
    async def get_user_playlists(self, user_id: int) -> List[Dict]:
        """Get all playlists for a user"""
        if not self.connected:
            return []
            
        try:
            collection = self.db.playlists
            cursor = collection.find({"user_id": user_id})
            playlists = [doc async for doc in cursor]
            return playlists
        except Exception as e:
            logger.error(f"Error getting playlists for user {user_id}: {e}")
            return []
            
    async def delete_playlist(self, user_id: int, name: str) -> bool:
        """Delete a user playlist"""
        if not self.connected:
            return False
            
        try:
            collection = self.db.playlists
            result = await collection.delete_one({"user_id": user_id, "name": name})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting playlist {name} for user {user_id}: {e}")
            return False
            
    async def cleanup_old_logs(self, days: int = 30):
        """Remove old command logs"""
        if not self.connected:
            return
            
        try:
            collection = self.db.command_logs
            cutoff_date = datetime.now() - timedelta(days=days)
            result = await collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            logger.info(f"Cleaned up {result.deleted_count} old command logs")
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")

# Global database instance
db = Database()

# Fallback functions for when database is not available
async def get_user_fallback(user_id: int) -> Dict:
    """Fallback user data when database unavailable"""
    return {
        "user_id": user_id,
        "play_count": 0,
        "is_banned": False
    }

async def create_user_fallback(user_id: int, username: str = None, first_name: str = None) -> bool:
    """Fallback user creation"""
    return True

async def get_banned_users_fallback() -> List[int]:
    """Fallback banned users list"""
    return []

# Export functions that work with or without database
async def get_user_safe(user_id: int) -> Dict:
    if db.connected:
        user = await db.get_user(user_id)
        if user:
            return user
    return await get_user_fallback(user_id)

async def create_user_safe(user_id: int, username: str = None, first_name: str = None) -> bool:
    if db.connected:
        return await db.create_user(user_id, username, first_name)
    return await create_user_fallback(user_id, username, first_name)

async def get_banned_users_safe() -> List[int]:
    if db.connected:
        return await db.get_banned_users()
    return await get_banned_users_fallback()

async def increment_play_count(*args, **kwargs):
    # Stub: play count tracking not implemented yet
    return True
async def get_user_stats(user_id: int):
    """
    Stub for user statistics.
    Returns default values until full implementation.
    """
    return {
        "plays": 0,
        "songs_requested": 0,
        "time_listened": 0
    }
