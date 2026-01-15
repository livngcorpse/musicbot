import asyncio
from pytgcalls import GroupCallFactory
from pyrogram import Client
import logging

from config import config

logger = logging.getLogger(__name__)

class CallManager:
    def __init__(self, app: Client):
        self.app = app
        self.factory = GroupCallFactory(app, GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM)
        self.group_call = self.factory.get_group_call()
        self.active_chats = {}  # chat_id -> {playing_status, current_song, queue}
        
        # Register event handlers
        @self.group_call.on_playout_ended
        async def on_playout_ended(gc, chat_id):
            logger.info(f"Playback ended in chat {chat_id}")
            if chat_id in self.active_chats:
                self.active_chats[chat_id]['playing'] = False
        
    async def initialize(self):
        """Initialize PyTgCalls"""
        try:
            await self.group_call.start()
            logger.info("PyTgCalls initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyTgCalls: {e}")
            raise
            
    async def join_voice_chat(self, chat_id: int):
        """Join a voice chat"""
        # Check state first - no exception needed
        if chat_id in self.active_chats:
            logger.info(f"Already in voice chat {chat_id}")
            return True
            
        try:
            await self.group_call.start(chat_id)
            self.active_chats[chat_id] = {
                'playing': False,
                'current_song': None,
                'queue': []
            }
            logger.info(f"Joined voice chat in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to join voice chat {chat_id}: {e}")
            return False
            
    async def leave_voice_chat(self, chat_id: int):
        """Leave a voice chat"""
        # Check state first
        if chat_id not in self.active_chats:
            logger.info(f"Not in voice chat {chat_id}")
            return True
            
        try:
            await self.group_call.stop(chat_id)
            del self.active_chats[chat_id]
            logger.info(f"Left voice chat in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to leave voice chat {chat_id}: {e}")
            # Clean up state anyway
            if chat_id in self.active_chats:
                del self.active_chats[chat_id]
            return False
            
    async def change_stream(self, chat_id: int, audio_file: str):
        """Change the current audio stream"""
        try:
            await self.group_call.change_stream(chat_id, audio_file)
            if chat_id in self.active_chats:
                self.active_chats[chat_id]['playing'] = True
            logger.info(f"Changed stream for chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to change stream for chat {chat_id}: {e}")
            return False
            
    async def pause_stream(self, chat_id: int):
        """Pause the current stream"""
        try:
            await self.group_call.pause_playout(chat_id)
            if chat_id in self.active_chats:
                self.active_chats[chat_id]['playing'] = False
            logger.info(f"Paused stream in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause stream in {chat_id}: {e}")
            return False
            
    async def resume_stream(self, chat_id: int):
        """Resume the current stream"""
        try:
            await self.group_call.resume_playout(chat_id)
            if chat_id in self.active_chats:
                self.active_chats[chat_id]['playing'] = True
            logger.info(f"Resumed stream in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume stream in {chat_id}: {e}")
            return False
            
    async def stop_stream(self, chat_id: int):
        """Stop the current stream"""
        return await self.leave_voice_chat(chat_id)
            
    def is_playing(self, chat_id: int) -> bool:
        """Check if audio is currently playing in a chat"""
        return chat_id in self.active_chats and self.active_chats[chat_id]['playing']
        
    def get_current_song(self, chat_id: int):
        """Get current playing song info"""
        if chat_id in self.active_chats:
            return self.active_chats[chat_id]['current_song']
        return None
        
    def set_current_song(self, chat_id: int, song_info: dict):
        """Set current playing song info"""
        if chat_id in self.active_chats:
            self.active_chats[chat_id]['current_song'] = song_info
            
    async def cleanup(self):
        """Clean up all active calls"""
        for chat_id in list(self.active_chats.keys()):
            try:
                await self.leave_voice_chat(chat_id)
            except Exception as e:
                logger.error(f"Error cleaning up chat {chat_id}: {e}")
        
        try:
            await self.group_call.stop()
        except Exception as e:
            logger.error(f"Error stopping group call: {e}")
            
        logger.info("CallManager cleaned up")

# Global instance
call_manager = None

async def init_call_manager(app: Client):
    """Initialize the global call manager"""
    global call_manager
    call_manager = CallManager(app)
    await call_manager.initialize()
    return call_manager
