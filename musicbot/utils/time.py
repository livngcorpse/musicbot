import re
from typing import Optional, Tuple
from datetime import datetime, timedelta

def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration"""
    if seconds < 0:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse duration string (e.g., '3:30', '2h30m', '180s') into seconds"""
    if not duration_str:
        return None
        
    duration_str = duration_str.lower().strip()
    
    # Handle HH:MM:SS or MM:SS format
    if ':' in duration_str:
        parts = duration_str.split(':')
        try:
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return None
    
    # Handle h/m/s format (e.g., '2h30m', '90s')
    total_seconds = 0
    
    # Extract hours
    hours_match = re.search(r'(\d+)h', duration_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Extract minutes
    minutes_match = re.search(r'(\d+)m', duration_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Extract seconds
    seconds_match = re.search(r'(\d+)s', duration_str)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    # If no units specified, treat as seconds
    if total_seconds == 0 and duration_str.isdigit():
        total_seconds = int(duration_str)
    
    return total_seconds if total_seconds > 0 else None

def format_time_ago(timestamp: datetime) -> str:
    """Format timestamp into 'X time ago' string"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def get_timezone_offset() -> int:
    """Get local timezone offset in seconds"""
    return datetime.now().astimezone().utcoffset().total_seconds()

def is_today(date: datetime) -> bool:
    """Check if date is today"""
    return date.date() == datetime.now().date()

def is_yesterday(date: datetime) -> bool:
    """Check if date is yesterday"""
    yesterday = datetime.now().date() - timedelta(days=1)
    return date.date() == yesterday

def format_relative_time(target_time: datetime) -> str:
    """Format time relative to now"""
    now = datetime.now()
    diff = target_time - now
    
    if diff.total_seconds() > 0:
        # Future time
        if diff.days > 0:
            return f"in {diff.days} day{'s' if diff.days > 1 else ''}"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"in {hours} hour{'s' if hours > 1 else ''}"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"in {minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "in a few seconds"
    else:
        # Past time
        return format_time_ago(target_time)

def parse_time_string(time_str: str) -> Optional[Tuple[int, int]]:
    """Parse time string like '14:30' or '2:30 PM' into (hour, minute)"""
    if not time_str:
        return None
    
    time_str = time_str.strip().upper()
    
    # Handle 24-hour format (HH:MM)
    match_24h = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
    if match_24h:
        hour, minute = int(match_24h.group(1)), int(match_24h.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)
    
    # Handle 12-hour format (H:MM AM/PM or HH:MM AM/PM)
    match_12h = re.match(r'^(\d{1,2}):(\d{2})\s*(AM|PM)$', time_str)
    if match_12h:
        hour, minute = int(match_12h.group(1)), int(match_12h.group(2))
        period = match_12h.group(3)
        
        if 1 <= hour <= 12 and 0 <= minute <= 59:
            if period == 'AM':
                if hour == 12:
                    hour = 0
            else:  # PM
                if hour != 12:
                    hour += 12
            return (hour, minute)
    
    return None

def seconds_to_human_readable(seconds: int) -> str:
    """Convert seconds to human readable format"""
    if seconds < 0:
        return "0 seconds"
    
    units = [
        (86400 * 365, "year"),
        (86400 * 30, "month"),
        (86400 * 7, "week"),
        (86400, "day"),
        (3600, "hour"),
        (60, "minute"),
        (1, "second")
    ]
    
    result = []
    for unit_seconds, unit_name in units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            seconds %= unit_seconds
            result.append(f"{count} {unit_name}{'s' if count > 1 else ''}")
    
    if not result:
        return "0 seconds"
    
    if len(result) == 1:
        return result[0]
    elif len(result) == 2:
        return f"{result[0]} and {result[1]}"
    else:
        return f"{', '.join(result[:-1])}, and {result[-1]}"

def calculate_eta(start_time: datetime, progress: float, total: float) -> Optional[str]:
    """Calculate ETA based on progress"""
    if progress <= 0 or total <= 0 or progress >= total:
        return None
    
    elapsed = datetime.now() - start_time
    elapsed_seconds = elapsed.total_seconds()
    
    # Calculate speed (units per second)
    speed = progress / elapsed_seconds if elapsed_seconds > 0 else 0
    
    if speed <= 0:
        return None
    
    # Calculate remaining time
    remaining = (total - progress) / speed
    remaining_timedelta = timedelta(seconds=int(remaining))
    
    # Format nicely
    if remaining_timedelta.days > 0:
        return f"{remaining_timedelta.days}d {remaining_timedelta.seconds // 3600}h"
    elif remaining_timedelta.seconds >= 3600:
        hours = remaining_timedelta.seconds // 3600
        minutes = (remaining_timedelta.seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    elif remaining_timedelta.seconds >= 60:
        minutes = remaining_timedelta.seconds // 60
        seconds = remaining_timedelta.seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        return f"{remaining_timedelta.seconds}s"

# Aliases for common usage
fmt_duration = format_duration
fmt_time_ago = format_time_ago
parse_time = parse_duration