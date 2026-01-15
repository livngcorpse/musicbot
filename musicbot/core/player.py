import asyncio
import subprocess
import os
import logging
from typing import Optional
import threading
from queue import Queue

from config import config
from .calls import call_manager
from .downloader import downloader

logger = logging.getLogger(__name__)

class AudioManager:
    def __init__(self):
        self.download_dir = config.DOWNLOAD_DIR
        self.current_processes = {}  # chat_id -> ffmpeg_process
        self.fifo_pipes = {}  # chat_id -> fifo_path
        
        # Create download directory
        os.makedirs(self.download_dir, exist_ok=True)
        
    async def prepare_audio_stream(self, chat_id: int, audio_file: str) -> bool:
        """Prepare audio file for streaming"""
        try:
            # Create FIFO pipe for this chat
            fifo_path = f"/tmp/musicbot_{chat_id}.fifo"
            
            if not os.path.exists(fifo_path):
                os.mkfifo(fifo_path)
            
            self.fifo_pipes[chat_id] = fifo_path
            
            # Start FFmpeg process to convert and stream audio
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', audio_file,
                '-f', 's16le',
                '-ar', '48000',
                '-ac', '2',
                '-vn',  # No video
                '-af', 'aresample=async=1',
                fifo_path
            ]
            
            # Kill existing process for this chat
            await self.stop_stream(chat_id)
            
            # Start FFmpeg process
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            self.current_processes[chat_id] = process
            
            logger.info(f"Started audio stream for chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error preparing audio stream for chat {chat_id}: {e}")
            return False
            
    async def stop_stream(self, chat_id: int):
        """Stop audio streaming for a chat"""
        try:
            # Stop FFmpeg process
            if chat_id in self.current_processes:
                process = self.current_processes[chat_id]
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                del self.current_processes[chat_id]
                
            # Clean up FIFO
            if chat_id in self.fifo_pipes:
                fifo_path = self.fifo_pipes[chat_id]
                if os.path.exists(fifo_path):
                    os.remove(fifo_path)
                del self.fifo_pipes[chat_id]
                
            logger.info(f"Stopped audio stream for chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error stopping stream for chat {chat_id}: {e}")
            
    def is_streaming(self, chat_id: int) -> bool:
        """Check if audio is currently streaming for a chat"""
        if chat_id in self.current_processes:
            process = self.current_processes[chat_id]
            return process.poll() is None
        return False
        
    async def get_audio_duration(self, audio_file: str) -> Optional[float]:
        """Get audio file duration using FFprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                audio_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
            return None
            
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return None
            
    async def validate_audio_file(self, audio_file: str) -> bool:
        """Validate that audio file exists and is playable"""
        try:
            if not os.path.exists(audio_file):
                return False
                
            # Quick validation using ffprobe
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                audio_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error validating audio file {audio_file}: {e}")
            return False

class Player:
    def __init__(self):
        self.audio_manager = AudioManager()
        self.playing_states = {}  # chat_id -> {is_playing, current_track, position}
        
    async def play_audio(self, chat_id: int, audio_file: str, song_info: dict = None) -> bool:
        """Play audio in a voice chat"""
        try:
            # Validate audio file
            if not await self.audio_manager.validate_audio_file(audio_file):
                logger.error(f"Invalid audio file: {audio_file}")
                return False
                
            # Join voice chat if not already joined
            if chat_id not in call_manager.active_chats:
                success = await call_manager.join_voice_chat(chat_id)
                if not success:
                    return False
                    
            # Start or change audio stream
            success = await call_manager.change_stream(chat_id, audio_file)
            
            if not success:
                return False
                
            # Set current song info
            call_manager.set_current_song(chat_id, song_info or {})
            
            # Mark as playing
            self.playing_states[chat_id] = {
                'is_playing': True,
                'current_track': song_info,
                'position': 0
            }
            
            if chat_id in call_manager.active_chats:
                call_manager.active_chats[chat_id]['playing'] = True
            
            logger.info(f"Started playing in chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio in chat {chat_id}: {e}")
            return False
            
    async def pause(self, chat_id: int) -> bool:
        """Pause current playback"""
        try:
            success = await call_manager.pause_stream(chat_id)
            if success and chat_id in self.playing_states:
                self.playing_states[chat_id]['is_playing'] = False
            return success
            
        except Exception as e:
            logger.error(f"Error pausing in chat {chat_id}: {e}")
            return False
            
    async def resume(self, chat_id: int) -> bool:
        """Resume paused playback"""
        try:
            success = await call_manager.resume_stream(chat_id)
            if success and chat_id in self.playing_states:
                self.playing_states[chat_id]['is_playing'] = True
            return success
            
        except Exception as e:
            logger.error(f"Error resuming in chat {chat_id}: {e}")
            return False
            
    async def stop(self, chat_id: int) -> bool:
        """Stop playback and leave voice chat"""
        try:
            # Stop audio stream
            await self.audio_manager.stop_stream(chat_id)
            
            # Leave voice chat
            success = await call_manager.leave_voice_chat(chat_id)
            
            # Clear playing state
            if chat_id in self.playing_states:
                del self.playing_states[chat_id]
                
            logger.info(f"Stopped playback in chat {chat_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error stopping in chat {chat_id}: {e}")
            return False
            
    async def skip(self, chat_id: int) -> bool:
        """Skip current track (will be handled by queue manager)"""
        try:
            # This will trigger the stream end handler
            # which should be handled by the queue system
            await self.stop(chat_id)
            return True
            
        except Exception as e:
            logger.error(f"Error skipping in chat {chat_id}: {e}")
            return False
            
    def is_playing(self, chat_id: int) -> bool:
        """Check if currently playing"""
        return (chat_id in self.playing_states and 
                self.playing_states[chat_id]['is_playing'])
                
    def get_current_track(self, chat_id: int) -> Optional[dict]:
        """Get current track information"""
        if chat_id in self.playing_states:
            return self.playing_states[chat_id]['current_track']
        return call_manager.get_current_song(chat_id)

# Global instances
audio_manager = AudioManager()
player = Player()
