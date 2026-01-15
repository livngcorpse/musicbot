import asyncio
import logging
from pyrogram import filters
from pyrogram.types import Message

from config import config
from utils.decorators import *
from utils.filters import *
from utils.time import format_duration
from core.downloader import downloader
from core.queue import queue_manager
from database.mongo import create_user_safe, increment_play_count

logger = logging.getLogger(__name__)

@music_command
@validate_input(min_args=1)
async def play_command(client, message: Message):
    """Handle /play command - search and play music"""
    try:
        # Extract query from message
        command_parts = message.text.split()
        query = " ".join(command_parts[1:])  # Remove '/play' prefix
        
        if not query:
            await message.reply("🎵 Please provide a song name or URL!\n\nUsage: `/play <song name or URL>`")
            return
            
        # Create user record if needed
        user = message.from_user
        await create_user_safe(user.id, user.username, user.first_name)
        
        # Send searching message    
        search_msg = await message.reply("🔍 Searching for your song...")

        # Extract video info
        video_info = await downloader.extract_info(query)
        if not video_info:
            await search_msg.edit("❌ Sorry, I couldn't find that song. Please try a different query.")
            return
            
        # Check duration
        duration = video_info.get('duration', 0)
        if duration > config.MAX_AUDIO_DURATION:
            await search_msg.edit(
                f"❌ Song is too long! Maximum allowed duration is {format_duration(config.MAX_AUDIO_DURATION)}."
            )
            return
            
        # Download audio
        await search_msg.edit("📥 Downloading audio...")
        audio_file = await downloader.download_audio(video_info['url'])
        
        if not audio_file:
            await search_msg.edit("❌ Failed to download the audio. Please try again.")
            return
            
        # Add to queue
        chat_id = message.chat.id
        success = queue_manager.add_to_queue(
            chat_id=chat_id,
            song_info=video_info,
            audio_file=audio_file,
            requested_by=user.id,
            message_id=message.id
        )
        
        if success:
            # Increment play count
            await increment_play_count(user.id)
            
            # Format response
            title = video_info.get('title', 'Unknown Title')
            duration_str = format_duration(duration) if duration else "Unknown"
            uploader = video_info.get('uploader', 'Unknown')
            
            response = (
                f"✅ <b>Added to queue:</b>\n\n"
                f"🎵 <b>{title}</b>\n"
                f"⏱ Duration: {duration_str}\n"
                f"👤 Requested by: {user.first_name}\n"
                f"🎤 Artist: {uploader}\n\n"
                f"Position in queue: {queue_manager.get_queue_length(chat_id)}"
            )
            
            await search_msg.edit(response)
        else:
            await search_msg.edit("❌ Failed to add song to queue. Queue might be full.")
            
    except Exception as e:
        logger.error(f"Error in play command: {e}")
        await message.reply("❌ An error occurred while processing your request.")

@music_command
async def play_file_command(client, message: Message):
    """Handle audio file attachments"""
    try:
        if not message.audio:
            return
            
        # Create user record
        user = message.from_user
        await create_user_safe(user.id, user.username, user.first_name)
        
        # Process audio file
        audio = message.audio
        title = audio.title or audio.file_name or "Uploaded Audio"
        duration = audio.duration or 0
        
        if duration > config.MAX_AUDIO_DURATION:
            await message.reply(
                f"❌ File is too long! Maximum allowed duration is {format_duration(config.MAX_AUDIO_DURATION)}."
            )
            return
            
        # Download file
        download_msg = await message.reply("📥 Downloading your audio file...")
        
        try:
            file_path = await client.download_media(audio.file_id)
            
            # Add to queue
            video_info = {
                'title': title,
                'duration': duration,
                'uploader': user.first_name,
                'url': f"tg_file_{message.id}",
                'id': f"tg_{message.id}"
            }
            
            success = queue_manager.add_to_queue(
                chat_id=message.chat.id,
                song_info=video_info,
                audio_file=file_path,
                requested_by=user.id,
                message_id=message.id
            )
            
            if success:
                await increment_play_count(user.id)
                duration_str = format_duration(duration) if duration else "Unknown"
                await download_msg.edit(
                    f"✅ Added to queue:\n\n"
                    f"🎵 <b>{title}</b>\n"
                    f"⏱ Duration: {duration_str}\n"
                    f"👤 Uploaded by: {user.first_name}"
                )
            else:
                await download_msg.edit("❌ Failed to add file to queue.")
                
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            await download_msg.edit("❌ Failed to download the audio file.")
            
    except Exception as e:
        logger.error(f"Error in play_file command: {e}")

def register_play_handler(app):
    """Register play command handlers"""
    from pyrogram.handlers import MessageHandler
    
    # Register /play command
    app.add_handler(
        MessageHandler(
            play_command,
            filters=filters.command(["play", "p"]) & 
                   filters.group &
                   is_authorized &
                   is_not_banned
        )
    )
    
    # Register audio file handler
    app.add_handler(
        MessageHandler(
            play_file_command,
            filters=filters.audio &
                   filters.group &
                   is_authorized &
                   is_not_banned
        )
    )
    
    logger.info("Play handlers registered")