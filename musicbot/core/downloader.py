import yt_dlp
import asyncio
import os
import logging
from typing import Dict, Optional
import re

from config import config

logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self):
        self.download_dir = config.DOWNLOAD_DIR
        self.max_duration = config.MAX_AUDIO_DURATION
        self.audio_quality = config.AUDIO_QUALITY
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        
        # yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        
        # Adjust quality settings
        if self.audio_quality == "low":
            self.ydl_opts['postprocessors'][0]['preferredquality'] = '128'
        elif self.audio_quality == "medium":
            self.ydl_opts['postprocessors'][0]['preferredquality'] = '160'
        # high quality uses 192kbps by default
        
    def is_valid_url(self, url: str) -> bool:
        """Check if the URL is valid"""
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        return bool(re.match(youtube_regex, url)) or url.startswith(('http://', 'https://'))
        
    async def extract_info(self, query: str) -> Optional[Dict]:
        """Extract video information without downloading"""
        try:
            loop = asyncio.get_event_loop()
            
            def _extract():
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    if not self.is_valid_url(query):
                        query = f"ytsearch:{query}"
                    
                    info = ydl.extract_info(query, download=False)
                    
                    # Handle search results
                    if 'entries' in info:
                        if info['entries']:
                            info = info['entries'][0]
                        else:
                            return None
                    
                    # Check duration
                    duration = info.get('duration', 0)
                    if duration > self.max_duration:
                        logger.warning(f"Song duration {duration}s exceeds limit {self.max_duration}s")
                        return None
                    
                    return {
                        'id': info.get('id'),
                        'title': info.get('title'),
                        'duration': duration,
                        'uploader': info.get('uploader'),
                        'thumbnail': info.get('thumbnail'),
                        'url': info.get('webpage_url'),
                        'extractor': info.get('extractor')
                    }
            
            return await loop.run_in_executor(None, _extract)
            
        except Exception as e:
            logger.error(f"Error extracting info for '{query}': {e}")
            return None
            
    async def download_audio(self, url: str, filename: str = None) -> Optional[str]:
        """Download audio from URL and return file path"""
        try:
            if not filename:
                # Generate filename from URL
                video_info = await self.extract_info(url)
                if not video_info:
                    return None
                filename = f"{video_info['id']}.mp3"
            
            filepath = os.path.join(self.download_dir, filename)
            
            # Check if file already exists
            if os.path.exists(filepath):
                logger.info(f"Audio file already exists: {filepath}")
                return filepath
                
            # Download options with specific output
            download_opts = self.ydl_opts.copy()
            download_opts.update({
                'outtmpl': filepath.replace('.mp3', '.%(ext)s'),
            })
            
            loop = asyncio.get_event_loop()
            
            def _download():
                with yt_dlp.YoutubeDL(download_opts) as ydl:
                    ydl.download([url])
                
                # Rename file to .mp3 if needed
                if not os.path.exists(filepath):
                    # Find the actual downloaded file
                    base_path = filepath.replace('.mp3', '')
                    for ext in ['.webm', '.m4a', '.opus']:
                        temp_file = base_path + ext
                        if os.path.exists(temp_file):
                            os.rename(temp_file, filepath)
                            break
                
                return filepath if os.path.exists(filepath) else None
            
            result = await loop.run_in_executor(None, _download)
            
            if result:
                logger.info(f"Downloaded audio: {result}")
                return result
            else:
                logger.error(f"Failed to download audio from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading audio from '{url}': {e}")
            return None
            
    async def search_youtube(self, query: str, max_results: int = 5) -> list:
        """Search YouTube and return list of results"""
        try:
            search_query = f"ytsearch{max_results}:{query}"
            
            loop = asyncio.get_event_loop()
            
            def _search():
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(search_query, download=False)
                    results = []
                    
                    if 'entries' in info:
                        for entry in info['entries']:
                            if entry:  # Skip None entries
                                results.append({
                                    'id': entry.get('id'),
                                    'title': entry.get('title'),
                                    'duration': entry.get('duration', 0),
                                    'uploader': entry.get('uploader'),
                                    'thumbnail': entry.get('thumbnail'),
                                    'url': entry.get('webpage_url'),
                                    'view_count': entry.get('view_count', 0)
                                })
                    
                    return results
            
            return await loop.run_in_executor(None, _search)
            
        except Exception as e:
            logger.error(f"Error searching YouTube for '{query}': {e}")
            return []
            
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Remove old downloaded files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            removed_count = 0
            for filename in os.listdir(self.download_dir):
                filepath = os.path.join(self.download_dir, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        removed_count += 1
                        logger.debug(f"Removed old file: {filename}")
            
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old audio files")
                
        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")

# Global instance
downloader = Downloader()