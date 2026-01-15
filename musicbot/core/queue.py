import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from config import config
from .player import player
from .calls import call_manager

logger = logging.getLogger(__name__)

@dataclass
class QueueItem:
    song_info: dict
    audio_file: str
    requested_by: int
    requested_at: datetime
    message_id: Optional[int] = None

class QueueManager:
    def __init__(self):
        self.queues = {}  # chat_id -> list of QueueItem
        self.now_playing = {}  # chat_id -> QueueItem
        self.max_queue_size = config.MAX_QUEUE_SIZE
        self.auto_leave_vc = config.AUTO_LEAVE_VC
        self.auto_leave_delay = config.AUTO_LEAVE_DELAY
        
        # Auto-leave timer tasks
        self.leave_timers = {}
        
    def add_to_queue(self, chat_id: int, song_info: dict, audio_file: str, 
                     requested_by: int, message_id: Optional[int] = None) -> bool:
        """Add a song to the queue"""
        try:
            # Initialize queue for chat if not exists
            if chat_id not in self.queues:
                self.queues[chat_id] = []
            
            # Check queue size limit
            if len(self.queues[chat_id]) >= self.max_queue_size:
                logger.warning(f"Queue for chat {chat_id} is full")
                return False
                
            # Create queue item
            queue_item = QueueItem(
                song_info=song_info,
                audio_file=audio_file,
                requested_by=requested_by,
                requested_at=datetime.now(),
                message_id=message_id
            )
            
            # Add to queue
            self.queues[chat_id].append(queue_item)
            logger.info(f"Added song to queue for chat {chat_id}. Queue size: {len(self.queues[chat_id])}")
            
            # Start playing if nothing is currently playing
            if not self.is_playing(chat_id):
                asyncio.create_task(self._play_next(chat_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding to queue for chat {chat_id}: {e}")
            return False
            
    async def _play_next(self, chat_id: int):
        """Play the next song in queue"""
        try:
            if chat_id not in self.queues or not self.queues[chat_id]:
                # Queue is empty, handle auto-leave
                await self._handle_empty_queue(chat_id)
                return
                
            # Get next song
            next_item = self.queues[chat_id].pop(0)
            self.now_playing[chat_id] = next_item
            
            # Play the song
            success = await player.play_audio(
                chat_id=chat_id,
                audio_file=next_item.audio_file,
                song_info=next_item.song_info
            )
            
            if not success:
                logger.error(f"Failed to play song in chat {chat_id}")
                # Try next song
                await self._play_next(chat_id)
            else:
                logger.info(f"Playing {next_item.song_info.get('title')} in chat {chat_id}")
                
        except Exception as e:
            logger.error(f"Error playing next song in chat {chat_id}: {e}")
            
    async def _handle_empty_queue(self, chat_id: int):
        """Handle when queue becomes empty"""
        try:
            # Cancel any existing leave timer
            if chat_id in self.leave_timers:
                self.leave_timers[chat_id].cancel()
                del self.leave_timers[chat_id]
                
            if self.auto_leave_vc:
                # Schedule auto-leave
                async def leave_after_delay():
                    await asyncio.sleep(self.auto_leave_delay)
                    if not self.is_playing(chat_id) and self.get_queue_length(chat_id) == 0:
                        await player.stop(chat_id)
                        logger.info(f"Auto-left voice chat {chat_id} due to inactivity")
                
                self.leave_timers[chat_id] = asyncio.create_task(leave_after_delay())
            else:
                # Just stop playing, don't leave VC
                await player.stop(chat_id)
                
        except Exception as e:
            logger.error(f"Error handling empty queue for chat {chat_id}: {e}")
            
    async def skip_current(self, chat_id: int) -> bool:
        """Skip the current playing song"""
        try:
            if chat_id in self.now_playing:
                # Stop current playback
                await player.skip(chat_id)
                
                # Clear now playing
                del self.now_playing[chat_id]
                
                # Play next song
                await self._play_next(chat_id)
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error skipping current song in chat {chat_id}: {e}")
            return False
            
    async def clear_queue(self, chat_id: int) -> int:
        """Clear the entire queue and return number of cleared items"""
        try:
            if chat_id in self.queues:
                cleared_count = len(self.queues[chat_id])
                self.queues[chat_id].clear()
                logger.info(f"Cleared {cleared_count} items from queue in chat {chat_id}")
                return cleared_count
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing queue for chat {chat_id}: {e}")
            return 0
            
    async def remove_from_queue(self, chat_id: int, index: int) -> bool:
        """Remove a specific item from queue by index"""
        try:
            if chat_id in self.queues and 0 <= index < len(self.queues[chat_id]):
                removed_item = self.queues[chat_id].pop(index)
                logger.info(f"Removed {removed_item.song_info.get('title')} from queue in chat {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing item from queue in chat {chat_id}: {e}")
            return False
            
    def get_queue(self, chat_id: int) -> List[QueueItem]:
        """Get the current queue for a chat"""
        return self.queues.get(chat_id, [])
        
    def get_now_playing(self, chat_id: int) -> Optional[QueueItem]:
        """Get currently playing item"""
        return self.now_playing.get(chat_id)
        
    def get_queue_length(self, chat_id: int) -> int:
        """Get queue length"""
        return len(self.queues.get(chat_id, []))
        
    def is_playing(self, chat_id: int) -> bool:
        """Check if something is currently playing"""
        return chat_id in self.now_playing or player.is_playing(chat_id)
        
    def get_queue_info(self, chat_id: int) -> Dict:
        """Get comprehensive queue information"""
        queue = self.get_queue(chat_id)
        now_playing = self.get_now_playing(chat_id)
        
        return {
            'now_playing': {
                'title': now_playing.song_info.get('title') if now_playing else None,
                'duration': now_playing.song_info.get('duration') if now_playing else None,
                'requested_by': now_playing.requested_by if now_playing else None,
                'requested_at': now_playing.requested_at.isoformat() if now_playing else None
            } if now_playing else None,
            'queue_length': len(queue),
            'queue_items': [
                {
                    'index': i,
                    'title': item.song_info.get('title'),
                    'duration': item.song_info.get('duration'),
                    'requested_by': item.requested_by,
                    'requested_at': item.requested_at.isoformat()
                }
                for i, item in enumerate(queue)
            ],
            'is_playing': self.is_playing(chat_id)
        }
        
    async def shuffle_queue(self, chat_id: int) -> bool:
        """Shuffle the queue"""
        try:
            import random
            if chat_id in self.queues and len(self.queues[chat_id]) > 1:
                random.shuffle(self.queues[chat_id])
                logger.info(f"Shuffled queue for chat {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error shuffling queue for chat {chat_id}: {e}")
            return False
            
    async def move_queue_item(self, chat_id: int, from_index: int, to_index: int) -> bool:
        """Move a queue item from one position to another"""
        try:
            queue = self.queues.get(chat_id, [])
            if (0 <= from_index < len(queue) and 
                0 <= to_index < len(queue) and 
                from_index != to_index):
                
                item = queue.pop(from_index)
                queue.insert(to_index, item)
                logger.info(f"Moved queue item in chat {chat_id} from {from_index} to {to_index}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error moving queue item in chat {chat_id}: {e}")
            return False
            
    async def cleanup_chat(self, chat_id: int):
        """Clean up queue data for a chat"""
        try:
            if chat_id in self.queues:
                del self.queues[chat_id]
            if chat_id in self.now_playing:
                del self.now_playing[chat_id]
            if chat_id in self.leave_timers:
                self.leave_timers[chat_id].cancel()
                del self.leave_timers[chat_id]
                
            logger.info(f"Cleaned up queue data for chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up chat {chat_id}: {e}")

# Global instance
queue_manager = QueueManager()