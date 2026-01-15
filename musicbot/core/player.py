import asyncio
import os
import subprocess
import logging
from typing import Optional

from config import config
from core.calls import call_manager

logger = logging.getLogger(__name__)


class AudioManager:
    """
    Handles audio validation and FFmpeg conversion.
    Produces a PyTgCalls-compatible PCM file.
    """

    def __init__(self):
        self.download_dir = config.DOWNLOAD_DIR
        os.makedirs(self.download_dir, exist_ok=True)

    async def validate_audio_file(self, audio_file: str) -> bool:
        if not os.path.exists(audio_file):
            return False

        try:
            proc = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v", "error",
                "-show_format",
                audio_file,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    async def prepare_audio_stream(self, chat_id: int, audio_file: str) -> Optional[str]:
        """
        Convert input audio to raw PCM (s16le, 48kHz, stereo).
        Returns path to converted file.
        """
        try:
            output_file = os.path.join(
                self.download_dir,
                f"{chat_id}_stream.raw"
            )

            cmd = [
                "ffmpeg",
                "-y",
                "-i", audio_file,
                "-f", "s16le",
                "-ar", "48000",
                "-ac", "2",
                output_file
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            await proc.wait()

            if not os.path.exists(output_file):
                logger.error("FFmpeg did not produce output file")
                return None

            return output_file

        except Exception as e:
            logger.error(f"FFmpeg conversion failed: {e}")
            return None


class Player:
    """
    High-level playback controller.
    Talks to CallManager only.
    """

    def __init__(self):
        self.audio_manager = AudioManager()
        self.playing_states = {}  # chat_id -> state

    async def play_audio(self, chat_id: int, audio_file: str, song_info: dict = None) -> bool:
        try:
            if not await self.audio_manager.validate_audio_file(audio_file):
                logger.error(f"Invalid audio file: {audio_file}")
                return False

            if chat_id not in call_manager.active_chats:
                if not await call_manager.join_voice_chat(chat_id):
                    return False

            stream_file = await self.audio_manager.prepare_audio_stream(chat_id, audio_file)
            if not stream_file:
                return False

            if not await call_manager.start_stream(chat_id, stream_file):
                return False

            call_manager.set_current_song(chat_id, song_info or {})

            self.playing_states[chat_id] = {
                "is_playing": True,
                "current_track": song_info,
                "position": 0
            }

            logger.info(f"Playback started in chat {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Play failed in chat {chat_id}: {e}")
            return False

    async def pause(self, chat_id: int) -> bool:
        try:
            if await call_manager.pause_stream(chat_id):
                if chat_id in self.playing_states:
                    self.playing_states[chat_id]["is_playing"] = False
                return True
            return False
        except Exception as e:
            logger.error(f"Pause failed in {chat_id}: {e}")
            return False

    async def resume(self, chat_id: int) -> bool:
        try:
            if await call_manager.resume_stream(chat_id):
                if chat_id in self.playing_states:
                    self.playing_states[chat_id]["is_playing"] = True
                return True
            return False
        except Exception as e:
            logger.error(f"Resume failed in {chat_id}: {e}")
            return False

    async def stop(self, chat_id: int) -> bool:
        try:
            await call_manager.leave_voice_chat(chat_id)
            self.playing_states.pop(chat_id, None)
            logger.info(f"Playback stopped in chat {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Stop failed in {chat_id}: {e}")
            return False

    async def skip(self, chat_id: int) -> bool:
        """
        Skip is equivalent to stop.
        Queue manager should handle auto-next.
        """
        return await self.stop(chat_id)

    def is_playing(self, chat_id: int) -> bool:
        return (
            chat_id in self.playing_states and
            self.playing_states[chat_id]["is_playing"]
        )

    def get_current_track(self, chat_id: int) -> Optional[dict]:
        if chat_id in self.playing_states:
            return self.playing_states[chat_id]["current_track"]
        return call_manager.get_current_song(chat_id)


# Global instance
player = Player()
