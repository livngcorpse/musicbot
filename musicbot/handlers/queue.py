import logging
from pyrogram import filters
from pyrogram.types import Message

from utils.decorators import *
from utils.filters import *
from core.queue import queue_manager
from utils.time import format_duration

logger = logging.getLogger(__name__)

@music_command
@require_voice_chat
async def queue_command(client, message: Message):
    """Handle /queue command - show current queue"""
    try:
        chat_id = message.chat.id
        queue_info = queue_manager.get_queue_info(chat_id)
        
        if not queue_info['is_playing'] and queue_info['queue_length'] == 0:
            await message.reply("📭 The queue is empty!")
            return
            
        response = "📋 <b>Queue Status:</b>\n\n"
        
        # Now playing
        if queue_info['now_playing']:
            np = queue_info['now_playing']
            duration_str = format_duration(np['duration']) if np['duration'] else "Unknown"
            response += (
                f"🎵 <b>Now Playing:</b>\n"
                f"{np['title']}\n"
                f"⏱ {duration_str}\n"
                f"👤 {np['requested_by']}\n\n"
            )
        else:
            response += "🔇 <b>Nothing currently playing</b>\n\n"
            
        # Queue items
        if queue_info['queue_length'] > 0:
            response += f"📝 <b>Up Next ({queue_info['queue_length']} items):</b>\n\n"
            
            # Show first 10 items to avoid message length limits
            queue_items = queue_info['queue_items'][:10]
            for item in queue_items:
                duration_str = format_duration(item['duration']) if item['duration'] else "Unknown"
                response += (
                    f"{item['index'] + 1}. {item['title']}\n"
                    f"   ⏱ {duration_str} | 👤 {item['requested_by']}\n\n"
                )
                
            # Show remaining count if there are more items
            if queue_info['queue_length'] > 10:
                remaining = queue_info['queue_length'] - 10
                response += f"... and {remaining} more items\n\n"
        else:
            response += "📭 <b>Queue is empty</b>\n\n"
            
        # Queue controls
        response += (
            "<b>Queue Controls:</b>\n"
            "/clear - Clear the entire queue\n"
            "/shuffle - Shuffle the queue\n"
        )
        
        await message.reply(response)
        
    except Exception as e:
        logger.error(f"Error in queue command: {e}")
        await message.reply("❌ An error occurred while fetching the queue.")

@music_command
@require_voice_chat
@require_queue
@admin_only
async def clear_command(client, message: Message):
    """Handle /clear command - clear the queue"""
    try:
        chat_id = message.chat.id
        cleared_count = await queue_manager.clear_queue(chat_id)
        
        if cleared_count > 0:
            await message.reply(f"✅ Cleared {cleared_count} items from the queue!")
        else:
            await message.reply("📭 The queue was already empty!")
            
    except Exception as e:
        logger.error(f"Error in clear command: {e}")
        await message.reply("❌ An error occurred while clearing the queue.")

@music_command
@require_voice_chat
@require_queue
@admin_only
async def shuffle_command(client, message: Message):
    """Handle /shuffle command - shuffle the queue"""
    try:
        chat_id = message.chat.id
        success = await queue_manager.shuffle_queue(chat_id)
        
        if success:
            await message.reply("🔀 Queue shuffled successfully!")
        else:
            await message.reply("❌ Failed to shuffle queue.")
            
    except Exception as e:
        logger.error(f"Error in shuffle command: {e}")
        await message.reply("❌ An error occurred while shuffling the queue.")

@music_command
@require_voice_chat
@require_queue
@admin_only
async def remove_command(client, message: Message):
    """Handle /remove command - remove specific item from queue"""
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("Usage: `/remove <position>`\nExample: `/remove 3`")
            return
            
        try:
            position = int(command_parts[1]) - 1  # Convert to 0-based index
        except ValueError:
            await message.reply("❌ Please provide a valid number!")
            return
            
        if position < 0:
            await message.reply("❌ Position must be greater than 0!")
            return
            
        chat_id = message.chat.id
        queue_length = queue_manager.get_queue_length(chat_id)
        
        if position >= queue_length:
            await message.reply(f"❌ Position {position + 1} is out of range! Queue has {queue_length} items.")
            return
            
        # Get item info before removing
        queue = queue_manager.get_queue(chat_id)
        removed_item = queue[position]
        title = removed_item.song_info.get('title', 'Unknown')
        
        success = await queue_manager.remove_from_queue(chat_id, position)
        
        if success:
            await message.reply(f"✅ Removed <b>{title}</b> from position {position + 1}!")
        else:
            await message.reply("❌ Failed to remove item from queue.")
            
    except Exception as e:
        logger.error(f"Error in remove command: {e}")
        await message.reply("❌ An error occurred while removing from queue.")

def register_queue_handlers(app):
    """Register queue command handlers"""
    
    # Queue command
    app.add_handler(
        filters.command(["queue", "q"]) & 
        filters.chat_type.groups &
        is_authorized &
        is_not_banned
    )(queue_command)
    
    # Clear queue command
    app.add_handler(
        filters.command(["clear"]) & 
        filters.chat_type.groups &
        is_authorized &
        is_not_banned
    )(clear_command)
    
    # Shuffle queue command
    app.add_handler(
        filters.command(["shuffle"]) & 
        filters.chat_type.groups &
        is_authorized &
        is_not_banned
    )(shuffle_command)
    
    # Remove from queue command
    app.add_handler(
        filters.command(["remove"]) & 
        filters.chat_type.groups &
        is_authorized &
        is_not_banned
    )(remove_command)
    
    logger.info("Queue handlers registered")