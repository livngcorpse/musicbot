import logging
from pyrogram import filters
from pyrogram.types import Message
import psutil
import platform
from datetime import datetime

from utils.decorators import *
from utils.filters import *
from config import config
from database.mongo import db, get_user_stats

logger = logging.getLogger(__name__)

@music_command
async def restart_command(client, message: Message):
    # Check if user is owner
    if message.from_user.id != config.OWNER_ID:
        await message.reply("❌ Only owner can use this command.")
        return
    """Handle /restart command - restart the bot"""
    try:
        await message.reply("🔄 Restarting bot...")
        # In a real implementation, you'd want to use a process manager
        # For now, we'll just log and exit
        logger.info("Restart command received - shutting down")
        import sys
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Error in restart command: {e}")
        await message.reply("❌ Failed to restart bot.")

@music_command
async def stats_command(client, message: Message):
    # Check if user is owner
    if message.from_user.id != config.OWNER_ID:
        await message.reply("❌ Only owner can use this command.")
        return
    """Handle /stats command - show bot statistics"""
    try:
        # System stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Bot stats (placeholder - would come from database)
        uptime = "N/A"  # Would track bot start time
        total_users = "N/A"  # Would come from database
        total_plays = "N/A"  # Would come from database
        
        response = (
            "📊 <b>Bot Statistics:</b>\n\n"
            f"🖥 <b>System:</b>\n"
            f"CPU: {cpu_percent}%\n"
            f"RAM: {memory.percent}% ({memory.used / 1024 / 1024:.1f}MB / {memory.total / 1024 / 1024:.1f}MB)\n"
            f"Disk: {disk.percent}% ({disk.used / 1024 / 1024 / 1024:.1f}GB / {disk.total / 1024 / 1024 / 1024:.1f}GB)\n"
            f"Platform: {platform.system()} {platform.release()}\n\n"
            f"🤖 <b>Bot:</b>\n"
            f"Uptime: {uptime}\n"
            f"Total Users: {total_users}\n"
            f"Total Plays: {total_plays}\n\n"
            f"⚙️ <b>Configuration:</b>\n"
            f"Max Queue Size: {config.MAX_QUEUE_SIZE}\n"
            f"Max Duration: {config.MAX_AUDIO_DURATION}s\n"
            f"Auto Leave VC: {config.AUTO_LEAVE_VC}\n"
        )
        
        await message.reply(response)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply("❌ Failed to fetch statistics.")

@music_command
async def eval_command(client, message: Message):
    # Check if user is owner
    if message.from_user.id != config.OWNER_ID:
        await message.reply("❌ Only owner can use this command.")
        return
    """Handle /eval command - evaluate Python code (owner only)"""
    try:
        # Extract code from message
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("Usage: `/eval <python code>`")
            return
            
        code = " ".join(command_parts[1:])
        
        # Safety warning - this is dangerous in production!
        await message.reply("⚠️ Executing code (DANGEROUS!)")
        
        # Execute code
        try:
            result = eval(code)
            await message.reply(f"✅ Result: `{result}`")
        except Exception as e:
            await message.reply(f"❌ Error: `{str(e)}`")
            
    except Exception as e:
        logger.error(f"Error in eval command: {e}")

@music_command
async def exec_command(client, message: Message):
    # Check if user is owner
    if message.from_user.id != config.OWNER_ID:
        await message.reply("❌ Only owner can use this command.")
        return
    """Handle /exec command - execute Python code (owner only)"""
    try:
        # Extract code from message
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("Usage: `/exec <python code>`")
            return
            
        code = " ".join(command_parts[1:])
        
        # Safety warning
        await message.reply("⚠️ Executing code (DANGEROUS!)")
        
        # Execute code
        try:
            exec(code)
            await message.reply("✅ Code executed successfully")
        except Exception as e:
            await message.reply(f"❌ Error: `{str(e)}`")
            
    except Exception as e:
        logger.error(f"Error in exec command: {e}")

@admin_only
async def ping_command(client, message: Message):
    """Handle /ping command - check bot responsiveness"""
    try:
        start_time = datetime.now()
        msg = await message.reply("🏓 Pinging...")
        end_time = datetime.now()
        
        latency = (end_time - start_time).total_seconds() * 1000
        
        response = (
            f"🏓 <b>Pong!</b>\n"
            f"Latency: {latency:.2f}ms\n"
            f"System: Online ✅"
        )
        
        await msg.edit(response)
        
    except Exception as e:
        logger.error(f"Error in ping command: {e}")
        await message.reply("❌ Ping failed.")

@admin_only
async def help_command(client, message: Message):
    """Handle /help command - show available commands"""
    try:
        user_id = message.from_user.id
        is_admin = (user_id == config.OWNER_ID or user_id in config.SUDO_USERS)
        
        help_text = (
            "🎵 <b>Music Bot Commands:</b>\n\n"
            "▶️ <b>Playback:</b>\n"
            "/play <song> - Play a song\n"
            "/pause - Pause playback\n"
            "/resume - Resume playback\n"
            "/skip - Skip current song (admin)\n"
            "/stop - Stop playback (admin)\n"
            "/current - Show current playing song\n\n"
            "📋 <b>Queue:</b>\n"
            "/queue - Show current queue\n"
            "/clear - Clear queue (admin)\n"
            "/shuffle - Shuffle queue (admin)\n"
            "/remove <pos> - Remove from queue (admin)\n\n"
        )
        
        if is_admin:
            help_text += (
                "🛠 <b>Admin:</b>\n"
                "/ping - Check bot status\n"
                "/help - Show this help\n"
                "/stats - Show bot statistics (owner)\n"
                "/restart - Restart bot (owner)\n"
            )
        
        await message.reply(help_text)
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.reply("❌ Failed to fetch help.")

def register_admin_handlers(app):
    """Register admin command handlers"""
    
    # Ping command
    app.add_handler(
        filters.command(["ping"]) & 
        filters.group &
        is_authorized
    )(ping_command)
    
    # Help command
    app.add_handler(
        filters.command(["help", "start"]) & 
        filters.group &
        is_authorized
    )(help_command)
    
    # Stats command (owner only)
    app.add_handler(
        filters.command(["stats"]) & 
        filters.group
    )(stats_command)
    
    # Restart command (owner only)
    app.add_handler(
        filters.command(["restart"]) & 
        filters.group
    )(restart_command)
    
    # Eval command (owner only) - DISABLE IN PRODUCTION
    app.add_handler(
        filters.command(["eval"]) & 
        filters.group
    )(eval_command)
    
    # Exec command (owner only) - DISABLE IN PRODUCTION
    app.add_handler(
        filters.command(["exec"]) & 
        filters.group
    )(exec_command)
    
    logger.info("Admin handlers registered")