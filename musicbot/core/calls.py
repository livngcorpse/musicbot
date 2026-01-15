import asyncio
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.types.input_stream import InputStream, InputAudioStream
from pytgcalls.types.stream import StreamAudioEnded
from pyrogram import Client
import logging

from config import config

logger = logging.getLogger(__name__)

class CallManager:
    def __init__(self, app: Client):
        self.app = app
        self.pytgcalls = PyTgCalls(app)
        self.active_chats = {}  # chat_id -> {playing_status, current_song, queue}
        
        # Register event handlers
        self.pytgcalls.on_stream_end()(self._on_stream_end)
        
    async def initialize(self):
        """Initialize PyTgCalls"""
        try:
            await self.pytgcalls.start()
            logger.info("PyTgCalls initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyTgCalls: {e}")
            raise
            
    async def join_voice_chat(self, chat_id: int):
        """Join a voice chat"""
        try:
            await self.pytgcalls.join_group_call(
                chat_id,
                InputStream(
                    InputAudioStream(
                        f"fifo://{chat_id}",  # FIFO pipe for audio streaming
                        48000,  # Sample rate
                        2       # Channels
                    )
                ),
                stream_type=StreamType().pulse_stream,
            )
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
        try:
            await self.pytgcalls.leave_group_call(chat_id)
            if chat_id in self.active_chats:
                del self.active_chats[chat_id]
            logger.info(f"Left voice chat in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to leave voice chat {chat_id}: {e}")
            return False
            
    async def change_stream(self, chat_id: int, audio_file: str):
        """Change the current audio stream"""
        try:
            await self.pytgcalls.change_stream(
                chat_id,
                InputStream(
                    InputAudioStream(
                        audio_file,
                        48000,
                        2
                    )
                )
            )
            logger.info(f"Changed stream for chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to change stream for chat {chat_id}: {e}")
            return False
            
    async def pause_stream(self, chat_id: int):
        """Pause the current stream"""
        try:
            await self.pytgcalls.pause_stream(chat_id)
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
            await self.pytgcalls.resume_stream(chat_id)
            if chat_id in self.active_chats:
                self.active_chats[chat_id]['playing'] = True
            logger.info(f"Resumed stream in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume stream in {chat_id}: {e}")
            return False
            
    async def stop_stream(self, chat_id: int):
        """Stop the current stream"""
        try:
            await self.pytgcalls.leave_group_call(chat_id)
            if chat_id in self.active_chats:
                self.active_chats[chat_id] = {
                    'playing': False,
                    'current_song': None,
                    'queue': []
                }
            logger.info(f"Stopped stream in {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop stream in {chat_id}: {e}")
            return False
            
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
            
    def _on_stream_end(self, client, update: StreamAudioEnded):
        """Handle stream end event"""
        chat_id = update.chat_id
        logger.info(f"Stream ended in chat {chat_id}")
        # Handle auto-play next song or leave VC
        # This will be implemented in the queue manager
        
    async def cleanup(self):
        """Clean up all active calls"""
        for chat_id in list(self.active_chats.keys()):
            await self.leave_voice_chat(chat_id)
        await self.pytgcalls.stop()
        logger.info("CallManager cleaned up")

# Global instance
call_manager = None

async def init_call_manager(app: Client):
    """Initialize the global call manager"""
    global call_manager
    call_manager = CallManager(app)
    await call_manager.initialize()
    return call_manager