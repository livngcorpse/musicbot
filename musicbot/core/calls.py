import logging
from typing import Dict

from pyrogram import Client
from pytgcalls import GroupCallFactory, GroupCallFileAction
from pytgcalls.group_call_type import GroupCallType
from pytgcalls.mtproto_client_type import MTProtoClientType

logger = logging.getLogger(__name__)


class CallManager:
    """
    Manages voice calls for multiple chats using PyTgCalls 3.x
    """

    def __init__(self, app: Client):
        self.app = app

        # Create factory bound to Pyrogram user client
        self.factory = GroupCallFactory(
            app,
            MTProtoClientType.PYROGRAM
        )

        # One VOICE_CHAT controller, reused per chat_id
        self.group_call = self.factory.get_group_call()

        # chat_id -> state
        self.active_chats: Dict[int, dict] = {}

        # ===== Events =====

        @self.group_call.on_playout_ended
        async def _on_playout_ended(chat_id: int):
            logger.info(f"Playback ended in chat {chat_id}")
            if chat_id in self.active_chats:
                self.active_chats[chat_id]["playing"] = False

                # Queue system will decide what to do next
                # (player / queue_manager handles auto-play)
    
    # ---------- Lifecycle ----------

    async def initialize(self):
        """
        PyTgCalls 3.x does not require global start.
        """
        logger.info("PyTgCalls ready (lazy start per chat)")

    async def cleanup(self):
        """
        Leave all active voice chats gracefully.
        """
        for chat_id in list(self.active_chats.keys()):
            try:
                await self.leave_voice_chat(chat_id)
            except Exception as e:
                logger.error(f"Cleanup failed for chat {chat_id}: {e}")

        logger.info("CallManager cleaned up")

    # ---------- Voice Chat Control ----------

    async def join_voice_chat(self, chat_id: int) -> bool:
        if chat_id in self.active_chats:
            return True

        try:
            await self.group_call.start(chat_id)
            self.active_chats[chat_id] = {
                "playing": False,
                "current_song": None,
                "queue": []
            }
            logger.info(f"Joined voice chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to join VC {chat_id}: {e}")
            return False

    async def leave_voice_chat(self, chat_id: int) -> bool:
        if chat_id not in self.active_chats:
            return True

        try:
            await self.group_call.stop(chat_id)
        except Exception as e:
            logger.warning(f"Error leaving VC {chat_id}: {e}")
        finally:
            self.active_chats.pop(chat_id, None)

        logger.info(f"Left voice chat {chat_id}")
        return True

    # ---------- Playback ----------

    async def start_stream(self, chat_id: int, audio_file: str) -> bool:
        """
        Start or replace audio stream in a chat.
        Expects a local, FFmpeg-ready audio file.
        """
        try:
            await self.group_call.change_stream(
                chat_id,
                GroupCallFileAction(audio_file)
            )
            self.active_chats[chat_id]["playing"] = True
            logger.info(f"Streaming started in chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stream in chat {chat_id}: {e}")
            return False

    async def pause_stream(self, chat_id: int) -> bool:
        try:
            await self.group_call.pause_playout(chat_id)
            self.active_chats[chat_id]["playing"] = False
            return True
        except Exception as e:
            logger.error(f"Pause failed in {chat_id}: {e}")
            return False

    async def resume_stream(self, chat_id: int) -> bool:
        try:
            await self.group_call.resume_playout(chat_id)
            self.active_chats[chat_id]["playing"] = True
            return True
        except Exception as e:
            logger.error(f"Resume failed in {chat_id}: {e}")
            return False

    async def stop_stream(self, chat_id: int) -> bool:
        return await self.leave_voice_chat(chat_id)

    # ---------- State Helpers ----------

    def is_playing(self, chat_id: int) -> bool:
        return chat_id in self.active_chats and self.active_chats[chat_id]["playing"]

    def set_current_song(self, chat_id: int, song_info: dict):
        if chat_id in self.active_chats:
            self.active_chats[chat_id]["current_song"] = song_info

    def get_current_song(self, chat_id: int):
        if chat_id in self.active_chats:
            return self.active_chats[chat_id]["current_song"]
        return None


# -------- Global instance --------

call_manager: CallManager | None = None


async def init_call_manager(app: Client) -> CallManager:
    global call_manager
    call_manager = CallManager(app)
    await call_manager.initialize()
    return call_manager
