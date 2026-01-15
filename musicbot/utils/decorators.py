import asyncio
import logging
from functools import wraps
from typing import Callable, Any
from datetime import datetime, timedelta

from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, RPCError

from config import config
from .filters import flood_control

logger = logging.getLogger(__name__)

def catch_errors(default_return=None):
    """Decorator to catch and log errors"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except FloodWait as e:
                logger.warning(f"FloodWait: Need to wait {e.value} seconds")
                await asyncio.sleep(e.value)
                try:
                    return await func(*args, **kwargs)
                except Exception as retry_error:
                    logger.error(f"Error after FloodWait retry: {retry_error}")
                    return default_return
            except RPCError as e:
                logger.error(f"RPC Error in {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator

def require_voice_chat(func: Callable):
    """Decorator to ensure bot is in a voice chat"""
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            from core.calls import call_manager
            
            chat_id = message.chat.id
            
            # Check if in voice chat
            if not call_manager.is_playing(chat_id):
                await message.reply("❌ I'm not in a voice chat! Use /play to start.")
                return
            
            return await func(client, message, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in require_voice_chat decorator: {e}")
            await message.reply("❌ An error occurred while checking voice chat status.")
            
    return wrapper

def require_playing(func: Callable):
    """Decorator to ensure music is currently playing"""
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            from core.queue import queue_manager
            
            chat_id = message.chat.id
            
            # Check if something is playing
            if not queue_manager.is_playing(chat_id):
                await message.reply("❌ Nothing is currently playing!")
                return
                
            return await func(client, message, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in require_playing decorator: {e}")
            await message.reply("❌ An error occurred while checking playback status.")
            
    return wrapper

def require_queue(func: Callable):
    """Decorator to ensure there's a queue"""
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            from core.queue import queue_manager
            
            chat_id = message.chat.id
            queue_length = queue_manager.get_queue_length(chat_id)
            
            if queue_length == 0:
                await message.reply("❌ The queue is empty!")
                return
                
            return await func(client, message, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in require_queue decorator: {e}")
            await message.reply("❌ An error occurred while checking the queue.")
            
    return wrapper

def log_command(command_name: str = None):
    """Decorator to log command usage"""
    def decorator(func: Callable):
        cmd_name = command_name or func.__name__
        
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args, **kwargs):
            try:
                user = message.from_user
                chat = message.chat
                
                logger.info(
                    f"Command '{cmd_name}' used by "
                    f"@{user.username or user.id} ({user.first_name}) "
                    f"in {chat.title or chat.id}"
                )
                
                # Log to database if enabled
                # await db.log_command(user.id, chat.id, cmd_name, message.date)
                
            except Exception as e:
                logger.error(f"Error logging command {cmd_name}: {e}")
            
            return await func(client, message, *args, **kwargs)
        return wrapper
    return decorator

def measure_execution_time(func: Callable):
    """Decorator to measure and log execution time"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = await func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper

def handle_large_messages(max_chars: int = 4096):
    """Decorator to handle messages that exceed Telegram's character limit"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args, **kwargs):
            try:
                result = await func(client, message, *args, **kwargs)
                
                if isinstance(result, str) and len(result) > max_chars:
                    # Split message into chunks
                    chunks = [result[i:i+max_chars] for i in range(0, len(result), max_chars)]
                    
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            # Edit original message
                            await message.edit_text(chunk)
                        else:
                            # Send additional messages
                            await message.reply(chunk)
                elif result:
                    # Handle other return types appropriately
                    pass
                    
                return result
                
            except Exception as e:
                logger.error(f"Error in handle_large_messages decorator: {e}")
                await message.reply("❌ An error occurred while processing your request.")
                
        return wrapper
    return decorator

def validate_input(min_args: int = 0, max_args: int = None):
    """Decorator to validate command arguments"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args, **kwargs):
            try:
                # Extract command arguments
                command_parts = message.text.split()
                args_count = len(command_parts) - 1  # Subtract command name
                
                # Check minimum arguments
                if min_args > 0 and args_count < min_args:
                    await message.reply(
                        f"❌ Not enough arguments! Minimum {min_args} required.\n"
                        f"Usage: {command_parts[0]} {'[arguments]' * min_args}"
                    )
                    return
                
                # Check maximum arguments
                if max_args is not None and args_count > max_args:
                    await message.reply(
                        f"❌ Too many arguments! Maximum {max_args} allowed.\n"
                        f"Usage: {command_parts[0]} {'[arguments]' * max_args}"
                    )
                    return
                
                return await func(client, message, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in validate_input decorator: {e}")
                await message.reply("❌ Invalid command usage.")
                
        return wrapper
    return decorator

def cooldown(seconds: int):
    """Cooldown decorator to prevent spam"""
    last_used = {}  # user_id -> last_used_timestamp
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(client: Client, message: Message, *args, **kwargs):
            try:
                user_id = message.from_user.id
                current_time = datetime.now().timestamp()
                
                # Check cooldown
                if user_id in last_used:
                    time_passed = current_time - last_used[user_id]
                    if time_passed < seconds:
                        remaining = int(seconds - time_passed)
                        await message.reply(
                            f"⏰ Please wait {remaining} second(s) before using this command again."
                        )
                        return
                
                # Update last used time
                last_used[user_id] = current_time
                
                return await func(client, message, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in cooldown decorator: {e}")
                return await func(client, message, *args, **kwargs)  # Execute anyway on error
                
        return wrapper
    return decorator

def admin_only(func: Callable):
    """Decorator for admin-only commands"""
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            user_id = message.from_user.id
            
            # Check owner
            if user_id == config.OWNER_ID:
                return await func(client, message, *args, **kwargs)
            
            # Check sudo users
            if user_id in config.SUDO_USERS:
                return await func(client, message, *args, **kwargs)
            
            # Check chat admins
            try:
                chat_member = await client.get_chat_member(message.chat.id, user_id)
                if chat_member.status in ["administrator", "creator"]:
                    return await func(client, message, *args, **kwargs)
            except:
                pass
            
            # Not authorized
            await message.reply("❌ You don't have permission to use this command!")
            
        except Exception as e:
            logger.error(f"Error in admin_only decorator: {e}")
            await message.reply("❌ An error occurred while checking permissions.")
            
    return wrapper

# Combined decorators for common use cases
def music_command(func: Callable):
    """Combined decorator for typical music commands"""
    return catch_errors()(
        log_command()(
            measure_execution_time(
                flood_control()(func)
            )
        )
    )

def admin_music_command(func: Callable):
    """Combined decorator for admin music commands"""
    return admin_only(
        catch_errors()(
            log_command()(
                measure_execution_time(
                    flood_control()(func)
                )
            )
        )
    )