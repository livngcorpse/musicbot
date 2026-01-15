import logging
from pyrogram import filters
from pyrogram.types import Message

from utils.decorators import *
from utils.filters import *
from core.queue import queue_manager
from core.player import player
from utils.time import format_duration

logger = logging.getLogger(__name__)

@music_command
@require_voice_chat
@require_playing
async def pause_command(client, message: Message):
    """Handle /pause command"""
    try:
        chat_id = message.chat.id
        
        if not player.is_playing(chat_id):
            await message.reply("❌ Nothing is currently playing!")
            return
            
        success = await player.pause(chat_id)
        if success:
            current_track = player.get_current_track(chat_id)
            title = current_track.get('title', 'Unknown') if current_track else 'Unknown'
            await message.reply(f"⏸ Paused: <b>{title}</b>")
        else:
            await message.reply("❌ Failed to pause playback.")
            
    except Exception as e:
        logger.error(f"Error in pause command: {e}")
        await message.reply("❌ An error occurred while pausing.")

@music_command
@require_voice_chat
async def resume_command(client, message: Message):
    """Handle /resume command"""
    try:
        chat_id = message.chat.id
        
        if player.is_playing(chat_id):
            await message.reply("❌ Already playing!")
            return
            
        success = await player.resume(chat_id)
        if success:
            current_track = player.get_current_track(chat_id)
            title = current_track.get('title', 'Unknown') if current_track else 'Unknown'
            await message.reply(f"▶️ Resumed: <b>{title}</b>")
        else:
            await message.reply("❌ Failed to resume playback.")
            
    except Exception as e:
        logger.error(f"Error in resume command: {e}")
        await message.reply("❌ An error occurred while resuming.")

@music_command
@require_voice_chat
@admin_only
async def skip_command(client, message: Message):
    """Handle /skip command"""
    try:
        chat_id = message.chat.id
        
        if not queue_manager.is_playing(chat_id):
            await message.reply("❌ Nothing is currently playing!")
            return
            
        # Check if there's a next song
        queue_length = queue_manager.get_queue_length(chat_id)
        if queue_length == 0:
            await message.reply("⏭ Stopping playback (queue is empty)")
            await player.stop(chat_id)
            return
            
        success = await queue_manager.skip_current(chat_id)
        if success:
            await message.reply("⏭ Skipped current track!")
        else:
            await message.reply("❌ Failed to skip track.")
            
    except Exception as e:
        logger.error(f"Error in skip command: {e}")
        await message.reply("❌ An error occurred while skipping.")

@music_command
@require_voice_chat
@admin_only
async def stop_command(client, message: Message):
    """Handle /stop command"""
    try:
        chat_id = message.chat.id
        
        success = await player.stop(chat_id)
        if success:
            await message.reply("⏹ Stopped playback and left voice chat.")
        else:
            await message.reply("❌ Failed to stop playback.")
            
    except Exception as e:
        logger.error(f"Error in stop command: {e}")
        await message.reply("❌ An error occurred while stopping.")

@music_command
@require_voice_chat
async def current_command(client, message: Message):
    """Handle /current command - show current playing song"""
    try:
        chat_id = message.chat.id
        
        current_track = player.get_current_track(chat_id)
        if not current_track:
            await message.reply("❌ Nothing is currently playing!")
            return
            
        title = current_track.get('title', 'Unknown Title')
        duration = current_track.get('duration', 0)
        uploader = current_track.get('uploader', 'Unknown')
        
        duration_str = format_duration(duration) if duration else "Unknown"
        
        response = (
            f"🎵 <b>Now Playing:</b>\n\n"
            f"<b>{title}</b>\n"
            f"⏱ Duration: {duration_str}\n"
            f"🎤 Artist: {uploader}"
        )
        
        await message.reply(response)
        
    except Exception as e:
        logger.error(f"Error in current command: {e}")
        await message.reply("❌ An error occurred while fetching current track.")

def register_control_handlers(app):
    """Register control command handlers"""
    
    # Pause command
    app.add_handler(
        filters.command(["pause"]) & 
        filters.group &
        is_authorized &
        is_not_banned
    )(pause_command)
    
    # Resume command
    app.add_handler(
        filters.command(["resume"]) & 
        filters.group &
        is_authorized &
        is_not_banned
    )(resume_command)
    
    # Skip command
    app.add_handler(
        filters.command(["skip", "next"]) & 
        filters.group &
        is_authorized &
        is_not_banned
    )(skip_command)
    
    # Stop command
    app.add_handler(
        filters.command(["stop", "leave"]) & 
        filters.group &
        is_authorized &
        is_not_banned
    )(stop_command)
    
    # Current playing command
    app.add_handler(
        filters.command(["current", "now", "np"]) & 
        filters.group &
        is_authorized &
        is_not_banned
    )(current_command)
    
    logger.info("Control handlers registered")