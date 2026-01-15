from pyrogram import filters
from pyrogram.types import Message
from functools import wraps
import logging

from config import config

logger = logging.getLogger(__name__)

def admin_filter():
    """Filter for admin-only commands"""
    async def func(_, __, message: Message):
        try:
            user_id = message.from_user.id
            
            # Check if user is owner
            if user_id == config.OWNER_ID:
                return True
                
            # Check if user is in sudo users
            if user_id in config.SUDO_USERS:
                return True
                
            # Check if user is admin in the chat
            chat_member = await message.chat.get_member(user_id)
            if chat_member.status in ["administrator", "creator"]:
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error in admin filter: {e}")
            return False
            
    return filters.create(func)

def owner_filter():
    """Filter for owner-only commands"""
    async def func(_, __, message: Message):
        try:
            return message.from_user.id == config.OWNER_ID
        except Exception:
            return False
            
    return filters.create(func)

def sudo_filter():
    """Filter for sudo users"""
    async def func(_, __, message: Message):
        try:
            user_id = message.from_user.id
            return user_id == config.OWNER_ID or user_id in config.SUDO_USERS
        except Exception:
            return False
            
    return filters.create(func)

def private_filter():
    """Filter for private chats only"""
    async def func(_, __, message: Message):
        return message.chat.type == "private"
        
    return filters.create(func)

def group_filter():
    """Filter for group chats only"""
    async def func(_, __, message: Message):
        return message.chat.type in ["group", "supergroup"]
        
    return filters.create(func)

def voice_chat_filter():
    """Filter for messages in voice chats or groups with voice capability"""
    async def func(client, _, message: Message):
        try:
            # Check if chat has voice chat capability
            if message.chat.type in ["group", "supergroup"]:
                return True
            return False
        except Exception:
            return False
            
    return filters.create(func)

def authorized_filter():
    """Filter for authorized users (can be expanded with database checks)"""
    async def func(_, __, message: Message):
        try:
            user_id = message.from_user.id
            
            # Basic authorization - all users can use basic commands
            # Advanced authorization can be implemented with database
            return True
        except Exception:
            return True  # Allow by default
            
    return filters.create(func)

def banned_filter():
    """Filter to check if user is banned (placeholder for database integration)"""
    async def func(_, __, message: Message):
        try:
            user_id = message.from_user.id
            
            # Placeholder - implement with database
            # banned_users = await db.get_banned_users()
            # return user_id not in banned_users
            
            return False  # No one banned by default
        except Exception:
            return False
            
    return filters.create(func)

def flood_control(max_messages: int = 5, window_seconds: int = 60):
    """Rate limiting decorator"""
    user_messages = {}  # user_id -> [(timestamp, message)]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(client, message: Message):
            try:
                user_id = message.from_user.id
                current_time = message.date.timestamp()
                
                # Initialize user record
                if user_id not in user_messages:
                    user_messages[user_id] = []
                
                # Clean old messages
                user_messages[user_id] = [
                    (timestamp, msg) for timestamp, msg in user_messages[user_id]
                    if current_time - timestamp < window_seconds
                ]
                
                # Check rate limit
                if len(user_messages[user_id]) >= max_messages:
                    await message.reply("⚠️ You're sending commands too fast! Please wait a moment.")
                    return
                
                # Add current message
                user_messages[user_id].append((current_time, message))
                
                # Execute function
                return await func(client, message)
                
            except Exception as e:
                logger.error(f"Error in flood control: {e}")
                return await func(client, message)  # Execute anyway on error
                
        return wrapper
    return decorator

def maintenance_filter():
    """Filter to check if bot is in maintenance mode"""
    async def func(_, __, message: Message):
        try:
            # Placeholder for maintenance mode
            # maintenance_mode = await db.get_maintenance_mode()
            maintenance_mode = False
            return not maintenance_mode
        except Exception:
            return True  # Allow if error
            
    return filters.create(func)

# Predefined filter combinations
admin_or_private = admin_filter() | private_filter()
authorized_and_not_banned = authorized_filter() & ~banned_filter()
group_and_voice_chat = group_filter() & voice_chat_filter()

# Convenience aliases
is_admin = admin_filter()
is_owner = owner_filter()
is_sudo = sudo_filter()
is_private = private_filter()
is_group = group_filter()
is_authorized = authorized_filter()
is_not_banned = ~banned_filter()
is_under_maintenance = maintenance_filter()